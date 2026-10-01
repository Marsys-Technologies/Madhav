"""Pravāha A5.3 — ka_gochara_v5 INERT writer skeleton (writerbase_conformance,
partial; steward ruling M20261001T014547-357e pins 1-2).

What this file proves:

  (a) registration + frozen-contract shape: the writer is discoverable via
      get_writer('ka_gochara_v5'), subclasses WriterBase, pins asset_id, and
      registers without conflicting with any existing writer;
  (b) hard chart refusal: any chart_id ≠ the pinned A5.3 candidate chart
      raises ChartRefusal on BOTH the planning path (plan_substeps) and the
      execution path (run, and the inherited run_substep which delegates to
      run) — before any other behaviour;
  (c) pending gate: for the pinned chart, every execution path raises
      NotImplementedError("A5.3: geometry/solver pending steward pins 3-7") —
      no astrology is implemented and none may land before steward pins 3-7;
  (d) inertness: the seed row ships is_active=false with depends_on=[] (the
      executable planner-predicate version is
      platform/scripts/__tests__/a53_gochara_v5_inert.test.ts; this static
      guard keeps the pytest suite honest without a TS runner), and the
      writer module source carries no connection-lifecycle call and never
      writes asset_throughput;
  (e) dry_run: the skeleton has no write path, so dry_run=True changes
      nothing — the pending gate still raises (mirrors the PR #2799
      template, which carries no dry_run branch).

No live DB: the only ctx.db_conn used is a recording fake that must observe
ZERO calls of any kind.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pipeline.orchestrator.writers.ka_gochara_v5 as writer_mod  # noqa: E402
from pipeline.orchestrator.writers import (  # noqa: E402
    ContextSpec,
    SubStep,
    WriterBase,
    get_writer,
)

SIDECAR = Path(__file__).resolve().parents[3]
PLATFORM = SIDECAR.parent
SEED = PLATFORM / "scripts" / "seed" / "asset_registry_seed.ts"

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER_CHART_ID = "11111111-2222-4333-8444-555555555555"


class _ExplodingConn:
    """Any touch at all is a test failure — the skeleton never goes near the
    DB, not even to open a cursor."""

    def __getattr__(self, name):
        raise AssertionError(
            f"ka_gochara_v5 skeleton touched ctx.db_conn.{name} — the inert "
            "skeleton must never read/write/commit/rollback/close the "
            "caller-owned connection")


def _ctx(chart_id: str = CHART_ID, dry_run: bool = False) -> ContextSpec:
    return ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="test-build",
                       db_conn=_ExplodingConn(),
                       config={"chart_id": chart_id}, dry_run=dry_run)


# ── (a) registration + frozen-contract shape ─────────────────────────────────


def test_writer_is_registered_and_discoverable():
    cls = get_writer(writer_mod.ASSET_ID)
    assert cls is writer_mod.GocharaV5Writer
    assert issubclass(cls, WriterBase)
    assert cls.asset_id == writer_mod.ASSET_ID == "ka_gochara_v5"


def test_writer_shape_conforms_to_frozen_contract():
    """WriterBase subclass with the light-writer shape: run(ctx) implemented,
    run_substep inherited (delegates to run), plan_substeps overridden only
    for the chart-scope refusal. register() itself hard-fails on a
    non-WriterBase subclass, so reaching here already proves the subclass
    predicate."""
    w = writer_mod.GocharaV5Writer()
    assert type(w).run is not WriterBase.run
    assert type(w).run_substep is WriterBase.run_substep
    assert type(w).plan_substeps is not WriterBase.plan_substeps
    assert w.has_substeps is False


def test_pinned_chart_id_is_the_a25_candidate_chart():
    assert writer_mod.PINNED_CHART_ID == CHART_ID


# ── (b) hard chart refusal — any chart ≠ the pinned A5.3 candidate chart ─────


def test_plan_substeps_refuses_any_other_chart():
    w = writer_mod.GocharaV5Writer()
    with pytest.raises(writer_mod.ChartRefusal):
        w.plan_substeps(_ctx(OTHER_CHART_ID))


def test_run_refuses_any_other_chart():
    w = writer_mod.GocharaV5Writer()
    with pytest.raises(writer_mod.ChartRefusal):
        w.run(_ctx(OTHER_CHART_ID))


def test_run_substep_refuses_any_other_chart_before_delegation():
    w = writer_mod.GocharaV5Writer()
    with pytest.raises(writer_mod.ChartRefusal):
        w.run_substep(_ctx(OTHER_CHART_ID), SubStep(key=writer_mod.ASSET_ID))


def test_chart_refusal_precedes_the_pending_gate():
    """A foreign chart must get ChartRefusal, never the NotImplementedError —
    the refusal is the outermost gate."""
    w = writer_mod.GocharaV5Writer()
    for call in (lambda: w.plan_substeps(_ctx(OTHER_CHART_ID)),
                 lambda: w.run(_ctx(OTHER_CHART_ID))):
        with pytest.raises(writer_mod.ChartRefusal) as exc:
            call()
        assert writer_mod.PENDING_MESSAGE not in str(exc.value)


# ── (c) pending gate — every execution path raises NotImplementedError ───────


def test_plan_substeps_raises_pending_for_pinned_chart():
    w = writer_mod.GocharaV5Writer()
    with pytest.raises(NotImplementedError, match="A5.3: geometry/solver "
                                                  "pending steward pins 3-7"):
        w.plan_substeps(_ctx())


def test_run_raises_pending_for_pinned_chart():
    w = writer_mod.GocharaV5Writer()
    with pytest.raises(NotImplementedError) as exc:
        w.run(_ctx())
    assert str(exc.value) == writer_mod.PENDING_MESSAGE


def test_run_substep_raises_pending_via_run_delegation():
    w = writer_mod.GocharaV5Writer()
    with pytest.raises(NotImplementedError) as exc:
        w.run_substep(_ctx(), SubStep(key=writer_mod.ASSET_ID))
    assert str(exc.value) == writer_mod.PENDING_MESSAGE


# ── (e) dry_run — no write path exists, so dry_run changes nothing ───────────


def test_dry_run_still_refuses_foreign_charts():
    w = writer_mod.GocharaV5Writer()
    with pytest.raises(writer_mod.ChartRefusal):
        w.run(_ctx(OTHER_CHART_ID, dry_run=True))


def test_dry_run_still_raises_pending_for_pinned_chart():
    w = writer_mod.GocharaV5Writer()
    with pytest.raises(NotImplementedError) as exc:
        w.run(_ctx(dry_run=True))
    assert str(exc.value) == writer_mod.PENDING_MESSAGE


# ── (d) inertness ─────────────────────────────────────────────────────────────


def test_seed_row_is_inactive_and_cites_both_planner_predicates():
    """The seeded row stays OUT of runPreparation's set
    (src/lib/build/runPreparation.ts, WHERE is_active = true) and
    recalibrationEnqueue's writer sweep (src/lib/build/recalibrationEnqueue.ts,
    is_active = true AND has_writer = true). The executable version of this
    check is platform/scripts/__tests__/a53_gochara_v5_inert.test.ts; this
    static guard keeps the pytest suite honest without a TS runner."""
    src = SEED.read_text()
    block = src.split("asset_id: 'ka_gochara_v5'", 1)[1]
    block = block.split("asset_id:", 1)[0]  # this asset's entry only
    assert "is_active: false" in block
    assert "is_active: true" not in block
    assert "depends_on: []" in block
    # the inertness comment cites both planner predicates
    assert "runPreparation" in block and "recalibrationEnqueue" in block


def test_writer_module_source_has_no_connection_lifecycle_or_throughput():
    # strip the module docstring — it discusses the prohibitions in prose
    src = inspect.getsource(writer_mod).replace(inspect.getdoc(writer_mod), "")
    for forbidden in (".commit(", ".rollback(", ".close(", "connect(",
                      "psycopg", "asset_throughput"):
        assert forbidden not in src, (
            f"writer module must not contain {forbidden!r} — the inert "
            "skeleton never touches the connection, opens none, and never "
            "writes build state")
