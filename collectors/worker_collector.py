"""Worker collector - reuses exact Phase 1 logic - FIXED IMPORTS."""

import logging
import os
import socket
from datetime import datetime
from typing import Any, Dict, List, Optional

import docker
import psutil

# FIXED: Use absolute import instead of relative
from models import SystemMetrics, DockerContainer


logger = logging.getLogger(__name__)


class WorkerSystemCollector:
    """Collects system-level metrics using psutil - identical to Phase 1."""
    
    def __init__(self):
        self.hostname = socket.gethostname()
        
    async def collect_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect system metrics using psutil - EXACT Phase 1 logic."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_total_gb = memory.total / (1024**3)
            memory_used_gb = memory.used / (1024**3)
            memory_percent = memory.percent
            
            # Disk metrics
            disk_usage = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "total_gb": usage.total / (1024**3),
                        "used_gb": usage.used / (1024**3),
                        "percent": (usage.used / usage.total) * 100
                    })
                except PermissionError:
                    # Skip partitions we can't access
                    continue
            
            # Create SystemMetrics object
            metrics = SystemMetrics(
                hostname=self.hostname,
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                memory_total_gb=memory_total_gb,
                memory_used_gb=memory_used_gb,
                memory_percent=memory_percent,
                disk_usage=disk_usage
            )
            
            logger.debug(f"Collected system metrics: CPU {cpu_percent}%, Memory {memory_percent}%")
            return metrics.to_dict()
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return None


class WorkerDockerCollector:
    """Collects Docker container metrics - identical to Phase 1."""
    
    def __init__(self):
        self.docker_client = None
        
    async def _get_docker_client(self):
        """Get Docker client, create if needed - EXACT Phase 1 logic."""
        if self.docker_client is None:
            try:
                socket_path = '/var/run/docker.sock'
                socket_exists = os.path.exists(socket_path)
                
                logger.debug(f"Docker socket exists: {socket_exists}")
                
                if not socket_exists:
                    logger.warning("Docker socket not found at /var/run/docker.sock")
                    return None
                
                # Try the most basic socket connection approach
                try:
                    logger.debug("Attempting basic Docker socket connection")
                    import docker.client
                    client = docker.client.DockerClient(base_url='unix:///var/run/docker.sock')
                    
                    # Test with version call
                    version_info = client.version()
                    logger.info(f"Docker connected successfully - Engine version: {version_info.get('Version', 'unknown')}")
                    self.docker_client = client
                    return self.docker_client
                    
                except Exception as e:
                    logger.error(f"Basic socket connection failed: {e}")
                
                # Try alternative socket connection with different syntax
                try:
                    logger.debug("Trying alternative Docker connection")
                    client = docker.DockerClient(base_url='unix://var/run/docker.sock')  # No triple slash
                    version_info = client.version()
                    logger.info(f"Docker connected with alternative syntax - Engine version: {version_info.get('Version', 'unknown')}")
                    self.docker_client = client
                    return self.docker_client
                    
                except Exception as e:
                    logger.error(f"Alternative socket connection failed: {e}")
                
                # Try with explicit socket API
                try:
                    logger.debug("Trying Docker with APIClient")
                    from docker import APIClient
                    api_client = APIClient(base_url='unix:///var/run/docker.sock')
                    version_info = api_client.version()
                    
                    # Create DockerClient from working APIClient
                    client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
                    logger.info(f"Docker APIClient connection successful - Engine version: {version_info.get('Version', 'unknown')}")
                    self.docker_client = client
                    return self.docker_client
                    
                except Exception as e:
                    logger.error(f"APIClient connection failed: {e}")
                
                logger.warning("All Docker connection methods failed")
                return None
                
            except Exception as e:
                logger.error(f"Failed to initialize Docker client: {e}")
                return None
                
        return self.docker_client
    
    async def collect_metrics(self) -> Optional[List[Dict[str, Any]]]:
        """Collect Docker container metrics - EXACT Phase 1 logic."""
        try:
            client = await self._get_docker_client()
            if client is None:
                logger.debug("Docker client not available, skipping container metrics")
                return []  # Return empty list instead of None
            
            containers = client.containers.list(all=True)
            container_metrics = []
            
            for container in containers:
                try:
                    # Get basic container info
                    cpu_percent = 0.0
                    memory_mb = 0.0
                    memory_percent = 0.0
                    
                    # Only get detailed stats for running containers
                    if container.status == "running":
                        try:
                            stats = container.stats(stream=False)
                            
                            # Calculate CPU percentage more safely
                            if ('cpu_stats' in stats and 'precpu_stats' in stats and 
                                'cpu_usage' in stats['cpu_stats'] and 'cpu_usage' in stats['precpu_stats']):
                                
                                cpu_delta = (stats['cpu_stats']['cpu_usage']['total_usage'] - 
                                           stats['precpu_stats']['cpu_usage']['total_usage'])
                                system_delta = (stats['cpu_stats']['system_cpu_usage'] - 
                                              stats['precpu_stats']['system_cpu_usage'])
                                
                                if system_delta > 0 and cpu_delta >= 0:
                                    cpu_count = len(stats['cpu_stats']['cpu_usage'].get('percpu_usage', [1]))
                                    cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0
                                    # Cap at reasonable values
                                    cpu_percent = min(cpu_percent, 100.0 * cpu_count)
                            
                            # Memory usage calculation
                            if 'memory_stats' in stats:
                                memory_usage = stats['memory_stats'].get('usage', 0)
                                memory_limit = stats['memory_stats'].get('limit', 1)
                                memory_mb = memory_usage / (1024 * 1024)
                                if memory_limit > 0:
                                    memory_percent = (memory_usage / memory_limit) * 100.0
                            
                        except Exception as e:
                            logger.debug(f"Failed to get detailed stats for {container.name}: {e}")
                    
                    # Get image name safely
                    image_name = "unknown"
                    try:
                        if container.image.tags:
                            image_name = container.image.tags[0]
                        else:
                            image_name = container.image.id[:12]
                    except:
                        image_name = "unknown"
                    
                    # Create container metrics
                    container_data = DockerContainer(
                        name=container.name,
                        container_id=container.id,
                        image=image_name,
                        status=container.status,
                        cpu_percent=cpu_percent,
                        memory_mb=memory_mb,
                        memory_percent=memory_percent,
                        timestamp=datetime.utcnow()
                    )
                    
                    container_metrics.append(container_data.to_dict())
                    
                except Exception as e:
                    logger.debug(f"Error processing container {getattr(container, 'name', 'unknown')}: {e}")
                    continue
            
            logger.debug(f"Collected metrics for {len(container_metrics)} containers")
            return container_metrics
            
        except Exception as e:
            logger.error(f"Failed to collect Docker metrics: {e}")
            return []  # Return empty list instead of None