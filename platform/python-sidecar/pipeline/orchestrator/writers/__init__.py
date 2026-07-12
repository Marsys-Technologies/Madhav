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
import threading
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


@dataclass
class SubStep:
    """
    One savepoint-isolated, heartbeated unit of a heavy writer's work.

    The grain is the writer's own natural chunk — e.g. for ga_dashas, one
    (system × ayanamsha) pair (35 in total). The orchestrator drives each
    SubStep returned by plan_substeps() as its own SAVEPOINT + last_built_at
    heartbeat, so a 40-minute asset stays under both watchdog reapers and a
    crash mid-asset resumes from the failed chunk (writer idempotency makes a
    re-run of a completed chunk a safe replace).

    `key` is unique within the asset and is the idempotency scope the writer's
    replace_prior_* must target. `label` is human-readable for SSE.
    """
    key: str
    label: str = ''

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.key


class WriterBase:
    """
    Base class for ALL orchestrator-driven writers (L0 Brahma Jñāna + L1 Gaṇita
    + every future layer L2–L5).

    ── FROZEN CONTRACT (Orchestrator Convergence Phase 2, 2026-06-12) ──────────
    This is the FINAL shape of the writer contract. Future layers onboard by
    CONFORMING to it (subclass + @register + registry metadata), never by
    extending it. If a new layer appears to need a contract change, STOP and
    raise it with the native — it means this freeze was wrong (a deliberate
    architectural decision, not a routine edit). See
    `ORCHESTRATOR_GENERALIZATION_INVESTIGATION_v1_0.md §2.B`.

    The contract is exactly two shapes:

      • LIGHT writer (L0 + light L1, the common case): implement `run(ctx)`.
        It does the whole asset in one unit. It never sees sub-steps — the
        orchestrator gives it a single default sub-step.

      • HEAVY writer (e.g. ga_dashas: ~40 min, 35 chunks): override BOTH
        `plan_substeps(ctx)` and `run_substep(ctx, step)`. The orchestrator
        drives each sub-step as its own savepoint + heartbeat. Such a writer
        gets a working `run(ctx)` for free (drives its own sub-steps, no
        heartbeat) for CLI / direct use.

    Subclasses MUST:
    - set class attribute `asset_id` (matches asset_registry.asset_id)
    - implement `run(ctx)`  OR  (`plan_substeps(ctx)` + `run_substep(ctx, step)`)

    Subclasses MUST NOT:
    - call ctx.db_conn.commit() / rollback() — the orchestrator owns the
      transaction + savepoint lifecycle (commits once per sub-step)
    - close ctx.db_conn — caller owns the connection
    - open their own connection — use ctx.db_conn exclusively
    - write asset_throughput — the orchestrator is the sole build-state writer

    Subclasses SHOULD:
    - be deterministic (same input + same source = same output rows + hashes)
    - call their own natural-key-scoped replace_prior_* (replace-not-accrete)
      on ctx.db_conn immediately before INSERT, scoped to the sub-step's key,
      so any chunk is safe to re-run
    - honor ctx.dry_run
    - log progress at INFO level every ~100-1000 rows
    """
    asset_id: str = ''  # subclass overrides

    # Hint mirroring asset_registry.has_substeps. The orchestrator drives
    # sub-steps for EVERY writer regardless (a light writer simply has one
    # default sub-step); this flag is advisory for cockpit/planner pre-invoke.
    has_substeps: bool = False

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        """
        FROZEN CONTRACT. Return the sub-steps the orchestrator will drive.

        Default: ONE sub-step covering the whole asset (the light-writer path).
        Heavy writers override to expose their natural chunk grain (e.g.
        ga_dashas → 35 SubStep(key=f'{system}:{ayanamsha}')).
        """
        return [SubStep(key=self.asset_id, label=self.asset_id)]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        """
        FROZEN CONTRACT. Execute one sub-step on ctx.db_conn (no commit/close).

        Default: delegate to run() — a light writer never sees sub-steps and is
        invoked once with its single default sub-step. Heavy writers override
        this AND plan_substeps, scoping their replace_prior_* to step.key.
        """
        return self.run(ctx)

    def run(self, ctx: ContextSpec) -> WriterResult:
        """
        FROZEN CONTRACT. The light-writer entry point (whole asset in one unit).

        A heavy writer that overrides run_substep but not run() gets a working
        run() for free: it drives its own sub-steps and aggregates (no
        heartbeat — that is orchestrator-only). A writer that implements neither
        run() nor run_substep() raises NotImplementedError.
        """
        if type(self).run_substep is not WriterBase.run_substep:
            agg = WriterResult(asset_id=self.asset_id, rows_inserted=0)
            for step in self.plan_substeps(ctx):
                r = self.run_substep(ctx, step)
                agg.rows_inserted += r.rows_inserted
                agg.rows_updated += r.rows_updated
                agg.rows_skipped += r.rows_skipped
                agg.duration_seconds += r.duration_seconds
            return agg
        raise NotImplementedError(
            f'{self.__class__.__name__} must implement run() '
            f'or (plan_substeps + run_substep)'
        )


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
            # Idempotent for the IDENTICAL class re-registering (benign — a test-collection
            # or dual-module-path re-import). Still a hard error on a GENUINE conflict:
            # a DIFFERENT class claiming the same asset_id. (W2 CI-collection robustness;
            # the one-writer-per-asset_id contract is preserved.)
            existing = _REGISTRY[asset_id]
            if existing is cls or (
                existing.__name__ == cls.__name__
                and existing.__module__.rsplit('.', 1)[-1] == cls.__module__.rsplit('.', 1)[-1]
            ):
                return cls
            raise ValueError(
                f'duplicate writer registration for asset_id={asset_id}: '
                f'existing={existing.__name__}, new={cls.__name__}'
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


# L-2: threading.Lock guards the _discovered check-and-set so concurrent worker
# threads cannot trigger duplicate-registration races during auto-discovery.
_discover_lock = threading.Lock()
_discovered = False


def _auto_discover() -> None:
    """
    Auto-discover and import all writer modules in this package.
    Called lazily on first get_writer(); idempotent after first call.
    Hard-fails on import errors — registration gap is not silently OK.

    Thread-safe: the _discover_lock prevents duplicate registration when multiple
    worker threads call get_writer() simultaneously before the main thread has
    finished calling discover_all() (L-2).
    """
    global _discovered
    with _discover_lock:
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
    'ContextSpec', 'WriterResult', 'WriterBase', 'SubStep',
    'register', 'get_writer', 'list_writers', 'discover_all',
    'WRITER_REGISTRY',  # backward-compat alias
]
