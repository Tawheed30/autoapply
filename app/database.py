import sqlite3
import os
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str):
        self.db_path = os.path.expanduser(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Activity log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT,
                details TEXT,
                result TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Job queue table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jd_text TEXT,
                jd_url TEXT,
                company TEXT,
                role TEXT,
                location TEXT,
                status TEXT DEFAULT 'queued',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                processed_at TEXT,
                result TEXT,
                error_message TEXT
            )
        """)

        # Contact info table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT NOT NULL,
                phone TEXT,
                location TEXT,
                active_master_version TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Resume versions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resume_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                upload_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 0,
                contact_extracted TEXT,
                file_path TEXT NOT NULL
            )
        """)

        # Tracker table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tracker (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                location TEXT,
                platform TEXT,
                region TEXT,
                jd_url TEXT,
                status TEXT DEFAULT 'staged',
                date_applied TEXT,
                notes TEXT,
                resume_version_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resume_version_id) REFERENCES resume_versions(id)
            )
        """)

        # Experience bank table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experience_bank (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                themes TEXT,
                role_source TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    def log_activity(self, action: str, target: str = None, details: str = None, result: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activity_log (timestamp, action, target, details, result)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.utcnow().isoformat(), action, target, details, result))
        conn.commit()
        conn.close()
        logger.info(f"Activity logged: {action} - {target}")

    def add_job_to_queue(self, jd_text: str = None, jd_url: str = None,
                         company: str = None, role: str = None, location: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO job_queue (jd_text, jd_url, company, role, location, status)
            VALUES (?, ?, ?, ?, ?, 'queued')
        """, (jd_text, jd_url, company, role, location))
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        self.log_activity("add_job_to_queue", f"job_id:{job_id}", f"company:{company}, role:{role}")
        return job_id
