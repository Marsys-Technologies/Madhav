"""Measuring build on the real migration/runner fixtures.

The field uses ruled scope without outcome-table reads. Scope drift and the
state guard still refuse before writing; deleting/changing outcomes leaves
scope and input verification invariant. The real runner fired-cap proof remains.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import psycopg
import pytest

from pipeline.orchestrator.asset_runner import get_writer_source_hash
from pipeline.orchestrator.birth_params import fetch_birth_params
from pipeline.orchestrator.writers import ContextSpec, SubStep, WRITER_REGISTRY, discover_all
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import horizon as hz

from . import _runner_world as rw
from .conftest import EPHE_PATH
from .test_a55_replace_chain import CHART_ID, _World, template  # noqa: F401

UTC = timezone.utc
FULL = (datetime(1998, 1, 1, tzinfo=UTC), datetime(2084, 2, 5, tzinfo=UTC))
ONE_CLASS = "marriage"


def _marker(run="all_classes_full", classes=None, horizon=FULL):
    return {"schema": writer_mod.TEST_SLICE_SCHEMA, "run": run, "horizon": [horizon[0].isoformat(), horizon[1].isoformat()],
            "classes": list(writer_mod.SCORED_CLASSES if classes is None else classes)}


@pytest.fixture()
def mworld(template):
    w = _World(template)
    try:
        rw.apply_orchestrator_schema(w.conn, life_events=True)
        discover_all()
        rw.seed_registry(w.conn, set(WRITER_REGISTRY) - {"bg_nakshatra_medical", "bg_transit_engine"})
        w.run_id = rw.stage_run(w.conn, _marker(), get_writer_source_hash(writer_mod.ASSET_ID))
        _set_state(w, "building")          # what `run_asset` commits before the first substep (a staged run reads dormant until the runner starts it)
        yield w
    finally:
        w.close()


def _ctx(w, **config):
    birth = fetch_birth_params(w.conn, CHART_ID)
    return ContextSpec(asset_id=writer_mod.ASSET_ID, build_id=w.run_id, db_conn=w.conn, dry_run=False,
                       config={"chart_id": CHART_ID, "birth_params": birth, "ephe_path": EPHE_PATH, **config})


def _row(w, sql, *args):
    return w.conn.execute(sql, args).fetchone()


def _set_state(w, state):
    w.conn.execute("UPDATE public.asset_throughput SET state = %s WHERE asset_id = 'ka_gochara_v5' AND chart_id = %s", (state, CHART_ID))


# ── scope: ordinary builds and the two older slice shapes (steward MB-CODEX-1 ruling 1; Codex blocker 1) ─────────────────────────────────

@pytest.fixture()
def oworld(template):
    """A real database with NO `life_events` table at all."""
    w = _World(template)
    try:
        rw.apply_orchestrator_schema(w.conn)
        discover_all()
        rw.seed_registry(w.conn, set(WRITER_REGISTRY) - {"bg_nakshatra_medical", "bg_transit_engine"})
        yield w
    finally:
        w.close()


@pytest.mark.parametrize("shape", ["ordinary", "one_class_full", "all_classes_1y"])
def test_an_ordinary_build_and_the_two_older_slice_shapes_need_no_life_events_table_keep_default_horizon_and_pin_no_basis(oworld, shape):
    """The real runner supplies only chart_id and birth_params. With the table ABSENT (an unusable log cannot stop these builds): the horizon is DEFAULT_HORIZON exactly as on
    main, the plan is the same, the manifest substep runs and the stored vector carries NO `horizon_basis` component, so it is byte-identical to main's."""
    import uuid
    w = oworld
    assert _row(w, "SELECT to_regclass('public.life_events')")[0] is None
    old = writer_mod.DEFAULT_HORIZON
    if shape == "ordinary":
        run_id, classes = str(uuid.uuid4()), writer_mod.SCORED_CLASSES
    else:
        classes = (ONE_CLASS,) if shape == "one_class_full" else writer_mod.SCORED_CLASSES
        horizon = old if shape == "one_class_full" else (datetime(2025, 4, 1, tzinfo=UTC), datetime(2026, 4, 1, tzinfo=UTC))
        run_id = rw.stage_run(w.conn, _marker(shape, classes, horizon), get_writer_source_hash(writer_mod.ASSET_ID))
        _set_state(w, "building")          # what `run_asset` commits before the first substep (a staged run reads dormant until the runner starts it)
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id=run_id, db_conn=w.conn, dry_run=False,
                      config={"chart_id": CHART_ID, "birth_params": fetch_birth_params(w.conn, CHART_ID), "ephe_path": EPHE_PATH})
    sl = writer_mod._test_slice(ctx)
    assert (sl is None) == (shape == "ordinary")
    assert writer_mod._horizon_basis(ctx, sl) is None
    expected = tuple(old) if shape != "all_classes_1y" else tuple(sl.horizon)
    assert tuple(writer_mod._effective_horizon(ctx, sl)) == expected
    plan = writer_mod.GocharaV5Writer().plan_substeps(ctx)
    assert (len(plan) == 298) if shape != "one_class_full" else (0 < len(plan) < 298)
    with w.conn.transaction():
        writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.MANIFEST_SUBSTEP, label="manifest"))
    horizon = _row(w, "SELECT lower(horizon), upper(horizon) FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = '5.0'", CHART_ID)
    vector = _row(w, "SELECT input_generation_vector FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = '5.0'", CHART_ID)[0]
    assert tuple(horizon) == expected and "horizon_basis" not in vector


# ── (a) the derivation from the real table ────────────────────────────────────────────────────────────────────────────────────────────

def test_the_pinned_scope_uses_birth_and_build_date_with_no_outcome_rows(mworld):
    w = mworld
    h = writer_mod._derive_horizon(_ctx(w))
    assert h.bounds == FULL and h.basis == "ruled_horizon"
    assert h.consumed_rows == () and h.first_event is None and h.birth_row is None
    created = _row(w, "SELECT created_at FROM public.build_runs WHERE id = %s", w.run_id)[0]
    assert h.build_date == created.astimezone(UTC).date()
    assert writer_mod._test_slice(_ctx(w)).horizon == FULL
    assert writer_mod._effective_horizon(_ctx(w), None) == writer_mod.DEFAULT_HORIZON


def test_the_manifest_pins_ruled_scope_without_outcome_provenance(mworld):
    w = mworld
    with w.conn.transaction():
        writer_mod.GocharaV5Writer().run_substep(_ctx(w), SubStep(key=writer_mod.MANIFEST_SUBSTEP, label="manifest"))
    horizon = _row(w, "SELECT lower(horizon), upper(horizon) FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = '5.0'", CHART_ID)
    vector = _row(w, "SELECT input_generation_vector FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = '5.0'", CHART_ID)[0]
    assert tuple(horizon) == FULL
    basis = vector["horizon_basis"]
    assert basis["schema"] == "horizon_basis/1" and basis["basis"] == "ruled_horizon" and basis["chart_id"] == CHART_ID
    assert basis["consumed_rows"] == [] and basis["chosen"] is None and basis["birth_row"] is None
    assert basis["build_date"] == _row(w, "SELECT (created_at AT TIME ZONE 'UTC')::date FROM public.build_runs WHERE id = %s", w.run_id)[0].isoformat()
    assert vector["stored_scope"] == "test_slice" and vector["test_slice"]["horizon"] == [x.isoformat() for x in FULL]


# ── (b) a revised log mid-build (steward ruling 3 on MB-1.4) ──────────────────────────────────────────────────────────────────────────────

def test_a_configured_scope_change_refuses_the_next_substep_and_writes_nothing(mworld):
    w = mworld
    with w.conn.transaction():
        writer_mod.GocharaV5Writer().run_substep(_ctx(w), SubStep(key=writer_mod.MANIFEST_SUBSTEP, label="manifest"))
    changed = (datetime(2007, 1, 1, tzinfo=UTC), FULL[1])
    with pytest.raises(writer_mod.HorizonBasisHorizonChanged, match="horizon_basis_horizon_changed"):
        with w.conn.transaction():
            writer_mod.GocharaV5Writer().run_substep(_ctx(w, horizon=changed), SubStep(key=writer_mod.SNAPSHOT_SUBSTEP, label="snapshot"))
    assert _row(w, "SELECT count(*) FROM public.ka_gochara_search_inventory WHERE chart_id = %s", CHART_ID)[0] == 0


def test_the_ruling_guard_refuses_a_different_configured_scope_before_publication(mworld):
    w = mworld
    with pytest.raises(hz.HorizonDerivationDisagreesWithRuling, match="horizon_derivation_disagrees_with_ruling"):
        writer_mod.GocharaV5Writer().plan_substeps(_ctx(w, horizon=(datetime(2007, 1, 1, tzinfo=UTC), FULL[1])))
    assert _row(w, "SELECT count(*) FROM public.kala_gochara_publication WHERE chart_id = %s", CHART_ID)[0] == 0


def test_an_outcome_date_flag_edit_leaves_the_pinned_scope_and_live_check_unchanged(mworld):
    w = mworld
    with w.conn.transaction():
        writer_mod.GocharaV5Writer().run_substep(_ctx(w), SubStep(key=writer_mod.MANIFEST_SUBSTEP, label="manifest"))
    before = writer_mod._horizon_basis(_ctx(w), writer_mod._test_slice(_ctx(w)))
    w.conn.execute("UPDATE public.life_events SET date_confidence = 'month_known' WHERE provenance->>'lel_id' = 'EVT.1998.02.16.01' AND chart_id = %s", (CHART_ID,))
    writer_mod._verify_live_inputs(_ctx(w), CHART_ID)
    assert writer_mod._horizon_basis(_ctx(w), writer_mod._test_slice(_ctx(w))) == before


def test_deleting_the_first_dated_outcome_leaves_field_scope_and_inputs_unchanged(mworld):
    w = mworld
    with w.conn.transaction():
        writer_mod.GocharaV5Writer().run_substep(_ctx(w), SubStep(key=writer_mod.MANIFEST_SUBSTEP, label="manifest"))
    before = writer_mod._horizon_basis(_ctx(w), writer_mod._test_slice(_ctx(w)))
    w.conn.execute("DELETE FROM public.life_events WHERE provenance->>'lel_id' = 'EVT.1998.02.16.01' AND chart_id = %s", (CHART_ID,))
    writer_mod._verify_live_inputs(_ctx(w), CHART_ID)
    assert writer_mod._horizon_basis(_ctx(w), writer_mod._test_slice(_ctx(w))) == before


# ── R-LEL: the real log's first eight rows, read through the real table ─────────────────────────────────────────────────────────────────

def test_the_measuring_writer_runs_when_the_outcome_table_is_absent(mworld):
    w = mworld
    w.conn.execute("DROP TABLE public.life_events")
    assert writer_mod._derive_horizon(_ctx(w)).bounds == FULL
    with w.conn.transaction():
        result = writer_mod.GocharaV5Writer().run_substep(_ctx(w), SubStep(key=writer_mod.MANIFEST_SUBSTEP, label="manifest"))
    assert result.asset_id == writer_mod.ASSET_ID
    writer_mod._verify_live_inputs(_ctx(w), CHART_ID)


# ── (c) the state guard on the real table ─────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("state", ["dormant", "error", "lit", "incomplete", "stale"])
def test_a_present_non_building_row_refuses_every_substep_kind_by_name_and_writes_nothing(mworld, state):
    w = mworld
    _set_state(w, state)
    before = {t: _row(w, f"SELECT count(*) FROM public.{t}")[0] for t in ("kala_gochara_publication", "ka_gochara_rule_path", "ka_gochara_search_inventory")}
    for key in (writer_mod.RULES_SUBSTEP, writer_mod.MANIFEST_SUBSTEP, writer_mod.SNAPSHOT_SUBSTEP, f"inventory:{ONE_CLASS}", f"record:{ONE_CLASS}:P1"):          # noqa: E501
        with pytest.raises(writer_mod.AssetNotBuilding, match=f"is '{state}', not 'building'"):
            with w.conn.transaction():
                writer_mod.GocharaV5Writer().run_substep(_ctx(w), SubStep(key=key, label=key))
    after = {t: _row(w, f"SELECT count(*) FROM public.{t}")[0] for t in before}
    assert after == before


def test_a_building_row_passes_the_guard_and_an_absent_row_is_skipped(mworld):
    w = mworld
    _set_state(w, "building")
    writer_mod._require_building(_ctx(w), CHART_ID)
    w.conn.execute("DELETE FROM public.asset_throughput WHERE asset_id = 'ka_gochara_v5' AND chart_id = %s", (CHART_ID,))
    writer_mod._require_building(_ctx(w), CHART_ID)


# ── (d) EMPIRICAL: the real runner with a tiny registry cap ───────────────────────────────────────────────────────────────────────────

def test_a_fired_cap_through_the_real_runner_ends_the_run_failed_and_the_asset_error_and_never_lit_or_complete(mworld):
    """What a fired `writer_timeout_seconds` does, observed through the REAL entry point (registry cap 3 s on a plan of 298+ substeps):
    the orchestrator's scheduler marks the asset and the run failed (the detector is STATE, never the error text: MEASURING_BUILD_CONTRACT MB-4.2), the run
    exits 0, the asset is NEVER promoted to lit/complete by the thread that outlived the eviction, and the chain holds only a contiguous prefix of the plan. NOT asserted: how many substeps the evicted thread committed after the eviction (a race with the process exit;
    the guard bounds it to the substep in flight)."""
    w = mworld
    w.conn.execute("UPDATE public.asset_registry SET writer_timeout_seconds = 3 WHERE asset_id = 'ka_gochara_v5'")
    out = rw.run_real_entry_point(w.dsn, w.run_id, ephe_env=EPHE_PATH, timeout=600.0)
    run = _row(w, "SELECT state FROM public.build_runs WHERE id = %s", w.run_id)[0]
    asset = _row(w, "SELECT state, error FROM public.build_run_assets WHERE run_id = %s", w.run_id)
    thr = _row(w, "SELECT state, last_error FROM public.asset_throughput WHERE asset_id = 'ka_gochara_v5' AND chart_id = %s", CHART_ID)
    events = rw.substep_events(out["stdout"])
    print("CAP 3s:", {"code": out["code"], "seconds": round(out["seconds"], 1), "run": run, "build_run_asset": asset[0], "throughput": thr[0],
                      "substeps_committed": len(events), "error_head": (asset[1] or "")[:100]})
    assert out["code"] == 0, "the runner exits 0 even when the run ends failed: the verdict is read from the database"
    assert run == "failed" and asset[0] == "error" and thr[0] == "error"
    assert "TIMEOUT: asset_id=ka_gochara_v5" in out["stderr"], "the scheduler's own log line: the cap fired (a log check, not the stored text)"
    assert thr[0] not in ("lit", "mature") and asset[0] != "complete"
    keys = [e["substep_key"] for e in events]
    plan = [s.key for s in writer_mod.GocharaV5Writer().plan_substeps(_ctx(w))]
    assert keys == plan[:len(keys)], "the substeps that committed are a contiguous prefix of the plan, in order"
    assert len(keys) < len(plan)
