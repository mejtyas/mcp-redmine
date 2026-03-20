"""FastMCP stdio server entry."""

from __future__ import annotations

from fastmcp import FastMCP

from .runtime import build_tool_map
from .tools_mutate import register_mutate_tools
from .tools_query import register_query_tools


def run() -> None:
    """Start the FastMCP stdio server with all Redmine tools registered."""
    mcp = FastMCP("mcp-redmine")
    tool_map = build_tool_map()
    register_query_tools(mcp, tool_map)
    register_mutate_tools(mcp, tool_map)
    mcp.run()
