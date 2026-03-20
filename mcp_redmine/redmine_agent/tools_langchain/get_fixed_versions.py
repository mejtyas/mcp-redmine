#!/usr/bin/env python3
"""Tool for getting fixed versions from Redmine."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.tools import BaseTool, tool

from ..helpers import resolve_project_id
from ..redmine_client import RedmineClient


def create_get_fixed_versions_tool(
    redmine: RedmineClient,
    get_username: Callable[[], str],
    base_url: str,
    get_cache: Callable[[], dict[str, Any]] | None = None,
) -> BaseTool:
    """Create the redmine_get_fixed_versions tool."""

    def _resolve_project_id(project_id=None, project_name=None):
        """Return (project_id, error_message | None)."""
        uname = get_username()
        cache = get_cache() if get_cache else None
        return resolve_project_id(redmine, uname, project_id, project_name, cache)

    @tool
    def redmine_get_fixed_versions(
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> str:
        """Get open fixed versions (milestones) for a project."""
        uname = get_username()
        rid, err = _resolve_project_id(project_id, project_name)
        if err:
            return str(err)
        if not rid:
            return "Chyba: project_id nebo project_name je povinný."
        try:
            versions = redmine.get_fixed_versions(uname, rid)
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "Forbidden" in error_msg:
                return f"Nemám oprávnění k přístupu k projektu #{rid}. Zadejte prosím jiný projekt, ke kterému máte přístup."
            raise
        if not versions:
            return f"Projekt #{rid} nemá žádné verze."
        open_v = [
            v
            for v in versions
            if not v.get("status") or v.get("status", "").lower() not in ("closed", "locked")
        ]
        if not open_v:
            return f"Projekt #{rid} nemá žádné otevřené verze."
        lines = []
        for v in open_v:
            vname = v.get("name") or f"Verze #{v['id']}"
            vid = v["id"]
            lines.append(f"• [{vname}]({base_url}/versions/{vid})")
        return f"Otevřené verze ({len(open_v)}):\n" + "\n".join(lines)

    return redmine_get_fixed_versions
