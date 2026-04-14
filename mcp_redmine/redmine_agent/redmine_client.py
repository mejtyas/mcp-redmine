#!/usr/bin/env python3
"""
Redmine API client for interacting with Redmine REST API.
Standalone MCP copy: reads URL and API key from environment only.
"""

from __future__ import annotations

import os
from typing import Any

import requests

from ..http_auth import get_request_redmine_api_key


class RedmineClient:
    """Client for Redmine REST API."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("REDMINE_API_KEY", "") or ""
        raw = base_url if base_url is not None else os.environ.get("REDMINE_URL", "") or ""
        self.base_url = raw.rstrip("/")

    def _get_headers(self, username: str | None = None, impersonate: bool = True) -> dict[str, str]:
        api_key = (get_request_redmine_api_key() or "").strip() or (self.api_key or "")
        headers: dict[str, str] = {"X-Redmine-API-Key": api_key, "Content-Type": "application/json"}
        if impersonate and username:
            headers["X-Redmine-Switch-User"] = username
        return headers

    def _make_request(
        self,
        method: str,
        endpoint: str,
        username: str | None = None,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        impersonate: bool = True,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(username, impersonate=impersonate)

        try:
            response = requests.request(
                method=method, url=url, headers=headers, json=data, params=params, timeout=30
            )

            response.raise_for_status()
            if response.text:
                result: dict[str, Any] = (
                    response.json() if isinstance(response.json(), dict) else {}
                )
                return result
            return {}
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Redmine API error: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"[ERROR] Response status: {e.response.status_code}")
                print(f"[ERROR] Response text: {e.response.text[:500]}")
                status_code = e.response.status_code
                response_text = e.response.text.strip()

                if response_text:
                    try:
                        error_detail = e.response.json()
                        error_msg = error_detail.get("errors", [str(e)])
                        if isinstance(error_msg, list):
                            error_msg = ", ".join(str(err) for err in error_msg)
                        raise Exception(f"Redmine API error ({status_code}): {error_msg}") from e
                    except (ValueError, requests.exceptions.JSONDecodeError):
                        raise Exception(
                            f"Redmine API error ({status_code}): {response_text}"
                        ) from e
                if status_code == 403:
                    raise Exception(
                        f"Redmine API error ({status_code}): Forbidden - insufficient permissions to access this resource"
                    ) from e
                if status_code == 404:
                    raise Exception(f"Redmine API error ({status_code}): Resource not found") from e
                if status_code == 401:
                    raise Exception(
                        f"Redmine API error ({status_code}): Unauthorized - invalid API key or user"
                    ) from e
                raise Exception(f"Redmine API error ({status_code}): {str(e)}") from e
            raise Exception(f"Redmine API error: {e}") from e

    def _fetch_paginated(
        self,
        endpoint: str,
        username: str | None = None,
        collection_key: str = "items",
        params: dict | None = None,
        impersonate: bool = True,
    ) -> list[dict]:
        all_items: list[dict] = []
        limit = 100
        offset = 0

        request_params = dict(params) if params else {}

        while True:
            request_params["limit"] = limit
            request_params["offset"] = offset

            result = self._make_request(
                "GET", endpoint, username, params=request_params, impersonate=impersonate
            )

            items = result.get(collection_key, [])
            if not items:
                break

            all_items.extend(items)

            total_count = result.get("total_count", 0)
            if total_count > 0 and len(all_items) >= total_count:
                break

            if len(items) < limit:
                break

            offset += limit

        return all_items

    def rest_json(
        self,
        method: str,
        endpoint: str,
        username: str | None = None,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        impersonate: bool = True,
    ) -> dict[str, Any]:
        """Low-level JSON REST call. ``endpoint`` must start with ``/``."""
        ep = endpoint.strip()
        if not ep.startswith("/"):
            raise ValueError("endpoint must start with /")
        return self._make_request(
            method.upper(), ep, username, data=data, params=params, impersonate=impersonate
        )

    def paginate_json(
        self,
        endpoint: str,
        collection_key: str,
        username: str | None = None,
        params: dict[str, Any] | None = None,
        impersonate: bool = True,
    ) -> list[dict]:
        """Fetch all pages for a GET collection endpoint (e.g. ``issues``, ``users``)."""
        ep = endpoint.strip()
        if not ep.startswith("/"):
            raise ValueError("endpoint must start with /")
        return self._fetch_paginated(
            ep, username, collection_key=collection_key, params=params, impersonate=impersonate
        )

    def get_users(self, username: str | None = None) -> list[dict]:
        return self._fetch_paginated(
            "/users.json", username, collection_key="users", impersonate=False
        )

    def get_current_user(self, username: str) -> dict[str, Any]:
        result = self._make_request("GET", "/users/current.json", username)
        user_data = result.get("user", {})
        return user_data if isinstance(user_data, dict) else {}

    def get_projects(self, username: str) -> list[dict[str, Any]]:
        return self._fetch_paginated("/projects.json", username, collection_key="projects")

    def get_project(self, username: str, project_id: int) -> dict[str, Any]:
        result = self._make_request("GET", f"/projects/{project_id}.json", username)
        project_data = result.get("project", {})
        return project_data if isinstance(project_data, dict) else {}

    def create_issue(
        self,
        username: str,
        project_id: int,
        subject: str,
        description: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        issue_data = {"project_id": project_id, "subject": subject}
        if description:
            issue_data["description"] = description

        issue_data.update(kwargs)

        data = {"issue": issue_data}
        result = self._make_request("POST", "/issues.json", username, data=data)
        issue_data_result = result.get("issue", {})
        return issue_data_result if isinstance(issue_data_result, dict) else {}

    def edit_issue(self, username: str, issue_id: int, **updates: Any) -> dict[str, Any]:
        print(
            f"[DEBUG] RedmineClient.edit_issue: issue_id={issue_id}, updates={updates}, username={username}"
        )
        data = {"issue": updates}
        result = self._make_request("PUT", f"/issues/{issue_id}.json", username, data=data)
        print(f"[DEBUG] RedmineClient.edit_issue API response: {result}")
        issue_data_result = result.get("issue", {})
        return issue_data_result if isinstance(issue_data_result, dict) else {}

    def add_note_to_issue(self, username: str, issue_id: int, notes: str) -> dict[str, Any]:
        return self.edit_issue(username, issue_id, notes=notes)

    def get_issue(self, username: str, issue_id: int) -> dict[str, Any]:
        result = self._make_request("GET", f"/issues/{issue_id}.json", username)
        issue_data_result = result.get("issue", {})
        return issue_data_result if isinstance(issue_data_result, dict) else {}

    def delete_issue(self, username: str, issue_id: int) -> None:
        self._make_request("DELETE", f"/issues/{issue_id}.json", username)

    def get_issue_statuses(self, username: str) -> list[dict]:
        return self._fetch_paginated(
            "/issue_statuses.json", username, collection_key="issue_statuses"
        )

    def create_fixed_version(
        self, username: str, project_id: int, name: str, **kwargs: Any
    ) -> dict[str, Any]:
        version_data = {"project_id": project_id, "name": name}
        version_data.update(kwargs)

        data = {"version": version_data}
        result = self._make_request(
            "POST", f"/projects/{project_id}/versions.json", username, data=data
        )
        version_data_result = result.get("version", {})
        return version_data_result if isinstance(version_data_result, dict) else {}

    def get_fixed_versions_id(self, username: str, project_id: int) -> list[int]:
        versions = self._fetch_paginated(
            f"/projects/{project_id}/versions.json", username, collection_key="versions"
        )
        result: list[int] = []
        for v in versions:
            version_id = v.get("id")
            if version_id is not None and isinstance(version_id, int):
                result.append(version_id)
        return result

    def get_fixed_versions(self, username: str, project_id: int) -> list[dict]:
        return self._fetch_paginated(
            f"/projects/{project_id}/versions.json", username, collection_key="versions"
        )

    def search_issues(self, username: str, **filters: Any) -> list[dict[str, Any]]:
        params = {}
        for key, value in filters.items():
            if value is not None:
                params[key] = value

        return self._fetch_paginated(
            "/issues.json", username, collection_key="issues", params=params
        )

    def get_issues_due_on(self, due_date: str, only_open: bool = True) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"due_date": due_date}
        raw = self._fetch_paginated(
            "/issues.json",
            username=None,
            collection_key="issues",
            params=params,
            impersonate=False,
        )
        if only_open:
            raw = [i for i in raw if (i.get("status") or {}).get("name") != "Closed"]
        return [i for i in raw if (i.get("due_date") or "").startswith(due_date)]

    def get_issues_count(self, username: str, **filters: Any) -> int:
        params = {"limit": 1}
        for key, value in filters.items():
            if value is not None:
                params[key] = value

        result = self._make_request("GET", "/issues.json", username, params=params)
        total_count = result.get("total_count", 0)
        return int(total_count) if isinstance(total_count, (int, str)) else 0

    def search(self, username: str, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        params = {"q": query}
        params.update(kwargs)

        return self._fetch_paginated(
            "/search.json", username, collection_key="results", params=params
        )

    def add_member_to_project(
        self, username: str, project_id: int, user_id: int, role_ids: list[int]
    ) -> dict[str, Any]:
        membership_data = {"user_id": user_id, "role_ids": role_ids}
        data = {"membership": membership_data}
        result = self._make_request(
            "POST", f"/projects/{project_id}/memberships.json", username, data=data
        )
        membership_data_result = result.get("membership", {})
        return membership_data_result if isinstance(membership_data_result, dict) else {}

    def remove_member_from_project(
        self, username: str, project_id: int, membership_id: int
    ) -> None:
        self._make_request("DELETE", f"/memberships/{membership_id}.json", username)

    def get_project_members(self, username: str, project_id: int) -> list[dict]:
        return self._fetch_paginated(
            f"/projects/{project_id}/memberships.json", username, collection_key="memberships"
        )

    def get_time_entries(
        self,
        username: str,
        project_id: int | None = None,
        issue_id: int | None = None,
        user_id: int | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list[dict]:
        params: dict = {}
        if project_id:
            params["project_id"] = project_id
        if issue_id:
            params["issue_id"] = issue_id
        if user_id:
            params["user_id"] = user_id
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._fetch_paginated(
            "/time_entries.json",
            username,
            collection_key="time_entries",
            params=params,
            impersonate=False,
        )

    def log_time(
        self,
        username: str,
        issue_id: int,
        hours: float,
        activity_id: int | None = None,
        comments: str | None = None,
        spent_on: str | None = None,
    ) -> dict:
        time_entry_data: dict[str, Any] = {"issue_id": issue_id, "hours": hours}
        if activity_id:
            time_entry_data["activity_id"] = activity_id
        if comments:
            time_entry_data["comments"] = comments
        if spent_on:
            time_entry_data["spent_on"] = spent_on

        data = {"time_entry": time_entry_data}
        result = self._make_request("POST", "/time_entries.json", username, data=data)
        time_entry_result = result.get("time_entry", {})
        return time_entry_result if isinstance(time_entry_result, dict) else {}

    def upload_file(
        self,
        username: str,
        content: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        url = f"{self.base_url}/uploads.json"
        api_key = (get_request_redmine_api_key() or "").strip() or (self.api_key or "")
        headers: dict[str, str] = {
            "X-Redmine-API-Key": api_key,
            "Content-Type": content_type,
        }
        if username:
            headers["X-Redmine-Switch-User"] = username
        params = {"filename": filename}

        try:
            response = requests.post(
                url=url, headers=headers, data=content, params=params, timeout=60
            )
            response.raise_for_status()
            result = response.json()
            upload_data = result.get("upload", {}) if isinstance(result, dict) else {}
            token = upload_data.get("token") if isinstance(upload_data, dict) else None
            return str(token) if token else ""
        except Exception as e:
            print(f"[ERROR] Redmine file upload error: {e}")
            raise Exception(f"Redmine file upload error: {e}") from e

    def add_issue_relation(
        self,
        username: str,
        issue_id: int,
        to_issue_id: int,
        relation_type: str = "relates",
        delay: int | None = None,
    ) -> dict[str, Any]:
        relation_data = {"issue_to_id": to_issue_id, "relation_type": relation_type}
        if delay:
            relation_data["delay"] = delay

        data = {"relation": relation_data}
        result = self._make_request(
            "POST", f"/issues/{issue_id}/relations.json", username, data=data
        )
        relation_data_result = result.get("relation", {})
        return relation_data_result if isinstance(relation_data_result, dict) else {}
