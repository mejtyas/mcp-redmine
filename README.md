# mcp-redmine (FastMCP)

stdio [MCP](https://modelcontextprotocol.io/) server with **16 Redmine tools**. This package is **standalone**: it ships its own [`mcp_redmine/redmine_agent/`](mcp_redmine/redmine_agent/) (REST client + LangChain tools) and does **not** depend on the Mattermost bot codebase.

Upstream tools are kept in sync with the Redmine LangChain tools in the [mattermost-ai-bot](https://gitlab.anycoders.cz/anycoders/mattermost-ai-bot) monorepo (`diego/agents/redmine_agent/`). The Mattermost upload helper is not included here.

**Source:** [github.com/mejtyas/mcp-redmine](https://github.com/mejtyas/mcp-redmine)

### Push this tree to GitHub (first time or refresh)

From your machine (with GitHub auth: SSH key or HTTPS + [PAT](https://github.com/settings/tokens)):

```bash
git clone https://github.com/mejtyas/mcp-redmine.git /tmp/mcp-redmine && cd /tmp/mcp-redmine
rsync -a /path/to/mattermost-ai-bot/mcp/mcp_redmine/ ./
git checkout -b main 2>/dev/null || git branch -M main
git add -A
git status
git commit -m "Import mcp-redmine"
git push -u origin main
```

If the remote already has commits, use `git pull origin main --rebase` before `git push`.

## Environment variables

| Variable | Meaning |
|----------|---------|
| `REDMINE_URL` or `redmine_url` | Redmine base URL (no trailing slash required) |
| `REDMINE_API_KEY` or `redmine_api_token` | REST API key |

Aliases are copied into `REDMINE_URL` / `REDMINE_API_KEY` before the server starts.

This server **does not** set `X-Redmine-Switch-User`. All actions run as the Redmine user tied to the API key.

## Build and run (Docker)

The Docker **build context** must be **this directory** (the folder that contains `Dockerfile`, `requirements.txt`, and the `mcp_redmine/` package).

**Clone / standalone repo (this folder is the git root):**

```bash
docker build -t mcp-redmine:latest .
```

**Inside [mattermost-ai-bot](https://gitlab.anycoders.cz/anycoders/mattermost-ai-bot) monorepo** — from repository root:

```bash
docker build -f mcp/mcp_redmine/Dockerfile -t mcp-redmine:latest mcp/mcp_redmine
```

From `mcp/`:

```bash
docker build -f mcp_redmine/Dockerfile -t mcp-redmine:latest mcp_redmine
```

The image installs only [`requirements.txt`](requirements.txt).

Run:

```bash
docker run --rm -i \
  -e REDMINE_URL=https://redmine.example.com \
  -e REDMINE_API_KEY=your_api_key \
  mcp-redmine:latest
```

`-i` keeps stdin open; Cursor uses the same when it launches MCP over stdio.

## Publish to Docker Hub

```bash
docker build -t mejtyas/mcp-redmine:latest .
docker push mejtyas/mcp-redmine:latest
```

(Run from this directory as build context, or use the monorepo `-f` / context paths above and the same tag.)

## Cursor `mcp.json` example

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
        "REDMINE_URL=https://your-redmine.example/",
        "-e",
        "REDMINE_API_KEY=your_token",
        "mejtyas/mcp-redmine:latest"
      ]
    }
  }
}
```

Use a real URL and token; do not commit API keys.

## Local run

```bash
pip install -r requirements.txt
export PYTHONPATH="$(pwd)"
export REDMINE_URL="https://your-redmine/"
export REDMINE_API_KEY="your_token"
python -m mcp_redmine
```

Run these commands from **this directory** (the folder that contains the `mcp_redmine` package directory). `PYTHONPATH` must be that folder’s path so `import mcp_redmine` resolves. There is no top-level Python package named `mcp` here, so the PyPI `mcp` library used by FastMCP is not shadowed.
