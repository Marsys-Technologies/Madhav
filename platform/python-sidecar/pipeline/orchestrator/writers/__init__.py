"""
L0 Brahma Jñāna writer registry — Phase β infrastructure.

Each writer module under this package registers itself via @register('bg_<id>').
The orchestrator imports this package and discovers all registered writers.

Per holistic design v1.1: ZERO LLM use in writers. Embeddings (Vertex AI) are
permitted as deterministic transforms for bg_texts in Phase δ; not used elsewhere.
"""
from __future__ import annotations
import importlib
import logging
import pkgutil
from dataclasses import dataclass, field
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ContextSpec:
    """Runtime context passed to every writer's run() method."""
    asset_id: str                              # e.g. 'bg_reference'
    build_id: str                              # unique per-build UUID for provenance
    db_conn: Any                               # psycopg connection (caller-owned; writer doesn't close or commit)
    config: dict[str, Any] = field(default_factory=dict)  # writer-specific config (e.g. chart_id for per_chart writers)
    dry_run: bool = False                      # if True, writer reports what it WOULD do but doesn't INSERT/UPDATE


@dataclass
class WriterResult:
    """What a writer returns after run()."""
    asset_id: str
    rows_inserted: int
    rows_updated: int = 0
    rows_skipped: int = 0
    duration_seconds: float = 0.0
    notes: str = ''


class WriterBase:
    """
    Base class for all L0 Brahma Jñāna writers.

    Subclasses MUST:
    - set class attribute `asset_id` (matches asset_registry.asset_id)
    - implement run(ctx: ContextSpec) -> WriterResult

    Subclasses MUST NOT:
    - call ctx.db_conn.commit() or ctx.db_conn.rollback() — caller owns the transaction
    - close ctx.db_conn — caller owns the connection

    Subclasses SHOULD:
    - be deterministic (same input + same source = same output rows + same content hashes)
    - use INSERT ... ON CONFLICT DO NOTHING (or DO UPDATE) for idempotency
    - log progress at INFO level every ~100-1000 rows
    """
    asset_id: str = ''  # subclass overrides

    def run(self, ctx: ContextSpec) -> WriterResult:
        raise NotImplementedError(f'{self.__class__.__name__} must implement run()')


# Registry: asset_id → writer class
_REGISTRY: dict[str, type[WriterBase]] = {}

# Backward-compat alias (used in existing tests)
WRITER_REGISTRY = _REGISTRY


def register(asset_id: str) -> Callable[[type[WriterBase]], type[WriterBase]]:
    """
    Decorator: register a writer class for an asset_id.

    Usage:
        @register('bg_reference')
        class ReferenceWriter(WriterBase):
            asset_id = 'bg_reference'
            def run(self, ctx): ...
    """
    def _decorate(cls: type[WriterBase]) -> type[WriterBase]:
        if asset_id in _REGISTRY:
            raise ValueError(
                f'duplicate writer registration for asset_id={asset_id}: '
                f'existing={_REGISTRY[asset_id].__name__}, new={cls.__name__}'
            )
        if not issubclass(cls, WriterBase):
            raise TypeError(f'{cls.__name__} must subclass WriterBase')
        _REGISTRY[asset_id] = cls
        logger.info(f'registered writer: {asset_id} → {cls.__name__}')
        return cls
    return _decorate


def get_writer(asset_id: str) -> Optional[type[WriterBase]]:
    """Return the registered writer class for an asset_id, or None."""
    _auto_discover()
    return _REGISTRY.get(asset_id)


def list_writers() -> dict[str, type[WriterBase]]:
    """Return a shallow copy of the registry (caller can iterate safely)."""
    return dict(_REGISTRY)


_discovered = False


def _auto_discover() -> None:
    """
    Auto-discover and import all writer modules in this package.
    Called lazily on first get_writer(); idempotent after first call.
    Hard-fails on import errors — registration gap is not silently OK.
    """
    global _discovered
    if _discovered:
        return
    _discovered = True
    import sys
    pkg_name = __name__
    pkg = sys.modules[pkg_name]
    for finder, mod_name, ispkg in pkgutil.iter_modules(pkg.__path__):
        if mod_name.startswith('_') or mod_name == 'tests':
            continue
        full_name = f'{pkg_name}.{mod_name}'
        try:
            importlib.import_module(full_name)
            logger.debug(f'discovered writer module: {full_name}')
        except Exception as e:
            logger.error(f'failed to import writer {full_name}: {e}')
            raise  # hard-fail — registration gap is not silently OK


# Public alias for explicit callers (e.g. bootstrap scripts)
def discover_all() -> None:
    """Explicit trigger for auto-discovery. Idempotent."""
    _auto_discover()


__all__ = [
    'ContextSpec', 'WriterResult', 'WriterBase',
    'register', 'get_writer', 'list_writers', 'discover_all',
    'WRITER_REGISTRY',  # backward-compat alias
]
