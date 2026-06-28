import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json

from app.config import Config
from app.database import Database
from app.logging_setup import setup_logging

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    db.log_activity("app_startup", "main", "FastAPI app started")
    yield
    logger.info("Application shutdown")
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


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        api_key_present=bool(config.get_api_key())
    )


class JobQueueRequest(BaseModel):
    jd_text: str = None
    jd_url: str = None
    company: str = None
    role: str = None
    location: str = None


@app.post("/api/webhook/submit-jd")
def submit_jd(request: JobQueueRequest, x_api_token: str = Header(None)):
    """Webhook endpoint to submit a job description."""
    webhook_token = config.get_webhook_token()
    if not webhook_token or x_api_token != webhook_token:
        logger.warning(f"Invalid webhook token attempt: {x_api_token}")
        raise HTTPException(status_code=403, detail="Invalid API token")

    if not request.jd_text and not request.jd_url:
        raise HTTPException(status_code=400, detail="Either jd_text or jd_url is required")

    job_id = db.add_job_to_queue(
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


@app.get("/", response_class=HTMLResponse)
def dashboard():
    """Serve the dashboard homepage."""
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
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 1rem;
            }
            .container {
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                padding: 2rem;
                max-width: 600px;
                width: 100%;
                text-align: center;
            }
            h1 {
                color: #1f2937;
                margin-bottom: 0.5rem;
                font-size: 2rem;
            }
            .subtitle {
                color: #6b7280;
                margin-bottom: 2rem;
                font-size: 1.1rem;
            }
            .status {
                background: #f0fdf4;
                border: 1px solid #86efac;
                color: #166534;
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 2rem;
                font-weight: 500;
            }
            .status.error {
                background: #fef2f2;
                border-color: #fca5a5;
                color: #991b1b;
            }
            .feature-list {
                text-align: left;
                margin-bottom: 2rem;
            }
            .feature-list li {
                list-style: none;
                padding: 0.75rem 0;
                border-bottom: 1px solid #f3f4f6;
                color: #374151;
            }
            .feature-list li:last-child {
                border-bottom: none;
            }
            .feature-list li:before {
                content: "✓ ";
                color: #10b981;
                font-weight: bold;
                margin-right: 0.5rem;
            }
            .footer {
                color: #9ca3af;
                font-size: 0.9rem;
            }
            @media (max-width: 480px) {
                .container {
                    padding: 1.5rem;
                }
                h1 {
                    font-size: 1.5rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Job Application Accelerator</h1>
            <p class="subtitle">Your AI-powered job application assistant</p>
            <div class="status">
                ✓ Dashboard is running
            </div>
            <div class="feature-list">
                <ul>
                    <li>Analyze job descriptions</li>
                    <li>Tailor your resume</li>
                    <li>Draft application answers</li>
                    <li>Generate cover letters</li>
                    <li>Track applications</li>
                    <li>Mobile-responsive interface</li>
                </ul>
            </div>
            <p class="footer">Phase 0 Scaffold – Coming Soon</p>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    port = config.get("app.port", 8787)
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
