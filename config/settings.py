import os
from pathlib import Path
from dotenv import load_dotenv

# Locate the .env file at the project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Settings:
    QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
    QWEN_BASE_URL: str = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    
    @classmethod
    def validate(cls):
        if not cls.QWEN_API_KEY:
            raise ValueError("❌ QWEN_API_KEY is missing! Please check your .env file.")

# Expose settings instance
settings = Settings()