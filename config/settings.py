# config/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Locate the .env file at the project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Settings:
    def __init__(self):
        # Bind variables directly to the instance (self) so getattr() and dot notation work flawlessly
        self.QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
        
        # Default fallback points to your Aliyun MaaS production endpoint matrix
        self.QWEN_BASE_URL: str = os.getenv(
            "QWEN_BASE_URL", 
            "https://ws-zp9gpq4ly3nzvc4s.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
        )
        
        # Centralized Model Name definition — change it here to update the entire swarm instantly
        self.MODEL_NAME: str = os.getenv("MODEL_NAME", "qwen3.7-max")

    def validate(self):
        """Validates that critical authentication variables are loaded."""
        if not self.QWEN_API_KEY:
            raise ValueError("❌ QWEN_API_KEY is missing! Please check your .env file.")

# Expose settings instance
settings = Settings()

# Automatically run validation on startup to catch configuration bugs before the API fires
settings.validate()