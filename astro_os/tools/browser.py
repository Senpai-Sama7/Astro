"""Browser Tool - Vision-guided web automation with playwright-stealth."""

import asyncio
import base64
import os
from dataclasses import dataclass
from typing import Optional, Callable, Awaitable
from datetime import datetime

try:
    from playwright.async_api import async_playwright, Page, Browser
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

try:
    from playwright_stealth import stealth_async
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False


@dataclass
class BrowserResult:
    action: str
    success: bool
    url: str
    title: str
    screenshot_b64: Optional[str] = None
    error: Optional[str] = None
    elements_found: int = 0


class BrowserTool:
    """Vision-guided browser automation with stealth capabilities."""
    
    def __init__(self, log_callback: Optional[Callable[[str], Awaitable[None]]] = None,
                 vision_callback: Optional[Callable[[str, str], Awaitable[str]]] = None):
        self.log_callback = log_callback
        self.vision_callback = vision_callback  # For multimodal analysis
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.history: list[BrowserResult] = []
    
    async def log(self, msg: str):
        if self.log_callback:
            await self.log_callback(msg)
    
    async def start(self, headless: bool = True):
        """Start browser with stealth mode."""
        if not HAS_PLAYWRIGHT:
            await self.log("[BROWSER] Playwright not installed")
            return False
        
        await self.log("[BROWSER] Starting browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ]
        )
        
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = await context.new_page()
        
        # Apply stealth
        if HAS_STEALTH:
            await stealth_async(self.page)
            await self.log("[BROWSER] Stealth mode enabled")
        
        await self.log("[BROWSER] Browser ready")
        return True
    
    async def stop(self):
        """Close browser."""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.page = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        await self.log("[BROWSER] Browser closed")
    
    async def screenshot(self) -> Optional[str]:
        """Take screenshot and return base64."""
        if not self.page:
            return None
        try:
            img_bytes = await self.page.screenshot(type="png")
            return base64.b64encode(img_bytes).decode()
        except Exception as e:
            await self.log(f"[BROWSER] Screenshot error: {e}")
            return None
    
    async def navigate(self, url: str) -> BrowserResult:
        """Navigate to URL."""
        if not self.page:
            return BrowserResult("navigate", False, url, "", error="Browser not started")
        
        await self.log(f"[BROWSER] Navigating to {url}")
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            title = await self.page.title()
            screenshot = await self.screenshot()
            
            result = BrowserResult("navigate", True, url, title, screenshot)
            self.history.append(result)
            await self.log(f"[BROWSER] Loaded: {title}")
            return result
        except Exception as e:
            result = BrowserResult("navigate", False, url, "", error=str(e))
            self.history.append(result)
            await self.log(f"[BROWSER] Navigation failed: {e}")
            return result
    
    async def click(self, selector: str) -> BrowserResult:
        """Click element by selector."""
        if not self.page:
            return BrowserResult("click", False, "", "", error="Browser not started")
        
        await self.log(f"[BROWSER] Clicking: {selector}")
        try:
            await self.page.click(selector, timeout=10000)
            await self.page.wait_for_load_state("domcontentloaded")
            url = self.page.url
            title = await self.page.title()
            screenshot = await self.screenshot()
            
            result = BrowserResult("click", True, url, title, screenshot)
            self.history.append(result)
            await self.log(f"[BROWSER] Clicked, now at: {title}")
            return result
        except Exception as e:
            # Try vision-guided click if selector fails
            if self.vision_callback:
                await self.log("[BROWSER] Selector failed, trying vision...")
                return await self.vision_click(selector)
            
            result = BrowserResult("click", False, self.page.url, "", error=str(e))
            self.history.append(result)
            await self.log(f"[BROWSER] Click failed: {e}")
            return result
    
    async def vision_click(self, description: str) -> BrowserResult:
        """Use vision to find and click element by description."""
        if not self.page or not self.vision_callback:
            return BrowserResult("vision_click", False, "", "", error="Vision not available")
        
        await self.log(f"[BROWSER] Vision search: {description}")
        screenshot = await self.screenshot()
        if not screenshot:
            return BrowserResult("vision_click", False, "", "", error="Screenshot failed")
        
        # Ask vision model to locate element
        prompt = f"""Analyze this webpage screenshot. Find the element matching: "{description}"
Return JSON with the approximate click coordinates:
{{"found": true, "x": 500, "y": 300, "confidence": 0.9, "element_description": "blue button labeled Submit"}}
Or if not found: {{"found": false, "reason": "why not found"}}"""
        
        try:
            response = await self.vision_callback(screenshot, prompt)
            import json
            data = json.loads(response)
            
            if data.get("found"):
                x, y = data["x"], data["y"]
                await self.log(f"[BROWSER] Vision found at ({x}, {y}): {data.get('element_description', '')}")
                await self.page.mouse.click(x, y)
                await self.page.wait_for_load_state("domcontentloaded")
                
                url = self.page.url
                title = await self.page.title()
                new_screenshot = await self.screenshot()
                
                result = BrowserResult("vision_click", True, url, title, new_screenshot)
                self.history.append(result)
                return result
            else:
                result = BrowserResult("vision_click", False, self.page.url, "", 
                                      error=data.get("reason", "Element not found"))
                self.history.append(result)
                return result
        except Exception as e:
            result = BrowserResult("vision_click", False, self.page.url, "", error=str(e))
            self.history.append(result)
            await self.log(f"[BROWSER] Vision click failed: {e}")
            return result
    
    async def type_text(self, selector: str, text: str) -> BrowserResult:
        """Type text into element."""
        if not self.page:
            return BrowserResult("type", False, "", "", error="Browser not started")
        
        await self.log(f"[BROWSER] Typing into: {selector}")
        try:
            await self.page.fill(selector, text, timeout=10000)
            url = self.page.url
            title = await self.page.title()
            
            result = BrowserResult("type", True, url, title)
            self.history.append(result)
            await self.log(f"[BROWSER] Typed {len(text)} chars")
            return result
        except Exception as e:
            result = BrowserResult("type", False, self.page.url if self.page else "", "", error=str(e))
            self.history.append(result)
            await self.log(f"[BROWSER] Type failed: {e}")
            return result
    
    async def get_text(self, selector: str = "body") -> str:
        """Get text content from element."""
        if not self.page:
            return ""
        try:
            return await self.page.inner_text(selector, timeout=5000)
        except:
            return ""
    
    async def get_html(self) -> str:
        """Get page HTML."""
        if not self.page:
            return ""
        try:
            return await self.page.content()
        except:
            return ""
