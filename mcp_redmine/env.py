"""Normalize Redmine-related environment variables before starting the MCP server."""

from __future__ import annotations

import os


def normalize_redmine_env() -> None:
    """Map aliases into REDMINE_URL / REDMINE_API_KEY for RedmineClient."""
    # Lowercase aliases match common docker -e style from Cursor configs.
    url = os.environ.get("REDMINE_URL") or os.environ.get("redmine_url")  # noqa: SIM112
    if url:
        os.environ["REDMINE_URL"] = url.strip().rstrip("/")

    key = os.environ.get("REDMINE_API_KEY") or os.environ.get("redmine_api_token")  # noqa: SIM112
    if key:
        os.environ["REDMINE_API_KEY"] = key
