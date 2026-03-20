#!/usr/bin/env python3
"""Tool for linking Redmine issues."""

from __future__ import annotations

from collections.abc import Callable

from langchain_core.tools import BaseTool, tool

from ..redmine_client import RedmineClient


def create_add_issue_relation_tool(
    redmine: RedmineClient, get_username: Callable[[], str]
) -> BaseTool:
    """Create the redmine_add_issue_relation tool."""

    @tool
    def redmine_add_issue_relation(
        issue_id: int, to_issue_id: int, relation_type: str = "relates", delay: int | None = None
    ) -> str:
        """Create a relation between two Redmine issues.
        Required: issue_id, to_issue_id.
        Optional: relation_type (relates, blocks, precedes, follows, etc.), delay."""
        uname = get_username()
        try:
            result = redmine.add_issue_relation(
                uname,
                issue_id=issue_id,
                to_issue_id=to_issue_id,
                relation_type=relation_type,
                delay=delay,
            )
            relation_id = result.get("id")
            return f"Vytvořil jsem vazbu ({relation_type}) mezi #{issue_id} a #{to_issue_id} (ID vazby: {relation_id})."
        except Exception as e:
            return f"Chyba při vytváření vazby mezi #{issue_id} a #{to_issue_id}: {str(e)}"

    return redmine_add_issue_relation
