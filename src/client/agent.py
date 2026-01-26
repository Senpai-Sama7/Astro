"""
ASTRO Client - Shared agent for TUI and CLI
"""

import os
import sys
from typing import Dict, Any, Optional

# Try to import HTTP clients
try:
    import httpx
    HTTP_CLIENT = "httpx"
except ImportError:
    try:
        import requests
        HTTP_CLIENT = "requests"
    except ImportError:
        HTTP_CLIENT = None


class AstroAgent:
    """Simple agent interface for TUI and programmatic use."""
    
    def __init__(self, api_url: str = "http://localhost:5000"):
        self.api_url = api_url.rstrip("/")
        self.cwd = os.getcwd()
        self.token = None
        self._get_token()
    
    def _get_token(self):
        """Get auth token from API."""
        try:
            if HTTP_CLIENT == "httpx":
                with httpx.Client(timeout=10) as client:
                    resp = client.post(
                        f"{self.api_url}/api/v1/auth/dev-token",
                        json={"userId": "tui-user", "role": "analyst"}
                    )
                    if resp.status_code == 200:
                        self.token = resp.json().get("token")
            elif HTTP_CLIENT == "requests":
                import requests
                resp = requests.post(
                    f"{self.api_url}/api/v1/auth/dev-token",
                    json={"userId": "tui-user", "role": "analyst"},
                    timeout=10
                )
                if resp.status_code == 200:
                    self.token = resp.json().get("token")
        except Exception:
            pass  # Token fetch failed, will retry on first message
    
    def process_message(self, message: str) -> Dict[str, Any]:
        """Process a message and return structured response."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            if HTTP_CLIENT == "httpx":
                with httpx.Client(timeout=60) as client:
                    resp = client.post(
                        f"{self.api_url}/api/v1/aria/chat",
                        json={"message": message},
                        headers=headers
                    )
                    if resp.status_code == 200:
                        return resp.json()
                    return {"response": f"Error: {resp.status_code}"}
            elif HTTP_CLIENT == "requests":
                import requests
                resp = requests.post(
                    f"{self.api_url}/api/v1/aria/chat",
                    json={"message": message},
                    headers=headers,
                    timeout=60
                )
                if resp.status_code == 200:
                    return resp.json()
                return {"response": f"Error: {resp.status_code}"}
            else:
                return {"response": "No HTTP client available. Install httpx or requests."}
        except Exception as e:
            print(f"Error processing message: {e}", file=sys.stderr)
            return {"response": f"Connection error: {str(e)}"}
