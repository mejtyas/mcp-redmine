#!/usr/bin/env python3
"""Tool for getting project members from Redmine."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.tools import BaseTool, tool

from ..helpers import resolve_project_id
from ..redmine_client import RedmineClient


def create_get_project_members_tool(
    redmine: RedmineClient,
    get_username: Callable[[], str],
    get_cache: Callable[[], dict[str, Any]] | None = None,
) -> BaseTool:
    """Create the redmine_get_project_members tool."""

    def _resolve_project_id(project_id=None, project_name=None):
        """Return (project_id, error_message | None)."""
        uname = get_username()
        cache = get_cache() if get_cache else None
        return resolve_project_id(redmine, uname, project_id, project_name, cache)

    @tool
    def redmine_get_project_members(
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> str:
        """Get members of a Redmine project."""
        uname = get_username()
        rid, err = _resolve_project_id(project_id, project_name)
        if err:
            return str(err)
        if not rid:
            return "Chyba: project_id nebo project_name je povinný."
        try:
            members = redmine.get_project_members(uname, rid)
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "Forbidden" in error_msg:
                return f"Nemám oprávnění k přístupu k projektu #{rid}. Zadejte prosím jiný projekt, ke kterému máte přístup."
            raise
        if not members:
            return f"Projekt #{rid} nemá žádné členy."
        lines = []
        for m in members[:20]:
            u = m.get("user", {})
            roles = ", ".join(r.get("name", "") for r in m.get("roles", []))
            lines.append(f"- {u.get('name', '?')} ({roles or 'Bez role'})")
        text = f"Členové projektu #{rid} ({len(members)}):\n" + "\n".join(lines)
        if len(members) > 20:
            text += f"\n… a dalších {len(members) - 20}"
        return text

    return redmine_get_project_members
