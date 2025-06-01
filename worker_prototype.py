# worker_prototype.py

import threading
import time
import json
import os
import logging
from datetime import datetime

import docker

# ------------------------------------------------------------------------------
# 1. Logging Setup (JSON‐formatted to stdout)
# ------------------------------------------------------------------------------
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "pid": os.getpid(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

logger = logging.getLogger("worker_prototype")
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# ------------------------------------------------------------------------------
# 2. Docker Client Initialization & Version Check
# ------------------------------------------------------------------------------
try:
    client = docker.from_env()
    docker_version = client.version().get("ApiVersion", "0.0")
    if float(docker_version) < 1.40:
        logger.error(f"Docker API v{docker_version} is too old; need ≥ 1.40")
        raise SystemExit(1)
    logger.info(f"Docker API v{docker_version} detected. Continuing.")
except Exception as e:
    logger.error(f"Failed to initialize Docker client: {e}", exc_info=True)
    raise SystemExit(1)

# ------------------------------------------------------------------------------
# 3. Globals & In‐Memory State
# ------------------------------------------------------------------------------
# In a real worker, this would be host_id from /etc/worker/host_id
HOST_ID = "local-prototype-host"
POLL_INTERVAL = 30  # seconds

running_containers = set()  # track container IDs we know are “running”

# ------------------------------------------------------------------------------
# 4. Event Listener Thread (listens to Docker container events)
# ------------------------------------------------------------------------------
def event_listener():
    """Listens for Docker container start/stop events and logs them."""
    logger.info("Event listener thread started.")
    try:
        for raw_event in client.events(decode=True, filters={"type": "container"}):
            # We're only interested in start/stop (“start”, “die”) events
            status = raw_event.get("status")
            cid = raw_event.get("id")
            ts_unix = raw_event.get("time")
            ts = datetime.utcfromtimestamp(ts_unix).isoformat() + "Z"
            name = raw_event["Actor"]["Attributes"].get("name")

            if status == "start":
                running_containers.add(cid)
                logger.info(json.dumps({
                    "event": "container_started",
                    "host_id": HOST_ID,
                    "container_id": cid,
                    "container_name": name,
                    "timestamp": ts
                }))
            elif status == "die":
                exit_code = raw_event["Actor"]["Attributes"].get("exitCode", "unknown")
                running_containers.discard(cid)
                logger.info(json.dumps({
                    "event": "container_died",
                    "host_id": HOST_ID,
                    "container_id": cid,
                    "container_name": name,
                    "exit_code": exit_code,
                    "timestamp": ts
                }))
            # (You can extend to “restart”, “kill”, etc.)
    except Exception as e:
        logger.error(f"Event listener encountered an error: {e}", exc_info=True)

# ------------------------------------------------------------------------------
# 5. Metrics Collector Thread (polls every POLL_INTERVAL)
# ------------------------------------------------------------------------------
def metrics_collector():
    """Every POLL_INTERVAL seconds, gather and print minimal stats for running containers."""
    while True:
        now = datetime.utcnow().isoformat() + "Z"
        if not running_containers:
            logger.info(json.dumps({
                "event": "metrics_snapshot",
                "host_id": HOST_ID,
                "timestamp": now,
                "containers": []
            }))
        else:
            points = []
            for cid in list(running_containers):
                try:
                    container = client.containers.get(cid)
                    stats = container.stats(stream=False)
                    # Extract a few fields for demonstration:
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
                    # Container may have stopped between event and polling
                    running_containers.discard(cid)
                except Exception as e:
                    logger.warning(f"Failed to get stats for {cid}: {e}")
            # Log the batch of metrics
            logger.info(json.dumps({
                "event": "metrics_snapshot",
                "host_id": HOST_ID,
                "timestamp": now,
                "containers": points
            }))
        # Also emit a “heartbeat” to simulate
        logger.info(json.dumps({
            "event": "heartbeat",
            "host_id": HOST_ID,
            "timestamp": now
        }))
        time.sleep(POLL_INTERVAL)

# ------------------------------------------------------------------------------
# 6. Main Execution
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # Start event listener in a separate daemon thread
    t1 = threading.Thread(target=event_listener, daemon=True)
    t1.start()

    # Start metrics + heartbeat loop on main thread
    try:
        logger.info("Starting metrics collector…")
        metrics_collector()
    except KeyboardInterrupt:
        logger.info("Worker prototype interrupted by user. Exiting.")
    except Exception as e:
        logger.error(f"Worker prototype encountered an error: {e}", exc_info=True)
    finally:
        logger.info("Worker prototype shutdown.")