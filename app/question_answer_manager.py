import logging
from typing import Dict, List, Optional
from app.database import Database
from app.tracker import TrackerManager

logger = logging.getLogger(__name__)


class QuestionAnswerManager:
    """Manage question answers and approval workflow."""

    def __init__(self, db: Database):
        self.db = db
        self.tracker = TrackerManager(db)

    def get_questions_for_job(self, job_id: int) -> List[Dict]:
        """Get all questions for a job."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, job_id, question, answer, question_type, confidence,
                   source_bullets, flagged, region_hint, approved
            FROM question_answers
            WHERE job_id = ?
            ORDER BY id
        """, (job_id,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_answer(self, question_id: int, answer_text: str) -> bool:
        """Update an answer."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE question_answers
            SET answer = ?
            WHERE id = ?
        """, (answer_text, question_id))

        conn.commit()
        conn.close()

        self.db.log_activity("answer_updated", f"question_id:{question_id}", answer_text[:50], "success")
        logger.info(f"Updated answer for question {question_id}")
        return True

    def use_bank_answer(self, question_id: int, answer_text: str, bank_id: int) -> bool:
        """Replace drafted answer with a bank answer."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE question_answers
            SET answer = ?
            WHERE id = ?
        """, (answer_text, question_id))

        # Increment usage in question_bank
        cursor.execute("""
            UPDATE question_bank
            SET used_count = used_count + 1
            WHERE id = ?
        """, (bank_id,))

        conn.commit()
        conn.close()

        self.db.log_activity("bank_answer_used", f"question_id:{question_id}, bank_id:{bank_id}", answer_text[:50], "success")
        logger.info(f"Used bank answer {bank_id} for question {question_id}")
        return True

    def approve_all_answers(self, job_id: int) -> tuple:
        """Approve all answers for a job. Returns (success, message, tracker_id)."""
        # Check if there are any flagged questions with null answers
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) as count
            FROM question_answers
            WHERE job_id = ? AND flagged = 1 AND answer IS NULL
        """, (job_id,))

        unfilled_flagged = cursor.fetchone()["count"]

        if unfilled_flagged > 0:
            conn.close()
            logger.warning(f"Cannot approve job {job_id}: {unfilled_flagged} flagged questions have no answer")
            return False, f"You must answer all {unfilled_flagged} flagged questions before approving", None

        # Approve all answers for this job
        cursor.execute("""
            UPDATE question_answers
            SET approved = 1
            WHERE job_id = ?
        """, (job_id,))

        # Get the job details to find tracker entry
        cursor.execute("""
            SELECT company, role
            FROM job_queue
            WHERE id = ?
        """, (job_id,))

        job = cursor.fetchone()
        conn.commit()
        conn.close()

        # Find and update tracker entry
        tracker = TrackerManager(self.db)
        from app.job_queue import JobQueueManager
        jq = JobQueueManager(self.db)
        jobs = jq.get_all_jobs()

        tracker_entry = None
        for entry in tracker.get_all_entries():
            if (entry.get("company") == job["company"] and
                entry.get("role") == job["role"] and
                entry.get("status") == "staged"):
                tracker_entry = entry
                break

        self.db.log_activity("answers_approved", f"job_id:{job_id}", f"All answers approved", "success")
        logger.info(f"Approved all answers for job {job_id}")

        return True, "All answers approved", tracker_entry["id"] if tracker_entry else None
