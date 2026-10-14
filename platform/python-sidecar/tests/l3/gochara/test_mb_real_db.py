"""The measuring-build PR on a REAL database (the a55 template + the real orchestrator tables + the real `life_events` DDL). Every test here is the `all_classes_full`
shape (the ONLY one that reads the log) except where it says otherwise: ordinary builds and the two older slice shapes keep DEFAULT_HORIZON and never read it.

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

def test_the_pinned_chart_horizon_is_derived_from_the_real_life_events_table_and_the_build_run(mworld):
    w = mworld
    h = writer_mod._derive_horizon(_ctx(w))
    assert h.bounds == FULL == tuple(writer_mod.MEASURING_HORIZON) and h.basis == "first_dated_event"
    assert (len(h.consumed_rows), h.excluded_not_fully_dated) == (5, 2) and h.birth_row.provenance_lel_id == "EVT.1984.02.05.01" and h.birth_row.domain == "other/birth"
    assert h.first_event.event_id == rw.lel_event_uuid("EVT.1998.02.16.01") and h.first_event.provenance_lel_id == "EVT.1998.02.16.01"
    assert set(h.flag_exact_but_id_undated) == {rw.lel_event_uuid("EVT.1995.XX.XX.01"), rw.lel_event_uuid("EVT.2001.03.XX.01")}, "457's default exact on proxy-dated rows: excluded and listed"
    assert rw.lel_event_uuid("EVT.1990.01.01.01") not in [r["event_id"] for r in h.consumed_rows], "another chart's row is never read: the chart filter (migration 423)"
    created = _row(w, "SELECT created_at FROM public.build_runs WHERE id = %s", w.run_id)[0]
    assert h.build_date == created.astimezone(UTC).date()
    assert tuple(writer_mod._test_slice(_ctx(w)).horizon) == FULL                           # the marker is validated against this derivation
    assert tuple(writer_mod._effective_horizon(_ctx(w), None)) == tuple(writer_mod.DEFAULT_HORIZON), "an ordinary (marker-less) build keeps DEFAULT_HORIZON"


def test_the_manifest_pins_the_horizon_and_its_basis_and_a_slice_marker_for_the_full_horizon_is_validated_against_the_database_derivation(mworld):
    w = mworld
    ctx = _ctx(w)
    with w.conn.transaction():
        writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.MANIFEST_SUBSTEP, label="manifest"))
    horizon = _row(w, "SELECT lower(horizon), upper(horizon) FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = '5.0'", CHART_ID)
    vector = _row(w, "SELECT input_generation_vector FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = '5.0'", CHART_ID)[0]
    assert tuple(horizon) == FULL
    basis = vector["horizon_basis"]
    assert basis["schema"] == "horizon_basis/1" and basis["basis"] == "first_dated_event" and basis["chart_id"] == CHART_ID
    assert basis["chosen"] == {"event_id": rw.lel_event_uuid("EVT.1998.02.16.01"), "lel_id": "EVT.1998.02.16.01", "event_date": "1998-02-16", "date_confidence": "exact", "shape": "point"}
    assert basis["build_date"] == _row(w, "SELECT (created_at AT TIME ZONE 'UTC')::date FROM public.build_runs WHERE id = %s", w.run_id)[0].isoformat()
    assert basis["birth_row"]["lel_id"] == "EVT.1984.02.05.01" and basis["birth_row"]["domain"] == "other/birth" and basis["birth_row"]["column_used"] == "domain"
    assert basis["excluded_not_fully_dated"] == 2 and basis["rows_total"] == 5 and len(basis["flag_exact_but_id_undated"]) == 2 and basis["rows_without_lel_id"] == []
    assert [r["provenance_lel_id"] for r in basis["consumed_rows"]] == [r[0] for r in rw.PINNED_LEL_ROWS], "EVERY consumed row of the chart is pinned, sorted by (event_date, event_id)"
    assert basis["fully_dated_readings"] == {"rule_F_start": "1995-01-01", "rule_I_start": "1998-01-01", "conjunction_start": "1998-01-01"}
    assert vector["stored_scope"] == "test_slice" and vector["test_slice"]["horizon"] == [FULL[0].isoformat(), FULL[1].isoformat()]


# ── (b) a revised log mid-build (steward ruling 3 on MB-1.4) ──────────────────────────────────────────────────────────────────────────────

def test_a_log_edit_that_changes_the_derived_horizon_refuses_the_next_substep_by_name_and_writes_nothing(mworld):
    """Codex blocker 6, on the PINNED chart (the real writer refuses any other): the manifest pins the 1998 basis, the first event is then deleted so 2007 becomes
    first, and the next substep refuses `horizon_basis_horizon_changed` (the pinned basis is compared FIRST), not the ruling guard's token."""
    w = mworld
    assert str(CHART_ID) == writer_mod.PINNED_CHART_ID
    ctx = _ctx(w)
    with w.conn.transaction():
        writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.MANIFEST_SUBSTEP, label="manifest"))
    w.conn.execute("DELETE FROM public.life_events WHERE provenance->>'lel_id' = 'EVT.1998.02.16.01' AND chart_id = %s", (CHART_ID,))          # the first dated event is now 2007
    with pytest.raises(writer_mod.HorizonBasisHorizonChanged, match="horizon_basis_horizon_changed") as e:
        with w.conn.transaction():
            writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.SNAPSHOT_SUBSTEP, label="snapshot"))
    assert "2007-01-01" in str(e.value) and not isinstance(e.value, hz.HorizonDerivationDisagreesWithRuling)
    assert _row(w, "SELECT count(*) FROM public.ka_gochara_search_inventory WHERE chart_id = %s", CHART_ID)[0] == 0


def test_the_ruling_guard_still_refuses_at_plan_time_before_anything_is_pinned(mworld):
    w = mworld
    w.conn.execute("DELETE FROM public.life_events WHERE provenance->>'lel_id' = 'EVT.1998.02.16.01' AND chart_id = %s", (CHART_ID,))
    with pytest.raises(hz.HorizonDerivationDisagreesWithRuling, match="horizon_derivation_disagrees_with_ruling"):
        writer_mod.GocharaV5Writer().plan_substeps(_ctx(w))
    assert _row(w, "SELECT count(*) FROM public.kala_gochara_publication WHERE chart_id = %s", CHART_ID)[0] == 0


def test_a_flag_edit_that_makes_the_first_event_no_longer_fully_dated_moves_the_start_and_refuses_by_name(mworld):
    w = mworld
    ctx = _ctx(w)
    with w.conn.transaction():
        writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.MANIFEST_SUBSTEP, label="manifest"))
    w.conn.execute("UPDATE public.life_events SET date_confidence = 'month_known' WHERE provenance->>'lel_id' = 'EVT.1998.02.16.01' AND chart_id = %s", (CHART_ID,))
    with pytest.raises(writer_mod.HorizonBasisHorizonChanged, match="horizon_basis_horizon_changed"):
        with w.conn.transaction():
            writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.SNAPSHOT_SUBSTEP, label="snapshot"))


def test_a_log_edit_that_does_not_change_the_horizon_is_a_report_line_with_the_changed_row_ids_and_never_a_refusal(mworld, caplog):
    w = mworld
    ctx = _ctx(w)
    with w.conn.transaction():
        writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.MANIFEST_SUBSTEP, label="manifest"))
    w.conn.execute("INSERT INTO public.life_events (chart_id, event_id, event_date, category, event_type, domain, description, chart_state, source_section, build_id, provenance,"
                   " date_confidence) VALUES (%s, %s, '2010-01-01', 'other', 'other', 'other/other', 'revision', '{}'::jsonb, 'test', 'test', "
                   "'{\"lel_id\": \"EVT.2010.01.01.01\"}'::jsonb, 'exact')", (CHART_ID, rw.lel_event_uuid("EVT.2010.01.01.01")))
    with caplog.at_level("WARNING"):
        with w.conn.transaction():
            writer_mod._verify_live_inputs(ctx, CHART_ID)                                    # no InputDrift: the horizon did not change
    assert any("horizon_basis_rows_changed" in r.message and rw.lel_event_uuid("EVT.2010.01.01.01") in r.message for r in caplog.records)


# ── R-LEL: the real log's first eight rows, read through the real table ─────────────────────────────────────────────────────────────────

def test_the_real_logs_first_eight_rows_through_the_real_table_derive_1998_and_report_the_exclusions(mworld):
    """Steward R-LEL (production read of 5 Oct 2026): the eight earliest rows in their real shapes — an interval arc dated ON the birth date with NO lel_id, the other/birth row,
    four rows flagged exact with undated ids, a year_only interval — derive [1998-01-01, 2084-02-05); the rows with no lel_id and with undated ids are excluded and REPORTED."""
    w = mworld
    w.conn.execute("DELETE FROM public.life_events WHERE chart_id = %s", (CHART_ID,))
    rw.insert_life_events(w.conn, rw.R_LEL_FIRST_EIGHT)
    h = writer_mod._derive_horizon(_ctx(w))
    assert h.bounds == FULL and h.first_event.provenance_lel_id == "EVT.1998.02.16.01" and h.birth_row.provenance_lel_id == "EVT.1984.02.05.01"
    basis = h.basis_record()
    assert basis["rows_without_lel_id"] == [{"event_id": rw.lel_event_uuid("row1"), "event_date": "1984-02-05"}]
    assert set(basis["flag_exact_but_id_undated"]) == {rw.lel_event_uuid(i) for i in ("EVT.1993.XX.XX.01", "EVT.1995.XX.XX.02", "EVT.1998.XX.XX.02", "EVT.2000.XX.XX.01")}
    assert basis["excluded_not_fully_dated"] == 6 and basis["rows_total"] == 8
    arc = next(r for r in basis["consumed_rows"] if r["event_id"] == rw.lel_event_uuid("row1"))            # (sorted by (event_date, event_id): the arc and the birth row share a date)
    assert arc["shape"] == "interval" and arc["interval_end"] == "2026-07-19" and arc["date_tightened_at"] and arc["provenance_lel_id"] is None


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
