"""LangChain tools for Redmine (standalone; no Mattermost)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.tools import BaseTool

from ..redmine_client import RedmineClient
from .add_issue_relation import create_add_issue_relation_tool
from .add_member_to_project import create_add_member_to_project_tool
from .create_fixed_version import create_create_fixed_version_tool
from .create_issue import create_create_issue_tool
from .edit_issue import create_edit_issue_tool
from .get_current_user import create_get_current_user_tool
from .get_fixed_versions import create_get_fixed_versions_tool
from .get_issue import create_get_issue_tool
from .get_project_members import create_get_project_members_tool
from .get_projects import create_get_projects_tool
from .get_time_entries import create_get_time_entries_tool
from .get_users import create_get_users_tool
from .log_time import create_log_time_tool
from .remove_member_from_project import create_remove_member_from_project_tool
from .search_issues import create_search_issues_tool
from .upload_attachment import create_upload_attachment_tool


def build_langchain_tools(
    redmine: RedmineClient,
    get_username: Callable[[], str],
    get_cache: Callable[[], dict[str, Any]] | None = None,
) -> list[BaseTool]:
    """Build LangChain tools bound to RedmineClient + username getter (MCP: username always empty)."""
    base_url = redmine.base_url.rstrip("/")

    return [
        create_get_users_tool(redmine, get_username, base_url, get_cache),
        create_get_current_user_tool(redmine, get_username, get_cache),
        create_get_projects_tool(redmine, get_username, base_url),
        create_create_issue_tool(redmine, get_username, get_cache),
        create_edit_issue_tool(redmine, get_username),
        create_get_issue_tool(redmine, get_username),
        create_search_issues_tool(redmine, get_username, get_cache),
        create_create_fixed_version_tool(redmine, get_username, get_cache),
        create_get_fixed_versions_tool(redmine, get_username, base_url, get_cache),
        create_add_member_to_project_tool(redmine, get_username, get_cache),
        create_remove_member_from_project_tool(redmine, get_username, get_cache),
        create_get_project_members_tool(redmine, get_username, get_cache),
        create_log_time_tool(redmine, get_username),
        create_upload_attachment_tool(redmine, get_username),
        create_add_issue_relation_tool(redmine, get_username),
        create_get_time_entries_tool(redmine, get_username, get_cache),
    ]


__all__ = ["build_langchain_tools"]
