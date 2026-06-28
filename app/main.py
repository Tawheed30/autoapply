import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import json
from typing import Set

from app.config import Config
from app.database import Database
from app.logging_setup import setup_logging
from app.job_queue import JobQueueManager
from app.tracker import TrackerManager
from app.background_worker import BackgroundWorker
from app.question_answer_manager import QuestionAnswerManager
from app.cover_letter_manager import CoverLetterManager

# Load config
config = Config()

# Set up logging
setup_logging(
    log_file=config.get("logging.file"),
    level=config.get("logging.level", "INFO"),
    max_bytes=config.get("logging.max_bytes", 10485760),
    backup_count=config.get("logging.backup_count", 5)
)

logger = logging.getLogger(__name__)

# Initialize database
db = Database(config.get("data.db_path"))

# Initialize managers
queue_manager = JobQueueManager(db)
tracker_manager = TrackerManager(db)

# Initialize scheduler
scheduler = BackgroundScheduler(daemon=True)
scheduler_running = False

# WebSocket connections for real-time updates
active_connections: Set[WebSocket] = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler_running
    logger.info("Application startup")
    db.log_activity("app_startup", "main", "FastAPI app started")

    # Start the background scheduler
    try:
        interval_minutes = config.get("background.job_queue_interval_minutes", 30)
        worker = BackgroundWorker(db, config, config.get_api_key())
        scheduler.add_job(
            worker.process_queued_jobs,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='process_queued_jobs',
            name='Process Queued Jobs',
            replace_existing=True,
        )
        scheduler.start()
        scheduler_running = True
        logger.info(f"Background scheduler started (interval: {interval_minutes} minutes)")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

    yield

    logger.info("Application shutdown")
    if scheduler_running:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")
    db.log_activity("app_shutdown", "main", "FastAPI app stopped")


app = FastAPI(title="Job Application Accelerator", lifespan=lifespan)


# Mount static files if directory exists
static_dir = "static"
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


class HealthResponse(BaseModel):
    status: str
    version: str
    api_key_present: bool
    scheduler_running: bool


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        api_key_present=bool(config.get_api_key()),
        scheduler_running=scheduler_running
    )


class JobQueueRequest(BaseModel):
    jd_text: str = None
    jd_url: str = None
    company: str = None
    role: str = None
    location: str = None


class AnswerUpdateRequest(BaseModel):
    answer: str


class UseBankAnswerRequest(BaseModel):
    answer: str
    bank_id: int


class CoverLetterUpdateRequest(BaseModel):
    cover_letter_text: str


@app.post("/api/webhook/submit-jd")
def submit_jd(request: JobQueueRequest, x_api_token: str = Header(None)):
    """Webhook endpoint to submit a job description."""
    webhook_token = config.get_webhook_token()
    if not webhook_token or x_api_token != webhook_token:
        logger.warning(f"Invalid webhook token attempt: {x_api_token}")
        raise HTTPException(status_code=403, detail="Invalid API token")

    if not request.jd_text and not request.jd_url:
        raise HTTPException(status_code=400, detail="Either jd_text or jd_url is required")

    job_id = queue_manager.add_job(
        jd_text=request.jd_text,
        jd_url=request.jd_url,
        company=request.company,
        role=request.role,
        location=request.location
    )

    logger.info(f"Job {job_id} queued via webhook")
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Job successfully queued for processing"
    }


@app.post("/api/job-queue/submit")
def submit_jd_dashboard(request: JobQueueRequest):
    """Dashboard endpoint to submit a job description."""
    if not request.jd_text and not request.jd_url:
        raise HTTPException(status_code=400, detail="Either jd_text or jd_url is required")

    job_id = queue_manager.add_job(
        jd_text=request.jd_text,
        jd_url=request.jd_url,
        company=request.company,
        role=request.role,
        location=request.location
    )

    logger.info(f"Job {job_id} queued via dashboard")
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Job successfully queued for processing"
    }


@app.get("/api/job-queue/all")
def get_all_jobs():
    """Get all jobs in the queue."""
    jobs = queue_manager.get_all_jobs()
    return {"jobs": jobs, "count": len(jobs)}


@app.get("/api/job-queue/status/{status}")
def get_jobs_by_status(status: str):
    """Get jobs filtered by status."""
    jobs = queue_manager.get_jobs_by_status(status)
    return {"jobs": jobs, "count": len(jobs), "status": status}


@app.post("/api/worker/trigger")
def trigger_worker():
    """Manually trigger the background worker."""
    try:
        worker = BackgroundWorker(db, config, config.get_api_key())
        worker.process_queued_jobs()
        return {"message": "Worker triggered successfully", "status": "success"}
    except Exception as e:
        logger.error(f"Error triggering worker: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Worker error: {str(e)}")


@app.get("/api/worker/status")
def get_worker_status():
    """Get background worker status."""
    return {
        "scheduler_running": scheduler_running,
        "scheduler_jobs": [{"id": job.id, "name": job.name, "next_run_time": str(job.next_run_time)} for job in scheduler.get_jobs()],
    }


@app.get("/api/tracker/all")
def get_all_tracker_entries():
    """Get all tracker entries."""
    entries = tracker_manager.get_all_entries()
    return {"entries": entries, "count": len(entries)}


@app.get("/api/tracker/status/{status}")
def get_tracker_by_status(status: str):
    """Get tracker entries filtered by status."""
    entries = tracker_manager.get_entries_by_status(status)
    return {"entries": entries, "count": len(entries), "status": status}


# Phase 4: Question & Answer Endpoints
@app.get("/api/questions/{job_id}")
def get_questions(job_id: int):
    """Get all questions and answers for a job."""
    try:
        qa_manager = QuestionAnswerManager(db)
        questions = qa_manager.get_questions_for_job(job_id)
        return {"job_id": job_id, "questions": questions, "count": len(questions)}
    except Exception as e:
        logger.error(f"Error getting questions for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/questions/{job_id}/{question_id}")
def update_answer(job_id: int, question_id: int, request: AnswerUpdateRequest):
    """Update an answer for a question."""
    try:
        qa_manager = QuestionAnswerManager(db)
        qa_manager.update_answer(question_id, request.answer)
        logger.info(f"Updated answer for question {question_id}")
        return {"message": "Answer updated", "question_id": question_id, "status": "success"}
    except Exception as e:
        logger.error(f"Error updating answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/questions/{job_id}/{question_id}/use-bank-answer")
def use_bank_answer(job_id: int, question_id: int, request: UseBankAnswerRequest):
    """Replace an answer with a bank answer."""
    try:
        qa_manager = QuestionAnswerManager(db)
        qa_manager.use_bank_answer(question_id, request.answer, request.bank_id)
        logger.info(f"Used bank answer {request.bank_id} for question {question_id}")
        return {"message": "Bank answer used", "question_id": question_id, "status": "success"}
    except Exception as e:
        logger.error(f"Error using bank answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/questions/{job_id}/approve-all")
def approve_all_answers(job_id: int):
    """Approve all answers for a job with validation."""
    try:
        qa_manager = QuestionAnswerManager(db)
        success, message, tracker_id = qa_manager.approve_all_answers(job_id)

        if not success:
            logger.warning(f"Failed to approve answers for job {job_id}: {message}")
            return JSONResponse(
                status_code=400,
                content={"status": "validation_error", "message": message, "job_id": job_id}
            )

        logger.info(f"Approved all answers for job {job_id}")
        return {"message": message, "job_id": job_id, "tracker_id": tracker_id, "status": "success"}
    except Exception as e:
        logger.error(f"Error approving answers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Phase 4: Cover Letter Endpoints
@app.get("/api/cover-letters/{job_id}")
def get_cover_letter(job_id: int):
    """Get cover letter for a job."""
    try:
        cl_manager = CoverLetterManager(db)
        letter = cl_manager.get_cover_letter(job_id)
        if not letter:
            return {"job_id": job_id, "cover_letter": None, "status": "not_found"}
        return {"job_id": job_id, "cover_letter": letter, "status": "success"}
    except Exception as e:
        logger.error(f"Error getting cover letter for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cover-letters/{job_id}")
def update_cover_letter(job_id: int, request: CoverLetterUpdateRequest):
    """Update cover letter for a job."""
    try:
        cl_manager = CoverLetterManager(db)
        cl_manager.update_cover_letter(job_id, request.cover_letter_text)
        logger.info(f"Updated cover letter for job {job_id}")
        return {"message": "Cover letter updated", "job_id": job_id, "status": "success"}
    except Exception as e:
        logger.error(f"Error updating cover letter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cover-letters/{job_id}/approve")
def approve_cover_letter(job_id: int):
    """Approve cover letter for a job."""
    try:
        cl_manager = CoverLetterManager(db)
        success, message, word_count = cl_manager.approve_cover_letter(job_id)
        logger.info(f"Approved cover letter for job {job_id} ({word_count} words)")
        return {
            "message": message,
            "job_id": job_id,
            "word_count": word_count,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error approving cover letter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def dashboard():
    """Serve the dashboard homepage."""
    dashboard_path = os.path.join("static", "dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path, media_type="text/html")
    return HTMLResponse("<h1>Dashboard file not found</h1>", status_code=404)


@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"WebSocket client connected. Total clients: {len(active_connections)}")
    db.log_activity("websocket_connected", "ws_endpoint", f"Clients: {len(active_connections)}", "success")

    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            # Echo back or process client messages if needed
            logger.debug(f"WebSocket message received: {data}")
    except WebSocketDisconnect:
        active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(active_connections)}")
        db.log_activity("websocket_disconnected", "ws_endpoint", f"Clients: {len(active_connections)}", "success")
    except Exception as e:
        active_connections.discard(websocket)
        logger.error(f"WebSocket error: {e}")
        db.log_activity("websocket_error", "ws_endpoint", str(e), "error")


async def broadcast_update(event: str, job_id: int, data: dict = None):
    """Broadcast update to all connected WebSocket clients."""
    payload = {
        "event": event,
        "job_id": job_id,
        "data": data or {}
    }
    message = json.dumps(payload)

    disconnected = set()
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            disconnected.add(connection)

    # Clean up disconnected clients
    for connection in disconnected:
        active_connections.discard(connection)

    logger.info(f"Broadcast '{event}' to {len(active_connections)} clients for job {job_id}")
    db.log_activity(f"broadcast_{event}", f"job_id:{job_id}", f"Clients: {len(active_connections)}", "success")


# Old HTML placeholder (can be removed later)
def old_dashboard_html():
    """Old inline HTML dashboard (replaced by static file)."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Job Application Accelerator</title>
        <meta name="theme-color" content="#2563eb">
        <meta name="description" content="Accelerate your job application process">
        <link rel="manifest" href="/static/manifest.json">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f9fafb;
                color: #1f2937;
            }
            .navbar {
                background: white;
                border-bottom: 1px solid #e5e7eb;
                padding: 1rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .navbar h1 {
                font-size: 1.5rem;
                margin: 0;
            }
            .nav-links {
                display: flex;
                gap: 1rem;
                list-style: none;
            }
            .nav-links a {
                color: #2563eb;
                text-decoration: none;
                cursor: pointer;
                padding: 0.5rem 1rem;
                border-radius: 4px;
            }
            .nav-links a:hover {
                background: #f0f4ff;
            }
            .nav-links a.active {
                background: #dbeafe;
                font-weight: 600;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem 1rem;
            }
            .tab-content {
                display: none;
            }
            .tab-content.active {
                display: block;
            }
            .form-group {
                margin-bottom: 1rem;
            }
            label {
                display: block;
                margin-bottom: 0.5rem;
                font-weight: 500;
                color: #374151;
            }
            input, textarea {
                width: 100%;
                padding: 0.75rem;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-family: inherit;
                font-size: 1rem;
            }
            textarea {
                min-height: 150px;
                resize: vertical;
            }
            button {
                background: #2563eb;
                color: white;
                padding: 0.75rem 1.5rem;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
                font-size: 1rem;
            }
            button:hover {
                background: #1d4ed8;
            }
            button:disabled {
                background: #9ca3af;
                cursor: not-allowed;
            }
            .status-badge {
                display: inline-block;
                padding: 0.25rem 0.75rem;
                border-radius: 12px;
                font-size: 0.875rem;
                font-weight: 600;
            }
            .status-queued {
                background: #fef3c7;
                color: #92400e;
            }
            .status-staged {
                background: #dbeafe;
                color: #1e40af;
            }
            .status-failed {
                background: #fee2e2;
                color: #991b1b;
            }
            .status-applied {
                background: #dcfce7;
                color: #166534;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 1rem;
            }
            th, td {
                text-align: left;
                padding: 0.75rem;
                border-bottom: 1px solid #e5e7eb;
            }
            th {
                background: #f3f4f6;
                font-weight: 600;
            }
            .message {
                padding: 1rem;
                border-radius: 6px;
                margin-bottom: 1rem;
            }
            .message.success {
                background: #dcfce7;
                color: #166534;
                border: 1px solid #86efac;
            }
            .message.error {
                background: #fee2e2;
                color: #991b1b;
                border: 1px solid #fca5a5;
            }
            @media (max-width: 640px) {
                .navbar {
                    flex-direction: column;
                    gap: 1rem;
                }
                table {
                    font-size: 0.875rem;
                }
                th, td {
                    padding: 0.5rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="navbar">
            <h1>⚡ Job Accelerator</h1>
            <ul class="nav-links">
                <a href="#" class="nav-link active" onclick="showTab('submit')">Submit</a>
                <a href="#" class="nav-link" onclick="showTab('queue')">Queue</a>
                <a href="#" class="nav-link" onclick="showTab('tracker')">Tracker</a>
                <a href="#" class="nav-link" onclick="showTab('status')">Status</a>
            </ul>
        </div>

        <div class="container">
            <!-- Submit Tab -->
            <div id="submit" class="tab-content active">
                <h2>Submit Job Description</h2>
                <form onsubmit="submitJob(event)">
                    <div class="form-group">
                        <label for="jd_text">Job Description (paste text)</label>
                        <textarea id="jd_text" placeholder="Paste the job description here..."></textarea>
                    </div>
                    <div class="form-group">
                        <label for="company">Company (optional)</label>
                        <input type="text" id="company" placeholder="e.g., Google, Microsoft">
                    </div>
                    <div class="form-group">
                        <label for="role">Role (optional)</label>
                        <input type="text" id="role" placeholder="e.g., Senior Software Engineer">
                    </div>
                    <div class="form-group">
                        <label for="location">Location (optional)</label>
                        <input type="text" id="location" placeholder="e.g., San Francisco, CA">
                    </div>
                    <button type="submit">Submit & Queue</button>
                </form>
                <div id="submit-message"></div>
            </div>

            <!-- Job Queue Tab -->
            <div id="queue" class="tab-content">
                <h2>Job Queue</h2>
                <button onclick="loadJobs()">Refresh</button>
                <button onclick="triggerWorker()">Trigger Worker</button>
                <div id="queue-list"></div>
            </div>

            <!-- Tracker Tab -->
            <div id="tracker" class="tab-content">
                <h2>Application Tracker</h2>
                <button onclick="loadTracker()">Refresh</button>
                <div id="tracker-list"></div>
            </div>

            <!-- Status Tab -->
            <div id="status" class="tab-content">
                <h2>System Status</h2>
                <div id="status-info"></div>
            </div>
        </div>

        <script>
            function showTab(tabName) {
                // Hide all tabs
                document.querySelectorAll('.tab-content').forEach(tab => {
                    tab.classList.remove('active');
                });
                // Show selected tab
                document.getElementById(tabName).classList.add('active');
                // Update nav links
                document.querySelectorAll('.nav-link').forEach(link => {
                    link.classList.remove('active');
                });
                event.target.classList.add('active');

                // Load data for the tab
                if (tabName === 'queue') loadJobs();
                if (tabName === 'tracker') loadTracker();
                if (tabName === 'status') loadStatus();
            }

            async function submitJob(event) {
                event.preventDefault();
                const jd_text = document.getElementById('jd_text').value;
                const company = document.getElementById('company').value;
                const role = document.getElementById('role').value;
                const location = document.getElementById('location').value;

                if (!jd_text) {
                    showMessage('submit-message', 'Please enter a job description', 'error');
                    return;
                }

                try {
                    const response = await fetch('/api/job-queue/submit', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ jd_text, company, role, location })
                    });

                    const data = await response.json();
                    if (response.ok) {
                        showMessage('submit-message', `Job ${data.job_id} queued successfully!`, 'success');
                        event.target.reset();
                    } else {
                        showMessage('submit-message', data.detail || 'Error submitting job', 'error');
                    }
                } catch (error) {
                    showMessage('submit-message', `Error: ${error.message}`, 'error');
                }
            }

            async function loadJobs() {
                try {
                    const response = await fetch('/api/job-queue/all');
                    const data = await response.json();

                    let html = '<table><thead><tr><th>ID</th><th>Company</th><th>Role</th><th>Status</th><th>Created</th></tr></thead><tbody>';
                    data.jobs.forEach(job => {
                        const status = job.status || 'unknown';
                        const created = new Date(job.created_at).toLocaleDateString();
                        html += `<tr><td>${job.id}</td><td>${job.company || '-'}</td><td>${job.role || '-'}</td><td><span class="status-badge status-${status}">${status}</span></td><td>${created}</td></tr>`;
                    });
                    html += '</tbody></table>';
                    document.getElementById('queue-list').innerHTML = html;
                } catch (error) {
                    document.getElementById('queue-list').innerHTML = `<p style="color: red;">Error loading jobs: ${error.message}</p>`;
                }
            }

            async function loadTracker() {
                try {
                    const response = await fetch('/api/tracker/all');
                    const data = await response.json();

                    let html = '<table><thead><tr><th>Company</th><th>Role</th><th>Status</th><th>Location</th><th>Created</th></tr></thead><tbody>';
                    data.entries.forEach(entry => {
                        const status = entry.status || 'unknown';
                        const created = new Date(entry.created_at).toLocaleDateString();
                        html += `<tr><td>${entry.company}</td><td>${entry.role}</td><td><span class="status-badge status-${status}">${status}</span></td><td>${entry.location || '-'}</td><td>${created}</td></tr>`;
                    });
                    html += '</tbody></table>';
                    document.getElementById('tracker-list').innerHTML = html;
                } catch (error) {
                    document.getElementById('tracker-list').innerHTML = `<p style="color: red;">Error loading tracker: ${error.message}</p>`;
                }
            }

            async function loadStatus() {
                try {
                    const health = await fetch('/health').then(r => r.json());
                    const worker = await fetch('/api/worker/status').then(r => r.json());

                    let html = `<div>
                        <p><strong>API Key Present:</strong> ${health.api_key_present ? '✓' : '✗'}</p>
                        <p><strong>Scheduler Running:</strong> ${health.scheduler_running ? '✓' : '✗'}</p>
                        <p><strong>Scheduler Jobs:</strong> ${worker.scheduler_jobs.length}</p>
                    </div>`;

                    if (worker.scheduler_jobs.length > 0) {
                        html += '<h3>Scheduled Jobs</h3><ul>';
                        worker.scheduler_jobs.forEach(job => {
                            html += `<li>${job.name} (Next: ${new Date(job.next_run_time).toLocaleString()})</li>`;
                        });
                        html += '</ul>';
                    }

                    document.getElementById('status-info').innerHTML = html;
                } catch (error) {
                    document.getElementById('status-info').innerHTML = `<p style="color: red;">Error loading status: ${error.message}</p>`;
                }
            }

            async function triggerWorker() {
                try {
                    const response = await fetch('/api/worker/trigger', { method: 'POST' });
                    const data = await response.json();
                    if (response.ok) {
                        showMessage('queue-list', 'Worker triggered! Processing jobs...', 'success');
                        setTimeout(loadJobs, 2000);
                    } else {
                        showMessage('queue-list', `Error: ${data.detail}`, 'error');
                    }
                } catch (error) {
                    showMessage('queue-list', `Error: ${error.message}`, 'error');
                }
            }

            function showMessage(elementId, message, type) {
                const element = document.getElementById(elementId);
                if (!element) return;
                element.innerHTML = `<div class="message ${type}">${message}</div>`;
                setTimeout(() => { element.innerHTML = ''; }, 5000);
            }
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    port = config.get("app.port", 8787)
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
