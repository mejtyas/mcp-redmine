"""Register redmine_execute_custom_request with the FastMCP server."""

from __future__ import annotations

import anyio
from fastmcp import FastMCP

from .redmine_agent.redmine_client import RedmineClient
from .sandbox_execute import DEFAULT_TIMEOUT_S, run_user_code

_TOOL_DESCRIPTION = """\
SECURITY: This runs Python inside the MCP server process with your Redmine API credentials. \
**You (the human operator) must read and approve every code snippet before the agent runs it.** \
Only use with trusted clients. The sandbox is best-effort, not a guarantee against malicious code.

When to use: Multi-step workflows (roughly five or more logical steps), batch processing, \
combining several API calls, or logic that does not map to a single dedicated `redmine_*` tool.

When NOT to use: Single simple operations (create one issue, fetch one issue, etc.) — use the \
existing `redmine_*` tools instead.

Contract (what to write):
- No `import`; no file or network access except via the injected `redmine` client.
- Variables available: `redmine` (configured `RedmineClient`), `output` (put your result here).
- Prefer `redmine.search_issues`, `redmine.edit_issue`, etc. For arbitrary REST JSON, use \
`redmine.rest_json(method, endpoint, data=..., params=...)` with `endpoint` starting with `/`, \
or `redmine.paginate_json(endpoint, collection_key, params=...)` for full list pagination.
- Set JSON-serializable data on `output`, e.g. `output["items"] = [...]`, `output["summary"] = "..."`.

Errors from Redmine (HTTP, permissions) are raised as exceptions from `redmine` methods and \
returned in the tool result as JSON with `"ok": false`.
"""


def register_execute_custom_tool(mcp: FastMCP, redmine: RedmineClient) -> None:
    @mcp.tool(
        name="redmine_execute_custom_request",
        description=_TOOL_DESCRIPTION,
    )
    async def redmine_execute_custom_request(
        code: str,
        timeout_seconds: float = DEFAULT_TIMEOUT_S,
    ) -> str:
        capped = min(max(timeout_seconds, 5.0), 600.0)

        def _run() -> str:
            return run_user_code(redmine, code, timeout_seconds=capped)

        return await anyio.to_thread.run_sync(_run)
