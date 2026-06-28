import logging
from datetime import datetime
from typing import Dict, List, Optional
from app.database import Database

logger = logging.getLogger(__name__)


class TrackerManager:
    def __init__(self, db: Database):
        self.db = db

    def create_entry(
        self,
        company: str,
        role: str,
        location: Optional[str] = None,
        platform: Optional[str] = None,
        region: Optional[str] = None,
        jd_url: Optional[str] = None,
        status: str = "staged",
        notes: Optional[str] = None,
        resume_version_id: Optional[int] = None,
    ) -> int:
        """Create a new tracker entry."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tracker
            (company, role, location, platform, region, jd_url, status, notes, resume_version_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (company, role, location, platform, region, jd_url, status, notes, resume_version_id))

        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()

        self.db.log_activity(
            "tracker_entry_created",
            f"entry_id:{entry_id}",
            f"company:{company}, role:{role}, status:{status}",
            "success"
        )

        logger.info(f"Tracker entry {entry_id} created: {company} - {role}")
        return entry_id

    def get_entry(self, entry_id: int) -> Optional[Dict]:
        """Get a single tracker entry by ID."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, company, role, location, platform, region, jd_url, status,
                   date_applied, notes, resume_version_id, created_at, updated_at
            FROM tracker
            WHERE id = ?
        """, (entry_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_entries_by_status(self, status: str) -> List[Dict]:
        """Get all tracker entries with a specific status."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, company, role, location, platform, region, status, created_at, updated_at
            FROM tracker
            WHERE status = ?
            ORDER BY created_at DESC
        """, (status,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_entries_by_region(self, region: str) -> List[Dict]:
        """Get all tracker entries for a specific region."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, company, role, location, platform, status, created_at
            FROM tracker
            WHERE region = ?
            ORDER BY created_at DESC
        """, (region,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_all_entries(self) -> List[Dict]:
        """Get all tracker entries."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, company, role, location, platform, region, status, created_at
            FROM tracker
            ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_status(self, entry_id: int, status: str):
        """Update tracker entry status."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE tracker
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, entry_id))

        conn.commit()
        conn.close()

        logger.info(f"Tracker entry {entry_id} status updated to {status}")

    def update_date_applied(self, entry_id: int, date_applied: str):
        """Update date applied for a tracker entry."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE tracker
            SET date_applied = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (date_applied, entry_id))

        conn.commit()
        conn.close()

        logger.info(f"Tracker entry {entry_id} date_applied updated to {date_applied}")
