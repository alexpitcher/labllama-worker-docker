"""Main worker application with bot registration and heartbeat."""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

import aiohttp
import uvicorn
from dotenv import load_dotenv

from api.routes import app
from config.logging import setup_logging


# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class LabLlamaWorker:
    """Main worker class with registration and heartbeat."""
    
    def __init__(self):
        self.bot_url = os.getenv("LABLLAMA_BOT_URL", "http://localhost:8000")
        self.worker_port = int(os.getenv("WORKER_PORT", "8080"))
        self.worker_host = os.getenv("WORKER_HOST", "0.0.0.0")
        self.heartbeat_interval = int(os.getenv("HEARTBEAT_INTERVAL", "30"))
        
        self.session = None
        self.heartbeat_task = None
        self.shutdown_event = asyncio.Event()
        
    async def start(self):
        """Start the worker with registration and heartbeat."""
        logger.info(f"Starting LabLlama Worker on {self.worker_host}:{self.worker_port}")
        logger.info(f"Bot URL: {self.bot_url}")
        
        # Create HTTP session
        self.session = aiohttp.ClientSession()
        
        # Register with bot
        await self.register_with_bot()
        
        # Start heartbeat
        self.heartbeat_task = asyncio.create_task(self.heartbeat_loop())
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Start FastAPI server
        config = uvicorn.Config(
            app=app,
            host=self.worker_host,
            port=self.worker_port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        try:
            await server.serve()
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            await self.shutdown()
    
    async def register_with_bot(self):
        """Register this worker with the bot."""
        try:
            # Get worker info
            async with self.session.get(f"http://localhost:{self.worker_port}/info") as response:
                if response.status == 200:
                    worker_info = await response.json()
                else:
                    logger.error("Failed to get worker info for registration")
                    return
            
            # Register with bot
            registration_url = f"{self.bot_url}/api/workers/register"
            
            async with self.session.post(registration_url, json=worker_info) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Successfully registered with bot: {result}")
                else:
                    error_text = await response.text()
                    logger.error(f"Registration failed ({response.status}): {error_text}")
                    
        except Exception as e:
            logger.error(f"Failed to register with bot: {e}")
    
    async def send_heartbeat(self):
        """Send heartbeat to bot."""
        try:
            heartbeat_url = f"{self.bot_url}/api/workers/heartbeat"
            
            # Get current worker status
            async with self.session.get(f"http://localhost:{self.worker_port}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                else:
                    health_data = {"status": "unhealthy"}
            
            heartbeat_data = {
                "worker_id": health_data.get("worker_info", {}).get("hostname", "unknown"),
                "status": health_data.get("status", "unknown"),
                "timestamp": health_data.get("timestamp"),
                "services": health_data.get("services", {})
            }
            
            async with self.session.post(heartbeat_url, json=heartbeat_data) as response:
                if response.status == 200:
                    logger.debug("Heartbeat sent successfully")
                else:
                    error_text = await response.text()
                    logger.warning(f"Heartbeat failed ({response.status}): {error_text}")
                    
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
    
    async def heartbeat_loop(self):
        """Continuous heartbeat loop."""
        logger.info(f"Starting heartbeat loop (interval: {self.heartbeat_interval}s)")
        
        while not self.shutdown_event.is_set():
            try:
                await self.send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                logger.info("Heartbeat loop cancelled")
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(self.heartbeat_interval)
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler():
            logger.info("Received shutdown signal")
            self.shutdown_event.set()
        
        # Register signal handlers
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, lambda s, f: signal_handler())
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, lambda s, f: signal_handler())
    
    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("Shutting down worker...")
        
        self.shutdown_event.set()
        
        # Cancel heartbeat
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Close HTTP session
        if self.session:
            await self.session.close()
        
        logger.info("Worker shutdown complete")


async def main():
    """Main application entry point."""
    worker = LabLlamaWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Worker encountered an error: {e}")
    finally:
        await worker.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)