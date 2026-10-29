"""Tenant isolation.

A customer can run several factories on one RootCause install. Each tenant gets its own SQLite file
so a query can never cross the boundary; there is no shared table with a tenant column to forget in
a WHERE clause. The default tenant keeps the original database path for compatibility.
"""

from __future__ import annotations

import re
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from .store.db import Store

DEFAULT_TENANT = "werk-sued"
tenant_var: ContextVar[str] = ContextVar("rootcause_tenant", default=DEFAULT_TENANT)
_TENANT_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def normalise_tenant(value: str | None) -> str:
    if not value:
        return DEFAULT_TENANT
    candidate = value.strip().lower()
    return candidate if _TENANT_RE.match(candidate) else DEFAULT_TENANT


def current_tenant() -> str:
    return tenant_var.get()


def set_tenant(value: str | None):
    return tenant_var.set(normalise_tenant(value))


class StoreRouter:
    """Resolve the current tenant's store on every call."""

    def __init__(self, base_path: Path, pack: dict[str, Any]) -> None:
        self.base_path = base_path
        self.pack = pack
        self._stores: dict[str, Store] = {}

    def _path_for(self, tenant: str) -> Path:
        if tenant == DEFAULT_TENANT:
            return self.base_path
        return self.base_path.parent / "tenants" / f"{tenant}.sqlite3"

    def for_tenant(self, tenant: str) -> Store:
        key = normalise_tenant(tenant)
        if key not in self._stores:
            store = Store(self._path_for(key))
            store.seed(self.pack)
            self._stores[key] = store
        return self._stores[key]

    def current(self) -> Store:
        return self.for_tenant(current_tenant())

    def close(self) -> None:
        for store in self._stores.values():
            store.close()
        self._stores.clear()

    def __getattr__(self, name: str):
        return getattr(self.current(), name)
