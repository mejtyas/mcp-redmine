#!/usr/bin/env python3
"""Tool for creating issues in Redmine."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.tools import BaseTool, tool

from ..helpers import resolve_project_id
from ..redmine_client import RedmineClient


def create_create_issue_tool(
    redmine: RedmineClient,
    get_username: Callable[[], str],
    get_cache: Callable[[], dict[str, Any]] | None = None,
) -> BaseTool:
    """Create the redmine_create_issue tool."""

    def _resolve_project_id(project_id=None, project_name=None):
        """Return (project_id, error_message | None)."""
        uname = get_username()
        cache = get_cache() if get_cache else None
        return resolve_project_id(redmine, uname, project_id, project_name, cache)

    @tool
    def redmine_create_issue(
        subject: str,
        project_id: int | None = None,
        project_name: str | None = None,
        description: str | None = None,
        status_id: int | None = None,
        priority_id: int | None = None,
        assigned_to_id: int | None = None,
        tracker_id: int | None = None,
        due_date: str | None = None,
        estimated_hours: float | None = None,
        parent_issue_id: int | None = None,
        done_ratio: int | None = None,
        start_date: str | None = None,
    ) -> str:
        """Create a new Redmine issue. Requires subject. Project: use project_id or project_name, OR when creating a sub-issue pass parent_issue_id and project will be derived from the parent (do NOT ask user for project). Default tracker_id=4 (Task) and priority_id=2 (Normal) - NEVER ask the user for priority. If assigned_to_id is not provided, it is set to the current user."""
        uname = get_username()
        rid: int | None = None
        err: str | None = None
        if project_id or project_name:
            rid, err = _resolve_project_id(project_id, project_name)
        elif parent_issue_id:
            try:
                parent = redmine.get_issue(uname, parent_issue_id)
                if not parent:
                    return f"Chyba: Nadřazený úkol #{parent_issue_id} nebyl nalezen."
                proj = parent.get("project") or {}
                rid = proj.get("id") if isinstance(proj, dict) else None
                if not rid:
                    return f"Chyba: Nepodařilo se zjistit projekt z nadřazeného úkolu #{parent_issue_id}."
            except Exception as e:
                return f"Chyba při načítání nadřazeného úkolu #{parent_issue_id}: {e}"
        if not rid and not err:
            err = "Chyba: Potřebuji vědět, do jakého projektu chcete vytvořit úkol (project_id/project_name), nebo zadejte parent_issue_id pro pod-úkol."
        if err:
            return err
        if not rid:
            return "Chyba: project_id nebo project_name je povinný."

        # Automatically get current user's ID if assigned_to_id is not provided
        if assigned_to_id is None:
            try:
                cache = get_cache() if get_cache else None
                # Check cache first
                if cache and uname in cache.get("current_user", {}):
                    current_user = cache["current_user"][uname]
                    print(f"[CACHE HIT] Current user for {uname}")
                else:
                    current_user = redmine.get_current_user(uname)
                    # Store in cache
                    if cache:
                        if "current_user" not in cache:
                            cache["current_user"] = {}
                        cache["current_user"][uname] = current_user
                        print(f"[CACHE STORE] Stored current user for {uname}")
                assigned_to_id = current_user.get("id")
                if not assigned_to_id:
                    return "Chyba: Nepodařilo se získat ID aktuálního uživatele. Zadejte prosím assigned_to_id explicitně."
            except Exception as e:
                return f"Chyba při získávání ID aktuálního uživatele: {e}"

        kwargs: dict = {}
        for key, val in [
            ("status_id", status_id),
            ("priority_id", priority_id),
            ("assigned_to_id", assigned_to_id),
            ("tracker_id", tracker_id),
            ("due_date", due_date),
            ("estimated_hours", estimated_hours),
            ("parent_issue_id", parent_issue_id),
            ("done_ratio", done_ratio),
            ("start_date", start_date),
        ]:
            if val is not None:
                kwargs[key] = val
        try:
            issue = redmine.create_issue(
                uname, project_id=rid, subject=subject, description=description, **kwargs
            )
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "Forbidden" in error_msg:
                return f"Nemám oprávnění k přístupu k projektu #{rid}. Zadejte prosím jiný projekt, ke kterému máte přístup."
            # Check for 422 error about missing assigned_to_id
            if "422" in error_msg and (
                "Přiřazeno" in error_msg
                or "prázdný" in error_msg
                or "assigned" in error_msg.lower()
            ):
                return "ERROR: Missing required field 'assigned_to_id'. The Redmine API requires an assigned user. Call redmine_get_current_user to get the current user's ID, then retry redmine_create_issue with assigned_to_id parameter set to that ID."
            raise
        iid = issue.get("id")
        # Add AI audit trail note
        if iid:
            try:
                ai_note = (
                    f"🤖 Tento úkol byl vytvořen pomocí AI asistenta na žádost uživatele @{uname}."
                )
                redmine.add_note_to_issue(uname, iid, ai_note)
            except Exception:
                pass  # Don't fail the whole operation if the note fails
        if not iid:
            return f"Vytvořil jsem úkol, ale nepodařilo se získat ID: {subject}"
        return f"Vytvořil jsem úkol #{iid}: {subject}"

    return redmine_create_issue
