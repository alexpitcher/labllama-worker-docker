"""Main worker application with bot registration and heartbeat - FIXED."""

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
    """Main worker class with registration and heartbeat - FIXED."""
    
    def __init__(self):
        self.bot_url = os.getenv("LABLLAMA_BOT_URL", "http://localhost:8000")
        self.worker_port = int(os.getenv("WORKER_PORT", "8080"))
        self.worker_host = os.getenv("WORKER_HOST", "0.0.0.0")
        self.heartbeat_interval = int(os.getenv("HEARTBEAT_INTERVAL", "30"))
        
        self.session = None
        self.heartbeat_task = None
        self.shutdown_event = asyncio.Event()
        
        logger.info(f"Worker configured - Bot URL: {self.bot_url}")
        
    async def start(self):
        """Start the worker with registration and heartbeat."""
        logger.info(f"Starting LabLlama Worker on {self.worker_host}:{self.worker_port}"
        '''                                                                                                                                                         
                                         bbbbbbbb                                                                                                        
LLLLLLLLLLL                              b::::::b            LLLLLLLLLLL             lllllll                                                             
L:::::::::L                              b::::::b            L:::::::::L             l:::::l                                                             
L:::::::::L                              b::::::b            L:::::::::L             l:::::l                                                             
LL:::::::LL                               b:::::b            LL:::::::LL             l:::::l                                                             
  L:::::L                 aaaaaaaaaaaaa   b:::::bbbbbbbbb      L:::::L                l::::l   aaaaaaaaaaaaa      mmmmmmm    mmmmmmm     aaaaaaaaaaaaa   
  L:::::L                 a::::::::::::a  b::::::::::::::bb    L:::::L                l::::l   a::::::::::::a   mm:::::::m  m:::::::mm   a::::::::::::a  
  L:::::L                 aaaaaaaaa:::::a b::::::::::::::::b   L:::::L                l::::l   aaaaaaaaa:::::a m::::::::::mm::::::::::m  aaaaaaaaa:::::a 
  L:::::L                          a::::a b:::::bbbbb:::::::b  L:::::L                l::::l            a::::a m::::::::::::::::::::::m           a::::a 
  L:::::L                   aaaaaaa:::::a b:::::b    b::::::b  L:::::L                l::::l     aaaaaaa:::::a m:::::mmm::::::mmm:::::m    aaaaaaa:::::a 
  L:::::L                 aa::::::::::::a b:::::b     b:::::b  L:::::L                l::::l   aa::::::::::::a m::::m   m::::m   m::::m  aa::::::::::::a 
  L:::::L                a::::aaaa::::::a b:::::b     b:::::b  L:::::L                l::::l  a::::aaaa::::::a m::::m   m::::m   m::::m a::::aaaa::::::a 
  L:::::L         LLLLLLa::::a    a:::::a b:::::b     b:::::b  L:::::L         LLLLLL l::::l a::::a    a:::::a m::::m   m::::m   m::::ma::::a    a:::::a 
LL:::::::LLLLLLLLL:::::La::::a    a:::::a b:::::bbbbbb::::::bLL:::::::LLLLLLLLL:::::Ll::::::la::::a    a:::::a m::::m   m::::m   m::::ma::::a    a:::::a 
L::::::::::::::::::::::La:::::aaaa::::::a b::::::::::::::::b L::::::::::::::::::::::Ll::::::la:::::aaaa::::::a m::::m   m::::m   m::::ma:::::aaaa::::::a 
L::::::::::::::::::::::L a::::::::::aa:::ab:::::::::::::::b  L::::::::::::::::::::::Ll::::::l a::::::::::aa:::am::::m   m::::m   m::::m a::::::::::aa:::a
LLLLLLLLLLLLLLLLLLLLLLLL  aaaaaaaaaa  aaaabbbbbbbbbbbbbbbb   LLLLLLLLLLLLLLLLLLLLLLLLllllllll  aaaaaaaaaa  aaaammmmmm   mmmmmm   mmmmmm  aaaaaaaaaa  aaaa
''')
        logger.info(f"Will register with bot at: {self.bot_url}")
        
        # Create HTTP session
        self.session = aiohttp.ClientSession()
        
        # Start FastAPI server
        config = uvicorn.Config(
            app=app,
            host=self.worker_host,
            port=self.worker_port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        # Start server in background
        server_task = asyncio.create_task(server.serve())
        
        # Wait a moment for server to start
        await asyncio.sleep(2)
        
        # Register with bot
        await self.register_with_bot()
        
        # Start heartbeat
        self.heartbeat_task = asyncio.create_task(self.heartbeat_loop())
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        try:
            await server_task
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            await self.shutdown()
    
    async def register_with_bot(self):
        """Register this worker with the bot - FIXED."""
        try:
            # FIXED: Get worker info from our own /info endpoint
            worker_url = f"http://localhost:{self.worker_port}/info"
            logger.debug(f"Getting worker info from: {worker_url}")
            
            async with self.session.get(worker_url) as response:
                if response.status == 200:
                    worker_info = await response.json()
                    logger.debug(f"Worker info retrieved: {worker_info}")
                else:
                    logger.error(f"Failed to get worker info: HTTP {response.status}")
                    return
            
            # FIXED: Register with the BOT at correct endpoint
            registration_url = f"{self.bot_url}/api/workers/register"
            logger.info(f"Registering with bot at: {registration_url}")
            
            async with self.session.post(registration_url, json=worker_info) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Successfully registered with bot: {result.get('message', 'OK')}")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Registration failed ({response.status}): {error_text}")
                    
        except Exception as e:
            logger.error(f"❌ Failed to register with bot: {e}")
            logger.debug(f"Bot URL was: {self.bot_url}")
    
    async def send_heartbeat(self):
        """Send heartbeat to bot - FIXED."""
        try:
            # FIXED: Send to BOT, not ourselves
            heartbeat_url = f"{self.bot_url}/api/workers/heartbeat"
            
            # Get current worker status from our own health endpoint
            health_url = f"http://localhost:{self.worker_port}/health"
            
            async with self.session.get(health_url) as response:
                if response.status == 200:
                    health_data = await response.json()
                else:
                    health_data = {"status": "unhealthy", "worker_info": {"hostname": "unknown"}}
            
            # FIXED: Extract worker ID properly
            worker_id = health_data.get("worker_info", {}).get("hostname", "unknown")
            
            heartbeat_data = {
                "worker_id": worker_id,
                "status": health_data.get("status", "unknown"),
                "timestamp": health_data.get("timestamp"),
                "services": health_data.get("services", {})
            }
            
            logger.debug(f"Sending heartbeat to: {heartbeat_url}")
            
            async with self.session.post(heartbeat_url, json=heartbeat_data) as response:
                if response.status == 200:
                    logger.debug("💓 Heartbeat sent successfully")
                else:
                    error_text = await response.text()
                    logger.warning(f"❌ Heartbeat failed ({response.status}): {error_text}")
                    
        except Exception as e:
            logger.error(f"❌ Failed to send heartbeat: {e}")
    
    async def heartbeat_loop(self):
        """Continuous heartbeat loop - FIXED."""
        logger.info(f"Starting heartbeat loop (interval: {self.heartbeat_interval}s)")
        
        # Wait a bit before first heartbeat to ensure registration
        await asyncio.sleep(5)
        
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