"""A5.3 day_on_demand — Moon / day tier is EPHEMERAL (AM-4). Only the Swiss
seam is faked (a linear Moon); the kernel arcs/roots, the module and the real
database (own throwaway DB) are production code."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import contacts as kc
from services.gochara_kernel import knots
from services.gochara_kernel import moon_on_demand as mod
from services.gochara_kernel import record_store as rs
from services.gochara_kernel.overlays import date_to_jd

from . import test_a53_record_store as base
from .test_a53_record_store import _pg_dsn, pg  # noqa: F401  (fixtures)

UTC = timezone.utc
START = datetime(2026, 3, 1, tzinfo=UTC)
END = datetime(2026, 3, 11, tzinfo=UTC)
RATE = 13.176   # deg/day, linear stand-in for the Moon
JD0 = date_to_jd(START.date())


def _lon(jd):
    return (100.0 + RATE * (jd - JD0)) % 360.0


@pytest.fixture
def linear_moon(monkeypatch):
    def calc(body, jd, ephe_path):
        return _lon(jd), 2
    monkeypatch.setattr(knots, "calc_sidereal_lon", calc)
    monkeypatch.setattr(kc, "calc_sidereal_lon", calc)


def test_events_are_half_open_ordered_and_hit_their_levels(linear_moon):
    events, _ = mod.solve_moon_events(START, END)
    assert events and events == sorted(events, key=lambda e: (e.t_exact, e.relation, e.level_deg))
    assert all(START <= e.t_exact < END for e in events)
    for e in events:
        jd = date_to_jd(e.t_exact.date()) + (e.t_exact - datetime(e.t_exact.year, e.t_exact.month, e.t_exact.day, tzinfo=UTC)).total_seconds() / 86400.0
        diff = abs(((_lon(jd) - e.level_deg + 180.0) % 360.0) - 180.0)
        assert diff < 1e-5, (e, diff)
    signs = [e for e in events if e.relation == "sign_ingress"]
    naks = [e for e in events if e.relation == "nakshatra_ingress"]
    # 10 days × 13.176°/day = 131.76° ⇒ 4–5 sign cusps and 9–10 nakṣatra cusps
    assert 4 <= len(signs) <= 5 and 9 <= len(naks) <= 10
    assert {e.solver_method for e in events} == {"swiss_refined"}


def test_end_is_excluded_and_start_is_included(linear_moon):
    events, _ = mod.solve_moon_events(START, END)
    first = events[0].t_exact
    again, _ = mod.solve_moon_events(first, END)           # start == an event instant
    assert again[0].t_exact == first
    shorter, _ = mod.solve_moon_events(START, first)       # end == that instant
    assert all(e.t_exact < first for e in shorter)


@pytest.mark.parametrize("start,end", [
    (datetime(2026, 3, 1), END),                                   # naive
    (START, datetime(2026, 3, 1, tzinfo=timezone(timedelta(hours=5, minutes=30)))),
    (END, START), (START, START),
    (START, START + timedelta(days=401)),                          # materialisation, refused
])
def test_bad_intervals_are_refused(start, end):
    with pytest.raises(ValueError):
        mod.solve_moon_events(start, end)


def test_partition_key_is_1081_shape():
    assert mod.partition_key(START, END) == \
        "moon:interval:2026-03-01T00:00:00Z/2026-03-11T00:00:00Z"


def test_result_digest_is_deterministic_and_binds_the_events(linear_moon):
    a, _ = mod.solve_moon_events(START, END)
    b, _ = mod.solve_moon_events(START, END)
    assert mod.result_digest(a) == mod.result_digest(b)
    assert mod.result_digest(a) != mod.result_digest(a[:-1])
    rendering = mod.result_rendering(a)
    assert "digest" not in rendering and "receipt" not in rendering
    json.loads(rendering)


# ── real DB: the only write is the coverage identity ────────────────────────

def _counts(conn):
    q = lambda t: conn.execute(f"SELECT count(*) FROM public.{t}").fetchone()[0]  # noqa: E731
    return (q("ka_gochara_relationship_record"), q("ka_gochara_contact"),
            q("ka_gochara_eval_window"), q("ka_gochara_sky_event"))


def _query(pg, linear_moon_active=True, **over):
    with pg.transaction():
        pg.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (base.CHART_ID,))
        sky = base._sky_convention_id(pg)
    store = rs.RecordStore(pg)
    kala = store.ensure_kala_convention()
    kw = dict(chart_id=base.CHART_ID, generation="5.5", start=START, end=END,
              sky_convention_id=sky, kala_convention_id=kala,
              natal_target_fact_ids=["f2", "f1"])
    kw.update(over)
    with pg.transaction():
        pg.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (base.CHART_ID,))
        store.ensure_bridge(kala, sky)
        return store, mod.run_moon_query(store, **kw)


def test_query_writes_only_its_coverage_and_returns_a_five_part_receipt(pg, linear_moon):
    before = _counts(pg)
    _, res = _query(pg)
    assert _counts(pg) == before          # no record, contact, window or sky event
    rows = pg.execute(
        "SELECT partition_key, relations_searched, targets_requested"
        " FROM public.kala_gochara_coverage WHERE generation = '5.5'"
        " AND partition_kind = 'moon_on_demand'").fetchall()
    assert rows == [(mod.partition_key(START, END),
                     ["nakshatra_ingress", "sign_ingress"], 39)]
    r = res.receipt
    assert set(r) == {"manifest", "coverage", "query_interval", "input_identity",
                      "result_digest"}
    assert r["manifest"] is None                       # no manifest row: stated, not invented
    assert r["coverage"]["partition_key"] == mod.partition_key(START, END)
    assert r["coverage"]["coverage_facts"]["relations_searched"] == \
        ["nakshatra_ingress", "sign_ingress"]
    assert r["query_interval"] == ["2026-03-01T00:00:00Z", "2026-03-11T00:00:00Z"]
    assert r["input_identity"]["natal_target_fact_ids"] == ["f1", "f2"]
    assert r["result_digest"] == mod.result_digest(res.events)


def test_replay_rederives_the_same_receipt_and_never_duplicates(pg, linear_moon):
    _, first = _query(pg)
    _, second = _query(pg)
    assert first.receipt == second.receipt
    n = pg.execute("SELECT count(*) FROM public.kala_gochara_coverage"
                   " WHERE generation = '5.5' AND partition_kind = 'moon_on_demand'"
                   ).fetchone()[0]
    assert n == 1


def test_a_reissued_interval_with_different_claims_fails_loudly(pg, linear_moon):
    store, _ = _query(pg)
    with pytest.raises(rs.IdentityCollisionError):
        with pg.transaction():
            pg.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (base.CHART_ID,))
            store.write_moon_coverage(
                chart_id=base.CHART_ID, generation="5.5",
                partition_key=mod.partition_key(START, END),
                convention_id=store.ensure_kala_convention(),
                horizon=(START, END), resolution=1.0,
                relations_searched=["sign_ingress"], targets_requested=12,
                targets_resolved=12, state_counts={"resolved": 12},
                unavailable_inputs={}, unsearched_reason=None, build_id="x")


def test_receipt_binds_the_manifest_when_one_exists(pg, linear_moon):
    with pg.transaction():
        pg.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (base.CHART_ID,))
        sky = base._sky_convention_id(pg)
    store = rs.RecordStore(pg)
    kala = store.ensure_kala_convention()
    mid = pg.execute(
        "INSERT INTO public.kala_gochara_publication (chart_id, generation,"
        " writer_asset_id, convention_id, input_generation_vector, ephemeris_backend,"
        " horizon, row_counts, content_digest, status) VALUES (%s,'5.6','ka_gochara_v5',%s,"
        " '{}'::jsonb,'{}'::jsonb,'[2026-01-01,2027-01-01)'::tstzrange,'{}'::jsonb,"
        " 'sha256:unpublished-candidate','candidate') RETURNING manifest_id",
        (base.CHART_ID, kala)).fetchone()[0]
    _, res = _query(pg, generation="5.6")
    assert res.receipt["manifest"] == {"manifest_id": str(mid),
                                       "content_digest": "sha256:unpublished-candidate",
                                       "status": "candidate"}
