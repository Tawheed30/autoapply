import pytest
from app.database import Database
import tempfile
import os


def test_database_init():
    """Test database initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)
        assert os.path.exists(db_path)


def test_activity_log(temp_data_dir):
    """Test activity logging."""
    db_path = os.path.join(temp_data_dir, "test.db")
    db = Database(db_path)
    db.log_activity("test_action", "test_target", "test_details", "success")

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activity_log WHERE action = 'test_action'")
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row["action"] == "test_action"
    assert row["target"] == "test_target"


def test_job_queue(temp_data_dir):
    """Test job queue operations."""
    db_path = os.path.join(temp_data_dir, "test.db")
    db = Database(db_path)

    job_id = db.add_job_to_queue(
        jd_text="Test JD",
        company="Test Co",
        role="Test Role",
        location="Test Location"
    )

    assert job_id is not None
    assert isinstance(job_id, int)

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM job_queue WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row["company"] == "Test Co"
    assert row["status"] == "queued"
