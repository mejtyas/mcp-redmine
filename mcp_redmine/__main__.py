"""python -m mcp_redmine (set PYTHONPATH to include the parent of this package, e.g. /app/mcp)."""

from __future__ import annotations

from .env import normalize_redmine_env


def main() -> None:
    """CLI entry for ``python -m mcp_redmine``."""
    normalize_redmine_env()
    from .server import run

    run()


if __name__ == "__main__":
    main()
