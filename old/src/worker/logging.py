# src/worker/logger.py

import logging
import os
import sys
import json
from worker.config import Config

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "host_id": Config.HOST_ID,
            "pid": os.getpid(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logger(name: str = "worker") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(Config.LOG_LEVEL)
    handler = logging.StreamHandler(sys.stdout)  # write JSON logs to stdout  [oai_citation:42‡Medium](https://medium.com/the-pythonworld/best-practices-for-structuring-a-python-project-like-a-pro-be6013821168?utm_source=chatgpt.com) [oai_citation:43‡Stack Overflow](https://stackoverflow.com/questions/45375480/docker-setup-with-complex-project-structure?utm_source=chatgpt.com)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger