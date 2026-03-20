#!/usr/bin/env python3
"""
Shared helper functions for Redmine agent tools.
These functions are used by both LangChain tools and BaseTool classes.
"""

from __future__ import annotations

from typing import Any

from .redmine_client import RedmineClient


def search_projects(projects: list[dict], search_term: str) -> list[dict]:
    """Search projects by name/identifier with the given search term."""
    term = search_term.lower().strip()
    if not term:
        return []
    return [
        p
        for p in projects
        if term in (p.get("name") or "").lower() or term in (p.get("identifier") or "").lower()
    ]


def generate_search_variations(name: str) -> list[str]:
    """Generate progressive search variations of a name (works for projects, users, etc.)

    Order: full name -> parts -> shortened versions
    Example: "Michael Jirsa" -> ["Michael Jirsa", "Michael", "Jirsa", "Micha", "Mich", "Mic", "Mi", "Jirs", "Jir", "Ji"]
    """
    name = name.strip()
    if not name:
        return []
    variations: list[str] = [name]
    parts = name.split()
    for part in parts:
        if part and part not in variations:
            variations.append(part)
    for part in parts:
        if len(part) > 2:
            for i in range(len(part) - 1, 1, -1):
                s = part[:i]
                if s not in variations:
                    variations.append(s)
    return variations


def resolve_project_id(
    redmine: RedmineClient,
    username: str,
    project_id: int | None = None,
    project_name: str | None = None,
    cache: dict[str, Any] | None = None,
) -> tuple[int | None, str | None]:
    """Resolve project_id from project_name if needed. Returns (project_id, error_message).

    If project_name is provided and project_id is not, automatically searches for the project.
    Uses exact match if available, otherwise progressive search.
    Uses cache to avoid redundant API calls within the same request.

    Args:
        redmine: RedmineClient instance
        username: Username for API calls
        project_id: Optional project ID (if provided, returns immediately)
        project_name: Optional project name to resolve
        cache: Optional cache dict for storing project lookups (structure: {"projects": {username: {project_name: project_id}}, "all_projects": {username: list[dict]}})

    Returns:
        Tuple of (project_id, error_message). If error_message is not None, project_id will be None.
    """
    if project_id:
        return int(project_id), None

    if not project_name:
        return None, None  # No project specified, let caller handle it

    # Check cache first
    if cache and username in cache.get("projects", {}):
        cached_projects = cache["projects"][username]
        if project_name in cached_projects:
            cached_id = cached_projects[project_name]
            if isinstance(cached_id, int):
                print(f"[CACHE HIT] Project '{project_name}' -> {cached_id}")
                return cached_id, None

    # Cache miss - fetch projects (or use cached list)
    if cache and username in cache.get("all_projects", {}):
        projects = cache["all_projects"][username]
        print(f"[CACHE HIT] Using cached project list for {username}")
    else:
        projects = redmine.get_projects(username)
        # Store in cache for future lookups
        if cache:
            if "all_projects" not in cache:
                cache["all_projects"] = {}
            cache["all_projects"][username] = projects
            print(f"[CACHE STORE] Stored {len(projects)} projects for {username}")
    pn_lower = project_name.lower().strip()

    # First, try exact match (case-insensitive) on name or identifier
    exact = [
        p
        for p in projects
        if (p.get("name") or "").lower().strip() == pn_lower
        or (p.get("identifier") or "").lower().strip() == pn_lower
    ]

    if len(exact) == 1:
        resolved_id = exact[0]["id"]
        # Store in cache
        if cache:
            if "projects" not in cache:
                cache["projects"] = {}
            if username not in cache["projects"]:
                cache["projects"][username] = {}
            cache["projects"][username][project_name] = resolved_id
            cache["projects"][username][resolved_id] = exact[0]  # Store full project data too
        return resolved_id, None

    if len(exact) > 1:
        lines = [f"• {p['name']} ({p.get('identifier', '')}): ID {p['id']}" for p in exact[:10]]
        return (
            None,
            f"Našel jsem {len(exact)} projektů s názvem '{project_name}'. Upřesněte prosím:\n"
            + "\n".join(lines),
        )

    # No exact match - try progressive search
    for var in generate_search_variations(project_name):
        if len(var) < 2:
            continue
        found = search_projects(projects, var)
        if found:
            if len(found) == 1:
                resolved_id = found[0]["id"]
                # Store in cache
                if cache:
                    if "projects" not in cache:
                        cache["projects"] = {}
                    if username not in cache["projects"]:
                        cache["projects"][username] = {}
                    cache["projects"][username][project_name] = resolved_id
                    cache["projects"][username][resolved_id] = found[
                        0
                    ]  # Store full project data too
                return resolved_id, None
            lines = [f"• {p['name']} ({p.get('identifier', '')}): ID {p['id']}" for p in found[:10]]
            return (
                None,
                f"Našel jsem {len(found)} projektů podobných '{project_name}':\n"
                + "\n".join(lines),
            )

    return None, f"Nenašel jsem projekt '{project_name}' v Redmine."


def search_users(users: list[dict], term: str) -> list[dict]:
    """Search users by name/login with the given search term."""
    t = term.lower().strip()
    if not t:
        return []
    out = []
    for u in users:
        fn = (u.get("firstname") or "").lower()
        ln = (u.get("lastname") or "").lower()
        login = (u.get("login") or "").lower()
        full = f"{fn} {ln}".strip()
        if t in fn or t in ln or t in full or t in login:
            out.append(u)
    return out
