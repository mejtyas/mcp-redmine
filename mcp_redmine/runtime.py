"""Build LangChain Redmine tools bound to env-based RedmineClient."""

from __future__ import annotations

import os
from typing import Any

from langchain_core.tools import BaseTool

from .redmine_agent.redmine_client import RedmineClient
from .redmine_agent.tools_langchain import build_langchain_tools


def build_runtime() -> tuple[dict[str, BaseTool], RedmineClient]:
    """Instantiate RedmineClient and return LangChain tools by name plus the shared client."""
    url = os.environ.get("REDMINE_URL", "").strip()
    key = os.environ.get("REDMINE_API_KEY", "").strip()
    if not url or not key:
        msg = "Set REDMINE_URL and REDMINE_API_KEY (or redmine_url / redmine_api_token)."
        raise RuntimeError(msg)

    redmine = RedmineClient()
    session_cache: dict[str, Any] = {}

    def get_username() -> str:
        """MCP uses API key only; never send X-Redmine-Switch-User."""
        return ""

    def get_cache() -> dict[str, Any]:
        return session_cache

    tools = build_langchain_tools(redmine, get_username, get_cache=get_cache)
    return {t.name: t for t in tools}, redmine


def build_tool_map() -> dict[str, BaseTool]:
    """Return LangChain tools by name (same client instance as :func:`build_runtime`)."""
    return build_runtime()[0]
