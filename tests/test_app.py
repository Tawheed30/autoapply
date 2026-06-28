import pytest
from app.config import Config
import tempfile
import os
import yaml


@pytest.fixture
def temp_config():
    """Provide a temporary config for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = {
            "app": {"host": "0.0.0.0", "port": 8787, "debug": True},
            "data": {
                "base_dir": tmpdir,
                "db_path": os.path.join(tmpdir, "test.db"),
                "resume_dir": os.path.join(tmpdir, "resumes"),
            },
            "logging": {
                "level": "INFO",
                "file": os.path.join(tmpdir, "app.log"),
            },
            "anthropic": {
                "models": {
                    "bulk_draft": "claude-haiku-4-5-20251001",
                    "resume_tailor": "claude-sonnet-4-6",
                }
            },
        }
        config_file = os.path.join(tmpdir, "config.yaml")
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        env_file = os.path.join(tmpdir, ".env")
        with open(env_file, "w") as f:
            f.write("ANTHROPIC_API_KEY=test_key\n")
            f.write("WEBHOOK_API_TOKEN=test_token\n")

        yield config_file, env_file, tmpdir


def test_config_loading(temp_config):
    """Test configuration loading."""
    config_file, env_file, _ = temp_config
    config = Config(config_file, env_file)

    assert config.get("app.port") == 8787
    assert config.get_api_key() == "test_key"
    assert config.get_webhook_token() == "test_token"


def test_config_with_defaults(temp_config):
    """Test configuration defaults."""
    config_file, env_file, _ = temp_config
    config = Config(config_file, env_file)

    assert config.get("anthropic.models.bulk_draft") == "claude-haiku-4-5-20251001"
    assert config.get("nonexistent_key", "default_value") == "default_value"


def test_app_endpoints(temp_data_dir):
    """Basic endpoint test - verify imports work."""
    from app.main import app, health_check
    assert app is not None
    assert health_check is not None
