"""Data models for worker - reusing Phase 1 patterns."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SystemMetrics:
    """System-level performance metrics - matches Phase 1 exactly."""
    
    hostname: str
    timestamp: datetime
    cpu_percent: float
    cpu_count: int
    memory_total_gb: float
    memory_used_gb: float
    memory_percent: float
    disk_usage: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hostname": self.hostname,
            "timestamp": self.timestamp,
            "cpu": {
                "percent": self.cpu_percent,
                "count": self.cpu_count
            },
            "memory": {
                "total_gb": self.memory_total_gb,
                "used_gb": self.memory_used_gb,
                "percent": self.memory_percent
            },
            "disk": self.disk_usage
        }


@dataclass
class DockerContainer:
    """Docker container metrics - matches Phase 1 exactly."""
    
    name: str
    container_id: str
    image: str
    status: str
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "id": self.container_id,
            "image": self.image,
            "status": self.status,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "memory_percent": self.memory_percent,
            "timestamp": self.timestamp
        }


@dataclass
class WorkerRegistration:
    """Worker registration data."""
    
    worker_id: str
    hostname: str
    ip_address: str
    port: int
    version: str
    capabilities: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "port": self.port,
            "version": self.version,
            "capabilities": self.capabilities,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class CommandRequest:
    """Safe command execution request."""
    
    command: str
    params: Dict[str, Any]
    timeout: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "params": self.params,
            "timeout": self.timeout
        }


@dataclass
class CommandResult:
    """Command execution result."""
    
    command: str
    success: bool
    output: str
    error: Optional[str]
    execution_time: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat()
        }