# src/worker/config.py

import os

class Config:
    # Redis configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")    # default to localhost  [oai_citation:28‡Medium](https://medium.com/the-pythonworld/best-practices-for-structuring-a-python-project-like-a-pro-be6013821168?utm_source=chatgpt.com) [oai_citation:29‡Discussions on Python.org](https://discuss.python.org/t/python-project-structure/36119?utm_source=chatgpt.com)
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))      # default Redis port  [oai_citation:30‡Medium](https://medium.com/the-pythonworld/best-practices-for-structuring-a-python-project-like-a-pro-be6013821168?utm_source=chatgpt.com) [oai_citation:31‡Discussions on Python.org](https://discuss.python.org/t/python-project-structure/36119?utm_source=chatgpt.com)

    # Polling/heartbeat interval (seconds)
    POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 30))  # default to 30s  [oai_citation:32‡Medium](https://medium.com/the-pythonworld/best-practices-for-structuring-a-python-project-like-a-pro-be6013821168?utm_source=chatgpt.com) [oai_citation:33‡Discussions on Python.org](https://discuss.python.org/t/python-project-structure/36119?utm_source=chatgpt.com)

    # Docker socket path
    DOCKER_SOCKET = os.getenv("DOCKER_SOCKET", "/var/run/docker.sock")  # readonly mount recommended  [oai_citation:34‡Snyk](https://snyk.io/blog/best-practices-containerizing-python-docker/?utm_source=chatgpt.com) [oai_citation:35‡Docker Documentation](https://docs.docker.com/build/building/best-practices/?utm_source=chatgpt.com)

    # Discord webhook for batched alerts
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

    # Log level
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    # Worker Host ID (should be unique per host)
    HOST_ID = os.getenv("HOST_ID", None)  # e.g. from /etc/worker/host_id, else fallback  [oai_citation:36‡Medium](https://medium.com/the-pythonworld/best-practices-for-structuring-a-python-project-like-a-pro-be6013821168?utm_source=chatgpt.com) [oai_citation:37‡Discussions on Python.org](https://discuss.python.org/t/python-project-structure/36119?utm_source=chatgpt.com)

    @classmethod
    def validate(cls):
        if not cls.HOST_ID:
            raise RuntimeError("HOST_ID not set; must provide unique host identifier")

# Perform validation on import
Config.validate()