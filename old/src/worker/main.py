# src/worker/main.py

import threading
import logging
from worker.config import Config
from worker.logger import setup_logger
from worker.event_listener import EventListener
from worker.metrics_collector import MetricsCollector

def main():
    logger = setup_logger("worker.main")
    logger.info("Starting worker...")

    # Shared state: set of container IDs currently known to be running
    running_containers = set()
    # In-memory queue for messages to send to Discord
    discord_queue = []

    # Start event listener
    event_thread = EventListener(running_containers)
    event_thread.start()

    # Start metrics collector
    metrics_thread = MetricsCollector(running_containers, discord_queue)
    metrics_thread.start()

    # Discord batch sender thread
    from worker.discord_batcher import DiscordBatchSender
    discord_thread = DiscordBatchSender(discord_queue)
    discord_thread.start()

    # Block forever
    event_thread.join()
    metrics_thread.join()
    discord_thread.join()

if __name__ == "__main__":
    main()