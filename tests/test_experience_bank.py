import pytest
import tempfile
import os
from app.database import Database
from app.experience_bank import ExperienceBank


@pytest.fixture
def bank_with_db():
    """Create a database and experience bank for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)
        bank = ExperienceBank(db)
        yield bank, db


def test_add_entry(bank_with_db):
    """Test adding an entry to the experience bank."""
    bank, _ = bank_with_db

    entry_id = bank.add_entry(
        category="bullet",
        content="Led team of engineers on cloud migration",
        themes="cloud,leadership",
        role_source="Tech Corp - Senior Engineer"
    )

    assert entry_id is not None
    assert isinstance(entry_id, int)


def test_get_entries_by_category(bank_with_db):
    """Test retrieving entries by category."""
    bank, _ = bank_with_db

    # Add multiple entries
    bank.add_entry("skill", "Python", themes="programming")
    bank.add_entry("skill", "AWS", themes="cloud")
    bank.add_entry("bullet", "Built REST APIs", themes="development")

    skills = bank.get_entries_by_category("skill")
    assert len(skills) == 2
    assert all(entry["category"] == "skill" for entry in skills)


def test_get_all_entries(bank_with_db):
    """Test retrieving all entries."""
    bank, _ = bank_with_db

    bank.add_entry("skill", "Python", themes="programming")
    bank.add_entry("skill", "AWS", themes="cloud")
    bank.add_entry("bullet", "Deployed to production", themes="devops")

    all_entries = bank.get_all_entries()
    assert len(all_entries) == 3


def test_search_by_themes(bank_with_db):
    """Test searching entries by theme."""
    bank, _ = bank_with_db

    bank.add_entry("skill", "Python", themes="programming,python")
    bank.add_entry("skill", "Kubernetes", themes="cloud,devops")
    bank.add_entry("bullet", "Deployed app", themes="devops,cloud")

    cloud_entries = bank.search_by_themes("cloud")
    assert len(cloud_entries) == 2

    devops_entries = bank.search_by_themes("devops")
    assert len(devops_entries) == 2


def test_detect_themes(bank_with_db):
    """Test theme detection."""
    bank, _ = bank_with_db

    # Test detection with various keywords
    themes = bank._detect_themes("Implemented security controls and vulnerability scanning")
    assert "security" in themes

    themes = bank._detect_themes("Managed AWS infrastructure and EC2 instances")
    assert "cloud" in themes

    themes = bank._detect_themes("Automated CI/CD pipeline with Kubernetes")
    assert "automation" in themes or "infrastructure" in themes


def test_clear_bank(bank_with_db):
    """Test clearing the experience bank."""
    bank, _ = bank_with_db

    bank.add_entry("skill", "Python", themes="programming")
    bank.add_entry("skill", "AWS", themes="cloud")

    all_entries = bank.get_all_entries()
    assert len(all_entries) == 2

    bank.clear_bank()

    all_entries = bank.get_all_entries()
    assert len(all_entries) == 0


def test_no_duplicates_on_same_content(bank_with_db):
    """Test that adding the same content twice creates two entries (duplicates allowed for now)."""
    bank, _ = bank_with_db

    bank.add_entry("skill", "Python", themes="programming")
    bank.add_entry("skill", "Python", themes="programming")

    entries = bank.get_entries_by_category("skill")
    assert len(entries) == 2  # Both entries exist


def test_experience_bank_persistence(bank_with_db):
    """Test that entries persist in the database."""
    bank, db = bank_with_db

    bank.add_entry("skill", "Python", themes="programming")
    bank.add_entry("bullet", "Led team of engineers", themes="leadership")

    # Create a new bank instance with the same database
    bank2 = ExperienceBank(db)
    entries = bank2.get_all_entries()

    assert len(entries) == 2
