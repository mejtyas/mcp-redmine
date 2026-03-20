#!/usr/bin/env python3
"""Tool for searching issues in Redmine."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.tools import BaseTool, tool

from ..helpers import resolve_project_id
from ..redmine_client import RedmineClient


def create_search_issues_tool(
    redmine: RedmineClient,
    get_username: Callable[[], str],
    get_cache: Callable[[], dict[str, Any]] | None = None,
) -> BaseTool:
    """Create the redmine_search_issues tool."""

    def _resolve_project_id(project_id=None, project_name=None):
        """Return (project_id, error_message | None)."""
        uname = get_username()
        cache = get_cache() if get_cache else None
        return resolve_project_id(redmine, uname, project_id, project_name, cache)

    @tool
    def redmine_search_issues(
        query: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
        status_id: str | None = None,
        assigned_to_id: str | None = None,
        author_id: str | None = None,
        tracker_id: int | None = None,
        priority_id: int | None = None,
    ) -> str:
        """Search Redmine issues with filters or full-text query.
        For full-text search (searching in subject/description), use the 'query' parameter.
        status_id can be 'open','closed', or a number.
        assigned_to_id can be 'me' or a number. author_id filters by issue creator (can be 'me' or a number).
        If project_name is provided, it will automatically search for the project first.
        IMPORTANT: when user asks for issues assigned to a specific user, pass assigned_to_id.
        When user asks for issues CREATED BY a specific user, pass author_id."""
        uname = get_username()
        rid, err = _resolve_project_id(project_id, project_name)
        if err:
            return str(err)

        # If full-text query is provided, use global search
        if query:
            search_params = {"issues": "1"}  # Only search issues
            if rid:
                search_params["scope"] = "my_projects" if rid == "my_projects" else ""

            print(f"[ACTION] Performing full-text search for: '{query}'")
            try:
                results = redmine.search(uname, query, **search_params)
                issue_ids = [r["id"] for r in results if r["type"] == "issue"]

                issues = []
                for iid in issue_ids[:20]:  # Fetch details for top 20 matches
                    try:
                        issue = redmine.get_issue(uname, iid)
                        if rid and issue.get("project", {}).get("id") != rid:
                            continue
                        issues.append(issue)
                    except Exception as e:
                        print(f"Error fetching issue {iid}: {e}")
            except Exception as e:
                return f"Chyba při vyhledávání: {e}"
        else:
            # Resolve 'me' for assigned_to_id and author_id
            cache = get_cache() if get_cache else None
            actual_assigned = assigned_to_id
            if assigned_to_id == "me":
                try:
                    # Check cache first
                    if cache and uname in cache.get("current_user", {}):
                        cu = cache["current_user"][uname]
                    else:
                        cu = redmine.get_current_user(uname)
                        # Store in cache
                        if cache:
                            if "current_user" not in cache:
                                cache["current_user"] = {}
                            cache["current_user"][uname] = cu
                    actual_assigned = str(cu["id"]) if cu.get("id") else assigned_to_id
                except Exception:
                    pass
            actual_author = author_id
            if author_id == "me":
                try:
                    # Check cache first
                    if cache and uname in cache.get("current_user", {}):
                        cu = cache["current_user"][uname]
                    else:
                        cu = redmine.get_current_user(uname)
                        # Store in cache
                        if cache:
                            if "current_user" not in cache:
                                cache["current_user"] = {}
                            cache["current_user"][uname] = cu
                    actual_author = str(cu["id"]) if cu.get("id") else author_id
                except Exception:
                    pass
            # Build filters
            filters: dict = {}
            if rid:
                filters["project_id"] = rid
            if status_id:
                if status_id.lower() == "open":
                    filters["status_id"] = "o"
                elif status_id.lower() == "closed":
                    filters["status_id"] = "c"
                elif status_id.isdigit():
                    filters["status_id"] = int(status_id)
                else:
                    filters["status_id"] = status_id
            if actual_assigned:
                filters["assigned_to_id"] = (
                    int(actual_assigned) if str(actual_assigned).isdigit() else actual_assigned
                )
            if actual_author:
                filters["author_id"] = (
                    int(actual_author) if str(actual_author).isdigit() else actual_author
                )
            if tracker_id:
                filters["tracker_id"] = tracker_id
            if priority_id:
                filters["priority_id"] = priority_id
            try:
                issues = redmine.search_issues(uname, **filters)
            except Exception as e:
                error_msg = str(e)
                if "403" in error_msg or "Forbidden" in error_msg:
                    project_info = f"projektu #{rid}" if rid else "zadaného projektu"
                    return f"Nemám oprávnění k přístupu k {project_info}. Zadejte prosím jiný projekt, ke kterému máte přístup."
                raise

        # Common results formatting
        if not issues:
            return "Nenašel jsem žádné úkoly odpovídající kritériím."

        # Filter out closed issues if status_id is "open" or "o"
        status_id_filter = status_id
        if status_id_filter == "o" or (
            isinstance(status_id_filter, str) and status_id_filter.lower() == "open"
        ):
            before_count = len(issues)
            issues = [
                issue for issue in issues if not issue.get("status", {}).get("is_closed", False)
            ]
            print(
                f"[ACTION] Filtered to {len(issues)} open issues (removed {before_count - len(issues)} closed)"
            )

        lines = []
        for iss in issues[:15]:
            lines.append(
                f"• #{iss['id']}: {iss.get('subject', '?')} ({iss.get('status', {}).get('name', '?')})"
            )
        text = f"Našel jsem {len(issues)} úkolů:\n" + "\n".join(lines)
        if len(issues) > 15:
            text += f"\n\n… a dalších {len(issues) - 15} úkolů"
        return text

    return redmine_search_issues
