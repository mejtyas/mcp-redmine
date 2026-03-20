#!/usr/bin/env python3
"""Tool for getting a single issue from Redmine."""

from __future__ import annotations

from collections.abc import Callable

from langchain_core.tools import BaseTool, tool

from ..redmine_client import RedmineClient


def create_get_issue_tool(redmine: RedmineClient, get_username: Callable[[], str]) -> BaseTool:
    """Create the redmine_get_issue tool."""

    @tool
    def redmine_get_issue(issue_id: int) -> str:
        """Get details of a Redmine issue by its ID."""
        uname = get_username()
        issue = redmine.get_issue(uname, issue_id)
        if not issue:
            return f"Úkol #{issue_id} nebyl nalezen."
        parts = [
            f"Úkol #{issue_id}: {issue.get('subject', 'Bez předmětu')}",
            f"Status: {issue.get('status', {}).get('name', '?')}",
        ]
        if issue.get("tracker", {}).get("name"):
            parts.append(f"Tracker: {issue['tracker']['name']}")
        if issue.get("assigned_to", {}).get("name"):
            parts.append(f"Přiřazeno: {issue['assigned_to']['name']}")
        if issue.get("description"):
            parts.append(f"Popis: {issue['description'][:200]}")
        return "\n".join(parts)

    return redmine_get_issue
