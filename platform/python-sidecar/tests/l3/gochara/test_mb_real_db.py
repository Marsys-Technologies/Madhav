"""The measuring-build PR on a REAL database (the a55 template + the real orchestrator tables + the real `life_events` DDL).

  (a) the derivation reads the real `life_events` table, every raw row, and the build date from the real `build_runs.created_at`: the pinned chart resolves to
      [1998-01-01, 2084-02-05) with the first dated event EVT.1998.02.16.01, and the manifest PINS the basis beside the horizon;
  (b) a later substep that re-derives a DIFFERENT basis (the log was revised mid-build) is refused by name, nothing continues;
  (c) the state guard against the real `asset_throughput`: refuses a present non-building row by name and writes nothing, passes `building`, skips an absent row;
  (d) EMPIRICAL (steward TIMEOUT-RULING 2): the REAL runner with a tiny registry cap. What a fired cap does to the run and the rows, observed and recorded here.
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


def _marker(run="one_class_full", classes=(ONE_CLASS,)):
    return {"schema": writer_mod.TEST_SLICE_SCHEMA, "run": run, "horizon": [FULL[0].isoformat(), FULL[1].isoformat()], "classes": list(classes)}


@pytest.fixture()
def mworld(template, monkeypatch):
    monkeypatch.setattr(hz, "LEL_BIRTH_WORD_COLUMN", "category")        # steward OS-1 pins the real column after a production read; the tests pin `category`
    w = _World(template)
    try:
        rw.apply_orchestrator_schema(w.conn)
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


# ── (a) the derivation from the real table ────────────────────────────────────────────────────────────────────────────────────────────

def test_the_pinned_chart_horizon_is_derived_from_the_real_life_events_table_and_the_build_run(mworld):
    w = mworld
    h = writer_mod._derive_horizon(_ctx(w))
    assert h.bounds == FULL == tuple(writer_mod.DEFAULT_HORIZON) and h.basis == "first_dated_event" and h.first_event_id == "EVT.1998.02.16.01"
    assert (len(h.consumed_rows), h.excluded_not_fully_dated) == (5, 2) and h.birth_row.event_id == "EVT.1984.02.05.01" and h.birth_word_column == "category"
    assert "EVT.1990.01.01.01" not in [r["event_id"] for r in h.consumed_rows], "another chart's row is never read: the chart filter (migration 423)"
    created = _row(w, "SELECT created_at FROM public.build_runs WHERE id = %s", w.run_id)[0]
    assert h.build_date == created.astimezone(UTC).date()
    assert writer_mod._effective_horizon(_ctx(w), None) == FULL


def test_the_manifest_pins_the_horizon_and_its_basis_and_a_slice_marker_for_the_full_horizon_is_validated_against_the_database_derivation(mworld):
    w = mworld
    ctx = _ctx(w)
    with w.conn.transaction():
        writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.MANIFEST_SUBSTEP, label="manifest"))
    horizon = _row(w, "SELECT lower(horizon), upper(horizon) FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = '5.0'", CHART_ID)
    vector = _row(w, "SELECT input_generation_vector FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = '5.0'", CHART_ID)[0]
    assert tuple(horizon) == FULL
    basis = vector["horizon_basis"]
    assert basis["schema"] == "horizon_basis/1" and basis["basis"] == "first_dated_event"
    assert basis["chosen"] == {"event_id": "EVT.1998.02.16.01", "event_date": "1998-02-16", "date_confidence": "exact", "shape": "point"}
    assert basis["build_date"] == _row(w, "SELECT (created_at AT TIME ZONE 'UTC')::date FROM public.build_runs WHERE id = %s", w.run_id)[0].isoformat()
    assert basis["birth_row"] == {"event_id": "EVT.1984.02.05.01", "column_used": "category"} and basis["excluded_not_fully_dated"] == 2
    assert [r["event_id"] for r in basis["consumed_rows"]] == sorted(r[0] for r in rw.PINNED_LEL_ROWS), "EVERY consumed row of the chart is pinned, sorted by id"
    assert basis["dating_rules"] == {"flag_exact": "EVT.1998.02.16.01", "id_digits": "EVT.1998.02.16.01"}
    assert vector["stored_scope"] == "test_slice" and vector["test_slice"]["horizon"] == [FULL[0].isoformat(), FULL[1].isoformat()]


# ── (b) a revised log mid-build (steward ruling 3 on MB-1.4) ──────────────────────────────────────────────────────────────────────────────

def test_a_log_edit_that_changes_the_derived_horizon_refuses_the_next_substep_by_name_and_writes_nothing(mworld):
    w = mworld
    ctx = _ctx(w)
    with w.conn.transaction():
        writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.MANIFEST_SUBSTEP, label="manifest"))
    w.conn.execute("DELETE FROM public.life_events WHERE event_id = 'EVT.1998.02.16.01' AND chart_id = %s", (CHART_ID,))          # the first dated event is now 2007
    with pytest.raises(hz.HorizonDerivationDisagreesWithRuling, match="horizon_derivation_disagrees_with_ruling"):
        with w.conn.transaction():
            writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.SNAPSHOT_SUBSTEP, label="snapshot"))
    assert _row(w, "SELECT count(*) FROM public.ka_gochara_search_inventory WHERE chart_id = %s", CHART_ID)[0] == 0


def test_a_flag_edit_that_makes_the_two_dating_rules_disagree_refuses_by_name(mworld):
    w = mworld
    ctx = _ctx(w)
    with w.conn.transaction():
        writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.MANIFEST_SUBSTEP, label="manifest"))
    w.conn.execute("UPDATE public.life_events SET date_confidence = 'month_known' WHERE event_id = 'EVT.1998.02.16.01' AND chart_id = %s", (CHART_ID,))
    with pytest.raises(hz.LelDatingRulesDisagree, match="lel_dating_rules_disagree"):
        with w.conn.transaction():
            writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.SNAPSHOT_SUBSTEP, label="snapshot"))


def test_a_log_edit_that_does_not_change_the_horizon_is_a_report_line_with_the_changed_row_ids_and_never_a_refusal(mworld, caplog):
    w = mworld
    ctx = _ctx(w)
    with w.conn.transaction():
        writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.MANIFEST_SUBSTEP, label="manifest"))
    w.conn.execute("INSERT INTO public.life_events (chart_id, event_id, event_date, category, description, chart_state, source_section, build_id, provenance, date_confidence)"
                   " VALUES (%s, 'EVT.2010.01.01.01', '2010-01-01', 'other', 'revision', '{}'::jsonb, 'test', 'test', '{}'::jsonb, 'exact')", (CHART_ID,))
    with caplog.at_level("WARNING"):
        with w.conn.transaction():
            writer_mod._verify_live_inputs(ctx, CHART_ID)                                    # no InputDrift: the horizon did not change
    assert any("horizon_basis_rows_changed" in r.message and "EVT.2010.01.01.01" in r.message for r in caplog.records)


# ── (c) the state guard on the real table ─────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("state", ["dormant", "error", "lit", "incomplete", "stale"])
def test_a_present_non_building_row_refuses_every_substep_kind_by_name_and_writes_nothing(mworld, state):
    w = mworld
    _set_state(w, state)
    before = {t: _row(w, f"SELECT count(*) FROM public.{t}")[0] for t in ("kala_gochara_publication", "ka_gochara_rule_path", "ka_gochara_search_inventory")}
    for key in (writer_mod.RULES_SUBSTEP, writer_mod.MANIFEST_SUBSTEP, writer_mod.SNAPSHOT_SUBSTEP, f"inventory:{ONE_CLASS}", f"record:{ONE_CLASS}:P1"):
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
    out = rw.run_real_entry_point(w.dsn, w.run_id, ephe_env=EPHE_PATH, timeout=600.0)       # the world's shim pins the birth-word column in the subprocess
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
