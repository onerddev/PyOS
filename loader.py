"""
Dynamic plugin loader for PyOS.

Automatically discovers and loads all classes inheriting from BaseTool
in the src/pyos/plugins/ directory. No manual configuration needed.
"""

import asyncio
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Optional, Type, Callable

from loguru import logger

try:
    from pyos.plugins.base import BaseTool, ToolResult
except ImportError:
    BaseTool = None
    ToolResult = None


class PluginLoader:
    """
    Dynamically loads and manages plugins (tools).
    
    Scans src/pyos/plugins/ for Python files and automatically registers
    any class that inherits from BaseTool. Provides:
    
    - Auto-discovery of new plugins
    - Plugin metadata reflection
    - Safe loading with error isolation
    - Tool registration callback
    """

    def __init__(self, plugins_dir: Optional[Path] = None):
        """
        Initialize plugin loader.
        
        Args:
            plugins_dir: Path to plugins directory (defaults to src/pyos/plugins)
        """
        if plugins_dir is None:
            current_file = Path(__file__).resolve()
            plugins_dir = current_file.parent.parent / "plugins"

        self.plugins_dir = plugins_dir
        self.loaded_plugins: dict[str, Type[BaseTool]] = {}
        self.instances: dict[str, BaseTool] = {}
        self.on_plugin_loaded: Optional[Callable[[BaseTool], None]] = None

        logger.info(f"PluginLoader initialized for {self.plugins_dir}")

    def scan_plugins(self) -> list[str]:
        """
        Scan plugins directory for potential plugin files.
        
        Returns:
            List of Python files (excluding __init__.py and base.py)
        """
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return []

        plugin_files = [
            f.stem
            for f in self.plugins_dir.glob("*.py")
            if f.name not in ("__init__.py", "base.py")
        ]

        logger.debug(f"Found {len(plugin_files)} potential plugin files: {plugin_files}")
        return plugin_files

    def _load_module_from_path(self, file_path: Path) -> Optional[object]:
        """
        Load a Python module from file path.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Imported module or None if loading failed
        """
        try:
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if spec is None or spec.loader is None:
                logger.error(f"Could not create spec for {file_path}")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[file_path.stem] = module
            spec.loader.exec_module(module)

            return module
        except Exception as e:
            logger.error(f"Failed to load module from {file_path}: {e}")
            return None

    def _find_tool_classes(self, module: object) -> list[Type[BaseTool]]:
        """
        Find all BaseTool subclasses in a module.
        
        Args:
            module: Imported module
            
        Returns:
            List of BaseTool subclasses
        """
        if BaseTool is None:
            return []

        tool_classes = []
        for name, obj in inspect.getmembers(module):
            # Skip BaseTool itself and private classes
            if name.startswith("_"):
                continue

            # Check if it's a class and inherits from BaseTool
            if (
                inspect.isclass(obj)
                and issubclass(obj, BaseTool)
                and obj is not BaseTool
            ):
                tool_classes.append(obj)

        return tool_classes

    async def load_all(self) -> dict[str, BaseTool]:
        """
        Load all plugins from the plugins directory.
        
        Returns:
            Dictionary mapping tool names to tool instances
        """
        plugin_files = self.scan_plugins()
        logger.info(f"Loading {len(plugin_files)} plugins...")

        for plugin_name in plugin_files:
            plugin_path = self.plugins_dir / f"{plugin_name}.py"
            await self.load_plugin_from_file(plugin_path)

        logger.info(f"✅ Loaded {len(self.instances)} tool(s)")
        return self.instances

    async def load_plugin_from_file(self, file_path: Path) -> list[BaseTool]:
        """
        Load all BaseTool classes from a single file.
        
        Args:
            file_path: Path to plugin file
            
        Returns:
            List of initialized tool instances
        """
        logger.debug(f"Loading plugin file: {file_path}")

        module = self._load_module_from_path(file_path)
        if module is None:
            return []

        tool_classes = self._find_tool_classes(module)
        if not tool_classes:
            logger.debug(f"No tools found in {file_path}")
            return []

        loaded_tools = []
        for tool_class in tool_classes:
            try:
                # Instantiate the tool
                tool_instance = tool_class()
                self.loaded_plugins[tool_instance.name] = tool_class
                self.instances[tool_instance.name] = tool_instance

                logger.info(f"  ✓ Loaded {tool_instance.name} ({tool_instance.category})")

                # Trigger callback if registered
                if self.on_plugin_loaded:
                    await self._call_if_async(self.on_plugin_loaded, tool_instance)

                loaded_tools.append(tool_instance)

            except Exception as e:
                logger.error(f"Failed to initialize {tool_class.__name__}: {e}")

        return loaded_tools

    async def _call_if_async(self, func: Callable, *args, **kwargs) -> None:
        """Safely call a function that may be async."""
        try:
            if asyncio.iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Callback error: {e}")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a loaded tool by name."""
        return self.instances.get(name)

    def list_tools(self) -> list[dict[str, str]]:
        """
        List all loaded tools with metadata.
        
        Returns:
            List of tool info dicts
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "version": tool.version,
                "requires_approval": tool.requires_approval,
            }
            for tool in self.instances.values()
        ]

    def filter_tools(self, category: Optional[str] = None) -> dict[str, BaseTool]:
        """
        Filter tools by category.
        
        Args:
            category: Tool category to filter by
            
        Returns:
            Dictionary of matching tools
        """
        if category is None:
            return self.instances

        return {
            name: tool
            for name, tool in self.instances.items()
            if tool.category == category
        }

    async def reload_all(self) -> None:
        """Reload all plugins (useful for development)."""
        logger.info("Reloading all plugins...")
        previous_count = len(self.instances)

        self.loaded_plugins.clear()
        self.instances.clear()

        await self.load_all()
        logger.info(f"Reload complete: {previous_count} → {len(self.instances)} tools")

    def summary(self) -> str:
        """Get a text summary of loaded plugins."""
        if not self.instances:
            return "No tools loaded"

        lines = [f"Loaded {len(self.instances)} tool(s):\n"]
        for tool in self.instances.values():
            lines.append(f"  • {tool.name:20} | {tool.description}")

        return "\n".join(lines)
