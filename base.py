"""
Base classes and interfaces for PyOS plugins.

This module defines the BaseTool interface that all plugins must implement.
The PluginLoader automatically discovers and registers classes inheriting
from BaseTool without requiring manual configuration.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Callable
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Standard result from any tool execution."""
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: Optional[dict[str, Any]] = None

    def __str__(self) -> str:
        status = "✅" if self.success else "❌"
        msg = f"{status} [{self.execution_time_ms:.0f}ms]"
        if self.success:
            msg += f": {str(self.output)[:100]}"
        else:
            msg += f": {self.error}"
        return msg


class BaseTool(ABC):
    """
    Base class for all PyOS tools/plugins.
    
    Any class inheriting from BaseTool will be automatically discovered
    and registered by the PluginLoader. Implement:
    
    - name: Unique tool identifier
    - description: What this tool does
    - execute(): Main async execution method
    - validate(): Optional input validation
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of this tool's purpose."""
        pass

    @property
    def version(self) -> str:
        """Tool version."""
        return "0.1.0"

    @property
    def category(self) -> str:
        """Tool category (e.g., 'vision', 'terminal', 'filesystem')."""
        return "general"

    @property
    def requires_approval(self) -> bool:
        """Whether this tool requires user approval before execution."""
        return False

    @property
    def dangerous_patterns(self) -> list[str]:
        """List of regex patterns that should trigger approval."""
        return []

    async def validate(self, *args: Any, **kwargs: Any) -> tuple[bool, str]:
        """
        Validate inputs before execution.
        
        Override to add custom validation logic.
        
        Returns:
            (is_valid, error_message)
        """
        return True, ""

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> ToolResult:
        """
        Execute the tool.
        
        Must be implemented by subclasses.
        
        Returns:
            ToolResult with success status, output, execution time
        """
        pass

    async def __call__(self, *args: Any, **kwargs: Any) -> ToolResult:
        """Allow tool to be called directly."""
        is_valid, error = await self.validate(*args, **kwargs)
        if not is_valid:
            return ToolResult(
                success=False,
                output=None,
                error=error,
            )
        return await self.execute(*args, **kwargs)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', category='{self.category}')>"
