"""core/mcp/ — Model Context Protocol (MCP) Subsystem for DAZY.

Provides:
- client: MCP protocol connection management (stdio, SSE, HTTP)
- manager: Dynamic MCP server attachment, lifecycle, and health checks
- tool_adapter: Translates MCP tool definitions into Mark-LVII provider schemas
- registry: Active server and tool catalog
- security: Permission policies, tool budgeting, and execution gates
"""
from .manager import MCPManager, get_mcp_manager
from .registry import MCPServerRecord, MCPRegistry
from .tool_adapter import adapt_mcp_tool
from .security import verify_mcp_call
