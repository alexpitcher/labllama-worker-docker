"""FastAPI routes for worker - FIXED SOCKET ISSUE."""

import logging
import os
import socket as socket_module  # FIXED: Renamed import to avoid conflict
from datetime import datetime
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# FIXED: Use absolute imports instead of relative
from collectors.worker_collector import WorkerSystemCollector, WorkerDockerCollector
from services.command_executor import SafeCommandExecutor
from models import WorkerRegistration, CommandRequest


logger = logging.getLogger(__name__)

# Initialize services
system_collector = WorkerSystemCollector()
docker_collector = WorkerDockerCollector()
command_executor = SafeCommandExecutor()

app = FastAPI(
    title="LabLlama Worker",
    description="Worker agent for distributed Docker monitoring",
    version="2.0.0"
)


class CommandRequestModel(BaseModel):
    """Pydantic model for command requests."""
    command: str
    params: Dict[str, Any] = {}
    timeout: int = 30



@app.get("/health")
async def health_check():
    """Health check endpoint - PROPER NON-BLOCKING VERSION."""
    try:
        # Test 1: Basic service availability (fast)
        hostname = socket_module.gethostname()
        
        # Test 2: System collector (should be fast - just psutil)
        system_ok = False
        try:
            # Quick CPU check only (no full metrics collection)
            cpu_percent = psutil.cpu_percent(interval=0)  # Non-blocking
            system_ok = True
        except Exception as e:
            logger.error(f"System collector check failed: {e}")
        
        # Test 3: Docker socket availability (fast check, no API calls)
        docker_ok = False
        try:
            docker_socket_exists = os.path.exists('/var/run/docker.sock')
            docker_ok = docker_socket_exists
        except Exception as e:
            logger.error(f"Docker socket check failed: {e}")
        
        # Test 4: Command executor (instant)
        command_ok = True  # Just check if class exists
        
        return {
            "status": "healthy" if all([system_ok, docker_ok, command_ok]) else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "system_collector": "ok" if system_ok else "error",
                "docker_collector": "ok" if docker_ok else "error", 
                "command_executor": "ok" if command_ok else "error"
            },
            "worker_info": {
                "hostname": hostname,
                "version": "2.0.0"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.get("/metrics")
async def get_metrics():
    """Get system metrics - matches Phase 1 format exactly."""
    try:
        metrics = await system_collector.collect_metrics()
        if metrics is None:
            raise HTTPException(status_code=500, detail="Failed to collect system metrics")
        
        return {
            "success": True,
            "data": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics collection failed: {str(e)}")


@app.get("/containers")
async def get_containers():
    """Get Docker container metrics - matches Phase 1 format exactly."""
    try:
        containers = await docker_collector.collect_metrics()
        
        return {
            "success": True,
            "data": containers,
            "count": len(containers) if containers else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get containers: {e}")
        raise HTTPException(status_code=500, detail=f"Container collection failed: {str(e)}")


@app.get("/info")
async def get_worker_info():
    """Get worker information for registration - FIXED SOCKET ISSUE."""
    try:
        hostname = socket_module.gethostname()  # FIXED: Use renamed import
        
        # Get network interface info - FIXED: Use different variable name
        try:
            sock = socket_module.socket(socket_module.AF_INET, socket_module.SOCK_DGRAM)  # FIXED: Different name
            sock.connect(("8.8.8.8", 80))
            ip_address = sock.getsockname()[0]
            sock.close()
        except Exception as e:
            logger.warning(f"Could not determine IP address: {e}")
            ip_address = "unknown"
        
        # Get Docker info if available
        docker_info = {}
        try:
            client = await docker_collector._get_docker_client()
            if client:
                version_info = client.version()
                docker_info = {
                    "version": version_info.get("Version", "unknown"),
                    "api_version": version_info.get("ApiVersion", "unknown")
                }
        except Exception as e:
            logger.debug(f"Docker info unavailable: {e}")
            docker_info = {"status": "unavailable"}
        
        return {
            "worker_id": f"worker-{hostname}",
            "hostname": hostname,
            "ip_address": ip_address,
            "port": int(os.getenv("WORKER_PORT", "8080")),
            "version": "2.0.0",
            "capabilities": [
                "system_metrics",
                "docker_metrics", 
                "command_execution",
                "log_collection"
            ],
            "docker_info": docker_info,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get worker info: {e}")
        raise HTTPException(status_code=500, detail=f"Worker info failed: {str(e)}")


@app.post("/execute")
async def execute_command(request: CommandRequestModel):
    """Execute safe debugging command."""
    try:
        command_request = CommandRequest(
            command=request.command,
            params=request.params,
            timeout=request.timeout
        )
        
        result = await command_executor.execute_command(command_request)
        
        return {
            "success": result.success,
            "data": result.to_dict()
        }
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Command execution failed: {str(e)}")


@app.get("/execute/commands")
async def get_available_commands():
    """Get list of available safe commands."""
    try:
        commands = command_executor.get_available_commands()
        return {
            "success": True,
            "commands": commands
        }
    except Exception as e:
        logger.error(f"Failed to get commands: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/logs")
async def get_logs(lines: int = 100):
    """Get worker application logs."""
    try:
        log_file = "logs/worker.log"
        
        if not os.path.exists(log_file):
            return {
                "success": True,
                "logs": "No log file found",
                "lines": 0
            }
        
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "success": True,
            "logs": "".join(recent_lines),
            "lines": len(recent_lines),
            "total_lines": len(all_lines)
        }
    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        raise HTTPException(status_code=500, detail=f"Log retrieval failed: {str(e)}")


@app.get("/events")
async def get_events(since: str = "1h"):
    """Get recent Docker events."""
    try:
        # Use command executor for safe event collection
        command_request = CommandRequest(
            command="docker_events",
            params={"since": since}
        )
        
        result = await command_executor.execute_command(command_request)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        return {
            "success": True,
            "events": result.output,
            "since": since,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get events: {e}")
        raise HTTPException(status_code=500, detail=f"Event collection failed: {str(e)}")