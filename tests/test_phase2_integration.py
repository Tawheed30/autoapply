import pytest
import tempfile
import os
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from app.database import Database
from app.job_queue import JobQueueManager
from app.tracker import TrackerManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)
        yield db


@pytest.fixture
def queue_manager(temp_db):
    """Create a JobQueueManager with temp database."""
    return JobQueueManager(temp_db)


@pytest.fixture
def tracker_manager(temp_db):
    """Create a TrackerManager with temp database."""
    return TrackerManager(temp_db)


# ===== Job Queue Tests =====

def test_add_job_with_jd_text(queue_manager):
    """Test adding a job with JD text."""
    job_id = queue_manager.add_job(
        jd_text="Senior Engineer needed",
        company="TechCorp",
        role="Senior Engineer",
        location="San Francisco"
    )

    assert job_id is not None
    job = queue_manager.get_job(job_id)
    assert job["jd_text"] == "Senior Engineer needed"
    assert job["company"] == "TechCorp"
    assert job["status"] == "queued"


def test_add_job_with_jd_url(queue_manager):
    """Test adding a job with JD URL."""
    job_id = queue_manager.add_job(
        jd_url="https://example.com/job",
        company="StartupX",
        role="Engineer"
    )

    assert job_id is not None
    job = queue_manager.get_job(job_id)
    assert job["jd_url"] == "https://example.com/job"
    assert job["company"] == "StartupX"


def test_add_job_requires_jd(queue_manager):
    """Test that add_job requires either jd_text or jd_url."""
    with pytest.raises(ValueError):
        queue_manager.add_job(company="Test", role="Test")


def test_get_queued_jobs(queue_manager):
    """Test retrieving queued jobs."""
    queue_manager.add_job(jd_text="Job 1", company="A")
    queue_manager.add_job(jd_text="Job 2", company="B")

    queued = queue_manager.get_queued_jobs()
    assert len(queued) == 2


def test_update_job_status(queue_manager):
    """Test updating job status."""
    job_id = queue_manager.add_job(jd_text="Test", company="Test")

    result = {"resume_path": "/path/to/resume.docx", "match_score": 85}
    queue_manager.update_job_status(job_id, status="staged", result=result)

    job = queue_manager.get_job(job_id)
    assert job["status"] == "staged"
    assert json.loads(job["result"])["match_score"] == 85


def test_update_job_error(queue_manager):
    """Test updating job with error."""
    job_id = queue_manager.add_job(jd_text="Test")

    queue_manager.update_job_status(
        job_id,
        status="failed",
        error_message="API error occurred"
    )

    job = queue_manager.get_job(job_id)
    assert job["status"] == "failed"
    assert job["error_message"] == "API error occurred"


def test_get_jobs_by_status(queue_manager):
    """Test filtering jobs by status."""
    job1 = queue_manager.add_job(jd_text="Job 1")
    job2 = queue_manager.add_job(jd_text="Job 2")

    queue_manager.update_job_status(job1, "staged")

    queued = queue_manager.get_jobs_by_status("queued")
    staged = queue_manager.get_jobs_by_status("staged")

    assert len(queued) == 1
    assert len(staged) == 1


# ===== Tracker Tests =====

def test_create_tracker_entry(tracker_manager):
    """Test creating a tracker entry."""
    entry_id = tracker_manager.create_entry(
        company="TechCorp",
        role="Engineer",
        location="SF",
        jd_url="https://example.com/job",
        status="staged"
    )

    assert entry_id is not None
    entry = tracker_manager.get_entry(entry_id)
    assert entry["company"] == "TechCorp"
    assert entry["role"] == "Engineer"
    assert entry["status"] == "staged"


def test_get_entries_by_status(tracker_manager):
    """Test filtering tracker entries by status."""
    id1 = tracker_manager.create_entry("A", "Role1", status="staged")
    id2 = tracker_manager.create_entry("B", "Role2", status="staged")
    id3 = tracker_manager.create_entry("C", "Role3", status="applied")

    staged = tracker_manager.get_entries_by_status("staged")
    applied = tracker_manager.get_entries_by_status("applied")

    assert len(staged) == 2
    assert len(applied) == 1


def test_update_tracker_status(tracker_manager):
    """Test updating tracker entry status."""
    entry_id = tracker_manager.create_entry("Company", "Role", status="staged")

    tracker_manager.update_status(entry_id, "applied")

    entry = tracker_manager.get_entry(entry_id)
    assert entry["status"] == "applied"


def test_update_tracker_date_applied(tracker_manager):
    """Test updating date applied."""
    entry_id = tracker_manager.create_entry("Company", "Role")

    today = datetime.now().isoformat()
    tracker_manager.update_date_applied(entry_id, today)

    entry = tracker_manager.get_entry(entry_id)
    assert entry["date_applied"] == today


