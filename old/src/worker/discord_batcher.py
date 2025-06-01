# src/worker/discord_batcher.py

import threading
import time
import requests
import logging
from worker.config import Config

logger = logging.getLogger("worker.discord_batcher")

class DiscordBatchSender(threading.Thread):
    def __init__(self, queue: list):
        super().__init__(daemon=True)
        self.queue = queue
        self.webhook = Config.DISCORD_WEBHOOK_URL

    def run(self):
        logger.info("Discord batch sender started.")
        while True:
            time.sleep(300)  # 5-minute interval  [oai_citation:60‡Docker Documentation](https://docs.docker.com/build/building/best-practices/?utm_source=chatgpt.com) [oai_citation:61‡Real Kinetic Blog](https://blog.realkinetic.com/building-minimal-docker-containers-for-python-applications-37d0272c52f3?utm_source=chatgpt.com)
            if not self.queue or not self.webhook:
                continue
            # Build embed
            fields = [{"name": f"Alert #{i+1}", "value": msg, "inline": False}
                      for i, msg in enumerate(self.queue)]
            payload = {
                "embeds": [
                    {
                        "title": f"Worker Alerts: {Config.HOST_ID}",
                        "color": 16711680,
                        "fields": fields
                    }
                ]
            }
            try:
                requests.post(self.webhook, json=payload, timeout=5)
                logger.info(f"Sent {len(self.queue)} alerts to Discord.")
                self.queue.clear()
            except Exception as e:
                logger.error(f"Discord POST error: {e}")