# mcp-redmine

Connect coding agents to [Redmine](https://www.redmine.org/) through the [Model Context Protocol](https://modelcontextprotocol.io/). Use a normal **API key**; the agent can search issues, update tickets, log time, and manage project basics without opening the web UI. Source: [github.com/mejtyas/mcp-redmine](https://github.com/mejtyas/mcp-redmine).

Docker image: [`mejtyas/mcp-redmine:latest`](https://hub.docker.com/r/mejtyas/mcp-redmine) (run with `docker run -i` for stdio).

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
| `redmine_execute_custom_request` | — |

Together these cover most day-to-day workflows: **projects**, **issues** (look up, search, create, edit), **versions**, **members**, **time logging**, **attachments**, and **relations**. For typical agent tasks—triage, updates, notes, light reporting—that is roughly **95% of what you need** without custom glue code.

## Before you start

1. In Redmine, open **My account** and create an **API access key** if you do not have one.
2. Set credentials using the **canonical** names below (shell, Cursor **`env`** block, or inline Docker `-e` `VAR=value` in **`args`**—see [Cursor](#cursor)). The server also accepts `redmine_url` and `redmine_api_token` as aliases.

| Variable | Value |
|----------|--------|
| `REDMINE_URL` | Base URL, e.g. `https://redmine.example.com` (no trailing slash required) |
| `REDMINE_API_KEY` | Your API key string |

Everything the agent does runs **as the Redmine user** tied to that key.

## Run the server (Docker)

```bash
docker run --rm -i \
  -e REDMINE_URL=https://your-redmine.example.com \
  -e REDMINE_API_KEY=your_key \
  mejtyas/mcp-redmine:latest
```

## Company HTTPS deployment (Cursor `url`)

For a shared host (for example `https://mcp-redmine.example.com/mcp`), the server can keep **one company Redmine URL** and require a **shared gate token** plus **each developer’s Redmine API key** on every HTTP request.

1. **Redmine URL** — either set `REDMINE_URL` in the container environment, or set `COMPANY_REDMINE_URL` in `mcp_redmine/config.py` (used when `REDMINE_URL` is unset).
2. **Server environment** (deployment / GitLab CI variables, not in `mcp.json`):
   - `MCP_TRANSPORT` — `streamable-http` (recommended) or `sse`
   - `MCP_AUTH_TOKEN` — long random secret shared inside the company (required for HTTP transport)
   - Optional: `MCP_HOST`, `MCP_PORT` (default `0.0.0.0` / `8000`), `MCP_PATH` (default `/mcp`)
3. **Cursor** — remote entry with two headers: company gate + personal Redmine key:

```json
{
  "mcpServers": {
    "mcp-redmine": {
      "url": "https://mcp-redmine.example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${env:MCP_AUTH_TOKEN}",
        "X-Redmine-API-Key": "${env:REDMINE_API_KEY}"
      }
    }
  }
}
```

Use the same header names if you terminate TLS in front of the app; the MCP process must still receive `Authorization: Bearer …` and `X-Redmine-API-Key: …`. Do not commit real tokens.

## Cursor

Open **Settings → MCP**, or edit `~/.cursor/mcp.json`. Use a top-level **`mcpServers`** object.

### Option A — `env` block (recommended)

Cursor sets **`env`** on the MCP server process. Use bare **`-e VAR`** in Docker **`args`** so those variables are forwarded into the container (no secrets duplicated in the `run` argument list).

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
        "REDMINE_URL",
        "-e",
        "REDMINE_API_KEY",
        "mejtyas/mcp-redmine:latest"
      ],
      "env": {
        "REDMINE_URL": "https://your-redmine.example.com",
        "REDMINE_API_KEY": "your_key"
      }
    }
  }
}
```

### Option B — inline `-e` in `args`

If you prefer everything in **`args`**, this shape also works:

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

Replace placeholders with your values. Do not commit real URLs or keys.
