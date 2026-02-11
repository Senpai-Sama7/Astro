"""MCP (Model Context Protocol) client implementation."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    import mcp  # noqa: F401
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    HAS_MCP = True
except ImportError:
    HAS_MCP = False


@dataclass
class MCPTool:
    """An MCP tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]


class MCPClient:
    """Client for connecting to MCP servers."""
    
    def __init__(self):
        self.sessions: Dict[str, 'ClientSession'] = {}
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, Any] = {}
    
    def is_available(self) -> bool:
        """Check if MCP is available."""
        return HAS_MCP
    
    async def connect_stdio(
        self,
        server_id: str,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None
    ) -> bool:
        """Connect to an MCP server via stdio."""
        if not HAS_MCP:
            raise ImportError("mcp package required. Run: pip install mcp")
        
        try:
            server_params = StdioServerParameters(
                command=command,
                args=args or [],
                env=env
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.sessions[server_id] = session
                    
                    # List available tools
                    tools_response = await session.list_tools()
                    for tool in tools_response.tools:
                        self.tools[f"{server_id}:{tool.name}"] = MCPTool(
                            name=tool.name,
                            description=tool.description,
                            input_schema=tool.inputSchema
                        )
                    
                    print(f"Connected to MCP server '{server_id}' with {len(tools_response.tools)} tools")
                    return True
                    
        except Exception as e:
            print(f"Failed to connect to MCP server '{server_id}': {e}")
            return False
    
    async def connect_sse(
        self,
        server_id: str,
        url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """Connect to an MCP server via SSE (Server-Sent Events).
        
        Note: This is for future MCP versions that support HTTP+SSE transport.
        """
        # TODO: Implement when MCP SSE transport is stable
        raise NotImplementedError("SSE transport not yet implemented")
    
    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """Call a tool on an MCP server."""
        if server_id not in self.sessions:
            raise ValueError(f"Not connected to server: {server_id}")
        
        session = self.sessions[server_id]
        
        try:
            result = await session.call_tool(tool_name, arguments=arguments)
            return result
        except Exception as e:
            raise RuntimeError(f"Tool call failed: {e}")
    
    async def read_resource(self, server_id: str, uri: str) -> Any:
        """Read a resource from an MCP server."""
        if server_id not in self.sessions:
            raise ValueError(f"Not connected to server: {server_id}")
        
        session = self.sessions[server_id]
        
        try:
            result = await session.read_resource(uri)
            return result
        except Exception as e:
            raise RuntimeError(f"Resource read failed: {e}")
    
    def list_tools(self, server_id: Optional[str] = None) -> List[MCPTool]:
        """List available tools."""
        if server_id:
            prefix = f"{server_id}:"
            return [t for name, t in self.tools.items() if name.startswith(prefix)]
        return list(self.tools.values())
    
    def get_tool(self, full_name: str) -> Optional[MCPTool]:
        """Get tool by full name (server:tool)."""
        return self.tools.get(full_name)
    
    async def disconnect(self, server_id: str):
        """Disconnect from a server."""
        if server_id in self.sessions:
            # Remove tools from this server
            prefix = f"{server_id}:"
            self.tools = {k: v for k, v in self.tools.items() if not k.startswith(prefix)}
            
            # Close session
            del self.sessions[server_id]
    
    async def disconnect_all(self):
        """Disconnect from all servers."""
        for server_id in list(self.sessions.keys()):
            await self.disconnect(server_id)


class MCPSkillAdapter:
    """Adapter to expose MCP tools as ASTRO skills."""
    
    def __init__(self, mcp_client: MCPClient, skill_registry):
        self.mcp_client = mcp_client
        self.skill_registry = skill_registry
    
    def register_mcp_tools_as_skills(self):
        """Register all MCP tools as ASTRO skills."""
        from ..skills import Skill, SkillConfig, SkillResult, SkillPermission
        
        for full_name, mcp_tool in self.mcp_client.tools.items():
            server_id, tool_name = full_name.split(":", 1)
            
            # Create a skill class dynamically
            class MCPToolSkill(Skill):
                def __init__(self, tool_name, mcp_tool, mcp_client, server_id):
                    self._tool_name = tool_name
                    self._mcp_tool = mcp_tool
                    self._mcp_client = mcp_client
                    self._server_id = server_id
                    
                    config = SkillConfig(
                        name=f"mcp_{tool_name}",
                        description=mcp_tool.description,
                        permissions=[SkillPermission.NETWORK],
                        icon="🔌"
                    )
                    super().__init__(config)
                
                def get_parameter_schema(self):
                    return self._mcp_tool.input_schema
                
                async def execute(self, params, context):
                    try:
                        result = await self._mcp_client.call_tool(
                            self._server_id,
                            self._tool_name,
                            params
                        )
                        return SkillResult.ok(
                            "Tool executed successfully",
                            data={"result": result}
                        )
                    except Exception as e:
                        return SkillResult.error(str(e))
            
            # Register the skill
            skill = MCPToolSkill(tool_name, mcp_tool, self.mcp_client, server_id)
            self.skill_registry.register(skill)
