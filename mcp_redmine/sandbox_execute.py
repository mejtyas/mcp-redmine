"""Best-effort sandbox for redmine_execute_custom_request (not a security boundary)."""

from __future__ import annotations

import ast
import json
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from typing import Any

from .redmine_agent.redmine_client import RedmineClient

MAX_CODE_BYTES = 32 * 1024
DEFAULT_TIMEOUT_S = 120

# Calls to these names are rejected when the callee is a simple Name(...)
FORBIDDEN_CALL_NAMES: frozenset[str] = frozenset(
    {
        "open",
        "exec",
        "eval",
        "compile",
        "__import__",
        "getattr",
        "setattr",
        "delattr",
        "breakpoint",
        "input",
        "help",
        "globals",
        "locals",
        "vars",
    }
)


class SandboxValidationError(ValueError):
    """User code failed static checks."""


def _safe_builtins() -> dict[str, Any]:
    b: dict[str, Any] = {}
    names = (
        "abs",
        "all",
        "any",
        "bin",
        "bool",
        "chr",
        "dict",
        "enumerate",
        "filter",
        "float",
        "format",
        "frozenset",
        "hash",
        "hex",
        "int",
        "isinstance",
        "issubclass",
        "iter",
        "len",
        "list",
        "map",
        "max",
        "min",
        "next",
        "oct",
        "ord",
        "pow",
        "range",
        "repr",
        "reversed",
        "round",
        "set",
        "slice",
        "sorted",
        "str",
        "sum",
        "tuple",
        "zip",
        "True",
        "False",
        "None",
        "Exception",
        "ValueError",
        "TypeError",
        "KeyError",
        "IndexError",
        "RuntimeError",
        "StopIteration",
    )
    import builtins as _bi

    for n in names:
        if hasattr(_bi, n):
            b[n] = getattr(_bi, n)
    b["print"] = lambda *a, **k: None  # noqa: ARG005 — discard; avoid log noise
    return b


class _SandboxAstValidator(ast.NodeVisitor):
    def visit_Import(self, node: ast.Import) -> None:
        raise SandboxValidationError("import is not allowed")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        raise SandboxValidationError("import is not allowed")

    def visit_Global(self, node: ast.Global) -> None:
        raise SandboxValidationError("global is not allowed")

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        raise SandboxValidationError("nonlocal is not allowed")

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr.startswith("__"):
            raise SandboxValidationError("dunder attribute access is not allowed")
        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        raise SandboxValidationError("walrus operator is not allowed")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        raise SandboxValidationError("async definitions are not allowed")

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        raise SandboxValidationError("class definitions are not allowed")

    def visit_Lambda(self, node: ast.Lambda) -> None:
        raise SandboxValidationError("lambda is not allowed")

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALL_NAMES:
            raise SandboxValidationError(f"call to {node.func.id!r} is not allowed")
        self.generic_visit(node)


def validate_user_source(source: str) -> ast.Module:
    if len(source.encode("utf-8")) > MAX_CODE_BYTES:
        raise SandboxValidationError(
            f"code exceeds maximum size ({MAX_CODE_BYTES} bytes UTF-8 encoded)"
        )
    try:
        tree = ast.parse(source, mode="exec")
    except SyntaxError as e:
        raise SandboxValidationError(f"syntax error: {e}") from e
    _SandboxAstValidator().visit(tree)
    return tree


def _execute_in_namespace(redmine: RedmineClient, tree: ast.Module) -> Any:
    out: dict[str, Any] = {}
    ns: dict[str, Any] = {
        "__builtins__": _safe_builtins(),
        "redmine": redmine,
        "output": out,
    }
    code = compile(tree, "<redmine_execute_custom_request>", "exec")
    exec(code, ns, ns)
    return ns.get("output", out)


def run_user_code(
    redmine: RedmineClient,
    source: str,
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_S,
) -> str:
    """
    Validate and run user code; return JSON string of ``output`` or an error message.

    The snippet must populate the injected dict ``output`` with JSON-serializable data.
    """
    try:
        tree = validate_user_source(source)
    except SandboxValidationError as e:
        return json.dumps({"ok": False, "error": str(e)}, default=str)

    def _run() -> Any:
        return _execute_in_namespace(redmine, tree)

    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(_run)
            user_output = fut.result(timeout=timeout_seconds)
    except FuturesTimeout:
        return json.dumps(
            {"ok": False, "error": f"execution timed out after {timeout_seconds}s"},
            default=str,
        )
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, default=str)

    try:
        json.dumps(user_output, default=str)
    except (TypeError, ValueError) as e:
        return json.dumps(
            {
                "ok": False,
                "error": f"output is not JSON-serializable: {e}",
            },
            default=str,
        )

    return json.dumps({"ok": True, "output": user_output}, default=str)
