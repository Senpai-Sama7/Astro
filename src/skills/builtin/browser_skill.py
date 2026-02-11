"""Browser automation skill using Playwright."""

from typing import Dict, Any
from pathlib import Path

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

from ..skill import Skill, SkillConfig, SkillContext, SkillResult, SkillPermission


class BrowserSkill(Skill):
    """Skill for browser automation."""
    
    def __init__(self):
        config = SkillConfig(
            name="browser",
            description="Automate web browser - navigate, click, extract data",
            permissions=[SkillPermission.NETWORK, SkillPermission.FILE_SYSTEM],
            icon="🌐"
        )
        super().__init__(config)
        self._playwright = None
        self._browser = None
        self._page = None
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "goto", "click", "type", "screenshot", 
                        "extract", "scroll", "back", "forward",
                        "close", "pdf"
                    ],
                    "description": "Browser action to perform"
                },
                "url": {
                    "type": "string",
                    "description": "URL for goto action"
                },
                "selector": {
                    "type": "string",
                    "description": "CSS selector for click/type/extract"
                },
                "text": {
                    "type": "string",
                    "description": "Text to type"
                },
                "output_path": {
                    "type": "string",
                    "description": "Path to save screenshot/PDF"
                }
            },
            "required": ["action"]
        }
    
    async def _ensure_browser(self):
        """Ensure browser is initialized."""
        if not HAS_PLAYWRIGHT:
            raise ImportError("playwright required. Run: pip install playwright && playwright install")
        
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
            self._page = await self._browser.new_page()
    
    async def execute(self, params: Dict[str, Any], context: SkillContext) -> SkillResult:
        if not HAS_PLAYWRIGHT:
            return SkillResult.error(
                "Playwright not installed. Run: pip install playwright && playwright install"
            )
        
        action = params.get("action")
        
        try:
            await self._ensure_browser()
            
            if action == "goto":
                url = params.get("url")
                if not url:
                    return SkillResult.error("URL required")
                
                await self._page.goto(url, wait_until="networkidle")
                title = await self._page.title()
                return SkillResult.ok(f"Navigated to: {title}", data={"title": title, "url": url})
            
            elif action == "click":
                selector = params.get("selector")
                if not selector:
                    return SkillResult.error("Selector required")
                
                await self._page.click(selector)
                return SkillResult.ok(f"Clicked: {selector}")
            
            elif action == "type":
                selector = params.get("selector")
                text = params.get("text", "")
                
                if not selector:
                    return SkillResult.error("Selector required")
                
                await self._page.fill(selector, text)
                return SkillResult.ok(f"Typed into: {selector}")
            
            elif action == "screenshot":
                output_path = params.get("output_path", "screenshot.png")
                selector = params.get("selector")
                
                path = Path(output_path)
                if not path.is_absolute():
                    path = Path(context.working_directory) / path
                
                if selector:
                    element = await self._page.query_selector(selector)
                    if element:
                        await element.screenshot(path=str(path))
                    else:
                        return SkillResult.error(f"Element not found: {selector}")
                else:
                    await self._page.screenshot(path=str(path), full_page=True)
                
                return SkillResult.ok(f"Screenshot saved: {path}", artifacts=[str(path)])
            
            elif action == "extract":
                selector = params.get("selector")
                
                if selector:
                    elements = await self._page.query_selector_all(selector)
                    texts = []
                    for el in elements:
                        text = await el.text_content()
                        if text:
                            texts.append(text.strip())
                    
                    return SkillResult.ok(
                        f"Extracted {len(texts)} elements",
                        data={"texts": texts}
                    )
                else:
                    # Extract all text
                    text = await self._page.text_content("body")
                    return SkillResult.ok(
                        f"Extracted page text ({len(text)} chars)",
                        data={"text": text}
                    )
            
            elif action == "scroll":
                await self._page.evaluate("window.scrollBy(0, window.innerHeight)")
                return SkillResult.ok("Scrolled down")
            
            elif action == "back":
                await self._page.go_back()
                return SkillResult.ok("Navigated back")
            
            elif action == "forward":
                await self._page.go_forward()
                return SkillResult.ok("Navigated forward")
            
            elif action == "pdf":
                output_path = params.get("output_path", "page.pdf")
                
                path = Path(output_path)
                if not path.is_absolute():
                    path = Path(context.working_directory) / path
                
                await self._page.pdf(path=str(path))
                return SkillResult.ok(f"PDF saved: {path}", artifacts=[str(path)])
            
            elif action == "close":
                await self._cleanup()
                return SkillResult.ok("Browser closed")
            
            else:
                return SkillResult.error(f"Unknown action: {action}")
                
        except Exception as e:
            return SkillResult.error(f"Browser action failed: {e}")
    
    async def _cleanup(self):
        """Clean up browser resources."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        self._page = None
    
    async def shutdown(self):
        """Shutdown skill."""
        await self._cleanup()
        await super().shutdown()
