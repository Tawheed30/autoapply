import pytest
import tempfile
import os
from app.database import Database
from app.job_queue import JobQueueManager
from app.question_drafter import QuestionDrafter
from app.cover_letter_generator import CoverLetterGenerator
from app.question_answer_manager import QuestionAnswerManager
from app.cover_letter_manager import CoverLetterManager
from app.question_bank import QuestionBank


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)
        yield db


@pytest.fixture
def sample_job(temp_db):
    """Create a sample queued job."""
    queue = JobQueueManager(temp_db)
    job_id = queue.add_job(
        jd_text="Senior Engineer needed",
        company="TechCorp",
        role="Engineer",
        location="SF"
    )
    return job_id


# ===== Question Answer Manager Tests =====

def test_get_questions_for_job_empty(temp_db, sample_job):
    """Test getting questions when none exist."""
    manager = QuestionAnswerManager(temp_db)
    questions = manager.get_questions_for_job(sample_job)
    assert questions == []


def test_add_and_get_questions(temp_db, sample_job):
    """Test adding and retrieving questions."""
    conn = temp_db.get_connection()
    cursor = conn.cursor()

    # Manually add questions
    cursor.execute("""
        INSERT INTO question_answers (job_id, question, answer, confidence, flagged)
        VALUES (?, ?, ?, ?, ?)
    """, (sample_job, "Why TechCorp?", "I love your company", "high", 0))

    cursor.execute("""
        INSERT INTO question_answers (job_id, question, answer, confidence, flagged)
        VALUES (?, ?, ?, ?, ?)
    """, (sample_job, "Salary?", None, "low", 1))

    conn.commit()
    conn.close()

    manager = QuestionAnswerManager(temp_db)
    questions = manager.get_questions_for_job(sample_job)

    assert len(questions) == 2
    assert questions[0]["answer"] == "I love your company"
    assert questions[1]["flagged"] == 1


def test_update_answer(temp_db, sample_job):
    """Test updating an answer."""
    conn = temp_db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO question_answers (job_id, question, answer)
        VALUES (?, ?, ?)
    """, (sample_job, "Why us?", "Old answer"))

    conn.commit()

    cursor.execute("SELECT id FROM question_answers WHERE job_id = ?", (sample_job,))
    question_id = cursor.fetchone()["id"]
    conn.close()

    manager = QuestionAnswerManager(temp_db)
    manager.update_answer(question_id, "New answer")

    questions = manager.get_questions_for_job(sample_job)
    assert questions[0]["answer"] == "New answer"


def test_use_bank_answer(temp_db, sample_job):
    """Test using a question bank answer."""
    # Add a bank answer
    bank = QuestionBank(temp_db)
    bank_id = bank.save_answer("Why us?", "Bank answer text", "company")

    # Add a question
    conn = temp_db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO question_answers (job_id, question, answer)
        VALUES (?, ?, ?)
    """, (sample_job, "Why us?", "Original answer"))

    conn.commit()

    cursor.execute("SELECT id FROM question_answers WHERE job_id = ?", (sample_job,))
    question_id = cursor.fetchone()["id"]
    conn.close()

    # Use bank answer
    manager = QuestionAnswerManager(temp_db)
    manager.use_bank_answer(question_id, "Bank answer text", bank_id)

    # Verify answer changed
    questions = manager.get_questions_for_job(sample_job)
    assert questions[0]["answer"] == "Bank answer text"

    # Verify used_count incremented
    bank_entry = bank.get_by_id(bank_id)
    assert bank_entry["used_count"] == 1


def test_approve_all_answers_success(temp_db, sample_job):
    """Test approving all answers when valid."""
    conn = temp_db.get_connection()
    cursor = conn.cursor()

    # Add questions (all with answers, none flagged)
    cursor.execute("""
        INSERT INTO question_answers (job_id, question, answer, flagged)
        VALUES (?, ?, ?, ?)
    """, (sample_job, "Q1", "A1", 0))

    cursor.execute("""
        INSERT INTO question_answers (job_id, question, answer, flagged)
        VALUES (?, ?, ?, ?)
    """, (sample_job, "Q2", "A2", 0))

    conn.commit()
    conn.close()

    manager = QuestionAnswerManager(temp_db)
    success, message, _ = manager.approve_all_answers(sample_job)

    assert success
    assert "approved" in message.lower()

    # Verify approved flag set
    questions = manager.get_questions_for_job(sample_job)
    assert all(q["approved"] == 1 for q in questions)


def test_approve_all_answers_fails_with_unfilled_flagged(temp_db, sample_job):
    """Test approval fails if flagged question is unanswered."""
    conn = temp_db.get_connection()
    cursor = conn.cursor()

    # Add a flagged question with no answer
    cursor.execute("""
        INSERT INTO question_answers (job_id, question, answer, flagged)
        VALUES (?, ?, ?, ?)
    """, (sample_job, "Visa?", None, 1))

    conn.commit()
    conn.close()

    manager = QuestionAnswerManager(temp_db)
    success, message, _ = manager.approve_all_answers(sample_job)

    assert not success
    assert "must answer all" in message.lower()


# ===== Cover Letter Manager Tests =====

def test_get_cover_letter_not_found(temp_db, sample_job):
    """Test getting non-existent cover letter."""
    manager = CoverLetterManager(temp_db)
    letter = manager.get_cover_letter(sample_job)
    assert letter is None


def test_add_and_get_cover_letter(temp_db, sample_job):
    """Test adding and retrieving cover letter."""
    conn = temp_db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cover_letters (job_id, company, role, cover_letter_text)
        VALUES (?, ?, ?, ?)
    """, (sample_job, "TechCorp", "Engineer", "Dear Hiring Manager,..."))

    conn.commit()
    conn.close()

    manager = CoverLetterManager(temp_db)
    letter = manager.get_cover_letter(sample_job)

    assert letter is not None
    assert letter["cover_letter_text"] == "Dear Hiring Manager,..."


def test_update_cover_letter(temp_db, sample_job):
    """Test updating cover letter."""
    conn = temp_db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cover_letters (job_id, company, role, cover_letter_text)
        VALUES (?, ?, ?, ?)
    """, (sample_job, "TechCorp", "Engineer", "Old text"))

    conn.commit()
    conn.close()

    manager = CoverLetterManager(temp_db)
    manager.update_cover_letter(sample_job, "New text with more words")

    letter = manager.get_cover_letter(sample_job)
    assert letter["cover_letter_text"] == "New text with more words"


def test_approve_cover_letter(temp_db, sample_job):
    """Test approving cover letter."""
    conn = temp_db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cover_letters (job_id, company, role, cover_letter_text)
        VALUES (?, ?, ?, ?)
    """, (sample_job, "TechCorp", "Engineer", "Dear Hiring Manager, I am writing..."))

    conn.commit()
    conn.close()

    manager = CoverLetterManager(temp_db)
    success, message, word_count = manager.approve_cover_letter(sample_job)

    assert success
    assert "approved" in message.lower()
    assert word_count > 0

    # Verify approved flag set
    letter = manager.get_cover_letter(sample_job)
    assert letter["approved"] == 1


def test_is_approved_check(temp_db, sample_job):
    """Test checking if cover letter is approved."""
    conn = temp_db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cover_letters (job_id, company, role, cover_letter_text, approved)
        VALUES (?, ?, ?, ?, ?)
    """, (sample_job, "TechCorp", "Engineer", "Text", 0))

    conn.commit()
    conn.close()

    manager = CoverLetterManager(temp_db)
    assert manager.is_approved(sample_job) == False

    manager.approve_cover_letter(sample_job)
    assert manager.is_approved(sample_job) == True
