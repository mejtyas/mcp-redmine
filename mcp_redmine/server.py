"""FastMCP server entry (stdio or HTTP: streamable-http / sse)."""

from __future__ import annotations

import os
from typing import Literal

from fastmcp import FastMCP

from .http_auth import RemoteSessionMiddleware
from .runtime import build_runtime
from .tools_execute_custom import register_execute_custom_tool
from .tools_mutate import register_mutate_tools
from .tools_query import register_query_tools

Transport = Literal["stdio", "sse", "streamable-http", "http"]


def run() -> None:
    """Start FastMCP with tools; transport from MCP_TRANSPORT (default stdio)."""
    raw = (os.environ.get("MCP_TRANSPORT") or "stdio").strip().lower()
    transport: Transport
    if raw in ("stdio", "sse", "streamable-http", "http"):
        transport = raw  # type: ignore[assignment]
    else:
        msg = f"Unknown MCP_TRANSPORT={raw!r}; use stdio, sse, streamable-http, or http."
        raise ValueError(msg)

    http_mode = transport != "stdio"
    mcp = FastMCP("mcp-redmine")
    if http_mode:
        mcp.add_middleware(RemoteSessionMiddleware())

    tool_map, redmine = build_runtime(http_mode=http_mode)
    register_query_tools(mcp, tool_map)
    register_mutate_tools(mcp, tool_map)
    register_execute_custom_tool(mcp, redmine)

    if transport == "stdio":
        mcp.run()
        return

    host = (os.environ.get("MCP_HOST") or "0.0.0.0").strip()
    port = int((os.environ.get("MCP_PORT") or "8000").strip())
    path = (os.environ.get("MCP_PATH") or "/mcp").strip()
    if not path.startswith("/"):
        path = "/" + path

    mcp.run(
        transport=transport,
        host=host,
        port=port,
        path=path,
    )
