"""
pipeline.orchestrator.writer_runtime_support
============================================

Service-free helpers that data writers (ga_* / bo_*) consume at runtime:
the writer-source digest (``get_writer_source_hash`` and the import-closure walk
it needs) and the once-per-process ``duration_seconds`` column probe.

Extracted verbatim from ``asset_runner`` (owner-approved narrow freeze
exception, N-266) so the digest closure of a ga_*/bo_* writer no longer reaches
``service_probes`` -> ``services/*`` through ``asset_runner``'s function-local
probe imports. ``asset_runner`` re-exports every name below, so existing callers
are unchanged.

HARD RULE: this module must import nothing from ``services/`` or
``service_probes`` (enforced by tests/test_writer_runtime_support_closure.py).
"""
from __future__ import annotations

import ast
import hashlib
import logging
from pathlib import Path

from .events import emit_event
from .writers import get_writer

# Deliberately the historical logger name: the duration-column-absent warning
# was emitted by asset_runner, and operator log filters / tests key on it.
logger = logging.getLogger("pipeline.orchestrator.asset_runner")

_WRITER_HASH_VERSION = b"nirmana-writer-source-v1\\0"
_REPO_ROOT = Path(__file__).resolve().parents[4]
_SIDECAR_ROOT = Path(__file__).resolve().parents[2]

def _writer_source_paths(asset_id: str) -> list[str]:
    """
    Locate the source file(s) whose git history represents a writer — wherever
    the writer lives (Orchestrator Convergence Phase 3: GA writers live in
    ga_writers/, not pipeline/orchestrator/writers/, so the old hard-coded path
    is wrong for them). Resolution order, generic + registry-driven:

      1. the registered class's `source_paths` (repo-relative) if declared
         (GA adapters set this to their ga_writers/ module);
      2. else the registered class's own module file (inspect.getfile);
      3. else fall back to the legacy convention.

    `_writer_source_files` extends these roots through local Python imports, so
    delegated implementation files are part of the provenance receipt too.
    """
    import inspect

    cls = get_writer(asset_id)
    if cls is not None:
        declared = getattr(cls, "source_paths", None)
        if declared:
            return list(declared)
        try:
            abs = inspect.getfile(cls)
            idx = abs.find("platform/python-sidecar/")
            return [abs[idx:] if idx >= 0 else abs]
        except Exception:
            pass
    return [f"platform/python-sidecar/pipeline/orchestrator/writers/{asset_id.replace('.', '/')}.py"]


def _local_module_path(module: str) -> Path | None:
    """Resolve an in-repo sidecar module without importing or executing it."""
    if not module:
        return None
    relative = Path(*module.split("."))
    module_file = _SIDECAR_ROOT / relative.with_suffix(".py")
    package_init = _SIDECAR_ROOT / relative / "__init__.py"
    if module_file.is_file():
        return module_file
    if package_init.is_file():
        return package_init
    return None


def _module_name_for_path(path: Path) -> str | None:
    try:
        relative = path.resolve().relative_to(_SIDECAR_ROOT)
    except ValueError:
        return None
    if relative.suffix != ".py":
        return None
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts) or None


def _local_import_files(path: Path) -> list[Path]:
    """Statically resolve direct local Python imports from one implementation file."""
    module_name = _module_name_for_path(path)
    if module_name is None:
        return []
    package = module_name if path.name == "__init__.py" else module_name.rpartition(".")[0]
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                package_parts = package.split(".") if package else []
                base_parts = package_parts[:len(package_parts) - node.level + 1]
                if not base_parts:
                    continue
                base = ".".join(base_parts)
                target = f"{base}.{node.module}" if node.module else base
            else:
                target = node.module or ""
            if target:
                imports.add(target)
                imports.update(f"{target}.{alias.name}" for alias in node.names)

    return [resolved for module in sorted(imports) if (resolved := _local_module_path(module)) is not None]


def _writer_source_files(paths: list[str]) -> list[tuple[str, bytes]]:
    """Load declared source plus its local implementation closure deterministically."""
    files: list[Path] = []
    for raw_path in paths:
        source_path = Path(raw_path)
        resolved = source_path if source_path.is_absolute() else _REPO_ROOT / source_path
        if resolved.is_file():
            files.append(resolved)
        elif resolved.is_dir():
            files.extend(path for path in resolved.rglob("*.py") if path.is_file() and "tests" not in path.parts)
        else:
            raise RuntimeError(f"writer source path is unavailable: {raw_path}")

    seen: set[Path] = set()
    pending = sorted(files, key=lambda item: item.as_posix())
    resolved_files: list[Path] = []
    while pending:
        path = pending.pop(0)
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        resolved_files.append(resolved)
        pending.extend(_local_import_files(resolved))

    out: list[tuple[str, bytes]] = []
    for resolved in sorted(resolved_files, key=lambda item: item.as_posix()):
        try:
            rel = resolved.relative_to(_REPO_ROOT).as_posix()
        except ValueError:
            rel = resolved.as_posix()
        out.append((rel, resolved.read_bytes()))
    if not out:
        raise RuntimeError("writer has no declared source files")
    return out


def get_writer_source_hash(asset_id: str) -> str:
    """Return a content hash of the concrete writer source used by an execution."""
    digest = hashlib.sha256(_WRITER_HASH_VERSION)
    for path, content in _writer_source_files(_writer_source_paths(asset_id)):
        encoded_path = path.encode("utf-8")
        digest.update(len(encoded_path).to_bytes(8, "big"))
        digest.update(encoded_path)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


# Cached once per process (C2, gate review A1_review_20260926T124832Z.md F-2):
# migration 1200 adds asset_throughput.duration_seconds, but a deploy of this
# code can legitimately reach production before that migration is actually
# applied — or the bulk migration runner can silently no-op while reporting
# success (CLAUDE.md §N.4's named hazard). Before this cache, the completion
# UPDATE named `duration_seconds = %s` unconditionally: on an out-of-order or
# silently-no-op deploy, EVERY data-writer completion write would raise
# `column "duration_seconds" does not exist` and no asset could ever complete
# a build again. None = not yet probed; True/False once probed, for the life
# of this process (never re-probed per write — a schema change mid-process is
# not a supported deploy shape here).
_DURATION_COLUMNS_PRESENT: bool | None = None


def _duration_columns_present(cur) -> bool:
    """
    Detect, once per process, whether asset_throughput.duration_seconds exists.

    Graceful degradation for migration 1200 (see module-level comment above):
    when the column is absent, the completion write must still succeed —
    it simply omits duration_seconds/rows_per_second from the UPDATE entirely,
    so the build completes and those two columns stay whatever they already
    were (NULL, on a fresh install). This must never be probed per write; the
    result is cached for the remainder of the process.

    R-2 (gate review A1_rereview_20260926T132725Z.md N-2): the absence branch is
    logged, once per process (same cardinality as the probe itself). Without
    this, an operator reading a NULL duration_seconds cannot tell "this
    particular build wasn't timed" (an ordinary skip path) from "migration 1200
    has never applied in this environment, so NOTHING will ever be timed here"
    — a silent, permanent, fleet-wide measurement outage wearing an ordinary
    NULL's clothes (CLAUDE.md §N.4's `[[feedback-deploy-migrations-silent-noop]]`
    hazard, one layer up: the migration silently does nothing, and — before this
    fix — the code silently did nothing about it either).
    """
    global _DURATION_COLUMNS_PRESENT
    if _DURATION_COLUMNS_PRESENT is None:
        # R-7 (gate review N-6): schema-qualified so a same-named table in
        # another schema of a multi-schema deployment can never produce a false
        # positive here. A false positive would make the completion UPDATE name
        # a column that doesn't actually exist in THIS asset_throughput, raise,
        # and reintroduce exactly the build-fatal hazard this cache exists to
        # prevent. 'public' matches this codebase's own established idiom for
        # probing column existence (see l0_class_lifetime_counts.py,
        # mimamsa/outcome.py, services/w2g_validations/_db.py — all filter
        # table_schema = 'public' rather than to_regclass, which this codebase
        # reserves for whole-table existence checks, a different question).
        cur.execute(
            """SELECT 1 FROM information_schema.columns
               WHERE table_schema = 'public' AND table_name = 'asset_throughput'
                 AND column_name = 'duration_seconds'"""
        )
        _DURATION_COLUMNS_PRESENT = cur.fetchone() is not None
        if not _DURATION_COLUMNS_PRESENT:
            logger.warning(
                "[orchestrator] asset_throughput.duration_seconds is ABSENT in "
                "this environment (migration 1200_asset_throughput_duration_"
                "seconds.sql has not applied here). Every completion write this "
                "process makes will omit duration_seconds/rows_per_second "
                "entirely -- a fleet-wide measurement outage for the lifetime "
                "of this process, not an ordinary per-row NULL. Apply migration "
                "1200 to restore duration tracking."
            )
            emit_event({
                "type": "asset.duration_columns_absent",
                "message": (
                    "asset_throughput.duration_seconds is absent; migration "
                    "1200_asset_throughput_duration_seconds.sql has not applied "
                    "in this environment -- duration/rate tracking is disabled "
                    "for the lifetime of this process"
                ),
            })
    return _DURATION_COLUMNS_PRESENT
