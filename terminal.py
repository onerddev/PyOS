"""
Terminal tools for PyOS-Agent.
"""

import subprocess
import time
from typing import Any, Optional
from loguru import logger

from pyos.plugins.base import BaseTool, ToolResult

class ExecuteCommandTool(BaseTool):
    """
    Executes a shell command on the host system.
    Requires security validation from the orchestrator.
    """
    
    @property
    def name(self) -> str:
        return "execute_command"
        
    @property
    def description(self) -> str:
        return "Executes a shell command and returns output. Use with caution."
        
    @property
    def category(self) -> str:
        return "terminal"
        
    @property
    def requires_approval(self) -> bool:
        return True

    async def execute(self, command: str, timeout: int = 30) -> ToolResult:
        start_time = time.time()
        try:
            logger.info(f"Executing command: {command}")
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            if process.returncode == 0:
                return ToolResult(
                    success=True,
                    output=process.stdout,
                    execution_time_ms=execution_time,
                    metadata={"returncode": 0}
                )
            else:
                return ToolResult(
                    success=False,
                    output=process.stdout,
                    error=process.stderr or f"Command failed with exit code {process.returncode}",
                    execution_time_ms=execution_time,
                    metadata={"returncode": process.returncode}
                )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout}s",
                execution_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )
