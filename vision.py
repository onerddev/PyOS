"""
Vision tools for PyOS-Agent.
"""

import time
import base64
from io import BytesIO
from typing import Any, Optional
from loguru import logger

try:
    import mss
    from PIL import Image
except ImportError:
    mss = None
    Image = None

from pyos.plugins.base import BaseTool, ToolResult

class TakeScreenshotTool(BaseTool):
    """
    Takes a screenshot of the current screen.
    Useful for AI to understand the desktop state.
    """
    
    @property
    def name(self) -> str:
        return "take_screenshot"
        
    @property
    def description(self) -> str:
        return "Captures the current screen and returns it as a base64 encoded string."
        
    @property
    def category(self) -> str:
        return "vision"

    async def execute(self, monitor: int = 1, quality: int = 85) -> ToolResult:
        start_time = time.time()
        
        if mss is None or Image is None:
            return ToolResult(
                success=False,
                output="",
                error="Required libraries (mss, Pillow) are not installed.",
                execution_time_ms=(time.time() - start_time) * 1000
            )
            
        try:
            with mss.mss() as sct:
                # Get the monitor info
                if monitor > len(sct.monitors):
                    monitor = 1
                    
                screenshot = sct.grab(sct.monitors[monitor])
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                # Resize if too large (optional optimization)
                # img.thumbnail((1280, 720))
                
                buffered = BytesIO()
                img.save(buffered, format="JPEG", quality=quality)
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                execution_time = (time.time() - start_time) * 1000
                
                return ToolResult(
                    success=True,
                    output=img_str,
                    execution_time_ms=execution_time,
                    metadata={
                        "size": screenshot.size,
                        "format": "JPEG",
                        "encoding": "base64"
                    }
                )
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return ToolResult(
                success=False,
                output="",
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )
