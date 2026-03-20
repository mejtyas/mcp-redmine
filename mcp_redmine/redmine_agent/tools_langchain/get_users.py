#!/usr/bin/env python3
"""Tool for getting users from Redmine."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.tools import BaseTool, tool

from ..helpers import generate_search_variations, search_users
from ..redmine_client import RedmineClient


def create_get_users_tool(
    redmine: RedmineClient,
    get_username: Callable[[], str],
    base_url: str,
    get_cache: Callable[[], dict[str, Any]] | None = None,
) -> BaseTool:
    """Create the redmine_get_users tool."""

    @tool
    def redmine_get_users(name: str | None = None, show_details: bool = False) -> str:
        """Get users from Redmine. Optional 'name' to search by firstname/lastname/login.
        Returns user ID, full name, and profile link. Use show_details=True ONLY
        if user explicitly asks for login, email, or admin status."""
        uname = get_username()
        cache = get_cache() if get_cache else None
        # Check cache first
        if cache and uname in cache.get("all_users", {}):
            users = cache["all_users"][uname]
            print(f"[CACHE HIT] Users list for {uname}")
        else:
            users = redmine.get_users(uname)
            # Store in cache
            if cache:
                if "all_users" not in cache:
                    cache["all_users"] = {}
                cache["all_users"][uname] = users
                print(f"[CACHE STORE] Stored {len(users)} users for {uname}")
        if name:
            for var in generate_search_variations(name):
                if len(var) < 2:
                    continue
                found = search_users(users, var)
                if found:
                    if len(found) == 1:
                        u = found[0]
                        uid = u["id"]
                        full = f"{u.get('firstname', '')} {u.get('lastname', '')}".strip()
                        return f"Uživatel {full} má Redmine ID: {uid} - [Profil]({base_url}/users/{uid})"
                    lines = [
                        f"- #{u['id']}: {u.get('firstname', '')} {u.get('lastname', '')} - [Profil]({base_url}/users/{u['id']})"
                        for u in found[:10]
                    ]
                    return f"Našel jsem {len(found)} uživatelů:\n" + "\n".join(lines)
            return f"Nenašel jsem uživatele '{name}' v Redmine."
        if not users:
            return "Nenašel jsem žádné uživatele."
        lines = []
        for u in users:
            uid = u["id"]
            full = f"{u.get('firstname', '')} {u.get('lastname', '')}".strip()
            line = f"• #{uid}: {full} - [Profil]({base_url}/users/{uid})"
            if show_details:
                if u.get("login"):
                    line += f"  Login: {u['login']}"
                if u.get("mail"):
                    line += f"  Email: {u['mail']}"
            lines.append(line)
        return f"Našel jsem {len(users)} uživatelů:\n" + "\n".join(lines)

    return redmine_get_users
