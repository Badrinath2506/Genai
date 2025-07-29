import logging
from datetime import datetime  # ✅ THIS IS WHAT YOU NEED

class QueryLogger:
    def __init__(self):
        self.logger = logging.getLogger("query_logger")
        self.logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        if not self.logger.hasHandlers():
            self.logger.addHandler(handler)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)

    def log_prompt(self, prompt, session_id=None):
        self.info({
            "type": "prompt",
            "prompt": prompt,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()  # ✅ NOW IT WORKS
        })

    def log_response(self, prompt, response, session_id=None):
        self.info({
            "type": "response",
            "prompt": prompt,
            "response": response,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        })

logger = QueryLogger()
