#!/usr/bin/env python3
"""Tool for getting projects from Redmine."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.tools import BaseTool, tool

from ..helpers import resolve_project_id
from ..redmine_client import RedmineClient


def create_get_projects_tool(
    redmine: RedmineClient,
    get_username: Callable[[], str],
    base_url: str,
    get_cache: Callable[[], dict[str, Any]] | None = None,
) -> BaseTool:
    """Create the redmine_get_projects tool."""

    def _resolve_project_id(project_id=None, project_name=None):
        """Return (project_id, error_message | None)."""
        uname = get_username()
        cache = get_cache() if get_cache else None
        return resolve_project_id(redmine, uname, project_id, project_name, cache)

    @tool
    def redmine_get_projects(project_id: int | None = None, project_name: str | None = None) -> str:
        """Get projects from Redmine. If project_name or project_id is provided,
        returns details of that specific project. Otherwise returns list of projects
        you belong to, including open issue counts."""
        uname = get_username()
        if project_id or project_name:
            rid, err = _resolve_project_id(project_id, project_name)
            if err:
                return str(err)
            if not rid:
                return "Chyba: project_id nebo project_name je povinný."
            try:
                project = redmine.get_project(uname, rid)
            except Exception as e:
                error_msg = str(e)
                if "403" in error_msg or "Forbidden" in error_msg:
                    return f"Nemám oprávnění k přístupu k projektu #{rid}. Zadejte prosím jiný projekt, ke kterému máte přístup."
                raise
            if not project:
                return f"Projekt #{rid} nebyl nalezen."
            ident = project.get("identifier", "")
            parts = [
                f"**Projekt: {project.get('name', '')}**",
                f"• ID: {rid}",
                f"• Identifikátor: {ident}",
                f"• Status: {project.get('status', '')}",
            ]
            if project.get("description"):
                parts.append(f"• Popis: {project['description']}")
            if project.get("created_on"):
                parts.append(f"• Vytvořeno: {project['created_on']}")
            if project.get("updated_on"):
                parts.append(f"• Aktualizováno: {project['updated_on']}")
            parts.append(f"• [Odkaz na projekt]({base_url}/projects/{ident})")
            return "\n".join(parts)

        # No specific project - return list of projects with issue counts
        projects = redmine.get_projects(uname)
        if not projects:
            return "Nenašel jsem žádné projekty."

        print(f"[ACTION] Listing {len(projects)} projects with issue counts (LangChain tool)")

        project_list = []
        # Limit to first 20 projects to avoid too many API calls
        for project in projects[:20]:
            pid = project.get("id")
            name = project.get("name", "Neznámý project")

            # Get open issues count for this project
            try:
                count = redmine.get_issues_count(uname, project_id=pid, status_id="o")
                project_list.append(f"• **{name}** (ID: {pid}): {count} otevřených úkolů")
            except Exception as e:
                print(f"Error getting count for project {pid}: {e}")
                project_list.append(f"• **{name}** (ID: {pid})")

        result_text = f"Tady je seznam tvých projektů (celkem {len(projects)}):\n\n" + "\n".join(
            project_list
        )
        if len(projects) > 20:
            result_text += f"\n\n… a dalších {len(projects) - 20} projektů"

        return result_text

    return redmine_get_projects
