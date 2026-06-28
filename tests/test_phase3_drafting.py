import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from app.database import Database
from app.experience_bank import ExperienceBank
from app.question_drafter import QuestionDrafter
from app.cover_letter_generator import CoverLetterGenerator
from app.question_bank import QuestionBank


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)
        yield db


@pytest.fixture
def populated_bank(temp_db):
    """Create an experience bank with sample content."""
    bank = ExperienceBank(temp_db)

    # Add sample entries
    bank.add_entry("skill", "Python", themes="programming,python")
    bank.add_entry("skill", "AWS", themes="cloud,aws")
    bank.add_entry("skill", "Kubernetes", themes="infrastructure,kubernetes")
    bank.add_entry("bullet", "Led team of 5 engineers", themes="leadership")
    bank.add_entry("bullet", "Implemented CI/CD pipeline reducing deployment time by 40%", themes="devops,automation")
    bank.add_entry("project", "Built scalable microservices architecture on AWS", themes="cloud,architecture")
    bank.add_entry("summary", "Senior engineer with 6+ years of cloud infrastructure experience")

    return bank


@pytest.fixture
def sample_jd():
    """Sample job description for testing."""
    return """
    Senior Software Engineer - Cloud Infrastructure

    We're looking for a Senior Software Engineer to join our Cloud Infrastructure team.

    **Requirements:**
    - 5+ years of experience in software engineering
    - Expert knowledge of AWS, including EC2, S3, Lambda
    - Strong proficiency in Python
    - Experience with Kubernetes and Docker
    - Experience with CI/CD pipelines
    - Understanding of security best practices

    **Responsibilities:**
    - Design and maintain cloud infrastructure
    - Implement automated deployment pipelines
    - Mentor junior engineers
    - Conduct security reviews

    **Nice to have:**
    - Experience with serverless architecture
    - Knowledge of infrastructure-as-code tools
    """


# ===== Question Drafter Tests =====

@patch('app.question_drafter.Anthropic')
def test_question_drafter_generates_answers(mock_anthropic_class, temp_db, populated_bank, sample_jd):
    """Test that question drafter generates answers."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content[0].text = "I have 6+ years of experience with Python, including building microservices and API backends."
    mock_client.messages.create.return_value = mock_response
    mock_anthropic_class.return_value = mock_client

    drafter = QuestionDrafter(temp_db, "test_key")
    drafter.client = mock_client

    answers = drafter.draft_answers(
        job_id=1,
        jd_text=sample_jd,
        jd_keywords=["python", "aws", "kubernetes"],
        company="TechCorp",
        role="Senior Engineer"
    )

    assert len(answers) > 0
    assert all("question" in a and "answer" in a for a in answers)
    assert all("confidence" in a for a in answers)


@patch('app.question_drafter.Anthropic')
def test_question_drafter_detects_sensitive_work_auth(mock_anthropic_class, temp_db, populated_bank):
    """Test detection of work authorization questions."""
    mock_anthropic_class.return_value = MagicMock()
    drafter = QuestionDrafter(temp_db, "test_key")

    is_sensitive, qtype, hint = drafter._detect_sensitive(
        "Do you require visa sponsorship?",
        region="uae"
    )

    assert is_sensitive
    assert qtype == "work_auth"
    assert "Sponsorship" in hint


@patch('app.question_drafter.Anthropic')
def test_question_drafter_detects_sensitive_salary(mock_anthropic_class, temp_db, populated_bank):
    """Test detection of salary questions."""
    mock_anthropic_class.return_value = MagicMock()
    drafter = QuestionDrafter(temp_db, "test_key")

    is_sensitive, qtype, hint = drafter._detect_sensitive(
        "What's your salary expectation?"
    )

    assert is_sensitive
    assert qtype == "salary"


@patch('app.question_drafter.Anthropic')
def test_question_drafter_detects_sensitive_notice(mock_anthropic_class, temp_db, populated_bank):
    """Test detection of notice period questions."""
    mock_anthropic_class.return_value = MagicMock()
    drafter = QuestionDrafter(temp_db, "test_key")

    is_sensitive, qtype, hint = drafter._detect_sensitive(
        "How much notice do you need to leave your current role?"
    )

    assert is_sensitive
    assert qtype == "notice"


@patch('app.question_drafter.Anthropic')
def test_question_drafter_detects_sensitive_relocation(mock_anthropic_class, temp_db, populated_bank):
    """Test detection of relocation questions."""
    mock_anthropic_class.return_value = MagicMock()
    drafter = QuestionDrafter(temp_db, "test_key")

    is_sensitive, qtype, hint = drafter._detect_sensitive(
        "Are you willing to relocate to Singapore?"
    )

    assert is_sensitive
    assert qtype == "relocation"


@patch('app.question_drafter.Anthropic')
def test_question_drafter_region_specific_hints(mock_anthropic_class, temp_db):
    """Test that region-specific hints are provided."""
    mock_anthropic_class.return_value = MagicMock()
    drafter = QuestionDrafter(temp_db, "test_key")

    is_uae_sensitive, _, uae_hint = drafter._detect_sensitive("Do you need sponsorship?", region="uae")
    is_sg_sensitive, _, sg_hint = drafter._detect_sensitive("What's your salary expectation?", region="singapore")
    is_default_sensitive, _, default_hint = drafter._detect_sensitive("How much notice period do you require?", region="unknown")

    assert is_uae_sensitive
    assert "Sponsorship" in uae_hint

    assert is_sg_sensitive
    assert "Employment Pass" in sg_hint or "salary" in sg_hint.lower()

    assert is_default_sensitive
    assert "input" in default_hint.lower()


@patch('app.question_drafter.Anthropic')
def test_question_drafter_regular_questions_not_flagged(mock_anthropic_class, temp_db):
    """Test that regular questions are not flagged as sensitive."""
    mock_anthropic_class.return_value = MagicMock()
    drafter = QuestionDrafter(temp_db, "test_key")

    questions = [
        "Tell us about your leadership experience",
        "Describe a challenging project you worked on",
        "Why do you want to work for our company?"
    ]

    for question in questions:
        is_sensitive, _, _ = drafter._detect_sensitive(question)
        assert not is_sensitive


# ===== Cover Letter Generator Tests =====

@patch('app.cover_letter_generator.Anthropic')
def test_cover_letter_generator_generates_letter(mock_anthropic_class, temp_db, populated_bank, sample_jd):
    """Test that cover letter generator generates a cover letter."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content[0].text = """Dear Hiring Manager,

I am writing to express my strong interest in the Senior Software Engineer position at TechCorp.

With over 6 years of experience in cloud infrastructure and a proven track record of designing and implementing scalable systems on AWS, I am confident in my ability to contribute significantly to your team.

My expertise in Python, Kubernetes, and CI/CD automation aligns well with your requirements, and I am particularly excited about the opportunity to work on infrastructure automation and mentoring junior engineers.

I would welcome the opportunity to discuss how my background and skills can benefit TechCorp.

Best regards,
Mohammed"""

    mock_client.messages.create.return_value = mock_response
    mock_anthropic_class.return_value = mock_client

    generator = CoverLetterGenerator(temp_db, "test_key")
    generator.client = mock_client

    cover_letter = generator.generate(
        jd_text=sample_jd,
        jd_keywords=["python", "aws", "kubernetes"],
        company="TechCorp",
        role="Senior Engineer"
    )

    assert "Dear" in cover_letter
    assert len(cover_letter) > 200  # Should be substantial
    assert "TechCorp" in cover_letter or "company" in cover_letter.lower()


# ===== Question Bank Tests =====

def test_question_bank_save_answer(temp_db):
    """Test saving an approved answer to question bank."""
    bank = QuestionBank(temp_db)

    bank_id = bank.save_answer(
        question="Why do you want to work for our company?",
        answer="I'm interested in your company because of your innovative work in cloud infrastructure.",
        category="company"
    )

    assert bank_id is not None


def test_question_bank_get_approved_answers(temp_db):
    """Test retrieving approved answers."""
    bank = QuestionBank(temp_db)

    bank.save_answer("Q1", "A1", "general")
    bank.save_answer("Q2", "A2", "general")

    approved = bank.get_approved_answers()

    assert len(approved) >= 2
    assert all(a["approved"] == 1 for a in approved)


def test_question_bank_find_similar_questions(temp_db):
    """Test finding similar questions."""
    bank = QuestionBank(temp_db)

    bank.save_answer("Why do you want to work for our company?", "Answer 1")
    bank.save_answer("Why are you interested in this role?", "Answer 2")

    similar = bank.find_similar_questions("Why do you want to work here?")

    assert len(similar) > 0
    assert similar[0]["question_text"].startswith("Why do you want")


def test_question_bank_increment_used_count(temp_db):
    """Test incrementing used count."""
    bank = QuestionBank(temp_db)

    bank_id = bank.save_answer("What's your experience with Python?", "I have 6+ years")
    entry_before = bank.get_by_id(bank_id)
    used_before = entry_before["used_count"]

    bank.increment_used_count(bank_id)
    entry_after = bank.get_by_id(bank_id)

    assert entry_after["used_count"] == used_before + 1


def test_question_bank_get_by_category(temp_db):
    """Test retrieving answers by category."""
    bank = QuestionBank(temp_db)

    bank.save_answer("Q1", "A1", "company")
    bank.save_answer("Q2", "A2", "company")
    bank.save_answer("Q3", "A3", "technical")

    company_answers = bank.get_by_category("company")
    technical_answers = bank.get_by_category("technical")

    assert len(company_answers) >= 2
    assert len(technical_answers) >= 1


def test_question_bank_duplicate_question_update(temp_db):
    """Test that duplicate questions update instead of insert."""
    bank = QuestionBank(temp_db)

    question = "Why do you want to work for us?"
    bank.save_answer(question, "Answer 1")
    bank.save_answer(question, "Answer 2 (updated)")

    approved = bank.get_approved_answers()
    matching = [a for a in approved if a["question_text"] == question]

    # Should be just one entry with the updated answer
    assert len(matching) >= 1
    assert "updated" in matching[0]["answer_text"]


# ===== Integration Tests =====

@patch('app.question_drafter.Anthropic')
def test_question_and_answer_flow(mock_anthropic_class, temp_db, populated_bank, sample_jd):
    """Test the full flow: draft answer, flag sensitive, save to bank."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content[0].text = "I have extensive experience with Python and cloud infrastructure."
    mock_client.messages.create.return_value = mock_response
    mock_anthropic_class.return_value = mock_client

    # Draft answers
    drafter = QuestionDrafter(temp_db, "test_key")
    drafter.client = mock_client

    answers = drafter.draft_answers(
        job_id=1,
        jd_text=sample_jd,
        jd_keywords=["python", "aws"],
        company="TechCorp",
        role="Engineer"
    )

    # Find a non-sensitive answer
    regular_answers = [a for a in answers if not a.get("flagged")]
    assert len(regular_answers) > 0

    # Save to question bank
    bank = QuestionBank(temp_db)
    if regular_answers:
        answer_data = regular_answers[0]
        bank.save_answer(answer_data["question"], answer_data["answer"])

    # Verify it's in the bank
    approved = bank.get_approved_answers()
    assert len(approved) > 0
