"""HTTP transport: company Bearer gate + per-request Redmine API key (ContextVar)."""

from __future__ import annotations

import os
from contextvars import ContextVar, Token
from typing import Any

from mcp import McpError
from mcp.types import ErrorData

from fastmcp.server.dependencies import get_http_headers, get_http_request
from fastmcp.server.middleware.middleware import CallNext, Middleware, MiddlewareContext

_redmine_api_key_var: ContextVar[str | None] = ContextVar("mcp_redmine_api_key", default=None)


class AuthMcpError(McpError):
    """Auth failure surfaced to MCP clients."""

    def __init__(self, message: str) -> None:
        super().__init__(ErrorData(code=-32000, message=message))


def get_request_redmine_api_key() -> str | None:
    """Effective Redmine key for this MCP request (HTTP), or None to fall back to env."""
    return _redmine_api_key_var.get()


def _reset_redmine_key_token(token: Token | None) -> None:
    if token is not None:
        _redmine_api_key_var.reset(token)


def _parse_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(None, 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip() or None
    return None


class RemoteSessionMiddleware(Middleware):
    """Require MCP_AUTH_TOKEN (Bearer) and X-Redmine-API-Key on HTTP; stdio unchanged."""

    def __init__(self) -> None:
        self._expected_gate = (os.environ.get("MCP_AUTH_TOKEN") or "").strip()

    async def on_request(
        self,
        context: MiddlewareContext[Any],
        call_next: CallNext[Any, Any],
    ) -> Any:
        token: Token | None = None
        try:
            try:
                get_http_request()
            except RuntimeError:
                return await call_next(context)

            headers = get_http_headers(include_all=True)
            if not self._expected_gate:
                raise AuthMcpError(
                    "Server misconfiguration: MCP_AUTH_TOKEN must be set for HTTP transport."
                )

            bearer = _parse_bearer(headers.get("authorization"))
            if bearer != self._expected_gate:
                raise AuthMcpError("Unauthorized: invalid or missing MCP gate token (Bearer).")

            redmine_key = (headers.get("x-redmine-api-key") or "").strip()
            if not redmine_key:
                raise AuthMcpError(
                    "Missing X-Redmine-API-Key header (your personal Redmine API key)."
                )

            token = _redmine_api_key_var.set(redmine_key)
            return await call_next(context)
        finally:
            _reset_redmine_key_token(token)
