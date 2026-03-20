#!/usr/bin/env python3
"""Tool for editing issues in Redmine."""

from __future__ import annotations

from collections.abc import Callable

from langchain_core.tools import BaseTool, tool

from ..redmine_client import RedmineClient


def create_edit_issue_tool(redmine: RedmineClient, get_username: Callable[[], str]) -> BaseTool:
    """Create the redmine_edit_issue tool."""

    @tool
    def redmine_edit_issue(
        issue_id: int,
        subject: str | None = None,
        description: str | None = None,
        status_id: int | None = None,
        status: str | None = None,
        priority_id: int | None = None,
        assigned_to_id: int | None = None,
        tracker_id: int | None = None,
        project_id: int | None = None,
        due_date: str | None = None,
        estimated_hours: float | None = None,
        parent_issue_id: int | None = None,
        done_ratio: int | None = None,
        start_date: str | None = None,
        notes: str | None = None,
    ) -> str:
        """Edit an existing Redmine issue. Requires issue_id. If 'status' name is provided
        instead of status_id, it will be auto-resolved."""
        uname = get_username()
        # Resolve status name → status_id
        if status and not status_id:
            try:
                statuses = redmine.get_issue_statuses(uname)
                match = next(
                    (s for s in statuses if s.get("name", "").lower() == status.lower()), None
                )
                if match:
                    status_id = match["id"]
                else:
                    sl = status.lower()
                    if sl in ("closed", "uzavřený", "uzavřeno"):
                        closed = next((s for s in statuses if s.get("is_closed")), None)
                        if closed:
                            status_id = closed["id"]
                    if not status_id:
                        names = ", ".join(s.get("name", "") for s in statuses[:8])
                        return f"Status '{status}' nenalezen. Dostupné: {names}"
            except Exception as e:
                return f"Chyba při hledání statusu: {e}"
        updates: dict = {}
        for key, val in [
            ("subject", subject),
            ("description", description),
            ("status_id", status_id),
            ("priority_id", priority_id),
            ("assigned_to_id", assigned_to_id),
            ("tracker_id", tracker_id),
            ("project_id", project_id),
            ("due_date", due_date),
            ("estimated_hours", estimated_hours),
            ("parent_issue_id", parent_issue_id),
            ("done_ratio", done_ratio),
            ("start_date", start_date),
            ("notes", notes),
        ]:
            if val is not None:
                updates[key] = val
        # Build AI audit trail note describing what was changed
        change_fields = [k for k in updates if k != "notes"]
        if change_fields:
            field_names = {
                "subject": "předmět",
                "description": "popis",
                "status_id": "status",
                "priority_id": "priorita",
                "assigned_to_id": "přiřazení",
                "tracker_id": "tracker",
                "project_id": "projekt",
                "due_date": "termín",
                "estimated_hours": "odhadovaný čas",
                "parent_issue_id": "nadřazený úkol",
                "done_ratio": "% dokončení",
                "start_date": "datum začátku",
            }
            changes_desc = ", ".join(field_names.get(f, f) for f in change_fields)
            ai_note = f"🤖 Úprava provedena pomocí AI asistenta na žádost uživatele @{uname}. Změněná pole: {changes_desc}."
        else:
            ai_note = f"🤖 Úprava provedena pomocí AI asistenta na žádost uživatele @{uname}."
        if updates.get("notes"):
            updates["notes"] = f"{updates['notes']}\n\n---\n{ai_note}"
        else:
            updates["notes"] = ai_note
        if not updates:
            return "Chyba: musíte zadat alespoň jedno pole k úpravě."
        try:
            redmine.edit_issue(uname, issue_id, **updates)
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "Forbidden" in error_msg:
                return f"Nemám oprávnění k přístupu k úkolu #{issue_id}. Zadejte prosím jiný úkol, ke kterému máte přístup."
            # Check for 422 error about missing assigned_to_id
            if "422" in error_msg and (
                "Přiřazeno" in error_msg
                or "prázdný" in error_msg
                or "assigned" in error_msg.lower()
            ):
                return "ERROR: Missing required field 'assigned_to_id'. The Redmine API requires an assigned user. Call redmine_get_current_user to get the current user's ID, then retry redmine_edit_issue with assigned_to_id parameter set to that ID."
            raise
        # Verify
        updated = redmine.get_issue(uname, issue_id)
        if updated:
            cur_status = updated.get("status", {}).get("name", "?")
            return f"Upravil jsem úkol #{issue_id} — aktuální status: {cur_status}"
        return f"Upravil jsem úkol #{issue_id}"

    return redmine_edit_issue
