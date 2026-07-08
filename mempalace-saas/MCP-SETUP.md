# MemPalace Universal MCP Server — Setup Guide

One MCP server, three transports. Works with every MCP client — old or new,
local or remote: Claude Code, Claude Desktop, ChatGPT connectors, Cursor,
Windsurf, Cline, Zed, or any agent built on an MCP-capable SDK.

| Transport | Endpoint | For |
|---|---|---|
| stdio | (process pipes) | Local clients: Claude Code, Claude Desktop, Cursor… |
| Streamable HTTP | `POST /mcp` | Modern remote clients (2025+ spec) |
| SSE (legacy) | `GET /sse` + `POST /messages/` | Older remote clients, ChatGPT connectors |

Protocol versions `2024-11-05` through `2025-11-25` are negotiated
automatically per connection.

---

## 1. Install

```bash
cd mempalace-saas
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

## 2. Local use (stdio) — Claude Code / Claude Desktop

```bash
# Claude Code
claude mcp add mempalace -- /absolute/path/to/mempalace-saas/venv/bin/python -m mempalace.mcp_universal
```

Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mempalace": {
      "command": "/absolute/path/to/mempalace-saas/venv/bin/python",
      "args": ["-m", "mempalace.mcp_universal"]
    }
  }
}
```

## 3. Remote use (HTTP server)

```bash
# Choose a strong secret — anyone with it has read/write access to your palace
export MEMPALACE_MCP_TOKEN="$(openssl rand -hex 24)"
echo "Token: $MEMPALACE_MCP_TOKEN"   # save this

venv/bin/python -m mempalace.mcp_universal --transport http --host 0.0.0.0 --port 8765
```

Health check: `curl http://localhost:8765/health`

Auth is accepted two ways (both checked on every request):
- Header: `Authorization: Bearer <token>` — preferred
- Query param: `?token=<token>` — for clients that can't send custom headers (e.g. ChatGPT)

Omit `MEMPALACE_MCP_TOKEN` to disable auth (only safe on localhost/private networks).

### Expose with ngrok

```bash
ngrok config add-authtoken <YOUR_NGROK_TOKEN>   # once
ngrok http 8765
# → https://<random>.ngrok-free.dev
```

Free random URLs change on every restart. For a stable URL, claim a free
static domain at dashboard.ngrok.com → Domains, then:

```bash
ngrok http 8765 --domain=your-name.ngrok-free.app
```

### Deploy on Railway (permanent URL)

The server respects `$PORT` automatically. Set the start command to:

```
python -m mempalace.mcp_universal --transport http --host 0.0.0.0
```

and add `MEMPALACE_MCP_TOKEN` in Railway → Variables.

## 4. Connect clients to the remote server

```bash
# Claude Code — modern transport (recommended)
claude mcp add --transport http mempalace https://<host>/mcp \
  --header "Authorization: Bearer <token>"

# Older SSE-only clients
claude mcp add --transport sse mempalace "https://<host>/sse?token=<token>"
```

### ChatGPT

1. Settings → Connectors → Advanced → enable **Developer mode**
2. Add connector with URL: `https://<host>/sse?token=<token>`
3. No OAuth needed — the token in the URL is the auth. Treat that URL as a password.

All 19 `mempalace_*` tools appear and are callable directly.

## 5. Verify

```bash
# Health
curl https://<host>/health

# Full handshake (expect an initialize result event)
curl -s -X POST https://<host>/mcp \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"curl","version":"1"}}}'
```

## Reference

```
python -m mempalace.mcp_universal [--transport stdio|http] [--host H] [--port P]
```

| Env var | Purpose | Default |
|---|---|---|
| `MEMPALACE_MCP_TOKEN` | Auth token for HTTP mode | unset (no auth) |
| `MEMPALACE_MCP_HOST` | Bind host | `127.0.0.1` |
| `MEMPALACE_MCP_PORT` | Bind port | `$PORT` or `8765` |
| `MEMPALACE_PALACE_PATH` | ChromaDB palace location | mempalace config default |

Troubleshooting:
- **401 unauthorized** — token missing/wrong; check header or `?token=`.
- **Client can't connect to `/mcp`** — it's probably an older client; use the `/sse` URL instead.
- **ngrok URL stopped working** — free random URLs die with the tunnel; restart ngrok and update the client config, or use a static domain.
