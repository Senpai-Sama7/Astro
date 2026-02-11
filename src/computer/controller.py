"""Computer controller for mouse and keyboard automation."""

import asyncio
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any
from enum import Enum

try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Move mouse to corner to abort
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False


class Action(Enum):
    """Computer actions."""
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    MOVE = "move"
    DRAG = "drag"
    SCROLL = "scroll"
    TYPE = "type"
    KEY_PRESS = "key_press"
    HOTKEY = "hotkey"
    SCREENSHOT = "screenshot"
    GET_SCREEN_SIZE = "get_screen_size"
    GET_CURSOR_POS = "get_cursor_pos"


@dataclass
class ActionResult:
    """Result of a computer action."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class ComputerController:
    """Control mouse and keyboard for computer automation."""
    
    def __init__(self):
        self.screen_width = 0
        self.screen_height = 0
        self._init_display()
    
    def _init_display(self):
        """Initialize display info."""
        if HAS_PYAUTOGUI:
            self.screen_width, self.screen_height = pyautogui.size()
    
    def is_available(self) -> bool:
        """Check if computer control is available."""
        return HAS_PYAUTOGUI
    
    async def execute(self, action: Action, **kwargs) -> ActionResult:
        """Execute a computer action."""
        if not HAS_PYAUTOGUI:
            return ActionResult(
                success=False,
                message="pyautogui not installed. Run: pip install pyautogui"
            )
        
        try:
            if action == Action.CLICK:
                return await self._click(**kwargs)
            elif action == Action.DOUBLE_CLICK:
                return await self._double_click(**kwargs)
            elif action == Action.RIGHT_CLICK:
                return await self._right_click(**kwargs)
            elif action == Action.MOVE:
                return await self._move(**kwargs)
            elif action == Action.DRAG:
                return await self._drag(**kwargs)
            elif action == Action.SCROLL:
                return await self._scroll(**kwargs)
            elif action == Action.TYPE:
                return await self._type(**kwargs)
            elif action == Action.KEY_PRESS:
                return await self._key_press(**kwargs)
            elif action == Action.HOTKEY:
                return await self._hotkey(**kwargs)
            elif action == Action.SCREENSHOT:
                return await self._screenshot(**kwargs)
            elif action == Action.GET_SCREEN_SIZE:
                return self._get_screen_size()
            elif action == Action.GET_CURSOR_POS:
                return self._get_cursor_pos()
            else:
                return ActionResult(success=False, message=f"Unknown action: {action}")
                
        except Exception as e:
            return ActionResult(success=False, message=f"Action failed: {e}")
    
    async def _click(self, x: Optional[int] = None, y: Optional[int] = None, **kwargs) -> ActionResult:
        """Click at position or current location."""
        if x is not None and y is not None:
            pyautogui.click(x, y)
            return ActionResult(success=True, message=f"Clicked at ({x}, {y})")
        else:
            pyautogui.click()
            return ActionResult(success=True, message="Clicked at current position")
    
    async def _double_click(self, x: Optional[int] = None, y: Optional[int] = None, **kwargs) -> ActionResult:
        """Double click at position or current location."""
        if x is not None and y is not None:
            pyautogui.doubleClick(x, y)
            return ActionResult(success=True, message=f"Double-clicked at ({x}, {y})")
        else:
            pyautogui.doubleClick()
            return ActionResult(success=True, message="Double-clicked at current position")
    
    async def _right_click(self, x: Optional[int] = None, y: Optional[int] = None, **kwargs) -> ActionResult:
        """Right click at position or current location."""
        if x is not None and y is not None:
            pyautogui.rightClick(x, y)
            return ActionResult(success=True, message=f"Right-clicked at ({x}, {y})")
        else:
            pyautogui.rightClick()
            return ActionResult(success=True, message="Right-clicked at current position")
    
    async def _move(self, x: int, y: int, duration: float = 0.5, **kwargs) -> ActionResult:
        """Move mouse to position."""
        pyautogui.moveTo(x, y, duration=duration)
        return ActionResult(success=True, message=f"Moved to ({x}, {y})")
    
    async def _drag(self, x: int, y: int, duration: float = 0.5, **kwargs) -> ActionResult:
        """Drag to position."""
        pyautogui.dragTo(x, y, duration=duration)
        return ActionResult(success=True, message=f"Dragged to ({x}, {y})")
    
    async def _scroll(self, amount: int, **kwargs) -> ActionResult:
        """Scroll up (positive) or down (negative)."""
        pyautogui.scroll(amount)
        direction = "up" if amount > 0 else "down"
        return ActionResult(success=True, message=f"Scrolled {direction} {abs(amount)} clicks")
    
    async def _type(self, text: str, interval: float = 0.01, **kwargs) -> ActionResult:
        """Type text."""
        pyautogui.typewrite(text, interval=interval)
        return ActionResult(success=True, message=f"Typed {len(text)} characters")
    
    async def _key_press(self, key: str, **kwargs) -> ActionResult:
        """Press a single key."""
        pyautogui.press(key)
        return ActionResult(success=True, message=f"Pressed key: {key}")
    
    async def _hotkey(self, keys: List[str], **kwargs) -> ActionResult:
        """Press hotkey combination."""
        pyautogui.hotkey(*keys)
        return ActionResult(success=True, message=f"Pressed hotkey: {'+'.join(keys)}")
    
    async def _screenshot(self, path: Optional[str] = None, **kwargs) -> ActionResult:
        """Take screenshot."""
        screenshot = pyautogui.screenshot()
        
        if path:
            screenshot.save(path)
            return ActionResult(
                success=True,
                message=f"Screenshot saved to {path}",
                data={"path": path, "size": screenshot.size}
            )
        else:
            return ActionResult(
                success=True,
                message="Screenshot captured",
                data={"size": screenshot.size, "mode": screenshot.mode}
            )
    
    def _get_screen_size(self) -> ActionResult:
        """Get screen dimensions."""
        return ActionResult(
            success=True,
            message=f"Screen size: {self.screen_width}x{self.screen_height}",
            data={"width": self.screen_width, "height": self.screen_height}
        )
    
    def _get_cursor_pos(self) -> ActionResult:
        """Get current cursor position."""
        x, y = pyautogui.position()
        return ActionResult(
            success=True,
            message=f"Cursor at ({x}, {y})",
            data={"x": x, "y": y}
        )
    
    def locate_on_screen(self, image_path: str, confidence: float = 0.9) -> Optional[Tuple[int, int]]:
        """Locate an image on screen. Returns center coordinates."""
        if not HAS_PYAUTOGUI:
            return None
        
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location:
                return pyautogui.center(location)
            return None
        except Exception:
            return None
