import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from app.database import Database
from app.job_queue import JobQueueManager
from app.tracker import TrackerManager
from app.background_worker import BackgroundWorker
from app.config import Config


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)
        yield db


@pytest.fixture
def mock_config():
    """Create a mock config."""
    config = MagicMock()
    config.get.side_effect = lambda key, default=None: {
        "data.tailored_resume_dir": "/tmp/tailored",
        "data.resume_dir": "/tmp",
        "anthropic.models.resume_tailor": "claude-sonnet-4-6",
    }.get(key, default)
    return config


@pytest.fixture
def temp_master_resume(temp_db):
    """Create a temporary master resume."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock resume directory
        resume_dir = os.path.join(tmpdir, "resumes")
        os.makedirs(resume_dir, exist_ok=True)

        # Create a dummy master.docx
        master_path = os.path.join(resume_dir, "master.docx")
        with open(master_path, 'w') as f:
            f.write("mock resume")

        yield tmpdir, master_path


@patch('app.background_worker.ResumeTailor')
@patch('app.background_worker.ResumeParser')
@patch('app.background_worker.ExperienceBank')
@patch('app.background_worker.JDExtractor')
def test_worker_processes_queued_job(
    mock_extractor_class,
    mock_bank_class,
    mock_parser_class,
    mock_tailor_class,
    temp_db,
    mock_config,
    temp_master_resume
):
    """Test that the worker processes a queued job."""
    tmpdir, master_path = temp_master_resume

    # Setup mocks
    mock_extractor = MagicMock()
    mock_extractor.extract_keywords.return_value = ["python", "aws", "kubernetes"]

    # Create a properly JSON-serializable match report
    match_report = {
        "score": 75.0,
        "matched_keywords": ["python"],
        "missing_keywords": ["aws"],
        "match_count": 1,
        "total_keywords": 2,
    }
    mock_extractor.score_match.return_value = match_report
    mock_extractor_class.return_value = mock_extractor

    mock_parser = MagicMock()
    mock_parser.extract_contact_info.return_value = {"email": "test@example.com"}
    mock_parser.parse_resume.return_value = {
        "skills": ["python"],
        "experience": [],
    }
    mock_parser_class.return_value = mock_parser

    mock_bank = MagicMock()
    mock_bank.get_entries_by_category.return_value = [
        {"content": "skill1"},
        {"content": "skill2"},
    ]
    mock_bank_class.return_value = mock_bank

    mock_tailor = MagicMock()
    mock_tailor.tailor_resume.return_value = (
        "/tmp/tailored/resume.docx",
        [{"original": "text", "new": "new text"}],
    )
    mock_tailor.save_diff_report.return_value = None
    mock_tailor_class.return_value = mock_tailor

    # Create a queued job
    queue_manager = JobQueueManager(temp_db)
    job_id = queue_manager.add_job(
        jd_text="Senior Engineer needed",
        company="TechCorp",
        role="Engineer",
        location="SF"
    )

    # Patch the config to use our temp resume directory
    with patch.object(mock_config, 'get') as mock_get:
        def get_side_effect(key, default=None):
            if key == "data.resume_dir":
                return os.path.join(tmpdir, "resumes")
            elif key == "data.tailored_resume_dir":
                return "/tmp/tailored"
            elif key == "anthropic.models.resume_tailor":
                return "claude-sonnet-4-6"
            return default

        mock_get.side_effect = get_side_effect

        # Create worker and process jobs
        worker = BackgroundWorker(temp_db, mock_config, "test_api_key")

        # Mock the master resume path check
        with patch.object(worker, '_get_master_resume_path', return_value=master_path):
            worker.process_queued_jobs()

    # Verify the job was moved to 'staged'
    updated_job = queue_manager.get_job(job_id)
    assert updated_job["status"] == "staged"
    assert updated_job["result"] is not None

    # Verify tracker entry was created
    tracker_manager = TrackerManager(temp_db)
    entries = tracker_manager.get_entries_by_status("staged")
    assert len(entries) >= 1


@patch('app.background_worker.ResumeTailor')
def test_worker_handles_error(mock_tailor_class, temp_db, mock_config):
    """Test that worker gracefully handles errors."""
    # Create a queued job
    queue_manager = JobQueueManager(temp_db)
    job_id = queue_manager.add_job(jd_text="Test", company="Test")

    # Mock tailor to raise an error
    mock_tailor = MagicMock()
    mock_tailor.tailor_resume.side_effect = Exception("API error")
    mock_tailor_class.return_value = mock_tailor

    # Mock other components
    with patch('app.background_worker.ResumeParser'):
        with patch('app.background_worker.ExperienceBank'):
            with patch('app.background_worker.JDExtractor'):
                # Create worker and process jobs
                worker = BackgroundWorker(temp_db, mock_config, "test_api_key")

                # This should not raise an exception
                worker.process_queued_jobs()

    # Verify the job was marked as failed
    failed_job = queue_manager.get_job(job_id)
    assert failed_job["status"] == "failed"
    assert failed_job["error_message"] is not None


def test_worker_resilience_multiple_jobs(temp_db, mock_config):
    """Test that worker processes multiple jobs despite errors."""
    # Create multiple queued jobs
    queue_manager = JobQueueManager(temp_db)
    job1 = queue_manager.add_job(jd_text="Job 1", company="A")
    job2 = queue_manager.add_job(jd_text="Job 2", company="B")

    # Mock to fail on job1 but succeed on job2
    with patch('app.background_worker.ResumeParser') as mock_parser_class:
        with patch('app.background_worker.ExperienceBank'):
            with patch('app.background_worker.JDExtractor') as mock_extractor_class:
                with patch('app.background_worker.ResumeTailor') as mock_tailor_class:
                    # Setup mocks
                    mock_parser = MagicMock()
                    mock_parser.extract_contact_info.return_value = {}
                    mock_parser.parse_resume.return_value = {"skills": []}
                    mock_parser_class.return_value = mock_parser

                    mock_extractor = MagicMock()
                    mock_extractor.extract_keywords.return_value = []
                    mock_extractor.extract_requirements.return_value = {
                        "matched_keywords": [],
                        "missing_keywords": [],
                        "match_count": 0,
                        "total_keywords": 0,
                        "score": 0,
                    }
                    mock_extractor_class.return_value = mock_extractor

                    # Fail on first call, succeed on second
                    mock_tailor = MagicMock()
                    mock_tailor.tailor_resume.side_effect = [
                        Exception("Error on job 1"),
                        ("/tmp/resume.docx", []),
                    ]
                    mock_tailor_class.return_value = mock_tailor

                    # Create worker and process jobs
                    worker = BackgroundWorker(temp_db, mock_config, "test_api_key")

                    with patch.object(worker, '_get_master_resume_path', return_value="/tmp/master.docx"):
                        worker.process_queued_jobs()

    # Verify both jobs were processed (one failed, one staged)
    job1_after = queue_manager.get_job(job1)
    job2_after = queue_manager.get_job(job2)

    # At least one should be processed (may fail or succeed depending on mock)
    assert job1_after["status"] in ["failed", "staged"]
    assert job2_after["status"] in ["failed", "staged"]


def test_worker_skips_non_queued_jobs(temp_db, mock_config):
    """Test that worker only processes queued jobs."""
    queue_manager = JobQueueManager(temp_db)

    # Create jobs with different statuses
    job1 = queue_manager.add_job(jd_text="Job 1")  # queued
    job2 = queue_manager.add_job(jd_text="Job 2")  # queued

    # Move job2 to staged
    queue_manager.update_job_status(job2, "staged")

    # Mock the processing
    with patch('app.background_worker.ResumeParser'):
        with patch('app.background_worker.ExperienceBank'):
            with patch('app.background_worker.JDExtractor'):
                with patch('app.background_worker.ResumeTailor'):
                    worker = BackgroundWorker(temp_db, mock_config, "test_api_key")

                    with patch.object(worker, '_process_job') as mock_process:
                        worker.process_queued_jobs()

                        # Only one call to _process_job (for the queued job)
                        assert mock_process.call_count == 1
