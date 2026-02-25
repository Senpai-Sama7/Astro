"""Live Canvas for visual AI interaction."""

import asyncio
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import uuid


class ElementType(Enum):
    """Types of canvas elements."""
    TEXT = "text"
    MARKDOWN = "markdown"
    CODE = "code"
    IMAGE = "image"
    CHART = "chart"
    TABLE = "table"
    FORM = "form"
    BUTTON = "button"
    IFRAME = "iframe"


@dataclass
class CanvasElement:
    """An element on the canvas."""
    id: str
    type: str
    content: Any
    x: int = 0
    y: int = 0
    width: int = 400
    height: int = 300
    style: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create(
        cls,
        type: ElementType,
        content: Any,
        x: int = 0,
        y: int = 0,
        width: int = 400,
        height: int = 300,
        style: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> 'CanvasElement':
        return cls(
            id=str(uuid.uuid4())[:8],
            type=type.value,
            content=content,
            x=x,
            y=y,
            width=width,
            height=height,
            style=style or {},
            metadata=metadata or {}
        )


class Canvas:
    """A live canvas for visual interaction."""
    
    def __init__(self, canvas_id: Optional[str] = None, title: str = "ASTRO Canvas"):
        self.id = canvas_id or str(uuid.uuid4())[:8]
        self.title = title
        self.elements: Dict[str, CanvasElement] = {}
        self.connections: List[asyncio.Queue] = []
        self.history: List[Dict] = []
        self._callbacks: Dict[str, List[Callable]] = {}
    
    def on(self, event: str, callback: Callable):
        """Register event callback."""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
    
    def emit(self, event: str, data: Any):
        """Emit event to all listeners."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(data)
            except Exception:
                pass
    
    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients."""
        self.history.append(message)
        
        # Send to all connections
        dead_connections = []
        for conn in self.connections:
            try:
                await conn.put(message)
            except Exception:
                dead_connections.append(conn)
        
        # Clean up dead connections
        for conn in dead_connections:
            self.connections.remove(conn)
    
    def add_element(self, element: CanvasElement) -> str:
        """Add element to canvas."""
        self.elements[element.id] = element
        
        asyncio.create_task(self.broadcast({
            "type": "element_added",
            "canvas_id": self.id,
            "element": asdict(element)
        }))
        
        return element.id
    
    def update_element(self, element_id: str, updates: Dict[str, Any]) -> bool:
        """Update an element."""
        if element_id not in self.elements:
            return False
        
        element = self.elements[element_id]
        for key, value in updates.items():
            if hasattr(element, key):
                setattr(element, key, value)
        
        asyncio.create_task(self.broadcast({
            "type": "element_updated",
            "canvas_id": self.id,
            "element_id": element_id,
            "updates": updates
        }))
        
        return True
    
    def remove_element(self, element_id: str) -> bool:
        """Remove element from canvas."""
        if element_id not in self.elements:
            return False
        
        del self.elements[element_id]
        
        asyncio.create_task(self.broadcast({
            "type": "element_removed",
            "canvas_id": self.id,
            "element_id": element_id
        }))
        
        return True
    
    def clear(self):
        """Clear all elements."""
        self.elements.clear()
        
        asyncio.create_task(self.broadcast({
            "type": "canvas_cleared",
            "canvas_id": self.id
        }))
    
    def get_state(self) -> Dict[str, Any]:
        """Get current canvas state."""
        return {
            "id": self.id,
            "title": self.title,
            "elements": [asdict(e) for e in self.elements.values()]
        }
    
    async def connect(self) -> asyncio.Queue:
        """Connect to canvas updates."""
        queue = asyncio.Queue()
        self.connections.append(queue)
        
        # Send current state
        await queue.put({
            "type": "state",
            "canvas": self.get_state()
        })
        
        return queue
    
    def disconnect(self, queue: asyncio.Queue):
        """Disconnect from canvas updates."""
        if queue in self.connections:
            self.connections.remove(queue)


class CanvasManager:
    """Manage multiple canvases."""
    
    def __init__(self):
        self.canvases: Dict[str, Canvas] = {}
    
    def create(self, title: str = "ASTRO Canvas") -> Canvas:
        """Create new canvas."""
        canvas = Canvas(title=title)
        self.canvases[canvas.id] = canvas
        return canvas
    
    def get(self, canvas_id: str) -> Optional[Canvas]:
        """Get canvas by ID."""
        return self.canvases.get(canvas_id)
    
    def list_canvases(self) -> List[Dict[str, Any]]:
        """List all canvases."""
        return [
            {"id": c.id, "title": c.title, "element_count": len(c.elements)}
            for c in self.canvases.values()
        ]
    
    def delete(self, canvas_id: str) -> bool:
        """Delete a canvas."""
        if canvas_id in self.canvases:
            del self.canvases[canvas_id]
            return True
        return False
