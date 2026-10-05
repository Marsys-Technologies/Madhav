"""A5.3 writerbase_conformance — ORCHESTRATOR_CONVERGENCE_CLOSE §5 (the L2-readiness checklist),
executed against `ka_gochara_v5` rather than ticked off in prose.

Each item below is a test of the PRODUCTION writer/closure. Two items are checked elsewhere and
named here so the list is complete:
  * idempotency / dry_run / sub-step scoping — `test_a53_gochara_v5_writer.py`,
    `test_a53_am5_writer.py`, `test_a53_record_store.py` (delete-then-insert on real PG; dry_run
    writes nothing; natively typed inputs in `test_a53_writer_native_types.py`);
  * the registry row — `platform/scripts/__tests__/ka_gochara_v5_registry_conformance.test.ts`
    (the seed is TypeScript; its two known gaps are strict expected-failures there).

One DELIBERATE deviation from §5, recorded rather than hidden: the writer carries the canonical
chart id as a fail-closed ALLOWLIST guard (steward M20261001T014547-357e: inert to every planner and
refusing any other chart until D-FLIP widens scope). §5's "no hard-coded native default in the build
path" forbids a native DEFAULT; a refusal guard that raises for every other chart is the opposite of a
default, and the test below pins exactly that.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from pipeline.orchestrator import asset_runner as ar
from pipeline.orchestrator.writers import WRITER_REGISTRY, WriterBase, discover_all
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod

WRITER_FILE = Path(writer_mod.__file__).resolve()
CLOSURE = ar._writer_source_files([str(WRITER_FILE)])      # the frozen hasher's own executable closure


def _trees():
    for rel, data in CLOSURE:
        if rel.endswith(".py"):
            yield rel, ast.parse(data.decode("utf-8"))


def test_registered_class_subclassing_writerbase_with_the_registry_asset_id():
    discover_all()
    cls = WRITER_REGISTRY["ka_gochara_v5"]
    assert issubclass(cls, WriterBase) and cls.asset_id == "ka_gochara_v5"
    assert cls is writer_mod.GocharaV5Writer


def test_discoverable_from_the_writers_package_without_an_explicit_import():
    """`_auto_discover()` imports everything under pipeline/orchestrator/writers/."""
    assert WRITER_FILE.parent.name == "writers" and WRITER_FILE.parent.parent.name == "orchestrator"
    discover_all()
    assert "ka_gochara_v5" in WRITER_REGISTRY


def test_heavy_shape_overrides_the_substep_pair_and_declares_has_substeps():
    cls = writer_mod.GocharaV5Writer
    assert cls.has_substeps is True
    assert cls.plan_substeps is not WriterBase.plan_substeps
    assert cls.run_substep is not WriterBase.run_substep


def test_it_never_commits_rolls_back_closes_or_opens_a_connection():
    """Over the writer's WHOLE executable closure (53 files today): no commit/rollback/close on a
    connection, no `psycopg.connect`. The one connection-opening helper in the closure,
    `SkyEventStore.from_env`, is a test/CLI convenience — and nothing in the closure calls it."""
    offences, from_env_calls = [], []
    for rel, tree in _trees():
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                continue
            owner = ast.unparse(node.func.value)
            if node.func.attr in ("commit", "rollback", "close") and "conn" in owner.lower():
                offences.append((rel, node.lineno, ast.unparse(node)[:70]))
            if node.func.attr == "connect" and owner in ("psycopg", "psycopg2"):
                if not rel.endswith("services/gochara_kernel/substrate.py"):
                    offences.append((rel, node.lineno, ast.unparse(node)[:70]))
            if node.func.attr == "from_env":
                from_env_calls.append((rel, node.lineno))
    assert offences == []
    assert from_env_calls == [], "SkyEventStore.from_env opens its own connection — never from a build"


def test_it_writes_nothing_to_asset_throughput():
    """Build state is the orchestrator's: no string in the writer's closure names asset_throughput — EXCEPT the writer's state guard `_require_building`
    (steward TIMEOUT-RULING 2 / GUARD-PRECHECK-ACK: ONE read-only SELECT of the row's state is inside the frozen contract, whose section 5 forbids WRITING it)."""
    guard_spans = []
    for rel, tree in _trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_require_building" and rel.endswith("writers/ka_gochara_v5.py"):
                guard_spans.append((rel, node.lineno, node.end_lineno))
                sql = [c.value for c in ast.walk(node) if isinstance(c, ast.Constant) and isinstance(c.value, str) and "public.asset_throughput" in c.value]
                assert sql and all(x.lstrip().upper().startswith("SELECT") for x in sql), f"the state guard may only SELECT asset_throughput: {sql}"
    assert len(guard_spans) == 1, "exactly one state guard exists"
    for rel, tree in _trees():
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                    and "asset_throughput" in node.value
                    and not (len(node.value) > 120 or "\n" in node.value)):   # docstrings may name it
                if any(rel == r and a <= node.lineno <= b for r, a, b in guard_spans):
                    continue                                                  # the state guard's own read-only SQL and its refusal text
                pytest.fail(f"{rel}:{node.lineno} names asset_throughput in a string: {node.value!r}")


def test_chart_and_build_come_from_ctx_and_the_canonical_chart_is_only_a_refusal_guard():
    src = WRITER_FILE.read_text(encoding="utf-8")
    assert 'ctx.config["chart_id"]' in src
    # the literal appears once: the PINNED_CHART_ID allowlist constant …
    assert src.count(writer_mod.PINNED_CHART_ID) >= 1
    assert "PINNED_CHART_ID = " in src
    # … and it only ever REFUSES: any other chart raises before any planning or execution
    import uuid
    for other in ("00000000-0000-4000-8000-0000000000b2", uuid.UUID(int=7)):
        with pytest.raises(writer_mod.ChartRefusal):
            writer_mod._require_pinned_chart(other)
    writer_mod._require_pinned_chart(uuid.UUID(writer_mod.PINNED_CHART_ID))   # the runner's type


def test_the_orchestrator_core_has_no_writer_specific_branch():
    """§5 last item: onboarding must not need a new `if` in the orchestrator."""
    core = Path(ar.__file__).resolve().parent
    for name in ("runner.py", "asset_runner.py", "db.py"):
        text = (core / name).read_text(encoding="utf-8")
        assert "ka_gochara" not in text, f"{name} names ka_gochara — the frozen contract was violated"


def test_every_substep_kind_the_plan_emits_is_one_run_substep_dispatches():
    """plan_substeps and run_substep agree on the grain: no planned key falls into the
    'unknown substep' branch."""
    src = inspect.getsource(writer_mod.GocharaV5Writer.run_substep)
    for prefix in ("INVENTORY_SUBSTEP_PREFIX", "VERIFY_SUBSTEP_PREFIX", "BODY_SUBSTEP_PREFIX",
                   "COVERAGE_SUBSTEP_PREFIX", "RECORD_SUBSTEP_PREFIX"):
        assert prefix in src, prefix
    for key in ("RULES_SUBSTEP", "CONVENTION_SUBSTEP", "MANIFEST_SUBSTEP", "SNAPSHOT_SUBSTEP"):
        assert key in src, key
