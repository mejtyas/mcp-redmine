"""Run blocking LangChain tools off the async event loop."""

from __future__ import annotations

from typing import Any

import anyio
from langchain_core.tools import BaseTool


async def invoke_tool(tool: BaseTool, args: dict[str, Any]) -> str:
    """Invoke a LangChain StructuredTool and return a string for MCP."""

    def _run() -> str:
        result = tool.invoke(args)
        if isinstance(result, str):
            return result
        return str(result)

    return await anyio.to_thread.run_sync(_run)
