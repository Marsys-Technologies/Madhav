"""Pravāha A5.3 — ka_gochara_v5 writer: registration, chart-scope, and the
phase-1 geometry_store substeps (steward pins 1-7, 2026-10-01).

What this file proves:

  (a) registration + frozen-contract shape: the writer is discoverable via
      get_writer('ka_gochara_v5'), subclasses WriterBase, pins asset_id, and
      ships the substep shape (has_substeps, own plan_substeps/run_substep,
      run inherited from WriterBase to aggregate);
  (b) hard chart refusal: any chart_id ≠ the pinned A5.3 candidate chart
      raises ChartRefusal on BOTH the planning path and the execution path —
      before any other behaviour;
  (c) plan (pin 5): 'rules' (rule_binding) → 'convention' → 'body:<Body>'
      ×8, Moon absent; the rules substep seeds the P1–P5 catalogue under the
      global family key with NO chart lock (N13);
  (d) substep behaviour: the chart family key precedes every write (steward
      ruling B / N13), the convention substep registers the convention row,
      each body substep drives SkyEventStore.build_boundary_substrate for
      exactly its body, and dry_run suppresses both solve and write;
  (e) inertness: the seed row ships is_active=false with depends_on=[], and
      the writer module source carries no connection-lifecycle call and never
      writes asset_throughput.

No live DB: ctx.db_conn is a recording fake; the store is monkeypatched with a
recording double so no Swiss solve runs here (the store's own tests cover the
solve path with a synthetic index).
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
from services.gochara_kernel.substrate import SUBSTRATE_BODIES  # noqa: E402

SIDECAR = Path(__file__).resolve().parents[3]
PLATFORM = SIDECAR.parent
SEED = PLATFORM / "scripts" / "seed" / "asset_registry_seed.ts"

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER_CHART_ID = "11111111-2222-4333-8444-555555555555"


class _RecordingConn:
    """Records every executed statement; any lifecycle call is a failure."""

    def __init__(self):
        self.statements: list[tuple[str, tuple]] = []

    def execute(self, sql, params=()):
        self.statements.append((sql, params))

        class _R:
            def fetchone(self):
                return None

            def fetchall(self):
                return []

        return _R()

    def commit(self):
        raise AssertionError("writer committed ctx.db_conn")

    def rollback(self):
        raise AssertionError("writer rolled back ctx.db_conn")

    def close(self):
        raise AssertionError("writer closed ctx.db_conn")


class _FakeStore:
    """Recording double for SkyEventStore (no Swiss solve, no DB)."""

    instances: list["_FakeStore"] = []

    def __init__(self, conn):
        self.conn = conn
        self.conventions_registered = 0
        self.bodies_built: list[str] = []
        _FakeStore.instances.append(self)

    def register_convention(self, vector=None):
        self.conventions_registered += 1
        return "sha256:" + "0" * 64

    def build_boundary_substrate(self, body, **kwargs):
        self.bodies_built.append(body)
        return {"objects": 135, "events": 135, "stations": 0}


class _FakeRuleStore:
    """Recording double for RuleRegistryStore (no DB)."""

    instances: list["_FakeRuleStore"] = []

    def __init__(self, conn):
        self.conn = conn
        self.seeds = 0
        _FakeRuleStore.instances.append(self)

    def seed(self):
        self.seeds += 1
        return {"predicates": 8, "factors": 11, "paths": 5,
                "prerequisites": 7, "soft_factors": 9, "seals": 5,
                "reused": 0}


@pytest.fixture(autouse=True)
def _fake_store(monkeypatch):
    _FakeStore.instances = []
    _FakeRuleStore.instances = []
    monkeypatch.setattr(writer_mod, "SkyEventStore", _FakeStore)
    monkeypatch.setattr(writer_mod, "RuleRegistryStore", _FakeRuleStore)
    yield


def _ctx(chart_id: str = CHART_ID, dry_run: bool = False,
         conn: _RecordingConn | None = None) -> ContextSpec:
    return ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="test-build",
                       db_conn=conn if conn is not None else _RecordingConn(),
                       config={"chart_id": chart_id}, dry_run=dry_run)


# ── (a) registration + frozen-contract shape ─────────────────────────────────


def test_writer_is_registered_and_discoverable():
    cls = get_writer(writer_mod.ASSET_ID)
    assert cls is writer_mod.GocharaV5Writer
    assert issubclass(cls, WriterBase)
    assert cls.asset_id == writer_mod.ASSET_ID == "ka_gochara_v5"


def test_writer_shape_conforms_to_frozen_contract():
    """Substep writer: own plan_substeps/run_substep, run inherited (the base
    aggregates plan_substeps over run_substep)."""
    w = writer_mod.GocharaV5Writer()
    assert type(w).run is WriterBase.run
    assert type(w).run_substep is not WriterBase.run_substep
    assert type(w).plan_substeps is not WriterBase.plan_substeps
    assert w.has_substeps is True


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


# ── (c) plan (pin 5): rules → convention → bodies ────────────────────────────


def test_plan_is_rules_then_convention_then_eight_bodies_moon_excluded():
    w = writer_mod.GocharaV5Writer()
    steps = w.plan_substeps(_ctx())
    keys = [s.key for s in steps]
    assert keys[0] == writer_mod.RULES_SUBSTEP
    assert keys[1] == writer_mod.CONVENTION_SUBSTEP
    assert keys[2:] == [f"body:{b}" for b in SUBSTRATE_BODIES]
    assert "Moon" not in SUBSTRATE_BODIES
    assert not any("moon" in k.lower() for k in keys)


# ── (d) substep behaviour ─────────────────────────────────────────────────────


def test_rules_substep_seeds_the_catalogue_without_the_chart_lock():
    """rule_binding: the registry tables ride the Gochara-5 GLOBAL family key
    (their write-guard triggers), so the writer must NOT take the chart
    family key in this substep (N13 mutual exclusion)."""
    conn = _RecordingConn()
    w = writer_mod.GocharaV5Writer()
    result = w.run_substep(_ctx(conn=conn), SubStep(key=writer_mod.RULES_SUBSTEP))
    store = _FakeRuleStore.instances[-1]
    assert store.seeds == 1
    assert not any("ka_gochara_lock_chart" in s[0] for s in conn.statements)
    assert result.rows_inserted == 8 + 11 + 5 + 7 + 9 + 5


def test_rules_substep_dry_run_suppresses_the_seed():
    w = writer_mod.GocharaV5Writer()
    result = w.run_substep(_ctx(dry_run=True),
                           SubStep(key=writer_mod.RULES_SUBSTEP))
    assert result.rows_inserted == 0
    assert _FakeRuleStore.instances == []


def test_chart_lock_precedes_every_write():
    conn = _RecordingConn()
    w = writer_mod.GocharaV5Writer()
    w.run_substep(_ctx(conn=conn), SubStep(key=writer_mod.CONVENTION_SUBSTEP))
    locks = [s for s in conn.statements if "ka_gochara_lock_chart" in s[0]]
    assert len(locks) == 1
    assert locks[0][1] == (CHART_ID,)


def test_convention_substep_registers_the_convention_row():
    w = writer_mod.GocharaV5Writer()
    result = w.run_substep(_ctx(), SubStep(key=writer_mod.CONVENTION_SUBSTEP))
    store = _FakeStore.instances[-1]
    assert store.conventions_registered == 1
    assert store.bodies_built == []
    assert "convention" in result.notes


def test_body_substep_builds_exactly_its_body():
    w = writer_mod.GocharaV5Writer()
    result = w.run_substep(_ctx(), SubStep(key="body:Saturn"))
    store = _FakeStore.instances[-1]
    assert store.bodies_built == ["Saturn"]
    assert result.rows_inserted == 135
    assert "Saturn" in result.notes


def test_unknown_substeps_answer_honestly_without_a_build():
    w = writer_mod.GocharaV5Writer()
    result = w.run_substep(_ctx(), SubStep(key="body:Pluto"))
    assert result.rows_inserted == 0
    assert "unknown body substep" in result.notes
    result = w.run_substep(_ctx(), SubStep(key="windows"))
    assert result.rows_inserted == 0
    assert "unknown substep" in result.notes
    assert _FakeStore.instances == [] or _FakeStore.instances[-1].bodies_built == []


def test_dry_run_suppresses_solve_and_write_and_takes_no_lock():
    conn = _RecordingConn()
    w = writer_mod.GocharaV5Writer()
    result = w.run_substep(_ctx(dry_run=True, conn=conn), SubStep(key="body:Sun"))
    assert result.rows_inserted == 0
    assert "dry_run" in result.notes
    assert conn.statements == []
    assert _FakeStore.instances == []


# ── (e) inertness ─────────────────────────────────────────────────────────────


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
            f"writer module must not contain {forbidden!r} — it never commits, "
            "rolls back or closes the caller-owned connection, opens none, and "
            "never writes build state")
