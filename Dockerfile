# Build context must be this directory (the folder that contains requirements.txt and mcp_redmine/).
# From mattermost-ai-bot: docker build -f mcp/mcp_redmine/Dockerfile -t mcp-redmine:latest mcp/mcp_redmine
# From mcp/:            docker build -f mcp_redmine/Dockerfile -t mcp-redmine:latest mcp_redmine
# Standalone GitHub repo (this folder = repo root): docker build -t mcp-redmine:latest .
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY mcp_redmine /app/mcp_redmine

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "mcp_redmine"]
