"""FastAPI routes for worker - FIXED IMPORTS."""

import logging
import os
import socket
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
    """Health check endpoint."""
    try:
        # Test system collector
        system_metrics = await system_collector.collect_metrics()
        system_ok = system_metrics is not None
        
        # Test docker collector
        docker_metrics = await docker_collector.collect_metrics()
        docker_ok = isinstance(docker_metrics, list)
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "system_collector": "ok" if system_ok else "error",
                "docker_collector": "ok" if docker_ok else "error",
                "command_executor": "ok"
            },
            "worker_info": {
                "hostname": socket.gethostname(),
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
    """Get worker information for registration."""
    try:
        hostname = socket.gethostname()
        
        # Get network interface info
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        
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
        except:
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