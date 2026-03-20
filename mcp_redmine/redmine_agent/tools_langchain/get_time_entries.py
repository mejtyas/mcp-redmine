#!/usr/bin/env python3
"""Tool for getting time entries from Redmine."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.tools import BaseTool, tool

from ..helpers import resolve_project_id
from ..redmine_client import RedmineClient


def create_get_time_entries_tool(
    redmine: RedmineClient,
    get_username: Callable[[], str],
    get_cache: Callable[[], dict[str, Any]] | None = None,
) -> BaseTool:
    """Create the redmine_get_time_entries tool."""

    def _resolve_project_id(project_id=None, project_name=None):
        """Return (project_id, error_message | None)."""
        uname = get_username()
        cache = get_cache() if get_cache else None
        return resolve_project_id(redmine, uname, project_id, project_name, cache)

    @tool
    def redmine_get_time_entries(
        project_id: int | None = None,
        project_name: str | None = None,
        issue_id: int | None = None,
        user_id: int | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        export_format: str = "text",
    ) -> str:
        """Get time entries from Redmine. Filter by project, issue, user, or date range (YYYY-MM-DD).
        Returns total hours and a list of entries.

        Args:
            export_format: "text" (default) for formatted text, "json" for JSON structure ready for export.
            When export_format="json", returns a JSON string that can be directly uploaded via mattermost_upload_file.
        """
        uname = get_username()
        rid = None
        if project_id or project_name:
            rid, err = _resolve_project_id(project_id, project_name)
            if err:
                return str(err)
        entries = redmine.get_time_entries(
            uname,
            project_id=rid,
            issue_id=issue_id,
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
        )
        if not entries:
            return "Nenašel jsem žádné časové záznamy."

        # If JSON export requested, return structured data ready for upload
        if export_format == "json":
            import json

            total_hours = sum(e.get("hours", 0) for e in entries)
            # Get user info if available
            user_info = None
            if user_id:
                try:
                    cache = get_cache() if get_cache else None
                    # Check cache first
                    if cache and uname in cache.get("all_users", {}):
                        users = cache["all_users"][uname]
                    else:
                        users = redmine.get_users(uname)
                        # Store in cache
                        if cache:
                            if "all_users" not in cache:
                                cache["all_users"] = {}
                            cache["all_users"][uname] = users
                    user = next((u for u in users if u.get("id") == user_id), None)
                    if user:
                        user_info = {"id": user.get("id"), "name": user.get("name", "")}
                except Exception:
                    user_info = {"id": user_id}

            export_data = {
                "summary": {
                    "total_entries": len(entries),
                    "total_hours": round(total_hours, 2),
                    "period": {
                        "from": from_date or "all",
                        "to": to_date or "all",
                    },
                    "user": user_info,
                    "project": {"id": rid} if rid else None,
                    "issue": {"id": issue_id} if issue_id else None,
                },
                "entries": entries,
            }
            # Return pure JSON string - agent will use this directly with content_text
            return json.dumps(export_data, ensure_ascii=False, indent=2)

        # Default: return formatted text
        total_hours = sum(e.get("hours", 0) for e in entries)
        # Show last 25 entries sorted by date desc
        recent = sorted(entries, key=lambda e: e.get("spent_on", ""), reverse=True)[:25]
        lines = []
        for e in recent:
            user = e.get("user", {}).get("name", "?")
            hours = e.get("hours", 0)
            issue = e.get("issue", {})
            issue_str = f" (úkol #{issue['id']})" if issue.get("id") else ""
            date = e.get("spent_on", "?")
            comment = e.get("comments", "")
            comment_str = f" — {comment}" if comment else ""
            lines.append(f"• {date}: {user} — {hours}h{issue_str}{comment_str}")

        # Include the actual date range used in the response so agent can reuse it for exports
        date_range_info = ""
        if from_date or to_date:
            date_range_info = f" (období: {from_date or 'začátek'} - {to_date or 'konec'})"
        elif not from_date and not to_date:
            date_range_info = " (všechny záznamy)"

        text = (
            f"Celkem **{len(entries)} záznamů**, dohromady **{total_hours:.1f} hodin**{date_range_info}.\n\nPosledních {len(recent)}:\n"
            + "\n".join(lines)
        )
        return text

    return redmine_get_time_entries
