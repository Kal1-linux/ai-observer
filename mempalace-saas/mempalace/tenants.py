"""
Tenant registry for multi-tenant MemPalace.

Maps API keys (sk-mp-...) to tenants, each with an isolated palace
(ChromaDB) and knowledge graph (SQLite) under:

    <MEMPALACE_DATA_DIR>/tenants/<tenant_id>/{palace, kg.db}

Keys live in the existing waitlist DB (email, api_key). Lookups accept the
plaintext key column (legacy) and a sha256-hashed key column when present.

The active tenant is carried in a contextvar so tool handlers deep in
mempalace.mcp_server can resolve the right palace without threading a
parameter through every call. When no tenant is set, handlers fall back to
the global single-user config — full backward compatibility.
"""

import hashlib
import os
import re
import sqlite3
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path


def _default_data_dir() -> str:
    if os.path.isdir("/app/data") and os.access("/app/data", os.W_OK):
        return "/app/data"
    return os.path.expanduser("~/.mempalace")


DATA_DIR = os.environ.get("MEMPALACE_DATA_DIR", _default_data_dir())


def _default_tenants_db() -> str | None:
    env = os.environ.get("MEMPALACE_TENANTS_DB")
    if env:
        return env
    for candidate in (
        os.path.join(DATA_DIR, "waitlist.db"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "waitlist.db"),
    ):
        if os.path.exists(candidate):
            return candidate
    return None


@dataclass(frozen=True)
class Tenant:
    tenant_id: str
    email: str

    @property
    def root_dir(self) -> str:
        return os.path.join(DATA_DIR, "tenants", self.tenant_id)

    @property
    def palace_path(self) -> str:
        return os.path.join(self.root_dir, "palace")

    @property
    def kg_path(self) -> str:
        return os.path.join(self.root_dir, "kg.db")

    def ensure_dirs(self) -> None:
        Path(self.root_dir).mkdir(parents=True, exist_ok=True)


# The active tenant for the current request/session. None = global/legacy mode.
current_tenant: ContextVar[Tenant | None] = ContextVar("current_tenant", default=None)


def _tenant_id_for(email: str, api_key: str) -> str:
    """Stable, filesystem-safe tenant id derived from the email."""
    slug = re.sub(r"[^a-z0-9]+", "-", email.lower()).strip("-")[:24]
    digest = hashlib.sha256(email.lower().encode()).hexdigest()[:10]
    return f"{slug}-{digest}"


def resolve(token: str, db_path: str | None = None) -> Tenant | None:
    """Look up an API key and return its Tenant, or None if unknown."""
    if not token:
        return None
    db = db_path or _default_tenants_db()
    if not db or not os.path.exists(db):
        return None
    try:
        conn = sqlite3.connect(db, timeout=5)
        try:
            cur = conn.cursor()
            row = cur.execute(
                "SELECT email, api_key FROM waitlist WHERE api_key = ?", (token,)
            ).fetchone()
            if row is None:
                # hashed-key column, if the schema has been upgraded
                try:
                    hashed = hashlib.sha256(token.encode()).hexdigest()
                    row = cur.execute(
                        "SELECT email, api_key FROM waitlist WHERE api_key_hash = ?", (hashed,)
                    ).fetchone()
                except sqlite3.OperationalError:
                    row = None
            if row is None:
                return None
            email, api_key = row
            tenant = Tenant(tenant_id=_tenant_id_for(email, api_key or token), email=email)
            tenant.ensure_dirs()
            return tenant
        finally:
            conn.close()
    except Exception:
        return None
