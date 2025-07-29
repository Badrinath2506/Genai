import os
from pathlib import Path
from typing import Dict, Any

class Config:
    # API Configurations
    CIRCUIT_API_URL = "http://localhost:8001"
    INVOICE_API_URL = "http://localhost:8000"
    
    # Logging Config
    LOG_BASE_PATH = Path("./logs")
    LOG_LEVEL = "DEBUG"
    
    # NLP Config
    NLP_MAX_RETRIES = 3
    
    # Timeouts
    API_TIMEOUT = 30.0
    
    @classmethod
    def get_logging_config(cls) -> Dict[str, Any]:
        os.makedirs(cls.LOG_BASE_PATH, exist_ok=True)
        
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "fmt": "%(asctime)s %(name)s %(levelname)s %(message)s"
                }
            },
            "handlers": {
                "prompt_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "json",
                    "filename": cls.LOG_BASE_PATH / "prompts" / "prompts.log",
                    "maxBytes": 10 * 1024 * 1024,  # 10MB
                    "backupCount": 5
                },
                "response_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "json",
                    "filename": cls.LOG_BASE_PATH / "responses" / "responses.log",
                    "maxBytes": 10 * 1024 * 1024,
                    "backupCount": 5
                },
                "debug_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "standard",
                    "filename": cls.LOG_BASE_PATH / "debug" / "debug.log",
                    "maxBytes": 5 * 1024 * 1024,
                    "backupCount": 3
                },
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "json",
                    "filename": cls.LOG_BASE_PATH / "errors" / "errors.log",
                    "maxBytes": 5 * 1024 * 1024,
                    "backupCount": 3
                },
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout"
                }
            },
            "loggers": {
                "prompt_logger": {
                    "handlers": ["prompt_file"],
                    "level": "INFO",
                    "propagate": False
                },
                "response_logger": {
                    "handlers": ["response_file"],
                    "level": "INFO",
                    "propagate": False
                },
                "query_system": {
                    "handlers": ["debug_file", "error_file", "console"],
                    "level": cls.LOG_LEVEL,
                    "propagate": False
                }
            }
        }

config = Config()