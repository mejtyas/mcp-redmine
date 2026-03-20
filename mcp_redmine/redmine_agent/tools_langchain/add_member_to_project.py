#!/usr/bin/env python3
"""Tool for adding members to projects in Redmine."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.tools import BaseTool, tool

from ..helpers import resolve_project_id
from ..redmine_client import RedmineClient


def create_add_member_to_project_tool(
    redmine: RedmineClient,
    get_username: Callable[[], str],
    get_cache: Callable[[], dict[str, Any]] | None = None,
) -> BaseTool:
    """Create the redmine_add_member_to_project tool."""

    def _resolve_project_id(project_id=None, project_name=None):
        """Return (project_id, error_message | None)."""
        uname = get_username()
        cache = get_cache() if get_cache else None
        return resolve_project_id(redmine, uname, project_id, project_name, cache)

    @tool
    def redmine_add_member_to_project(
        user_id: int,
        role_ids: list[int],
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> str:
        """Add a member to a Redmine project. Requires user_id, role_ids, and either project_id or project_name."""
        uname = get_username()
        rid, err = _resolve_project_id(project_id, project_name)
        if err:
            return str(err)
        if not rid:
            return "Chyba: project_id nebo project_name je povinný."
        if not role_ids:
            return "Chyba: role_ids je povinný (seznam ID rolí)."
        try:
            m = redmine.add_member_to_project(
                uname, project_id=rid, user_id=user_id, role_ids=role_ids
            )
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "Forbidden" in error_msg:
                return f"Nemám oprávnění k přístupu k projektu #{rid}. Zadejte prosím jiný projekt, ke kterému máte přístup."
            raise
        return f"Přidal jsem uživatele #{user_id} do projektu #{rid} (membership #{m.get('id')})"

    return redmine_add_member_to_project
