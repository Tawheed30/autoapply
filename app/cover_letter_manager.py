import logging
from typing import Dict, Optional
from app.database import Database

logger = logging.getLogger(__name__)


class CoverLetterManager:
    """Manage cover letters and approval workflow."""

    def __init__(self, db: Database):
        self.db = db

    def get_cover_letter(self, job_id: int) -> Optional[Dict]:
        """Get cover letter for a job."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, job_id, company, role, cover_letter_text, approved, created_at
            FROM cover_letters
            WHERE job_id = ?
        """, (job_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def update_cover_letter(self, job_id: int, cover_letter_text: str) -> bool:
        """Update cover letter text."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE cover_letters
            SET cover_letter_text = ?
            WHERE job_id = ?
        """, (cover_letter_text, job_id))

        conn.commit()
        conn.close()

        self.db.log_activity("cover_letter_updated", f"job_id:{job_id}", cover_letter_text[:50], "success")
        logger.info(f"Updated cover letter for job {job_id}")
        return True

    def approve_cover_letter(self, job_id: int) -> tuple:
        """Approve cover letter for a job. Returns (success, message, word_count)."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE cover_letters
            SET approved = 1
            WHERE job_id = ?
        """, (job_id,))

        # Get the cover letter to count words
        cursor.execute("""
            SELECT cover_letter_text
            FROM cover_letters
            WHERE job_id = ?
        """, (job_id,))

        row = cursor.fetchone()
        conn.commit()
        conn.close()

        word_count = len(row["cover_letter_text"].split()) if row else 0

        self.db.log_activity("cover_letter_approved", f"job_id:{job_id}", f"Word count: {word_count}", "success")
        logger.info(f"Approved cover letter for job {job_id} ({word_count} words)")

        return True, "Cover letter approved", word_count

    def is_approved(self, job_id: int) -> bool:
        """Check if cover letter is approved."""
        letter = self.get_cover_letter(job_id)
        return letter["approved"] == 1 if letter else False
