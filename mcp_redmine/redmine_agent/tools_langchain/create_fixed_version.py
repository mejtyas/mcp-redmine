#!/usr/bin/env python3
"""Tool for creating fixed versions in Redmine."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.tools import BaseTool, tool

from ..helpers import resolve_project_id
from ..redmine_client import RedmineClient


def create_create_fixed_version_tool(
    redmine: RedmineClient,
    get_username: Callable[[], str],
    get_cache: Callable[[], dict[str, Any]] | None = None,
) -> BaseTool:
    """Create the redmine_create_fixed_version tool."""

    def _resolve_project_id(project_id=None, project_name=None):
        """Return (project_id, error_message | None)."""
        uname = get_username()
        cache = get_cache() if get_cache else None
        return resolve_project_id(redmine, uname, project_id, project_name, cache)

    @tool
    def redmine_create_fixed_version(
        name: str,
        project_id: int | None = None,
        project_name: str | None = None,
        description: str | None = None,
    ) -> str:
        """Create a fixed version (milestone) in a project."""
        uname = get_username()
        rid, err = _resolve_project_id(project_id, project_name)
        if err:
            return str(err)
        if not rid:
            return "Chyba: project_id nebo project_name je povinný."
        kwargs = {}
        if description:
            kwargs["description"] = description
        try:
            ver = redmine.create_fixed_version(uname, project_id=rid, name=name, **kwargs)
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "Forbidden" in error_msg:
                return f"Nemám oprávnění k přístupu k projektu #{rid}. Zadejte prosím jiný projekt, ke kterému máte přístup."
            raise
        return f"Vytvořil jsem verzi #{ver.get('id')}: {name}"

    return redmine_create_fixed_version
