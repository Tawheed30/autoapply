import logging
import json
from datetime import datetime
from typing import Dict, List, Optional
from app.database import Database

logger = logging.getLogger(__name__)


class JobQueueManager:
    def __init__(self, db: Database):
        self.db = db

    def add_job(
        self,
        jd_text: Optional[str] = None,
        jd_url: Optional[str] = None,
        company: Optional[str] = None,
        role: Optional[str] = None,
        location: Optional[str] = None,
    ) -> int:
        """Add a new job to the queue with status='queued'."""
        if not jd_text and not jd_url:
            raise ValueError("Either jd_text or jd_url is required")

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO job_queue (jd_text, jd_url, company, role, location, status)
            VALUES (?, ?, ?, ?, ?, 'queued')
        """, (jd_text, jd_url, company, role, location))

        job_id = cursor.lastrowid
        conn.commit()
        conn.close()

        self.db.log_activity(
            "job_queued",
            f"job_id:{job_id}",
            f"company:{company}, role:{role}",
            "success"
        )

        logger.info(f"Job {job_id} queued: {company} - {role}")
        return job_id

    def get_queued_jobs(self) -> List[Dict]:
        """Get all jobs with status='queued'."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, jd_text, jd_url, company, role, location, created_at
            FROM job_queue
            WHERE status = 'queued'
            ORDER BY created_at ASC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_job_status(
        self,
        job_id: int,
        status: str,
        result: Optional[Dict] = None,
        error_message: Optional[str] = None,
    ):
        """Update job status and optionally store result or error."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        result_json = json.dumps(result) if result else None

        cursor.execute("""
            UPDATE job_queue
            SET status = ?, processed_at = ?, result = ?, error_message = ?
            WHERE id = ?
        """, (status, datetime.utcnow().isoformat(), result_json, error_message, job_id))

        conn.commit()
        conn.close()

        logger.info(f"Job {job_id} updated to status={status}")

    def get_job(self, job_id: int) -> Optional[Dict]:
        """Get a single job by ID."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, jd_text, jd_url, company, role, location, status, created_at, processed_at, result, error_message
            FROM job_queue
            WHERE id = ?
        """, (job_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_jobs_by_status(self, status: str) -> List[Dict]:
        """Get all jobs with a specific status."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, jd_text, jd_url, company, role, location, status, created_at, processed_at, error_message
            FROM job_queue
            WHERE status = ?
            ORDER BY created_at DESC
        """, (status,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_all_jobs(self) -> List[Dict]:
        """Get all jobs."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, jd_text, jd_url, company, role, location, status, created_at, processed_at, error_message
            FROM job_queue
            ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
