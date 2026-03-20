"""Register write-oriented Redmine MCP tools."""

from __future__ import annotations

from fastmcp import FastMCP
from langchain_core.tools import BaseTool

from .invoke_tool import invoke_tool


def register_mutate_tools(mcp: FastMCP, t: dict[str, BaseTool]) -> None:
    """Register create/update/member/time/attachment/relation tools (8 tools)."""

    @mcp.tool(
        name="redmine_create_issue",
        description=t["redmine_create_issue"].description or "",
    )
    async def redmine_create_issue(
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
        payload = {
            "subject": subject,
            "project_id": project_id,
            "project_name": project_name,
            "description": description,
            "status_id": status_id,
            "priority_id": priority_id,
            "assigned_to_id": assigned_to_id,
            "tracker_id": tracker_id,
            "due_date": due_date,
            "estimated_hours": estimated_hours,
            "parent_issue_id": parent_issue_id,
            "done_ratio": done_ratio,
            "start_date": start_date,
        }
        return await invoke_tool(t["redmine_create_issue"], payload)

    @mcp.tool(
        name="redmine_edit_issue",
        description=t["redmine_edit_issue"].description or "",
    )
    async def redmine_edit_issue(
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
        payload = {
            "issue_id": issue_id,
            "subject": subject,
            "description": description,
            "status_id": status_id,
            "status": status,
            "priority_id": priority_id,
            "assigned_to_id": assigned_to_id,
            "tracker_id": tracker_id,
            "project_id": project_id,
            "due_date": due_date,
            "estimated_hours": estimated_hours,
            "parent_issue_id": parent_issue_id,
            "done_ratio": done_ratio,
            "start_date": start_date,
            "notes": notes,
        }
        return await invoke_tool(t["redmine_edit_issue"], payload)

    @mcp.tool(
        name="redmine_create_fixed_version",
        description=t["redmine_create_fixed_version"].description or "",
    )
    async def redmine_create_fixed_version(
        name: str,
        project_id: int | None = None,
        project_name: str | None = None,
        description: str | None = None,
    ) -> str:
        return await invoke_tool(
            t["redmine_create_fixed_version"],
            {
                "name": name,
                "project_id": project_id,
                "project_name": project_name,
                "description": description,
            },
        )

    @mcp.tool(
        name="redmine_add_member_to_project",
        description=t["redmine_add_member_to_project"].description or "",
    )
    async def redmine_add_member_to_project(
        user_id: int,
        role_ids: list[int],
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> str:
        return await invoke_tool(
            t["redmine_add_member_to_project"],
            {
                "user_id": user_id,
                "role_ids": role_ids,
                "project_id": project_id,
                "project_name": project_name,
            },
        )

    @mcp.tool(
        name="redmine_remove_member_from_project",
        description=t["redmine_remove_member_from_project"].description or "",
    )
    async def redmine_remove_member_from_project(
        membership_id: int,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> str:
        return await invoke_tool(
            t["redmine_remove_member_from_project"],
            {
                "membership_id": membership_id,
                "project_id": project_id,
                "project_name": project_name,
            },
        )

    @mcp.tool(
        name="redmine_log_time",
        description=t["redmine_log_time"].description or "",
    )
    async def redmine_log_time(
        issue_id: int,
        hours: float,
        activity_id: int | None = None,
        comments: str | None = None,
        spent_on: str | None = None,
    ) -> str:
        return await invoke_tool(
            t["redmine_log_time"],
            {
                "issue_id": issue_id,
                "hours": hours,
                "activity_id": activity_id,
                "comments": comments,
                "spent_on": spent_on,
            },
        )

    @mcp.tool(
        name="redmine_upload_attachment",
        description=t["redmine_upload_attachment"].description or "",
    )
    async def redmine_upload_attachment(
        filename: str,
        content_base64: str | None = None,
        file_path: str | None = None,
    ) -> str:
        return await invoke_tool(
            t["redmine_upload_attachment"],
            {
                "filename": filename,
                "content_base64": content_base64,
                "file_path": file_path,
            },
        )

    @mcp.tool(
        name="redmine_add_issue_relation",
        description=t["redmine_add_issue_relation"].description or "",
    )
    async def redmine_add_issue_relation(
        issue_id: int,
        to_issue_id: int,
        relation_type: str = "relates",
        delay: int | None = None,
    ) -> str:
        return await invoke_tool(
            t["redmine_add_issue_relation"],
            {
                "issue_id": issue_id,
                "to_issue_id": to_issue_id,
                "relation_type": relation_type,
                "delay": delay,
            },
        )
