import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_data_dir():
    """Provide a temporary data directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_config(temp_data_dir):
    """Provide a temporary config file for testing."""
    config_content = f"""
app:
  host: 0.0.0.0
  port: 8787
  debug: true

data:
  base_dir: "{temp_data_dir}"
  db_path: "{temp_data_dir}/test.db"
  resume_dir: "{temp_data_dir}/resumes"
  tailored_resume_dir: "{temp_data_dir}/tailored"

anthropic:
  models:
    bulk_draft: "claude-haiku-4-5-20251001"
    resume_tailor: "claude-sonnet-4-6"
"""
    config_file = Path(temp_data_dir) / "config.yaml"
    config_file.write_text(config_content)
    return str(config_file)
