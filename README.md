# mcp-redmine

[MCP](https://modelcontextprotocol.io/) server (stdio, FastMCP) that talks to [Redmine](https://www.redmine.org/) over its REST API. Source: [github.com/mejtyas/mcp-redmine](https://github.com/mejtyas/mcp-redmine).

## Tools (17)

| Read | Create / update |
|------|-----------------|
| `redmine_get_users` | `redmine_create_issue` |
| `redmine_get_current_user` | `redmine_edit_issue` |
| `redmine_get_projects` | `redmine_create_fixed_version` |
| `redmine_get_issue` | `redmine_add_member_to_project` |
| `redmine_search_issues` | `redmine_remove_member_from_project` |
| `redmine_get_fixed_versions` | `redmine_log_time` |
| `redmine_get_project_members` | `redmine_upload_attachment` |
| `redmine_get_time_entries` | `redmine_add_issue_relation` |
| [`redmine_execute_custom_request`](#advanced-redmine_execute_custom_request) (multi-step Python; **read every snippet before use**) | — |

## How to use it

1. Create a Redmine **API key** (My account → API access key) if you do not have one.

2. Set your instance URL and key (either spelling works):

   | Variable | Meaning |
   |----------|---------|
   | `REDMINE_URL` or `redmine_url` | Base URL, e.g. `https://redmine.example.com` |
   | `REDMINE_API_KEY` or `redmine_api_token` | API key string |

3. **Run with Docker** (needs `-i` for stdio):

   ```bash
   docker run --rm -i \
     -e REDMINE_URL=https://your-redmine.example.com \
     -e REDMINE_API_KEY=your_key \
     mejtyas/mcp-redmine:latest
   ```

   To build the image yourself from this repo: `docker build -t mejtyas/mcp-redmine:latest .` then use that tag in the command above.

4. **Or run from source** (from the repo root, the folder that contains `mcp_redmine/`):

   ```bash
   pip install -r requirements.txt
   export PYTHONPATH="$(pwd)"
   export REDMINE_URL="https://your-redmine.example.com"
   export REDMINE_API_KEY="your_key"
   python -m mcp_redmine
   ```

All Redmine actions run as the user tied to that API key.

## Advanced: `redmine_execute_custom_request`

This tool is **always registered**. Use it for multi-step or batch logic that does not fit the other tools.

1. **Read and approve every `code` argument** before your agent runs it. This is **arbitrary code execution** in the MCP process (with your API key). The sandbox blocks `import` and many dangerous calls but is **not** a strong security boundary.
2. Prefer dedicated `redmine_*` tools for single operations when they suffice.

**Contract:** The snippet runs with `redmine` (a configured `RedmineClient`) and `output` (place JSON-serializable results here). No `import`. Use `redmine.rest_json` / `redmine.paginate_json` for raw REST paths (path must start with `/`). Many client methods take a first `username` argument; with API-key-only usage pass `""`.

**Example — summarize open issues for a project (multi-step):**

```python
issues = redmine.search_issues("", project_id=1, status_id="open")
output["count"] = len(issues)
output["subjects"] = [i.get("subject", "") for i in issues[:20]]
```

**Example — read custom JSON endpoint then derive fields:**

```python
data = redmine.rest_json("GET", "/projects/1.json")
proj = data.get("project") or {}
output["name"] = proj.get("name")
output["id"] = proj.get("id")
```

**Example — paginate a collection, filter in code, then batch-update:**

```python
rows = redmine.paginate_json("/issues.json", "issues", params={"project_id": 1, "status_id": "open"})
stale = [i for i in rows if (i.get("updated_on") or "") < "2024-01-01"]
for issue in stale[:5]:
    iid = issue.get("id")
    if isinstance(iid, int):
        redmine.edit_issue("", iid, notes="Ping from automation.")
output["updated"] = len(stale[:5])
output["candidates"] = len(stale)
```

The tool returns JSON: `{"ok": true, "output": ...}` on success, or `{"ok": false, "error": "..."}` on validation, timeout, Redmine errors, or non-serializable `output`.

## Add it to Cursor

1. Open **Cursor Settings → MCP** (or edit your MCP config JSON if you manage it by hand).

2. Add a server. **Docker** (same as the run command above), for example:

   ```json
   {
     "mcpServers": {
       "mcp-redmine": {
         "command": "docker",
         "args": [
           "run",
           "-i",
           "--rm",
           "-e",
           "REDMINE_URL=https://your-redmine.example.com/",
           "-e",
           "REDMINE_API_KEY=your_key",
           "mejtyas/mcp-redmine:latest"
         ]
       }
     }
   }
   ```

3. Put your real URL and key in the `-e` lines. Do not commit API keys.

**Local Python instead of Docker:** point `command` at your `python`, set `"args": ["-m", "mcp_redmine"]`, set `"cwd"` to the repo root, and put `PYTHONPATH`, `REDMINE_URL`, and `REDMINE_API_KEY` in an `"env"` object (same values as in step 4 under [How to use it](#how-to-use-it)).
