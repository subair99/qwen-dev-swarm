# config.py
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class ConfigError(Exception):
    """Custom exception for missing configuration."""
    pass

def get_required_env(var_name: str) -> str:
    """
    Retrieves an environment variable.
    Raises ConfigError if the variable is not set or is empty.
    This ensures the variable MUST be provided via the .env file.
    """
    value = os.getenv(var_name)
    if not value:
        raise ConfigError(
            f"Missing required environment variable: '{var_name}'. "
            f"Please ensure it is defined in your .env file."
        )
    return value

# ─────────────────────────────────────────────────────────────
# CENTRALIZED CONFIGURATION
# These are the ONLY places these values should be defined.
# ─────────────────────────────────────────────────────────────
QWEN_API_KEY = get_required_env("QWEN_API_KEY")
QWEN_BASE_URL = get_required_env("QWEN_BASE_URL")
MODEL_NAME = get_required_env("MODEL_NAME")
GUARDRAIL_MODEL_NAME = get_required_env("GUARDRAIL_MODEL_NAME")