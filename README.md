# Job Application Accelerator

An AI-powered tool that accelerates your job application process by analyzing job descriptions, tailoring your resume, and drafting application answers and cover letters.

## Features

- **JD Analysis** — Extract key skills, requirements, and ATS keywords from job postings
- **Resume Tailoring** — Intelligently reword your resume to match job descriptions while preserving formatting
- **Application Drafting** — Generate answers to common questions and tailored cover letters
- **Mobile Dashboard** — Review and approve applications from your phone with real-time updates
- **Background Processing** — Process job submissions 24/7 via webhook or background worker
- **Experience Bank** — Maintain a structured library of your genuine skills and achievements
- **Activity Tracking** — Monitor every step with a detailed activity log
- **Cost Tracking** — Real-time API usage and cost monitoring

## Tech Stack

- **Backend:** FastAPI + Python 3.11+
- **Database:** SQLite (activity log, job queue, tracker, experience bank)
- **AI:** Anthropic Claude API (configurable models for cost optimization)
- **Resume Handling:** `python-docx` (layout-preserving edits)
- **Background Jobs:** APScheduler + WebSocket (real-time mobile updates)
- **Mobile:** PWA with ServiceWorker caching, responsive design
- **Testing:** pytest

## Quick Start

### 1. Clone and Setup

```bash
git clone <repo-url>
cd Job-Application-Accelerator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
# Edit config.yaml if needed (optional — defaults work for most setups)
```

### 3. Run Locally

```bash
python app.py
# or: python -m uvicorn app.main:app --reload
```

Open `http://localhost:8787` in your browser.

### 4. Upload Your Master Resume

- Access the dashboard and upload your master resume (`.docx` file)
- The tool extracts your contact info and creates an experience bank from it

### 5. Submit a Job Description

- Paste a JD in the dashboard or use the webhook to queue one
- The background worker processes it (tailors resume, drafts answers)
- Review, edit, and approve on the dashboard

## Webhook Integration

Submit jobs programmatically:

```bash
curl -X POST http://localhost:8787/api/webhook/submit-jd \
  -H "X-API-Token: YOUR_WEBHOOK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jd_text": "Job description here...",
    "company": "Acme Corp",
    "role": "Software Engineer",
    "location": "Remote"
  }'
```

Set `YOUR_WEBHOOK_TOKEN` in `.env` (any random string you choose).

## Enable Background Daemon (macOS)

```bash
mkdir -p ~/.job-accelerator
cp launchagent/com.accelerator.job-application.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.accelerator.job-application.plist
```

## Enable Background Daemon (Linux)

```bash
mkdir -p ~/.config/systemd/user/
cp systemd/job-accelerator.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable job-accelerator
systemctl --user start job-accelerator
```

## Database Schema

The tool uses SQLite with these main tables:

- **activity_log** — Timestamped log of every action
- **job_queue** — Submitted JDs awaiting processing
- **contact_info** — Extracted from active resume
- **resume_versions** — History of uploaded resumes
- **tracker** — Application tracking (company, role, status, etc.)
- **experience_bank** — Structured repository of your genuine skills and achievements

## Project Structure

```
.
├── app/
│   ├── main.py              # FastAPI app + endpoints
│   ├── database.py          # SQLite schema + operations
│   ├── config.py            # Config loading (.yaml + .env)
│   └── logging_setup.py     # Logging configuration
├── data/                    # Data directory (created at runtime)
│   ├── accelerator.db       # SQLite database
│   ├── resumes/             # Uploaded master resumes
│   ├── tailored/            # Tailored resumes (outputs)
│   └── accelerator.log      # Application log
├── static/                  # CSS, JS, manifest.json
├── templates/               # HTML templates (if needed)
├── tests/                   # pytest suite
├── config.yaml              # Configuration
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
└── BUILD_LOG.md            # Phase audit reports
```

## Configuration

Edit `config.yaml` to customize:

- **Port:** `app.port` (default: 8787)
- **Data directory:** `data.base_dir` (default: `./data`)
- **API models:** `anthropic.models` (with cost-optimized defaults)
- **Background job interval:** `background.job_queue_interval_minutes`
- **Region-aware flags:** Customize sensitive question detection per region

Override with environment variables:
```bash
export APP_PORT=9000
export DATA_BASE_DIR=~/my-accelerator-data
```

## Cost Discipline

This tool is designed to minimize API costs:

- **Bulk operations** (routine answer drafting) → `claude-haiku-4-5-20251001` (cheapest)
- **Quality operations** (resume tailoring, cover letters) → `claude-sonnet-4-6`
- **Optional:** `claude-opus-4-8` (user-selectable in dashboard)
- **Local operations:** Keyword extraction, ATS scoring, activity logging, all analytics

The dashboard shows real-time token usage and estimated costs.

## Hard Rules

1. **No fabrication** — Never add fake experience or keywords; tailor only genuine content
2. **Preserve layout** — Only text changes; formatting, fonts, spacing remain identical
3. **Human-in-the-loop** — Tool prepares; you review and submit
4. **No auto-submit** — Never logs into or auto-submits on LinkedIn, Indeed, Naukri, etc.
5. **Sensitive questions** — Work authorization, visa, salary left for you to answer
6. **Webhook auth** — All submissions require valid `X-API-Token` header

## Testing

```bash
pytest
pytest -v                    # Verbose
pytest --cov               # With coverage report
```

## Troubleshooting

**API key not found:**
```bash
# Ensure .env exists and contains ANTHROPIC_API_KEY
cat .env | grep ANTHROPIC_API_KEY
```

**Database not initializing:**
```bash
# Check data directory permissions
ls -la data/
```

**Background worker not running:**
```bash
# Check logs
tail -f data/accelerator.log
```

**Port already in use:**
```bash
# Change port in config.yaml or via environment variable
export APP_PORT=9000
```

## Support

For issues or feedback, please open an issue on the project repository.

## License

MIT License (see LICENSE file)

## Contact

**Application email:** mohammedtawheed9317@outlook.com

---

**Build Status:** Phase 0 Scaffold Complete
