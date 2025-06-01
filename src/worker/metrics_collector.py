# src/worker/metrics_collector.py

import threading
import time
import logging
from datetime import datetime, timezone
import docker
import redis
import requests
from worker.config import Config

logger = logging.getLogger("worker.metrics_collector")

class MetricsCollector(threading.Thread):
    def __init__(self, running_containers: set, discord_queue: list):
        super().__init__(daemon=True)
        self.running_containers = running_containers
        self.discord_queue = discord_queue
        # Docker client
        self.client = docker.DockerClient(base_url=f"unix://{Config.DOCKER_SOCKET}")
        # Redis client
        self.redis = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=0)

    def _send_heartbeat(self):
        now_ts = int(time.time())
        key = f"heartbeat:{Config.HOST_ID}"
        try:
            self.redis.set(key, now_ts, ex=2 * Config.POLL_INTERVAL)
        except Exception as e:
            logger.error(f"Failed to set heartbeat in Redis: {e}")
            self.discord_queue.append(f"Heartbeat failure: {e}")

    def _collect_and_send_metrics(self):
        now = datetime.now(timezone.utc).isoformat()
        points = []
        for cid in list(self.running_containers):
            try:
                container = self.client.containers.get(cid)
                stats = container.stats(stream=False)
                cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
                num_cpus = len(stats["cpu_stats"]["cpu_usage"].get("percpu_usage", [])) or 1
                cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0 if system_delta > 0 else 0.0

                mem_usage = stats["memory_stats"]["usage"]
                mem_limit = stats["memory_stats"]["limit"]
                mem_percent = (mem_usage / mem_limit) * 100.0 if mem_limit > 0 else 0.0

                points.append({
                    "container_id": cid,
                    "container_name": container.name,
                    "cpu_percent": round(cpu_percent, 2),
                    "memory_usage": mem_usage,
                    "memory_limit": mem_limit,
                    "memory_percent": round(mem_percent, 2)
                })
            except docker.errors.NotFound:
                # Container disappeared between event and poll
                self.running_containers.discard(cid)
            except Exception as e:
                logger.warning(f"Metrics error for {cid}: {e}")
                self.discord_queue.append(f"Metrics failure for {cid}: {e}")

        payload = {
            "host_id": Config.HOST_ID,
            "timestamp": now,
            "containers": points,
            "schema_version": 2
        }
        headers = {"Authorization": f"Bearer {os.getenv('API_KEY', '')}"}

        # Replace with actual server URL or environment variable
        url = os.getenv("METRICS_URL", "http://localhost:5000/api/metrics/batch")
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=5)
            if not resp.ok:
                raise ValueError(f"HTTP {resp.status_code}: {resp.text}")
            logger.info({
                "event": "metrics_sent",
                "count": len(points),
                "timestamp": now
            })
        except Exception as e:
            logger.error(f"Failed to send metrics: {e}")
            self.discord_queue.append(f"Metrics POST failure: {e}")

    def run(self):
        logger.info("Metrics collector thread started.")
        while True:
            self._send_heartbeat()
            self._collect_and_send_metrics()
            time.sleep(Config.POLL_INTERVAL)