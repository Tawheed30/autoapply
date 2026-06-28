import logging
from typing import List, Dict, Optional
from app.database import Database

logger = logging.getLogger(__name__)


class QuestionBank:
    """Manage approved questions and answers for reuse."""

    def __init__(self, db: Database):
        self.db = db

    def save_answer(self, question: str, answer: str, category: str = "general") -> int:
        """Save an approved answer to the question bank."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO question_bank (question_text, answer_text, category, approved, used_count)
                VALUES (?, ?, ?, 1, 0)
            """, (question, answer, category))

            bank_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Saved approved answer to question bank: {question[:50]}...")

            self.db.log_activity(
                "answer_approved",
                f"bank_id:{bank_id}",
                f"category:{category}",
                "success"
            )

            return bank_id

        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                # Question already exists, update it
                cursor.execute("""
                    UPDATE question_bank
                    SET answer_text = ?, approved = 1
                    WHERE question_text = ?
                """, (answer, question))
                conn.commit()
                logger.info(f"Updated existing answer in question bank: {question[:50]}...")
                return None
            else:
                logger.error(f"Error saving to question bank: {e}")
                raise
        finally:
            conn.close()

    def get_approved_answers(self) -> List[Dict]:
        """Get all approved answers from the question bank."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, question_text, answer_text, category, used_count, approved
            FROM question_bank
            WHERE approved = 1
            ORDER BY used_count DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def find_similar_questions(self, question_text: str, threshold: float = 0.6) -> List[Dict]:
        """Find similar approved questions in the bank."""
        all_approved = self.get_approved_answers()

        # Simple similarity check: word overlap
        question_words = set(question_text.lower().split())
        similar = []

        for entry in all_approved:
            bank_question_words = set(entry["question_text"].lower().split())
            overlap = len(question_words & bank_question_words)
            total = len(question_words | bank_question_words)

            if total > 0:
                similarity = overlap / total
                if similarity >= threshold:
                    similar.append({**entry, "similarity": similarity})

        # Sort by similarity
        similar.sort(key=lambda x: x["similarity"], reverse=True)
        return similar[:3]  # Return top 3 matches

    def increment_used_count(self, bank_id: int):
        """Increment the used_count for an answer."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE question_bank
            SET used_count = used_count + 1
            WHERE id = ?
        """, (bank_id,))

        conn.commit()
        conn.close()

        logger.info(f"Incremented used_count for question bank entry {bank_id}")

    def get_by_id(self, bank_id: int) -> Optional[Dict]:
        """Get a specific answer from the question bank."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, question_text, answer_text, category, used_count, approved
            FROM question_bank
            WHERE id = ?
        """, (bank_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_by_category(self, category: str) -> List[Dict]:
        """Get all approved answers in a category."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, question_text, answer_text, used_count
            FROM question_bank
            WHERE category = ? AND approved = 1
            ORDER BY used_count DESC
        """, (category,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
