import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any
from ..config import config

class QueryLogger:
    def __init__(self):
        self.log_paths = config.setup_logging()
        self._setup_loggers()
    
    def _setup_loggers(self):
        """Configure all loggers with appropriate handlers"""
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Main application logger
        self.app_logger = logging.getLogger("query_system")
        self.app_logger.setLevel(logging.DEBUG)
        
        # Debug handler
        debug_handler = RotatingFileHandler(
            self.log_paths["debug_log"],
            maxBytes=config.LOG_MAX_SIZE,
            backupCount=config.LOG_BACKUP_COUNT
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        self.app_logger.addHandler(debug_handler)
        
        # Error handler
        error_handler = RotatingFileHandler(
            self.log_paths["error_log"],
            maxBytes=config.LOG_MAX_SIZE,
            backupCount=config.LOG_BACKUP_COUNT
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.app_logger.addHandler(error_handler)
        
        # Specialized loggers
        self.prompt_logger = self._create_special_logger("prompt", self.log_paths["prompt_log"])
        self.response_logger = self._create_special_logger("response", self.log_paths["response_log"])
    
    def _create_special_logger(self, name: str, path: Path) -> logging.Logger:
        """Create a dedicated logger for specific purposes"""
        logger = logging.getLogger(f"query_system.{name}")
        logger.setLevel(logging.INFO)
        
        handler = RotatingFileHandler(
            path,
            maxBytes=config.LOG_MAX_SIZE,
            backupCount=config.LOG_BACKUP_COUNT
        )
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logger.addHandler(handler)
        return logger
    
    def log_prompt(self, prompt: str):
        """Log user prompt to dedicated prompt log"""
        self.prompt_logger.info(prompt)
        self.app_logger.debug(f"User prompt logged: {prompt}")
    
    def log_response(self, prompt: str, response: Dict[str, Any]):
        """Log query and response together"""
        log_entry = {
            "prompt": prompt,
            "response": response
        }
        self.response_logger.info(json.dumps(log_entry))
        self.app_logger.debug(f"Query response logged for prompt: {prompt[:50]}...")
    
    def log_error(self, error: Exception, context: str = ""):
        """Log errors with context"""
        self.app_logger.error(f"{context}: {str(error)}", exc_info=True)

logger = QueryLogger()