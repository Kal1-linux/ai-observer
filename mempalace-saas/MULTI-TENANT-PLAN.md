# MemPalace SaaS — Multi-Tenant Roadmap

Goal: go from "one palace, one shared token" to "every user gets their own
private memory palace, reachable from any MCP client, at one permanent URL."

## Where we are today

- `mcp_universal.py` — universal MCP server (stdio / streamable HTTP / SSE),
  single palace, single shared `MEMPALACE_MCP_TOKEN`.
- `server.py` — FastAPI SaaS with a signup flow that already issues per-user
  API keys (`sk-mp-<uuid>`) into `waitlist.db` (email + api_key).
- One global ChromaDB palace path and one `KnowledgeGraph`, shared by all callers.

The missing piece: connect the per-user keys to per-user palaces inside the
MCP server itself.

## Target architecture

```
Client (Claude/ChatGPT/Cursor/agent)
        │  Authorization: Bearer sk-mp-abc…   (or ?token=)
        ▼
  MCP Universal Server (HTTP)
        │  key → tenant lookup (tenants.db)
        ▼
  TenantContext (contextvar, set per connection)
        │
        ▼
  data/tenants/<tenant_id>/
      ├── palace/          ← ChromaDB, isolated per tenant
      └── kg.db            ← knowledge graph, isolated per tenant
```

Every tool call executes against the palace of the tenant whose key opened the
connection. No shared state, no cross-tenant reads possible by construction.

## Phases

### Phase 1 — Tenant isolation in the MCP server (the core)
1. `mempalace/tenants.py`: registry module
   - `resolve(token) -> Tenant | None` (lookup in `waitlist.db`/`tenants.db`)
   - `Tenant.palace_path`, `Tenant.kg_path` under `data/tenants/<id>/`
   - key hashing at rest (store sha256, not plaintext keys)
2. Refactor tool handlers to take an explicit `ctx` (config/paths) instead of
   the module-global `_config`/`_kg`. This is the main surgery — ~19 handlers,
   mechanical change.
3. In `mcp_universal.py` HTTP mode: extract token per connection, resolve
   tenant, run the MCP session with that tenant's context (contextvar set
   before the session task starts — must verify propagation through
   StreamableHTTPSessionManager's task group; fallback: session-id → tenant map).
4. stdio mode keeps current behavior (local single user, env-configured path).
5. Backward compat: `MEMPALACE_MCP_TOKEN` still works as a "root" single-tenant
   token when no tenant DB exists.

Deliverable: two different API keys see two completely separate palaces.
Test: create 2 tenants, write with A, confirm B cannot read it.

### Phase 2 — Account lifecycle
- Signup endpoint (exists) + key rotation + key revocation endpoints
- Per-tenant quotas: max drawers, max requests/min (simple token bucket)
- Usage tracking table (tenant_id, tool, timestamp) → billing groundwork
- Admin CLI: `mempalace tenants list|create|revoke`

### Phase 3 — Platform auth (OAuth)
- ChatGPT standard connectors and claude.ai remote MCP prefer OAuth 2.1
  (dynamic client registration + PKCE). The MCP SDK ships helpers for this.
- OAuth issues tokens that map to the same tenant registry — bearer keys and
  OAuth coexist.
- Also add ChatGPT deep-research `search`/`fetch` alias tools (thin wrappers
  over `mempalace_search`).

### Phase 4 — Production deployment
- Railway (already provisioned): mount persistent volume at `/app/data`,
  tenants live under `/app/data/tenants/`
- Start command: `python -m mempalace.mcp_universal --transport http --host 0.0.0.0`
- Permanent URL replaces ngrok; ChatGPT/Claude connectors never break
- Backups: nightly tar of `/app/data` to object storage
- Observability: structured logs with tenant_id, `/health` extended with
  per-tenant counts

### Phase 5 — Product polish (after everything above works)
- Web dashboard: browse your palace, see agent diaries, revoke keys
- Team palaces: N users → 1 shared palace (membership table)
- Embedding upgrades / reranking for search quality
- Billing (Stripe) keyed off the Phase 2 usage table

## What this unlocks

- **Sell it**: one URL, per-user keys, private memory — the SaaS is real.
- **Multi-agent fleets**: each customer's agents share *their* palace only.
- **Cross-AI continuity as the product**: sign up → paste one URL into
  ChatGPT and Claude → both share the user's memory.

## Risks / open questions

- Contextvar propagation through the SDK's session task group (Phase 1.3) —
  needs a spike; the session-id→tenant map is the safe fallback.
- ChromaDB with many tenants = many PersistentClient instances → memory
  pressure; use an LRU cache of open clients (close least-recently-used).
- SQLite is fine to ~thousands of tenants; Postgres migration is a Phase 4+
  concern, not now.
- Key-in-URL (`?token=`) is needed for ChatGPT but leaks into logs — hash keys
  at rest, redact tokens in access logs.

## Suggested order of attack

1. Phase 1 (tenant isolation) — the only hard engineering, everything else
   depends on it.
2. Phase 4 Railway deploy immediately after — permanent URL makes testing with
   real clients painless.
3. Phase 2, then 3, then 5.
