import os
from pathlib import Path
from datetime import datetime

class Config:
    # API endpoints
    CIRCUIT_API_URL = "http://localhost:8001/query"
    INVOICE_API_URL = "http://localhost:8000/query"
    
    # Logging configuration
    LOG_BASE_PATH = "./logs"
    LOG_MAX_SIZE = 5 * 1024 * 1024  # 5MB
    LOG_BACKUP_COUNT = 3
    
    # NLP settings
    MAX_RESPONSE_LENGTH = 500
    
    @staticmethod
    def setup_logging():
        """Ensure log directories exist"""
        os.makedirs(Config.LOG_BASE_PATH, exist_ok=True)
        current_date = datetime.now().strftime("%Y%m%d")
        
        return {
            "prompt_log": Path(Config.LOG_BASE_PATH) / f"prompts_{current_date}.log",
            "response_log": Path(Config.LOG_BASE_PATH) / f"responses_{current_date}.log",
            "debug_log": Path(Config.LOG_BASE_PATH) / f"debug_{current_date}.log",
            "error_log": Path(Config.LOG_BASE_PATH) / f"error_{current_date}.log"
        }

config = Config()