#!/usr/bin/env python3
"""
MemPalace Universal MCP Server
==============================
Modern MCP server built on the official `mcp` SDK. Reuses every tool handler
from mempalace.mcp_server (single source of truth for tool logic) and adds:

  * Automatic protocol-version negotiation — works with old clients
    (2024-11-05) and new ones (2025-03-26, 2025-06-18) alike.
  * Three transports from one process:
      stdio            — local clients (Claude Code, Claude Desktop)
      streamable-http  — modern remote clients (POST /mcp)
      sse              — legacy remote clients (GET /sse + POST /messages)
    In HTTP mode both /mcp and /sse are served simultaneously, so any
    MCP-capable client can connect regardless of age.
  * Optional bearer-token auth for HTTP mode via MEMPALACE_MCP_TOKEN.

Usage:
  python -m mempalace.mcp_universal                     # stdio (default)
  python -m mempalace.mcp_universal --transport http    # serve /mcp + /sse
  python -m mempalace.mcp_universal --transport http --host 0.0.0.0 --port 8765

Install (local):
  claude mcp add mempalace -- python -m mempalace.mcp_universal
Install (remote, modern client):
  claude mcp add --transport http mempalace https://<host>/mcp
Install (remote, legacy client):
  claude mcp add --transport sse mempalace https://<host>/sse
"""

import argparse
import contextlib
import json
import logging
import os
import sys

import anyio
import mcp.types as types
from mcp.server.lowlevel import Server

from .version import __version__
from .mcp_server import TOOLS  # reuse existing tool registry + handlers

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
logger = logging.getLogger("mempalace_mcp_universal")

app = Server("mempalace", version=__version__)


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(name=name, description=t["description"], inputSchema=t["input_schema"])
        for name, t in TOOLS.items()
    ]


def _coerce_args(tool_name: str, tool_args: dict) -> dict:
    """Coerce numeric args — some transports deliver ints as floats/strings."""
    schema_props = TOOLS[tool_name]["input_schema"].get("properties", {})
    for key, value in list(tool_args.items()):
        declared = schema_props.get(key, {}).get("type")
        if declared == "integer" and not isinstance(value, int):
            tool_args[key] = int(value)
        elif declared == "number" and not isinstance(value, (int, float)):
            tool_args[key] = float(value)
    return tool_args


# validate_input=False: older/lenient clients send ints as strings; we coerce
# ourselves in _coerce_args instead of hard-rejecting.
@app.call_tool(validate_input=False)
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name not in TOOLS:
        raise ValueError(f"Unknown tool: {name}")
    args = _coerce_args(name, arguments or {})
    # Handlers are sync and may block on ChromaDB/network — run in a thread.
    result = await anyio.to_thread.run_sync(lambda: TOOLS[name]["handler"](**args))
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


# ── stdio transport ──────────────────────────────────────────────────────────


async def run_stdio():
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())


# ── HTTP transports (streamable-http + legacy SSE in one Starlette app) ─────


def build_http_app():
    from mcp.server.sse import SseServerTransport
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse, Response
    from starlette.routing import Mount, Route

    from . import tenants

    auth_token = os.environ.get("MEMPALACE_MCP_TOKEN")

    # stateless=True: each POST is handled in a task spawned from the request
    # handler, so the tenant contextvar set below propagates into tool calls.
    session_manager = StreamableHTTPSessionManager(app=app, json_response=False, stateless=True)
    sse_transport = SseServerTransport("/messages/")

    def _extract_token(request) -> str:
        header = request.headers.get("authorization", "")
        if header.startswith("Bearer "):
            return header[len("Bearer "):]
        return request.query_params.get("token", "")

    def _authenticate(request):
        """Return (authorized, tenant). Root token → global palace (tenant None).
        Any key found in the tenant registry → that tenant's isolated palace."""
        token = _extract_token(request)
        tenant = tenants.resolve(token)
        if tenant:
            return True, tenant
        if not auth_token:  # auth disabled
            return True, None
        return (token == auth_token), None

    async def handle_streamable_http(scope, receive, send):
        from starlette.requests import Request

        ok, tenant = _authenticate(Request(scope, receive))
        if not ok:
            await JSONResponse({"error": "unauthorized"}, status_code=401)(scope, receive, send)
            return
        tenants.current_tenant.set(tenant)
        await session_manager.handle_request(scope, receive, send)

    async def handle_sse(request):
        ok, tenant = _authenticate(request)
        if not ok:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        tenants.current_tenant.set(tenant)
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as (read, write):
            await app.run(read, write, app.create_initialization_options())
        return Response()

    async def health(request):
        return JSONResponse(
            {
                "status": "ok",
                "server": "mempalace",
                "version": __version__,
                "tools": len(TOOLS),
                "transports": {"streamable_http": "/mcp", "sse": "/sse"},
            }
        )

    @contextlib.asynccontextmanager
    async def lifespan(starlette_app):
        async with session_manager.run():
            logger.info("MemPalace MCP HTTP server ready — /mcp (streamable) + /sse (legacy)")
            yield

    starlette_app = Starlette(
        routes=[
            Route("/", health),
            Route("/health", health),
            Route("/sse", handle_sse),
            Mount("/messages/", app=sse_transport.handle_post_message),
        ],
        lifespan=lifespan,
    )

    # Starlette's Mount 307-redirects /mcp -> /mcp/, which MCP clients don't
    # follow. Dispatch /mcp (with or without trailing slash) directly instead.
    async def root_app(scope, receive, send):
        path = scope.get("path", "")
        if scope["type"] == "http" and (path == "/mcp" or path.startswith("/mcp/")):
            await handle_streamable_http(scope, receive, send)
        else:
            await starlette_app(scope, receive, send)

    # lifespan events must still reach the Starlette app
    async def app_with_lifespan(scope, receive, send):
        if scope["type"] == "lifespan":
            await starlette_app(scope, receive, send)
        else:
            await root_app(scope, receive, send)

    return app_with_lifespan


def run_http(host: str, port: int):
    import uvicorn

    uvicorn.run(build_http_app(), host=host, port=port, log_level="info")


def main():
    parser = argparse.ArgumentParser(description="MemPalace Universal MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse", "streamable-http"],
        default="stdio",
        help="stdio (default) or http (serves both streamable-http and legacy SSE)",
    )
    parser.add_argument("--host", default=os.environ.get("MEMPALACE_MCP_HOST", "127.0.0.1"))
    parser.add_argument(
        "--port", type=int, default=int(os.environ.get("MEMPALACE_MCP_PORT", os.environ.get("PORT", "8765")))
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        logger.info(f"MemPalace Universal MCP Server v{__version__} (stdio)")
        anyio.run(run_stdio)
    else:
        # http, sse, streamable-http all serve the combined app — every
        # endpoint is always available, so any client version can connect.
        logger.info(f"MemPalace Universal MCP Server v{__version__} (http on {args.host}:{args.port})")
        run_http(args.host, args.port)


if __name__ == "__main__":
    main()
