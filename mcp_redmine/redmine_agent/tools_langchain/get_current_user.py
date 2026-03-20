#!/usr/bin/env python3
"""Tool for getting the current user from Redmine."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.tools import BaseTool, tool

from ..redmine_client import RedmineClient


def create_get_current_user_tool(
    redmine: RedmineClient,
    get_username: Callable[[], str],
    get_cache: Callable[[], dict[str, Any]] | None = None,
) -> BaseTool:
    """Create the redmine_get_current_user tool."""

    @tool
    def redmine_get_current_user() -> str:
        """Get the current user's Redmine ID and name. Use this when you need to assign an issue to the current user."""
        uname = get_username()
        try:
            cache = get_cache() if get_cache else None
            # Check cache first
            if cache and uname in cache.get("current_user", {}):
                current_user = cache["current_user"][uname]
                print(f"[CACHE HIT] Current user for {uname}")
            else:
                current_user = redmine.get_current_user(uname)
                # Store in cache
                if cache:
                    if "current_user" not in cache:
                        cache["current_user"] = {}
                    cache["current_user"][uname] = current_user
                    print(f"[CACHE STORE] Stored current user for {uname}")
            user_id = current_user.get("id")
            full_name = (
                f"{current_user.get('firstname', '')} {current_user.get('lastname', '')}".strip()
            )
            if user_id:
                return f"Current user Redmine ID: {user_id} - {full_name or 'Unknown'}"
            return f"Current user Redmine ID: Unknown - {full_name or 'Unknown'}"
        except Exception as e:
            return f"Chyba při získávání informací o aktuálním uživateli: {e}"

    return redmine_get_current_user
