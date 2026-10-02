"""A5.3 — the window sweep against the REAL applied schema (1081 + 1152–1157), on a throwaway
database (NOT_RUN skip when the server is unreachable).

One admitted P3 record (Saturn's residence in Libra, the 7th signature house of marriage from the
fixture's Aries lagna) is materialised through the real record grain, then swept. The contract
checks that matter live in the database, not in the sweep: the 1156 coverage guard, the membership
guard, the score/evidence/severity CHECKs, the half-open interval, and delete-then-insert.
"""
from __future__ import annotations

import uuid
from datetime import timedelta

import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import record_store as rs
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel.rule_registry import RuleRegistryStore
from services.gochara_kernel.window_store import WindowStore

from .test_a53_record_store import (CHART, CHART_ID, DAY, HORIZON, T0, _coverage_kwargs,  # noqa: F401
                                    _grain_kwargs, _pg_dsn, _seed_saturn_crossings,
                                    _sky_convention_id, pg)

GEN = "5.0"
CLS, PATH, VERSION = "marriage", "P3", "1.0.0"


def _declared_rows(path, version):
    """The real factor rows + the applicability block the 1.1.0 row declares (spans ⇒ step)."""
    rows = []
    for row in ws.registry_factor_rows(path, version):
        row = dict(row)
        if row["factor_id"] == "activity_kernel":
            row["applicability"] = {
                "span": {"object_kinds": ["sign_span", "house_span", "star"], "function": "step",
                         "inside": 1.0, "outside": 0.0},
                "angular": {"object_kinds": ["degree_point", "derived_point", "saham", "house_lord"],
                            "function": "linear", "orb_deg": None}}
        elif row["factor_id"] == "graduated_drishti":
            row["applicability"] = {"relations": ["aspect"]}
        rows.append(row)
    return rows


@pytest.fixture()
def grain(pg):
    """Registry sealed, coverage written, one admitted P3 record materialised."""
    conn = pg
    RuleRegistryStore(conn).seed()
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        sky_cid = _sky_convention_id(conn)
        _seed_saturn_crossings(conn, sky_cid)
    store = rs.RecordStore(conn)
    kala_cid = store.ensure_kala_convention()
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        rs.write_class_coverage(store, **_coverage_kwargs(store, kala_cid, sky_cid))
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        counts = rs.materialise_record_grain(store, **{**_grain_kwargs(store, sky_cid), "chart": CHART})
    assert counts["records"] == 1
    return conn


def _sweep_and_write(conn, rows_for):
    ws_store = WindowStore(conn)
    recs = ws_store.read_grain(chart_id=CHART_ID, generation=GEN, event_class=CLS,
                               path_id=PATH, rule_version=VERSION)
    drafts, excluded = ws.draft_windows(CLS, recs, rows_for)
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        counts = ws_store.replace_grain_windows(
            chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id=PATH,
            rule_version=VERSION, drafts=drafts)
        verified = ws_store.verify_grain(chart_id=CHART_ID, generation=GEN, event_class=CLS,
                                         path_id=PATH, rule_version=VERSION)
    return recs, drafts, excluded, counts, verified


def _window_rows(conn):
    return conn.execute(
        "SELECT lower(interval), upper(interval), peak_instant, score, evidence_for,"
        " evidence_against, outcome_valence_for_native, severity, null_states_used,"
        " coverage_partition_key FROM public.ka_gochara_eval_window ORDER BY 1").fetchall()


def test_the_materialised_record_is_admitted_and_scored(grain):
    (rec,) = WindowStore(grain).read_grain(chart_id=CHART_ID, generation=GEN, event_class=CLS,
                                           path_id=PATH, rule_version=VERSION)
    assert (rec.admission_state, rec.operator_role, rec.relation) == ("admitted", "scored", "residence")
    assert rec.supports == ((T0 + 10 * DAY, T0 + 200 * DAY),)


def test_todays_registry_stores_an_honest_unqualified_window(grain):
    recs, drafts, excluded, counts, verified = _sweep_and_write(grain, ws.registry_factor_rows)
    assert counts == {"windows": 1, "memberships": 1, "replaced": 0} and verified == {"windows": 1}
    (row,) = _window_rows(grain)
    lo, hi, peak, score, ev_for, ev_against, valence, severity, null_states, key = row
    assert (lo, hi) == (T0 + 10 * DAY, T0 + 200 * DAY)           # the whole connected union
    assert (peak, score, ev_for, ev_against, severity) == (None, None, None, None, None)
    assert valence == "unqualified" and list(null_states) == ["unqualified"] and key == CLS


def test_a_declared_applicability_row_qualifies_the_same_record_with_no_code_change(grain):
    _sweep_and_write(grain, _declared_rows)
    (row,) = _window_rows(grain)
    lo, hi, peak, score, ev_for, ev_against, valence, severity, null_states, _ = row
    assert (lo, hi) == (T0 + 10 * DAY, T0 + 200 * DAY)
    assert peak == T0 + 10 * DAY and lo <= peak < hi            # earliest instant of the plateau max
    assert (score, ev_for, ev_against) == (1.0, 1.0, 0.0)
    assert severity is None                                      # named null, never 0
    assert valence == "favourable"                               # marriage is a gain class
    assert list(null_states) == []


def test_a_rerun_replaces_the_grain_never_accretes(grain):
    _sweep_and_write(grain, ws.registry_factor_rows)
    _, _, _, counts, _ = _sweep_and_write(grain, _declared_rows)
    assert counts == {"windows": 1, "memberships": 1, "replaced": 1}
    assert len(_window_rows(grain)) == 1
    assert grain.execute("SELECT count(*) FROM public.ka_gochara_eval_window_record").fetchone()[0] == 1


def test_the_independent_sql_union_check_catches_a_missing_window(grain):
    _sweep_and_write(grain, _declared_rows)
    with grain.transaction():
        grain.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        grain.execute("DELETE FROM public.ka_gochara_eval_window")
        with pytest.raises(RuntimeError, match="window verification failed"):
            WindowStore(grain).verify_grain(chart_id=CHART_ID, generation=GEN, event_class=CLS,
                                            path_id=PATH, rule_version=VERSION)


def test_a_not_admitted_record_never_forms_a_window(grain):
    with grain.transaction():
        grain.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        grain.execute(
            "UPDATE public.ka_gochara_record_prerequisite SET result = 'false'")
        grain.execute(
            "UPDATE public.ka_gochara_relationship_record SET admission_state = 'not_admitted'")
    _, drafts, excluded, counts, _ = _sweep_and_write(grain, _declared_rows)
    assert drafts == [] and excluded["not_admitted"] == 1
    assert counts == {"windows": 0, "memberships": 0, "replaced": 0}


# ── through the writer's own substep ─────────────────────────────────────────

def test_the_writer_window_substep_runs_on_the_runners_native_types(grain, monkeypatch):
    monkeypatch.setattr(writer_mod, "calc_sidereal_lon", lambda body, jd, ephe: (10.0, 2))
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-window", db_conn=grain,
                      config={"chart_id": uuid.UUID(CHART_ID), "horizon": HORIZON}, dry_run=False)
    w = writer_mod.GocharaV5Writer()
    with grain.transaction():
        res = w.run_substep(ctx, SubStep(key=f"window:{CLS}:{PATH}", label="w"))
    assert res.rows_inserted == 2                                # 1 window + 1 membership row
    assert "1 window(s) (1 unqualified" in res.notes and "independent SQL union check passed" in res.notes
    (row,) = _window_rows(grain)
    assert row[3] is None and row[6] == "unqualified"
    # the dry run solves and writes nothing
    dry = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-dry", db_conn=grain,
                      config={"chart_id": uuid.UUID(CHART_ID), "horizon": HORIZON}, dry_run=True)
    assert w.run_substep(dry, SubStep(key=f"window:{CLS}:{PATH}", label="w")).rows_inserted == 0


def test_a_window_grain_outside_the_planned_paths_is_refused_by_name(grain):
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-x", db_conn=grain,
                      config={"chart_id": uuid.UUID(CHART_ID), "horizon": HORIZON}, dry_run=False)
    with grain.transaction():
        res = writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=f"window:{CLS}:P2", label="w"))
    assert res.rows_inserted == 0 and "unknown window grain" in res.notes
