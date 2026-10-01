"""ASTRA v1.2 R1 + R2 (steward M20261001T210959-b3c5): the half-open horizon's final edge.

The two findings pull against each other and are designed — and tested — together:

  R1  activity that begins within the last sampling step before the excluded end h1 has its
      only above-threshold SAMPLE at the appended horizon limit. Filtering that sample (it
      must never be a peak) used to discard the whole component: positive in-domain activity,
      ZERO windows.
  R2  restoring the limit as a series point must not let a REFINED peak land on h1: month/day
      rows with a peak on the excluded end abort the writer's validator (HorizonViolation).

Everything below runs the REAL chain — `solve_episodes` (producer) → the ledger's row shape →
`fetch_contacts` (real parsing) → `project_class_windows` → `_validate_windows_within_horizon`
(the writer's own validator). Only the planet-position accessor is a deterministic synthetic
body; no rule is re-implemented in a test.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

import pipeline.orchestrator.writers.ka_gochara_v4_41_candidate as writer_mod
from scripts.kala_gochara_cutover import step06b_windows_projection as sb
from services.gochara_kernel import arcs as gk_arcs
from services.gochara_kernel import episodes as gk_episodes
from services.gochara_kernel import legacy_semantics as leg

from .test_a25_v41_candidate_writer_pg import (  # noqa: F401  (fixtures are imported for pytest)
    CHART_ID,
    CHART_UUID,
    _H0,
    _H1,
    _SYNTH_TOL_ARCSEC,
    _daily_knots,
    _dt,
    _episode,
    _seed_manifest,
    disposable_dsn,
    pg,
    pg_dict,
)

UTC = timezone.utc
TARGET_DEG = 300.0
ORB_DEG = 5.0


# ── the real producer, the real fetch parser, a synthetic Sun ────────────────

def _sun_series(speed: float, centre_jd: float):
    return lambda jd: (TARGET_DEG + speed * (jd - centre_jd)) % 360.0


def _produce(speed: float, centre_offset_days: float):
    """Real `solve_episodes` for a Sun whose exact conjunction with TARGET_DEG lies
    `centre_offset_days` after the horizon end. Returns (episodes, position_fn)."""
    centre = _H1 + centre_offset_days
    curve = _sun_series(speed, centre)
    jds, lons = _daily_knots(date(2026, 3, 1), date(2026, 5, 20), curve)
    idx = gk_arcs.build_arc_index("Sun", jds, lons, tolerance_arcsec=_SYNTH_TOL_ARCSEC)
    eps = gk_episodes.solve_episodes(idx, "Sun", "conjunction", TARGET_DEG, (_H0, _H1),
                                     "orb_conj_slow", refine=False, orb_override_deg=ORB_DEG)
    return eps, (lambda body, jd: curve(jd))


class _Rows:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _LedgerConn:
    """Answers `fetch_contacts`' one SELECT with ledger-shaped dict rows (the runner's
    native row type) built from the producer's episodes."""

    def __init__(self, episodes):
        self._rows = [{
            "contact_id": f"c{i}", "body": "Sun", "relation": "conjunction",
            "target_type": "karaka", "target_ref": "SUN",
            "target_longitude_deg": TARGET_DEG,
            "t_in": _dt(e.t_in), "t_exact": _dt(e.t_exact) if e.t_exact is not None else None,
            "t_out": _dt(e.t_out), "orb_max_deg": ORB_DEG, "completeness_state": "applied",
            "aspect_deg": 0.0, "independence_group": "ig-sun", "branch": "direct",
        } for i, e in enumerate(episodes)]

    def execute(self, sql, params=()):
        assert "FROM kala_gochara_contacts" in sql
        return _Rows(self._rows)


def _class_ctx():
    return sb.ClassContext(
        "marriage", [0.9], {s: True for s in leg.PERMISSION_SYSTEM_IDS},
        weight_by_target_ref={"SUN": 0.9})


def _fetch(episodes):
    """The REAL `fetch_contacts` parse, then the windows core's own relation→primitive join
    (its production table `RELATION_TO_PRIMITIVE`; the map join itself is the identity here —
    one karaka SUN target, one class)."""
    return [dict(c, _primitive=sb.RELATION_TO_PRIMITIVE[c["relation"]])
            for c in sb.fetch_contacts(_LedgerConn(episodes), "chart", "4.1")]


def _project(episodes, pos_fn):
    contacts = _fetch(episodes)
    rows, report = sb.project_class_windows(
        _class_ctx(), contacts, (_H0, _H1), lambda jd: {"factor_by_body": {}},
        planet_pos_fn=pos_fn)
    return contacts, rows, report


H1_DATE = date(2026, 4, 18)


# ── R1: Codex's counterexample, verbatim ─────────────────────────────────────

def test_r1_the_v11_final_day_counterexample_yields_windows_not_zero():
    """Target 300°, speed 0.5°/day, orb 5°, exact centre 9.5 days after the horizon end:
    t_in = 2026-04-17T12:00Z, t_exact None, t_out = h1; λ(2026-04-17T18:00Z) > 0. The
    only above-threshold sample is the horizon limit."""
    eps, pos = _produce(speed=0.5, centre_offset_days=9.5)
    assert len(eps) == 1
    ep = eps[0]
    assert _dt(ep.t_in).isoformat() == "2026-04-17T12:00:00+00:00"
    assert ep.t_exact is None and ep.t_out == _H1
    contacts, rows, report = _project([ep], pos)
    # the geometry really is the reproduced one: positive activity strictly in-domain …
    evaluate = sb.make_eval_fn(_class_ctx(), contacts, lambda jd: {"factor_by_body": {}},
                               planet_pos_fn=pos)
    inside = _H1 - 0.25                                   # 2026-04-17T18:00Z
    assert evaluate(inside)["lambda_raw"] > 1e-9
    # … and the projection keeps it
    assert rows, "positive in-domain activity produced ZERO windows (the v1.1/v1.2 R1 defect)"
    assert report["final_edge_components"] == 1
    era = [r for r in rows if r["resolution"] == "era"]
    assert len(era) == 1
    assert era[0]["window_start"] == date(2026, 4, 17)
    assert era[0]["window_end"] == H1_DATE            # an exclusive endpoint may equal the limit
    assert era[0]["peak_date"] == date(2026, 4, 17)   # the peak is never ON the excluded end
    writer_mod._validate_windows_within_horizon(rows)  # the writer's own validator
    # ASTRA v1.3: the stand-in is DISCLOSED on the row — a distinct basis + a qualification block
    # — never left looking like an ordinary located peak
    assert era[0]["peak_basis"] == sb.PEAK_BASIS_HORIZON_LIMITED
    q = era[0]["suppression_state"]["horizon_limited_sample"]
    assert q["kind"] == "horizon_limited_sample" and q["attained_extremum"] is False
    assert q["reason"] == "only_above_threshold_sample_is_the_horizon_limit"
    assert q["selected_instant_utc"] < q["excluded_horizon_end_utc"]
    assert q["excluded_horizon_end_utc"] == "2026-04-18T00:00:00+00:00"
    assert q["offset_from_excluded_end_seconds"] == pytest.approx(8.64, abs=0.01)
    assert "never a located extremum" in q["substitution_rule"]
    assert report["horizon_limited_rows"] == 1


def test_r1_an_interval_that_opens_exactly_at_the_excluded_end_is_still_dropped():
    """The control: no in-domain extent ⇒ no window (the half-open rule still bites)."""
    eps, pos = _produce(speed=0.5, centre_offset_days=10.0)   # orb opens exactly at h1
    assert eps == []                                           # the producer already drops it
    contacts = _fetch([])
    rows, report = sb.project_class_windows(
        _class_ctx(), contacts, (_H0, _H1), lambda jd: {"factor_by_body": {}}, planet_pos_fn=pos)
    assert rows == [] and report["final_edge_components"] == 0


def test_r1_legitimate_final_day_activity_with_in_domain_samples_is_unchanged():
    """The pre-existing behaviour (an in-domain peak sample exists): no stand-in is used."""
    eps, pos = _produce(speed=1.0, centre_offset_days=-3.0)    # exact 3 days BEFORE h1, in-orb through h1
    assert len(eps) == 1
    _contacts, rows, report = _project(eps, pos)
    assert rows and report["final_edge_components"] == 0 and report["peaks_clamped_to_horizon_limit"] == 0
    assert max(r["window_end"] for r in rows) == H1_DATE
    writer_mod._validate_windows_within_horizon(rows)
    # an ordinary located peak is NOT qualified: ordinary basis, no qualification block
    assert report["horizon_limited_rows"] == 0
    assert {r["peak_basis"] for r in rows} == {sb.PEAK_BASIS}
    assert all("horizon_limited_sample" not in r["suppression_state"] for r in rows)


# ── R2: refined peaks stay strictly inside the horizon ───────────────────────

def test_r2_a_sun_contact_centred_exactly_on_the_excluded_end_does_not_abort():
    """Sun contact whose exact centre is precisely h1; target 300°, 1°/day, orb 5°. Codex's
    table: era 04-13..04-18 peak 04-17; month peak 04-18; day row 04-18 — and the writer
    raised HorizonViolation."""
    eps, pos = _produce(speed=1.0, centre_offset_days=0.0)
    assert len(eps) == 1
    _contacts, rows, report = _project(eps, pos)
    assert {r["resolution"] for r in rows} >= {"era", "month", "day"}, \
        "the legitimate interval must keep its month/day family"
    for r in rows:
        assert r["peak_date"] < H1_DATE, (r["resolution"], r["peak_date"])
        if r["resolution"] in ("month", "day"):
            assert r["window_start"] < H1_DATE, (r["resolution"], r["window_start"])
    assert report["peaks_clamped_to_horizon_limit"] >= 1     # recorded, never implied
    writer_mod._validate_windows_within_horizon(rows)         # no HorizonViolation
    # ASTRA v1.3: the clamped month/day rows are qualified; the era row (its peak is a real sample) is not
    by_tier = {t: [r for r in rows if r["resolution"] == t] for t in ("era", "month", "day")}
    assert all(r["peak_basis"] == sb.PEAK_BASIS for r in by_tier["era"])
    assert all("horizon_limited_sample" not in r["suppression_state"] for r in by_tier["era"])
    for r in by_tier["month"] + by_tier["day"]:
        assert r["peak_basis"] == sb.PEAK_BASIS_HORIZON_LIMITED
        q = r["suppression_state"]["horizon_limited_sample"]
        assert q["reason"] == "refined_peak_reached_the_excluded_end"
        assert q["attained_extremum"] is False
        assert q["selected_instant_utc"] < q["excluded_horizon_end_utc"]
    assert report["horizon_limited_rows"] == len(by_tier["month"]) + len(by_tier["day"])


# ── R1 and R2 together (they pull against each other) ────────────────────────

def test_r1_and_r2_in_one_projection_both_hold():
    eps_a, pos_a = _produce(speed=0.5, centre_offset_days=9.5)   # R1 geometry
    eps_b, pos_b = _produce(speed=1.0, centre_offset_days=0.0)   # R2 geometry
    # two different synthetic Suns cannot share one position accessor; project each class
    # context against its own contacts and validate the UNION of rows through the writer
    _ca, rows_a, rep_a = _project(eps_a, pos_a)
    _cb, rows_b, rep_b = _project(eps_b, pos_b)
    assert rows_a and rows_b
    assert rep_a["final_edge_components"] == 1 and rep_b["peaks_clamped_to_horizon_limit"] >= 1
    writer_mod._validate_windows_within_horizon(rows_a + rows_b)


def test_the_stand_in_is_in_domain_and_never_below_the_interval_start():
    h = 100.0
    assert sb.in_domain_peak_stand_in(h, 50.0) == pytest.approx(h - sb.HORIZON_EDGE_EPS_DAYS)
    assert sb.in_domain_peak_stand_in(h, 50.0) < h
    # an interval that opens inside the bisection tolerance of h1 keeps its own start
    assert sb.in_domain_peak_stand_in(h, h - 1e-6) == h - 1e-6
    assert sb.in_domain_peak_stand_in(h, h - 1e-6) < h


# ── the same R1 geometry through the REAL ledger on a disposable PostgreSQL ──

def test_r1_through_the_real_ledger_and_fetch_on_a_disposable_pg(pg, pg_dict):
    """Producer → `ledger.write_contacts` (real INSERT, real constraints) →
    `fetch_contacts` (real SELECT, dict rows) → projection → the writer's validator."""
    eps, pos = _produce(speed=0.5, centre_offset_days=9.5)
    ep = eps[0]
    d = {**_episode("Sun", _dt(ep.t_in)),
         "t_in": _dt(ep.t_in), "t_exact": None, "t_out": _dt(ep.t_out),
         "exact_crossing": False, "truncated_at_horizon": ep.truncated_at_horizon,
         "target_longitude_deg": TARGET_DEG, "orb_max_deg": ORB_DEG,
         "orb_source": "orb_conj_slow"}
    writer_mod._validate_episodes_within_horizon([d])
    cid, _ = _seed_manifest(pg_dict, CHART_UUID)
    writer_mod.ledger.write_contacts(pg_dict, CHART_UUID, "4.1", cid, [d], "a25pg-r1", bodies=["Sun"])
    pg_dict.commit()
    contacts = [dict(c, _primitive=sb.RELATION_TO_PRIMITIVE[c["relation"]])
                for c in sb.fetch_contacts(pg_dict, CHART_UUID, "4.1")]
    assert len(contacts) == 1 and contacts[0]["_t_exact_jd"] is None
    rows, report = sb.project_class_windows(
        _class_ctx(), contacts, (_H0, _H1), lambda jd: {"factor_by_body": {}}, planet_pos_fn=pos)
    assert rows and report["final_edge_components"] == 1
    writer_mod._validate_windows_within_horizon(rows)


# ── ASTRA v1.3 amendment 1: the stand-in is disclosed in PERSISTED rows and in the governed
#    writer's own audit output (not only in the projection's class report) ─────────────────

from pipeline.orchestrator.writers import SubStep  # noqa: E402

from .test_a25_v41_candidate_writer_pg import _ctx, _seed_windows_inputs  # noqa: E402,F401


def _patch_writer_seams(monkeypatch, pos_fn):
    """Only two seams are replaced, both documented: the per-class PERMISSION context (so the
    synthetic Sun is licensed — whether the real permission systems admit a synthetic geometry is
    not what is under test) and the planet-position accessor. Everything else is the real chain:
    ledger rows → fetch_contacts → project_windows_core → write_windows → the writer's notes."""
    step06a, step06b = writer_mod.step06a_context, writer_mod.step06b_windows
    monkeypatch.setattr(step06a, "build_all_class_contexts",
                        lambda swe, conn, chart, generation: ({"marriage": {"stub": True}}, [], 0))
    monkeypatch.setattr(
        step06b, "build_projection_class_context",
        lambda conn, chart, cls_name, ctx_dict, all_contexts, **kw: step06b.ClassContext(
            "marriage", [0.9], {s: True for s in leg.PERMISSION_SYSTEM_IDS},
            weight_by_target_ref={"SUN": 0.9}))
    monkeypatch.setattr(step06b, "_default_planet_pos_fn", lambda: pos_fn)


def _write_contact(pg_dict, ep):
    d = {**_episode("Sun", _dt(ep.t_in)),
         "t_in": _dt(ep.t_in), "t_exact": _dt(ep.t_exact) if ep.t_exact is not None else None,
         "t_out": _dt(ep.t_out), "exact_crossing": ep.t_exact is not None,
         "truncated_at_horizon": ep.truncated_at_horizon,
         "target_longitude_deg": TARGET_DEG, "orb_max_deg": ORB_DEG, "orb_source": "orb_conj_slow"}
    writer_mod._validate_episodes_within_horizon([d])
    cid, _ = _seed_manifest(pg_dict, CHART_UUID)
    writer_mod.ledger.write_contacts(pg_dict, CHART_UUID, "4.1", cid, [d], "a25pg-disclosure", bodies=["Sun"])
    pg_dict.commit()


def _persisted_windows(pg_dict):
    return pg_dict.execute(
        "SELECT resolution, peak_basis, peak_date, suppression_state -> 'horizon_limited_sample' AS limited"
        " FROM kala_gochara_windows WHERE chart_id = %s AND generation = '4.1' ORDER BY resolution",
        (CHART_ID,)).fetchall()


def test_r1_stand_in_is_disclosed_in_the_persisted_row_and_the_governed_writers_notes(pg, pg_dict, monkeypatch):
    eps, pos = _produce(speed=0.5, centre_offset_days=9.5)
    _write_contact(pg_dict, eps[0])
    _seed_windows_inputs(pg, CHART_ID)
    _patch_writer_seams(monkeypatch, pos)
    res = writer_mod.GocharaV41CandidateWriter().run_substep(
        _ctx(pg_dict, CHART_UUID), SubStep(key="windows", label="w"))
    pg_dict.commit()

    rows = _persisted_windows(pg_dict)
    assert [r["resolution"] for r in rows] == ["era"], rows
    (row,) = rows
    assert row["peak_basis"] == sb.PEAK_BASIS_HORIZON_LIMITED
    assert row["peak_date"] == date(2026, 4, 17)
    q = row["limited"]                                      # jsonb -> dict, read back from PostgreSQL
    assert q["kind"] == "horizon_limited_sample" and q["attained_extremum"] is False
    assert q["reason"] == "only_above_threshold_sample_is_the_horizon_limit"
    assert q["excluded_horizon_end_utc"] == "2026-04-18T00:00:00+00:00"
    assert q["selected_instant_utc"] < q["excluded_horizon_end_utc"]
    assert q["offset_from_excluded_end_seconds"] == pytest.approx(8.64, abs=0.01)
    assert q["substitution_rule"] and "supremum lies at the excluded end" in q["substitution_rule"]
    # the governed writer's own audit output carries the counters the class report used to drop
    assert "horizon_limited_rows=1" in res.notes
    assert "final_edge_components=1" in res.notes
    assert "peaks_clamped_to_horizon_limit=0" in res.notes
    assert f"horizon_limited_basis={sb.PEAK_BASIS_HORIZON_LIMITED}" in res.notes
    # a consumer can select exactly the qualified rows by the distinct basis alone
    assert pg_dict.execute(
        "SELECT count(*) AS n FROM kala_gochara_windows WHERE chart_id = %s AND generation = '4.1'"
        " AND peak_basis LIKE '%%:horizon_limited_sample'", (CHART_ID,)).fetchone()["n"] == 1


def test_r2_clamped_month_and_day_rows_are_disclosed_the_era_row_is_not(pg, pg_dict, monkeypatch, caplog):
    eps, pos = _produce(speed=1.0, centre_offset_days=0.0)
    _write_contact(pg_dict, eps[0])
    _seed_windows_inputs(pg, CHART_ID)
    _patch_writer_seams(monkeypatch, pos)
    with caplog.at_level("INFO"):
        res = writer_mod.GocharaV41CandidateWriter().run_substep(
            _ctx(pg_dict, CHART_UUID), SubStep(key="windows", label="w"))
    pg_dict.commit()

    by_tier = {r["resolution"]: r for r in _persisted_windows(pg_dict)}
    assert set(by_tier) == {"era", "month", "day"}
    assert by_tier["era"]["peak_basis"] == sb.PEAK_BASIS and by_tier["era"]["limited"] is None
    for tier in ("month", "day"):
        assert by_tier[tier]["peak_basis"] == sb.PEAK_BASIS_HORIZON_LIMITED
        assert by_tier[tier]["limited"]["reason"] == "refined_peak_reached_the_excluded_end"
        assert by_tier[tier]["peak_date"] < H1_DATE
    assert "horizon_limited_rows=2" in res.notes and "peaks_clamped_to_horizon_limit=1" in res.notes
    # …and in the writer's log line
    assert any("horizon_limited_rows=2" in r.getMessage() and "peaks_clamped_to_horizon_limit=1" in r.getMessage()
               for r in caplog.records)


def test_an_ordinary_interior_peak_is_persisted_unqualified(pg, pg_dict, monkeypatch):
    eps, pos = _produce(speed=1.0, centre_offset_days=-3.0)
    _write_contact(pg_dict, eps[0])
    _seed_windows_inputs(pg, CHART_ID)
    _patch_writer_seams(monkeypatch, pos)
    res = writer_mod.GocharaV41CandidateWriter().run_substep(
        _ctx(pg_dict, CHART_UUID), SubStep(key="windows", label="w"))
    pg_dict.commit()
    rows = _persisted_windows(pg_dict)
    assert rows and {r["peak_basis"] for r in rows} == {sb.PEAK_BASIS}
    assert all(r["limited"] is None for r in rows)
    assert "horizon_limited_rows=0" in res.notes
