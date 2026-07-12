import os
import yaml
from pathlib import Path
from dotenv import load_dotenv


class Config:
    def __init__(self, config_file: str = "config.yaml", env_file: str = ".env"):
        self.config_file = config_file
        self.env_file = env_file

        # Load .env first
        load_dotenv(env_file)

        # Load YAML config
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f) or {}

        # Override with environment variables if present
        self._apply_env_overrides()

    def _apply_env_overrides(self):
        """Apply environment variable overrides to config."""
        if "APP_PORT" in os.environ:
            self.config["app"]["port"] = int(os.environ["APP_PORT"])
        if "DATA_BASE_DIR" in os.environ:
            base_dir = os.path.expanduser(os.environ["DATA_BASE_DIR"])
            self._rebase_data_dir(base_dir)

        # Use /tmp for database on Vercel (ephemeral filesystem)
        if os.environ.get("ENVIRONMENT") == "production":
            self._rebase_data_dir("/tmp")
            self.config["logging"]["file"] = "/tmp/accelerator.log"

    def _rebase_data_dir(self, base_dir: str):
        """Point every data subdirectory (db, resumes, tailored output,
        tracker backups) at base_dir. Previously only db_path was rebased,
        so resume uploads/tailoring/tracker backups silently kept writing
        to the relative "data/..." default -- which is read-only on Vercel's
        ephemeral filesystem and diverges from a user-set DATA_BASE_DIR."""
        self.config["data"]["base_dir"] = base_dir
        self.config["data"]["db_path"] = os.path.join(base_dir, "accelerator.db")
        self.config["data"]["resume_dir"] = os.path.join(base_dir, "resumes")
        self.config["data"]["tailored_resume_dir"] = os.path.join(base_dir, "tailored")
        self.config["data"]["tracker_backup_dir"] = os.path.join(base_dir, "tracker_backups")

    def get(self, key: str, default=None):
        """Get a config value using dot notation (e.g., 'app.port')."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def get_api_key(self) -> str:
        """Get the Anthropic API key from environment."""
        return os.environ.get("ANTHROPIC_API_KEY", "")

    def get_webhook_token(self) -> str:
        """Get the webhook API token from environment."""
        return os.environ.get("WEBHOOK_API_TOKEN", "")

    def __getitem__(self, key: str):
        return self.get(key)
