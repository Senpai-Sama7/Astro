"""Screen vision for understanding what's on the screen."""

import base64
import io
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False


class ScreenVision:
    """Analyze and understand screen content."""
    
    def __init__(self):
        self.last_screenshot = None
    
    def is_available(self) -> bool:
        """Check if vision capabilities are available."""
        return HAS_PIL and HAS_PYAUTOGUI
    
    def capture(self) -> Optional[Any]:
        """Capture screen screenshot."""
        if not HAS_PYAUTOGUI:
            return None
        
        self.last_screenshot = pyautogui.screenshot()
        return self.last_screenshot
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> Optional[Any]:
        """Capture specific screen region."""
        if not HAS_PYAUTOGUI:
            return None
        
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        return screenshot
    
    def to_base64(self, image=None) -> Optional[str]:
        """Convert image to base64 string for LLM."""
        if not HAS_PIL:
            return None
        
        img = image or self.last_screenshot
        if not img:
            return None
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    
    def save(self, path: str, image=None) -> bool:
        """Save screenshot to file."""
        try:
            img = image or self.last_screenshot
            if img:
                img.save(path)
                return True
            return False
        except Exception:
            return False
    
    def get_dimensions(self, image=None) -> Tuple[int, int]:
        """Get image dimensions."""
        img = image or self.last_screenshot
        if img:
            return img.size
        return (0, 0)
    
    def locate_image(self, image_path: str, confidence: float = 0.9) -> Optional[Dict[str, int]]:
        """Find an image on screen."""
        if not HAS_PYAUTOGUI:
            return None
        
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location:
                center = pyautogui.center(location)
                return {
                    "x": center.x,
                    "y": center.y,
                    "left": location.left,
                    "top": location.top,
                    "width": location.width,
                    "height": location.height
                }
            return None
        except Exception:
            return None
    
    def locate_all(self, image_path: str, confidence: float = 0.9) -> List[Dict[str, int]]:
        """Find all occurrences of an image on screen."""
        if not HAS_PYAUTOGUI:
            return []
        
        try:
            locations = list(pyautogui.locateAllOnScreen(image_path, confidence=confidence))
            results = []
            for loc in locations:
                center = pyautogui.center(loc)
                results.append({
                    "x": center.x,
                    "y": center.y,
                    "left": loc.left,
                    "top": loc.top,
                    "width": loc.width,
                    "height": loc.height
                })
            return results
        except Exception:
            return []
    
    async def analyze_with_llm(self, llm_provider, prompt: str = "Describe what you see on the screen") -> Optional[str]:
        """Analyze screenshot using LLM vision capabilities."""
        if not llm_provider:
            return None
        
        base64_image = self.to_base64()
        if not base64_image:
            return None
        
        try:
            # This depends on the LLM provider supporting vision
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": base64_image}}
                    ]
                }
            ]
            
            response = await llm_provider.complete(messages)
            return response.content
        except Exception as e:
            return f"Vision analysis failed: {e}"
