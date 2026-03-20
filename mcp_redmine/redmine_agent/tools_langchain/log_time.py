#!/usr/bin/env python3
"""Tool for logging time in Redmine."""

from __future__ import annotations

from collections.abc import Callable

from langchain_core.tools import BaseTool, tool

from ..redmine_client import RedmineClient


def create_log_time_tool(redmine: RedmineClient, get_username: Callable[[], str]) -> BaseTool:
    """Create the redmine_log_time tool."""

    @tool
    def redmine_log_time(
        issue_id: int,
        hours: float,
        activity_id: int | None = None,
        comments: str | None = None,
        spent_on: str | None = None,
    ) -> str:
        """Log time spent on a Redmine issue.
        Required: issue_id, hours.
        Optional: activity_id, comments, spent_on (YYYY-MM-DD)."""
        uname = get_username()
        try:
            result = redmine.log_time(
                uname,
                issue_id=issue_id,
                hours=hours,
                activity_id=activity_id,
                comments=comments,
                spent_on=spent_on,
            )
            time_id = result.get("id")
            return f"Zaznamenal jsem {hours}h u úkolu #{issue_id} (ID záznamu: {time_id})."
        except Exception as e:
            return f"Chyba při zaznamenávání času k úkolu #{issue_id}: {str(e)}"

    return redmine_log_time
