"""Writer registry — maps asset_id → writer callable."""
from __future__ import annotations

from typing import Callable, Optional

import psycopg

# WriterFn signature: (chart_id: str, conn: psycopg.Connection) -> int (rows written)
WriterFn = Callable[[str, psycopg.Connection], int]

WRITER_REGISTRY: dict[str, WriterFn] = {}


def register(asset_id: str):
    """Decorator: @register('ganita.positions') def write_fn(chart_id, conn): ..."""
    def decorator(fn: WriterFn) -> WriterFn:
        WRITER_REGISTRY[asset_id] = fn
        return fn
    return decorator


def get_writer(asset_id: str) -> Optional[WriterFn]:
    _auto_discover()
    return WRITER_REGISTRY.get(asset_id)


_discovered = False


def _auto_discover() -> None:
    """Import all writer modules so their @register decorators fire."""
    global _discovered
    if _discovered:
        return
    _discovered = True
    import importlib
    import pkgutil
    import pipeline.orchestrator.writers as _pkg
    for _info in pkgutil.iter_modules(_pkg.__path__):
        if not _info.name.startswith("_"):
            try:
                importlib.import_module(f"pipeline.orchestrator.writers.{_info.name}")
            except Exception:
                pass
