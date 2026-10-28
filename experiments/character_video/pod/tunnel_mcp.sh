#!/bin/bash
# Second tunnel for WanGP's MCP server (start WanGP with --mcp-webui --mcp-port 8000).
# The Host header is rewritten to localhost because MCP servers reject other hosts.
# Anyone with the printed URL can submit jobs and read /workspace: close it when done.
[ -x /usr/local/bin/cloudflared ] || { wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /tmp/cf && cp /tmp/cf /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared; }
cloudflared tunnel --url http://localhost:8000 --http-host-header localhost:8000
