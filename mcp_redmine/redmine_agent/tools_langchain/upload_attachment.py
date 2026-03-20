#!/usr/bin/env python3
"""Tool for uploading attachments to Redmine."""

from __future__ import annotations

import base64
import os
from collections.abc import Callable

from langchain_core.tools import BaseTool, tool

from ..redmine_client import RedmineClient


def create_upload_attachment_tool(
    redmine: RedmineClient, get_username: Callable[[], str]
) -> BaseTool:
    """Create the redmine_upload_attachment tool."""

    @tool
    def redmine_upload_attachment(
        filename: str, content_base64: str | None = None, file_path: str | None = None
    ) -> str:
        """Upload a file to Redmine and return an upload token.
        Required: filename, and either content_base64 or file_path."""
        uname = get_username()

        content = None
        if content_base64:
            try:
                content = base64.b64decode(content_base64)
            except Exception as e:
                return f"Chyba při dekódování Base64 obsahu: {e}"
        elif file_path:
            try:
                if not os.path.exists(file_path):
                    return f"Chyba: Soubor '{file_path}' neexistuje."
                with open(file_path, "rb") as f:
                    content = f.read()
            except Exception as e:
                return f"Chyba při čtení souboru '{file_path}': {e}"
        else:
            return "Chyba: Musíte zadat buď content_base64 nebo file_path."

        try:
            token = redmine.upload_file(uname, content, filename)
            return f"Soubor '{filename}' byl úspěšně nahrán. Token: {token}"
        except Exception as e:
            return f"Chyba při nahrávání souboru '{filename}': {str(e)}"

    return redmine_upload_attachment
