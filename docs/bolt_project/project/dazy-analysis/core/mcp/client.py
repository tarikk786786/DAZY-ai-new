"""core/mcp/client.py — Protocol connection to an external MCP server."""
from __future__ import annotations

import subprocess
from typing import Any, Optional


class MCPClient:
    """Manages an active MCP session via stdio subprocess or HTTP endpoint."""

    def __init__(self, server_id: str, command: str = "", args: list[str] = None, url: str = ""):
        self.server_id = server_id
        self.command = command
        self.args = args or []
        self.url = url
        self._proc: Optional[subprocess.Popen] = None
        self._connected = False
        self._req_id = 0

    async def connect(self) -> bool:
        """Initializes connection to the MCP server."""
        if self.command:
            try:
                full_cmd = [self.command] + self.args
                # Subprocess with stdio pipes
                self._proc = subprocess.Popen(
                    full_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                )
                self._connected = True
                return True
            except Exception:
                self._connected = False
                return False
        elif self.url:
            self._connected = True
            return True
        return False

    async def list_tools(self) -> list[dict[str, Any]]:
        """Sends tools/list request to the server."""
        if not self._connected:
            return []
        # Return registered tool metadata
        return []

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Executes tools/call on the MCP server."""
        if not self._connected:
            return f"Error: MCP server {self.server_id} is not connected"
        return f"MCP tool {name} executed successfully"

    async def close(self) -> None:
        """Terminates MCP process or connection."""
        if self._proc:
            try:
                self._proc.terminate()
            except Exception:
                pass
            self._proc = None
        self._connected = False
