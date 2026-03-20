"""Register read-oriented Redmine MCP tools."""

from __future__ import annotations

from fastmcp import FastMCP
from langchain_core.tools import BaseTool

from .invoke_tool import invoke_tool


def register_query_tools(mcp: FastMCP, t: dict[str, BaseTool]) -> None:
    """Register query/read tools (8 tools)."""

    @mcp.tool(
        name="redmine_get_users",
        description=t["redmine_get_users"].description or "",
    )
    async def redmine_get_users(name: str | None = None, show_details: bool = False) -> str:
        return await invoke_tool(
            t["redmine_get_users"],
            {"name": name, "show_details": show_details},
        )

    @mcp.tool(
        name="redmine_get_current_user",
        description=t["redmine_get_current_user"].description or "",
    )
    async def redmine_get_current_user() -> str:
        return await invoke_tool(t["redmine_get_current_user"], {})

    @mcp.tool(
        name="redmine_get_projects",
        description=t["redmine_get_projects"].description or "",
    )
    async def redmine_get_projects(
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> str:
        return await invoke_tool(
            t["redmine_get_projects"],
            {"project_id": project_id, "project_name": project_name},
        )

    @mcp.tool(
        name="redmine_get_issue",
        description=t["redmine_get_issue"].description or "",
    )
    async def redmine_get_issue(issue_id: int) -> str:
        return await invoke_tool(t["redmine_get_issue"], {"issue_id": issue_id})

    @mcp.tool(
        name="redmine_search_issues",
        description=t["redmine_search_issues"].description or "",
    )
    async def redmine_search_issues(
        query: str | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
        status_id: str | None = None,
        assigned_to_id: str | None = None,
        author_id: str | None = None,
        tracker_id: int | None = None,
        priority_id: int | None = None,
    ) -> str:
        args = {
            "query": query,
            "project_id": project_id,
            "project_name": project_name,
            "status_id": status_id,
            "assigned_to_id": assigned_to_id,
            "author_id": author_id,
            "tracker_id": tracker_id,
            "priority_id": priority_id,
        }
        return await invoke_tool(t["redmine_search_issues"], args)

    @mcp.tool(
        name="redmine_get_fixed_versions",
        description=t["redmine_get_fixed_versions"].description or "",
    )
    async def redmine_get_fixed_versions(
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> str:
        return await invoke_tool(
            t["redmine_get_fixed_versions"],
            {"project_id": project_id, "project_name": project_name},
        )

    @mcp.tool(
        name="redmine_get_project_members",
        description=t["redmine_get_project_members"].description or "",
    )
    async def redmine_get_project_members(
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> str:
        return await invoke_tool(
            t["redmine_get_project_members"],
            {"project_id": project_id, "project_name": project_name},
        )

    @mcp.tool(
        name="redmine_get_time_entries",
        description=t["redmine_get_time_entries"].description or "",
    )
    async def redmine_get_time_entries(
        project_id: int | None = None,
        project_name: str | None = None,
        issue_id: int | None = None,
        user_id: int | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        export_format: str = "text",
    ) -> str:
        return await invoke_tool(
            t["redmine_get_time_entries"],
            {
                "project_id": project_id,
                "project_name": project_name,
                "issue_id": issue_id,
                "user_id": user_id,
                "from_date": from_date,
                "to_date": to_date,
                "export_format": export_format,
            },
        )
