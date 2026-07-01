# config/settings.py
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

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

class Settings:
    def __init__(self):
        # Bind variables directly to the instance
        self.QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
        self.DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
        
        # Default fallback points to your Aliyun MaaS production endpoint
        self.QWEN_BASE_URL: str = os.getenv(
            "QWEN_BASE_URL", 
            "https://ws-zp9gpq4ly3nzvc4s.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
        )
        
        # Centralized Model Name definition
        self.MODEL_NAME: str = os.getenv("MODEL_NAME", "qwen3.7-max")

    @property
    def api_key(self) -> str:
        """Returns the first available API key."""
        return self.QWEN_API_KEY or self.DASHSCOPE_API_KEY

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