#!/usr/bin/env python3
"""Tool for removing members from projects in Redmine."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.tools import BaseTool, tool

from ..helpers import resolve_project_id
from ..redmine_client import RedmineClient


def create_remove_member_from_project_tool(
    redmine: RedmineClient,
    get_username: Callable[[], str],
    get_cache: Callable[[], dict[str, Any]] | None = None,
) -> BaseTool:
    """Create the redmine_remove_member_from_project tool."""

    def _resolve_project_id(project_id=None, project_name=None):
        """Return (project_id, error_message | None)."""
        uname = get_username()
        cache = get_cache() if get_cache else None
        return resolve_project_id(redmine, uname, project_id, project_name, cache)

    @tool
    def redmine_remove_member_from_project(
        membership_id: int,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> str:
        """Remove a member from a Redmine project by membership_id."""
        uname = get_username()
        rid, err = _resolve_project_id(project_id, project_name)
        if err:
            return str(err)
        if not rid:
            return "Chyba: project_id nebo project_name je povinný."
        try:
            redmine.remove_member_from_project(uname, project_id=rid, membership_id=membership_id)
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "Forbidden" in error_msg:
                return f"Nemám oprávnění k přístupu k projektu #{rid}. Zadejte prosím jiný projekt, ke kterému máte přístup."
            raise
        return f"Odebral jsem člena (membership #{membership_id}) z projektu #{rid}"

    return redmine_remove_member_from_project
