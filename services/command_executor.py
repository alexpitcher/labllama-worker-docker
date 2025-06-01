"""Safe command execution service for worker - FIXED IMPORTS."""

import asyncio
import logging
import subprocess
import time
from typing import Dict, Any, Optional

# FIXED: Use absolute import instead of relative
from models import CommandRequest, CommandResult
from datetime import datetime


logger = logging.getLogger(__name__)


class SafeCommandExecutor:
    """Executes whitelisted debugging commands safely."""
    
    def __init__(self):
        # Whitelist of safe debugging commands
        self.SAFE_COMMANDS = {
            "docker_logs": self._docker_logs,
            "docker_inspect": self._docker_inspect,
            "docker_events": self._docker_events,
            "system_dmesg": self._system_dmesg,
            "system_uptime": self._system_uptime,
            "disk_usage": self._disk_usage,
            "memory_info": self._memory_info,
            "process_list": self._process_list
        }
    
    async def execute_command(self, request: CommandRequest) -> CommandResult:
        """Execute a safe command and return structured results."""
        start_time = time.time()
        
        if request.command not in self.SAFE_COMMANDS:
            return CommandResult(
                command=request.command,
                success=False,
                output="",
                error=f"Command '{request.command}' not in whitelist",
                execution_time=0.0,
                timestamp=datetime.utcnow()
            )
        
        try:
            logger.info(f"Executing safe command: {request.command}")
            
            # Execute the whitelisted command
            output = await self.SAFE_COMMANDS[request.command](request.params)
            
            execution_time = time.time() - start_time
            
            return CommandResult(
                command=request.command,
                success=True,
                output=output,
                error=None,
                execution_time=execution_time,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Command execution failed: {e}")
            
            return CommandResult(
                command=request.command,
                success=False,
                output="",
                error=str(e),
                execution_time=execution_time,
                timestamp=datetime.utcnow()
            )
    
    async def _docker_logs(self, params: Dict[str, Any]) -> str:
        """Get Docker container logs."""
        container = params.get("container")
        lines = params.get("lines", 50)
        
        if not container:
            raise ValueError("Container name required")
        
        cmd = ["docker", "logs", "--tail", str(lines), container]
        result = await self._run_command(cmd, timeout=30)
        return result
    
    async def _docker_inspect(self, params: Dict[str, Any]) -> str:
        """Get Docker container inspection data."""
        container = params.get("container")
        
        if not container:
            raise ValueError("Container name required")
        
        cmd = ["docker", "inspect", container]
        result = await self._run_command(cmd, timeout=15)
        return result
    
    async def _docker_events(self, params: Dict[str, Any]) -> str:
        """Get recent Docker events."""
        since = params.get("since", "5m")
        
        cmd = ["docker", "events", "--since", since, "--until", "now"]
        result = await self._run_command(cmd, timeout=15)
        return result
    
    async def _system_dmesg(self, params: Dict[str, Any]) -> str:
        """Get system kernel messages."""
        lines = params.get("lines", 100)
        
        cmd = ["dmesg", "--time-format", "iso", f"--lines={lines}"]
        result = await self._run_command(cmd, timeout=15)
        return result
    
    async def _system_uptime(self, params: Dict[str, Any]) -> str:
        """Get system uptime information."""
        cmd = ["uptime", "-p"]
        result = await self._run_command(cmd, timeout=5)
        return result
    
    async def _disk_usage(self, params: Dict[str, Any]) -> str:
        """Get disk usage information."""
        path = params.get("path", "/")
        
        cmd = ["df", "-h", path]
        result = await self._run_command(cmd, timeout=10)
        return result
    
    async def _memory_info(self, params: Dict[str, Any]) -> str:
        """Get memory information."""
        cmd = ["cat", "/proc/meminfo"]
        result = await self._run_command(cmd, timeout=5)
        return result
    
    async def _process_list(self, params: Dict[str, Any]) -> str:
        """Get running process list."""
        sort_by = params.get("sort_by", "cpu")
        lines = params.get("lines", 20)
        
        if sort_by == "memory":
            cmd = ["ps", "aux", "--sort=-%mem"]
        else:
            cmd = ["ps", "aux", "--sort=-%cpu"]
        
        result = await self._run_command(cmd, timeout=10)
        
        # Limit output lines
        lines_list = result.split('\n')
        if len(lines_list) > lines + 1:  # +1 for header
            result = '\n'.join(lines_list[:lines + 1])
        
        return result
    
    async def _run_command(self, cmd: list, timeout: int = 30) -> str:
        """Run a command with timeout and safety checks."""
        try:
            # Additional safety: prevent dangerous commands
            dangerous_patterns = ["rm", "del", "format", "mkfs", "dd", "sudo", "su"]
            cmd_str = " ".join(cmd).lower()
            
            for pattern in dangerous_patterns:
                if pattern in cmd_str:
                    raise ValueError(f"Dangerous command pattern detected: {pattern}")
            
            # Run the command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/tmp"  # Run in safe directory
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            output = stdout.decode('utf-8', errors='replace')
            if stderr:
                error_output = stderr.decode('utf-8', errors='replace')
                output += f"\nSTDERR:\n{error_output}"
            
            return output.strip()
            
        except asyncio.TimeoutError:
            logger.error(f"Command timeout: {cmd}")
            raise ValueError(f"Command timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            raise
    
    def get_available_commands(self) -> Dict[str, str]:
        """Get list of available safe commands."""
        return {
            "docker_logs": "Get container logs - params: container, lines(optional)",
            "docker_inspect": "Get container details - params: container",
            "docker_events": "Get Docker events - params: since(optional)",
            "system_dmesg": "Get kernel messages - params: lines(optional)",
            "system_uptime": "Get system uptime - params: none",
            "disk_usage": "Get disk usage - params: path(optional)",
            "memory_info": "Get memory information - params: none",
            "process_list": "Get process list - params: sort_by(cpu/memory), lines(optional)"
        }