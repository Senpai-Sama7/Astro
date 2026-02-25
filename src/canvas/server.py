"""WebSocket server for canvas real-time updates."""

import asyncio
import json

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    WebSocketServerProtocol = None

from .canvas import CanvasManager


class CanvasServer:
    """WebSocket server for live canvas updates."""
    
    def __init__(self, canvas_manager: CanvasManager, host: str = "localhost", port: int = 8765):
        self.canvas_manager = canvas_manager
        self.host = host
        self.port = port
        self.server = None
        self.clients: set = set()
        self._running = False
    
    async def start(self):
        """Start the canvas WebSocket server."""
        if not HAS_WEBSOCKETS:
            raise ImportError("websockets required. Run: pip install websockets")
        
        self._running = True
        self.server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port
        )
        print(f"Canvas server started on ws://{self.host}:{self.port}")
    
    async def stop(self):
        """Stop the server."""
        self._running = False
        
        # Close all client connections
        # Use list(self.clients) to avoid "set changed size during iteration"
        for client in list(self.clients):
            try:
                await client.close()
            except Exception:
                pass
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
    
    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle a client connection."""
        self.clients.add(websocket)
        
        try:
            # Parse canvas ID from path
            canvas_id = path.strip('/').split('/')[-1] if path else None
            
            if canvas_id:
                canvas = self.canvas_manager.get(canvas_id)
                if not canvas:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": f"Canvas not found: {canvas_id}"
                    }))
                    return
                
                # Connect to canvas
                queue = await canvas.connect()
                
                # Start tasks for sending and receiving
                receive_task = asyncio.create_task(self._receive_messages(websocket, canvas))
                send_task = asyncio.create_task(self._send_updates(websocket, queue))
                
                await asyncio.gather(receive_task, send_task)
            else:
                # List available canvases
                await websocket.send(json.dumps({
                    "type": "canvases_list",
                    "canvases": self.canvas_manager.list_canvases()
                }))
                
                # Just echo back for now
                async for message in websocket:
                    data = json.loads(message)
                    
                    if data.get("action") == "create_canvas":
                        canvas = self.canvas_manager.create(data.get("title", "New Canvas"))
                        await websocket.send(json.dumps({
                            "type": "canvas_created",
                            "canvas_id": canvas.id
                        }))
                    
                    elif data.get("action") == "list_canvases":
                        await websocket.send(json.dumps({
                            "type": "canvases_list",
                            "canvases": self.canvas_manager.list_canvases()
                        }))
        
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)
    
    async def _receive_messages(self, websocket: WebSocketServerProtocol, canvas):
        """Receive messages from client."""
        async for message in websocket:
            try:
                data = json.loads(message)
                action = data.get("action")
                
                if action == "add_element":
                    from .canvas import CanvasElement, ElementType
                    element = CanvasElement.create(
                        type=ElementType(data.get("element_type", "text")),
                        content=data.get("content"),
                        x=data.get("x", 0),
                        y=data.get("y", 0),
                        width=data.get("width", 400),
                        height=data.get("height", 300)
                    )
                    canvas.add_element(element)
                
                elif action == "update_element":
                    canvas.update_element(
                        data.get("element_id"),
                        data.get("updates", {})
                    )
                
                elif action == "remove_element":
                    canvas.remove_element(data.get("element_id"))
                
                elif action == "clear_canvas":
                    canvas.clear()
                
                elif action == "user_interaction":
                    # Handle user interactions (button clicks, form submissions)
                    canvas.emit("user_interaction", data)
            
            except Exception:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "An internal error occurred while processing the request."
                }))
    
    async def _send_updates(self, websocket: WebSocketServerProtocol, queue: asyncio.Queue):
        """Send canvas updates to client."""
        while True:
            try:
                message = await queue.get()
                await websocket.send(json.dumps(message))
            except Exception:
                break
