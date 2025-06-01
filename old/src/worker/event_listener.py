# src/worker/event_listener.py

import threading
import logging
from datetime import datetime, timezone
import docker
from worker.config import Config

logger = logging.getLogger("worker.event_listener")

class EventListener(threading.Thread):
    def __init__(self, running_containers: set):
        super().__init__(daemon=True)  # daemon thread will exit when main exits  [oai_citation:46‡Medium](https://medium.com/the-pythonworld/best-practices-for-structuring-a-python-project-like-a-pro-be6013821168?utm_source=chatgpt.com) [oai_citation:47‡Discussions on Python.org](https://discuss.python.org/t/python-project-structure/36119?utm_source=chatgpt.com)
        self.running_containers = running_containers
        # Connect to Docker via socket path in config
        self.client = docker.DockerClient(base_url=f"unix://{Config.DOCKER_SOCKET}")

    def run(self):
        logger.info("Event listener thread started.")
        try:
            for raw_event in self.client.events(decode=True, filters={"type": "container"}):
                status = raw_event.get("status")
                cid = raw_event.get("id")
                ts_unix = raw_event.get("time")
                ts = datetime.fromtimestamp(ts_unix, tz=timezone.utc).isoformat()

                # Container name from attributes; validate non-empty
                name = raw_event["Actor"]["Attributes"].get("name", "")
                if status == "start":
                    self.running_containers.add(cid)
                    logger.info({
                        "event": "container_started",
                        "container_id": cid,
                        "container_name": name,
                        "timestamp": ts
                    })
                elif status == "die":
                    exit_code = raw_event["Actor"]["Attributes"].get("exitCode", "")
                    self.running_containers.discard(cid)
                    logger.info({
                        "event": "container_died",
                        "container_id": cid,
                        "container_name": name,
                        "exit_code": exit_code,
                        "timestamp": ts
                    })
                # Additional statuses (e.g., restart) can be added here
        except Exception as e:
            logger.error(f"Event listener error: {e}", exc_info=True)