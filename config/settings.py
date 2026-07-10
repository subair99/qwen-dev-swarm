# config/settings.py
import os
import stat
import logging
from pathlib import Path

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """
    Dynamically finds the project root by locating pyproject.toml.
    This is the most robust method for uv projects, as it works perfectly 
    whether you use a flat layout or a src/ layout.
    """
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    
    # Fallback to Current Working Directory if pyproject.toml isn't found
    return Path.cwd()

# Locate the .env file at the project root
PROJECT_ROOT = get_project_root()

if HAS_DOTENV:
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

def mask_secret(secret: str) -> str:
    """
    Masks a secret string for safe display in logs or UI.
    Example: 'sk-1234567890abcdef' -> 'sk-1...cdef'
    """
    if not secret or len(secret) < 8:
        return "***"
    return f"{secret[:4]}...{secret[-4:]}"

class Settings:
    def __init__(self):
        # 1. API Keys (Allow either QWEN or DASHSCOPE)
        self.QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
        self.DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
        
        # 2. Strictly require Base URL (NO DEFAULT FALLBACK)
        self.QWEN_BASE_URL: str = os.getenv("QWEN_BASE_URL")
        if not self.QWEN_BASE_URL:
            raise ValueError("❌ QWEN_BASE_URL is missing! It must be defined in your .env file.")
        
        # 3. Strictly require Model Names (NO DEFAULT FALLBACKS)
        self.MODEL_NAME: str = os.getenv("MODEL_NAME")
        if not self.MODEL_NAME:
            raise ValueError("❌ MODEL_NAME is missing! It must be defined in your .env file.")
            
        self.GUARDRAIL_MODEL_NAME: str = os.getenv("GUARDRAIL_MODEL_NAME")
        if not self.GUARDRAIL_MODEL_NAME:
            raise ValueError("❌ GUARDRAIL_MODEL_NAME is missing! It must be defined in your .env file.")

    @property
    def api_key(self) -> str:
        """Returns the first available API key."""
        return self.QWEN_API_KEY or self.DASHSCOPE_API_KEY

    @property
    def masked_api_key(self) -> str:
        """Returns a masked version of the API key for safe logging/UI display."""
        return mask_secret(self.api_key)

    def validate(self):
        """Validates that at least one critical authentication variable is loaded."""
        if not self.api_key:
            raise ValueError(
                "❌ API Key is missing! Please set QWEN_API_KEY or DASHSCOPE_API_KEY "
                "in your .env file, or run with: uv run --env-file .env"
            )

# Expose settings instance
settings = Settings()

# Automatically run validation on startup
settings.validate()

# ✅ EXPOSE SPECIFIC SETTINGS AT THE MODULE LEVEL
# This allows other modules to import them directly: 
# from config.settings import QWEN_API_KEY, QWEN_BASE_URL, MODEL_NAME, GUARDRAIL_MODEL_NAME
QWEN_API_KEY = settings.api_key
QWEN_BASE_URL = settings.QWEN_BASE_URL
MODEL_NAME = settings.MODEL_NAME
GUARDRAIL_MODEL_NAME = settings.GUARDRAIL_MODEL_NAME


_llm_client = None

def get_llm_client():
    """
    Returns a singleton OpenAI-compatible client configured with the project settings.
    This is used by the guardrails and orchestrator to interact with the Qwen/DashScope API.
    """
    global _llm_client
    if _llm_client is None:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "The 'openai' package is required for the LLM client. "
                "Install it via: uv pip install openai"
            )
            
        if not settings.api_key:
            raise ValueError("API key is missing. Cannot initialize LLM client.")
            
        _llm_client = OpenAI(
            api_key=settings.api_key,
            base_url=settings.QWEN_BASE_URL
        )
    return _llm_client


def _check_env_file_permissions():
    """Warns if the .env file has insecure permissions (readable by others)."""
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        file_stat = env_path.stat()
        # Check if 'others' have read access (octal 0o004)
        if file_stat.st_mode & stat.S_IROTH:
            logger.warning(
                "⚠️ SECURITY WARNING: Your .env file is readable by other users on this system! "
                "Run: chmod 600 .env"
            )

# Run this check on startup
_check_env_file_permissions()