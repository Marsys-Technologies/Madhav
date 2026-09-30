"""ASTRA_REVIEW_A5_4 P1-3 — the §5 vedha interval gate on the '4.0'
projection path (GOCHARA_DESIGN_SPECS_v1_4 §5; FABLE #16/#17/#25, N4;
D-PG353).

The reviewer's executable probes against the pre-rework projection, which
still called the legacy whole-row DATE-grain PG353 multiplier: "a clean row
still yielded 0.85; an obstruction ending March 1 still yielded 0.70 on
April 1; duplicate identical roots yielded 0.49." Each is a mutation the
tests below catch. Every test is pure arithmetic over T0-8-shaped overlay
rows (the ka_vedha_gochara writer's jsonb detail) — no Swiss, no DB.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from .test_step06b_windows_projection import (  # noqa: E402
    WRITER_PATH, _clean_overlay_row, _ctx, _open_gates)
from .test_step06b_angular_m1 import _contact, T_EXACT, _load_writer  # noqa: E402
from services.gochara_kernel import legacy_semantics as leg  # noqa: E402

w = _load_writer()

JD_2025_01_01 = w.jd_of(__import__("datetime").datetime(2025, 1, 1, tzinfo=w.UTC))


def _jd(iso: str) -> float:
    from datetime import datetime
    return w.jd_of(datetime.fromisoformat(iso + "T12:00:00+00:00"))


def _interval(body, t_in, t_out, *, state="active", group=None, segments=None):
    return {"obstructor_body": body, "t_in": t_in, "t_out": t_out,
            "half_open": True, "state": state, "exception": "none",
            "independence_group": group or f"ig:{body}:{t_in}",
            "segments": segments or [{"start": t_in, "end": t_out, "state": state}],
            "operator_role": "scored", "provenance": "verse_cited"}


def _parked_contact(cid, body, target=100.0, weight_ref="Venus"):
    c = _contact(cid, JD_2025_01_01 - 400.0, JD_2025_01_01, JD_2025_01_01 + 800.0,
                 target=target, body=body)
    c["target_ref"] = weight_ref
    return c


def _activity(contacts, gate, t_jd, weights):
    ctx = _ctx(weights_by_ref=weights)
    pos = lambda b, jd: 100.0  # noqa: E731 — every body parked on its target
    return w.make_eval_fn(ctx, contacts, gate, planet_pos_fn=pos)(t_jd)


# ── the legacy multiplier the projection no longer calls (for contrast) ──────

def _legacy_factor(rows, date_iso):
    return leg.compute_quality_gates(rows, date_iso, date_iso, {1: "agitation"})[0]


# ── 1. clean row: 1.0, not 0.85 ─────────────────────────────────────────────

def test_clean_covered_row_is_clear_factor_one():
    gate = w.make_vedha_gate([_clean_overlay_row("Sun", start="2025-01-01",
                                                 end="2025-06-01")])
    g = gate(_jd("2025-02-01"))
    assert g["state"] == "clear" and g["factor"] == 1.0
    assert g["factor_by_body"] == {} and g["fired"] == []
    # the legacy multiplier on the same row (malefic_count 0 ⇒ the
    # VEDHA_ZERO_MALEFIC_FACTOR 0.85) — the reviewer's "clean row 0.85"
    legacy_row = {"window_start": "2025-01-01", "window_end": "2025-06-01",
                  "vedha_kind": "house_vedha", "graha": "Sun",
                  "detail": {"malefic_count": 0}, "classical_citation": None}
    assert _legacy_factor([legacy_row], "2025-02-01") < 1.0
    # and λ is bitwise-identical to the open-gate evaluation
    c = _parked_contact("sun", "Sun")
    ev = _activity([c], gate, _jd("2025-02-01"), {"Venus": 0.8})
    ev_open = _activity([c], _open_gates, _jd("2025-02-01"), {"Venus": 0.8})
    assert ev["lambda_raw"] == ev_open["lambda_raw"]
    assert ev["quality_gates"] == 1.0


# ── 2. obstruction [Jan 1, Mar 1): clear on Mar 1 and Apr 1 ──────────────────

def _obstructed_sun_row(**kw):
    return _clean_overlay_row(
        "Sun", start="2025-01-01", end="2025-06-01",
        intervals=[_interval("Mars", "2025-01-01", "2025-03-01", **kw)])


def test_obstruction_ending_march_first_is_clear_on_april_first():
    gate = w.make_vedha_gate([_obstructed_sun_row()])
    assert gate(_jd("2025-02-01"))["state"] == "obstructed"
    assert gate(_jd("2025-03-01"))["state"] == "clear"    # half-open boundary day
    assert gate(_jd("2025-04-01"))["state"] == "clear"
    assert gate(_jd("2025-04-01"))["factor"] == 1.0
    # legacy: the row's window overlaps April ⇒ 0.70-class attenuation still applied
    legacy_row = {"window_start": "2025-01-01", "window_end": "2025-06-01",
                  "vedha_kind": "house_vedha", "graha": "Sun",
                  "detail": {"malefic_count": 1}, "classical_citation": None}
    assert _legacy_factor([legacy_row], "2025-04-01") < 1.0


def test_active_obstruction_without_cited_scale_is_structure_not_a_number():
    """D-PG353: no generalised PG353 attenuation. An active obstruction is
    reported (`obstructed`, the fired interval, rule provenance) with
    factor None → null_state omit: λ is unchanged, the state is on the row."""
    gate = w.make_vedha_gate([_obstructed_sun_row()])
    g = gate(_jd("2025-02-01"))
    assert g["state"] == "obstructed" and g["factor"] is None
    assert g["null_state"] == "omit" and "none_cited" in g["scale"]
    assert g["fired"][0]["primary_graha"] == "Sun"
    assert g["fired"][0]["fired"][0]["obstructor_body"] == "Mars"
    assert g["fired"][0]["rule"]["classical_citation"].startswith("Phaladipika")
    assert g["fired"][0]["primary_contact"]["primary_house"] == 3
    assert g["fired"][0]["rule"]["vedha_house"] == 9
    assert g["fired"][0]["primary_contact"]["residence"] == ["2025-01-01", "2025-06-01"]
    c = _parked_contact("sun", "Sun")
    ev = _activity([c], gate, _jd("2025-02-01"), {"Venus": 0.8})
    assert ev["lambda_raw"] == _activity([c], _open_gates, _jd("2025-02-01"),
                                         {"Venus": 0.8})["lambda_raw"]
    assert ev["quality_gates_detail"]["state"] == "obstructed"
    assert ev["quality_gates_detail"]["scoped_application"] == []


def test_inactive_and_cancelled_segments_never_attenuate():
    cancelled = _interval("Mars", "2025-01-01", "2025-03-01", state="cancelled_vipareeta")
    inactive = _interval("Saturn", "2025-01-01", "2025-03-01", state="inactive")
    gate = w.make_vedha_gate([_clean_overlay_row(
        "Sun", start="2025-01-01", end="2025-06-01", intervals=[cancelled, inactive])],
        cited_scale=lambda iv: 0.5)
    g = gate(_jd("2025-02-01"))
    assert g["state"] == "clear" and g["factor"] == 1.0


def test_vipareeta_carve_is_a_sub_interval_o_vi_4():
    iv = _interval("Mars", "2025-01-01", "2025-06-01", segments=[
        {"start": "2025-01-01", "end": "2025-02-15", "state": "active"},
        {"start": "2025-02-15", "end": "2025-03-15", "state": "cancelled_vipareeta"},
        {"start": "2025-03-15", "end": "2025-06-01", "state": "active"}])
    gate = w.make_vedha_gate([_clean_overlay_row(
        "Sun", start="2025-01-01", end="2025-06-01", intervals=[iv])],
        cited_scale=lambda iv: 0.5)
    assert gate(_jd("2025-02-01"))["state"] == "obstructed"
    assert gate(_jd("2025-03-01"))["state"] == "clear"     # inside the carve
    assert gate(_jd("2025-04-01"))["state"] == "obstructed"


# ── 3. duplicate roots attenuate once (0.7, not 0.49) ───────────────────────

def test_duplicate_identical_roots_attenuate_once_with_a_cited_scale():
    dup = [_interval("Mars", "2025-01-01", "2025-03-01", group="root-1"),
           _interval("Mars", "2025-01-01", "2025-03-01", group="root-1")]
    gate = w.make_vedha_gate([_clean_overlay_row(
        "Sun", start="2025-01-01", end="2025-06-01", intervals=dup)],
        cited_scale=lambda iv: 0.7)
    g = gate(_jd("2025-02-01"))
    assert g["factor_by_body"] == {"Sun": pytest.approx(0.7)}
    assert g["factor"] == pytest.approx(0.7)
    assert g["factor"] != pytest.approx(0.49)
    # two DISTINCT roots do multiply (positive control)
    two = [_interval("Mars", "2025-01-01", "2025-03-01", group="root-1"),
           _interval("Saturn", "2025-01-01", "2025-03-01", group="root-2")]
    gate2 = w.make_vedha_gate([_clean_overlay_row(
        "Sun", start="2025-01-01", end="2025-06-01", intervals=two)],
        cited_scale=lambda iv: 0.7)
    assert gate2(_jd("2025-02-01"))["factor_by_body"]["Sun"] == pytest.approx(0.49)


# ── 4. coverage: unavailable, never a clean 1.0 ──────────────────────────────

def test_empty_overlay_is_unavailable_not_clean():
    gate = w.make_vedha_gate([])
    g = gate(_jd("2025-02-01"))
    assert g["state"] == "unavailable" and g["factor"] is None
    assert g["coverage"] == {"overlay": "kala_vedha_gochara", "computed": False,
                             "covers_instant": False}
    assert g["null_state"] == "omit"


def test_instant_outside_computed_horizon_is_unavailable():
    gate = w.make_vedha_gate([_clean_overlay_row("Sun", start="2025-01-01",
                                                 end="2025-06-01")])
    g = gate(_jd("2025-09-01"))
    assert g["state"] == "unavailable" and g["factor"] is None
    assert g["coverage_horizons"] == [["2025-01-01", "2025-06-01"]]
    assert g["coverage"]["covers_instant"] is False and "gap" in g["reason"]
    assert gate(_jd("2025-05-31"))["state"] == "clear"
    assert gate(_jd("2025-06-01"))["state"] == "unavailable"  # half-open horizon


def test_unavailable_state_reaches_the_window_row():
    ctx = _ctx(weights_by_ref={"Venus": 0.8})
    c = _parked_contact("sun", "Sun")
    rows, _ = w.project_class_windows(
        ctx, [c], (JD_2025_01_01 - 5.0, JD_2025_01_01 + 5.0), w.make_vedha_gate([]),
        planet_pos_fn=lambda b, jd: 100.0)
    assert rows
    for r in rows:
        assert r["suppression_state"]["quality_gates_detail"]["state"] == "unavailable"
        assert any(s.startswith("vedha:unavailable") for s in r["contributing_systems"])


def test_legacy_shape_rows_are_ignored_never_pg353():
    legacy_row = {"window_start": "2025-01-01", "window_end": "2025-06-01",
                  "vedha_kind": "house_vedha", "graha": "Sun",
                  "detail": {"malefic_count": 2}, "classical_citation": None}
    gate = w.make_vedha_gate([legacy_row])
    g = gate(_jd("2025-02-01"))
    assert g["state"] == "unavailable" and g["legacy_shape_rows_ignored"] == 1
    assert w.parse_vedha_overlay_rows([legacy_row])["rows"] == []


# ── 5. scoped to the primary graha ──────────────────────────────────────────

def test_obstruction_scopes_to_the_primary_grahas_own_contacts():
    """A Venus-primary obstruction attenuates Venus's contacts only; Saturn's
    contact is untouched. The legacy gate multiplied the whole class λ."""
    gate = w.make_vedha_gate([_clean_overlay_row(
        "Venus", start="2025-01-01", end="2025-06-01",
        intervals=[_interval("Mars", "2025-01-01", "2025-03-01")])],
        cited_scale=lambda iv: 0.5)
    ven = _parked_contact("ven", "Venus", weight_ref="Venus")
    sat = _parked_contact("sat", "Saturn", target=200.0, weight_ref="Saturn")
    ctx = _ctx(weights_by_ref={"Venus": 1.0, "Saturn": 1.0})
    pos = lambda b, jd: {"Venus": 100.0, "Saturn": 200.0}[b]  # noqa: E731
    ev = w.make_eval_fn(ctx, [sat], gate, planet_pos_fn=pos)(_jd("2025-02-01"))
    assert ev["activity"] == pytest.approx(1.0)  # Saturn untouched
    assert ev["quality_gates_detail"]["scoped_application"] == []
    ev_v = w.make_eval_fn(ctx, [ven], gate, planet_pos_fn=pos)(_jd("2025-02-01"))
    assert ev_v["activity"] == pytest.approx(0.5)  # Venus halved
    assert ev_v["quality_gates_detail"]["scoped_application"][0]["contact_id"] == "ven"
    assert ev_v["quality_gates"] == pytest.approx(0.5)
    ev_both = w.make_eval_fn(ctx, [ven, sat], gate, planet_pos_fn=pos)(_jd("2025-02-01"))
    assert ev_both["activity"] == pytest.approx(1.0 - 0.5 * 0.0)  # 1 − (1−1)(1−0.5)


# ── 6. Moon-primary rows: P6 testimony, day-row annotation only ─────────────

def test_moon_vedha_is_testimony_annotating_day_rows_only():
    moon_row = _clean_overlay_row(
        "Moon", start="1900-01-01", end="2100-01-01", operator_role="testimony",
        intervals=[_interval("Saturn", "1900-01-01", "2100-01-01")])
    gate = w.make_vedha_gate([moon_row], cited_scale=lambda iv: 0.5)
    g = gate(JD_2025_01_01)
    assert g["state"] == "clear" and g["factor_by_body"] == {}
    assert g["annotations"] and g["annotations"][0]["operator_role"] == "testimony"
    ctx = _ctx(weights_by_ref={"Venus": 0.8})
    c = _contact("moon", JD_2025_01_01 - 10.0, JD_2025_01_01, JD_2025_01_01 + 10.0,
                 body="Moon")
    # linear motion through the target: a peaked λ curve so month/day rows exist
    rows, _ = w.project_class_windows(
        ctx, [c], (JD_2025_01_01 - 30.0, JD_2025_01_01 + 30.0), gate,
        planet_pos_fn=lambda b, jd: (100.0 + 0.5 * (jd - JD_2025_01_01)) % 360.0)
    tiers = {r["resolution"]: r for r in rows}
    assert {"era", "month", "day"} <= set(tiers)
    for tier in ("era", "month"):
        d = tiers[tier]["suppression_state"]["quality_gates_detail"]
        assert d["annotations"] == [] and d["annotations_withheld_for_tier"] == 1
    d_day = tiers["day"]["suppression_state"]["quality_gates_detail"]
    assert len(d_day["annotations"]) == 1 and d_day["annotations_withheld_for_tier"] is None
    # never a factor: the Moon contact's activity is untouched
    assert tiers["day"]["suppression_state"]["quality_gates"] == 1.0


def test_projection_no_longer_calls_the_legacy_whole_row_multiplier():
    import inspect
    src = inspect.getsource(w)
    assert "compute_quality_gates(" not in src
    assert "make_vedha_gate(vedha_rows)" in inspect.getsource(w.main)



# ── ASTRA v1.1 P1-3: the SHARED v3 engine, on ACTUAL writer payloads ─────────

import dataclasses  # noqa: E402
from datetime import date  # noqa: E402

from services.gochara_v3.context import VedhaRow  # noqa: E402
from services.gochara_v3 import engine as E  # noqa: E402
from services.ka_vedha_gochara import writer as W, logic as L, gate as VG  # noqa: E402


def _writer_row(graha, res_start, res_end, occupants=(), *, companions=(),
                horizon=("2025-01-01", "2026-01-01"), as_vedha_row=True):
    """A kala_vedha_gochara row built by the WRITER's own pure detail
    builder (_house_vedha_detail) over logic.build_obstruction_intervals /
    carve_vipareeta — the actual T0-8 payload shape."""
    p_in, p_out = date.fromisoformat(res_start), date.fromisoformat(res_end)
    ivs = L.build_obstruction_intervals(
        p_in, p_out, [(b, date.fromisoformat(a), date.fromisoformat(z)) for b, a, z in occupants])
    for iv in ivs:
        iv["vipareeta_companions"] = L.carve_vipareeta(
            iv, [(g, date.fromisoformat(a), date.fromisoformat(z)) for g, a, z in companions])
        iv["intensity_qualifier"] = None
        iv["independence_group"] = f"ig:{iv['obstructor_body']}:{iv['t_in'].isoformat()}"
    detail = W._house_vedha_detail(
        upstream_fp={"fixture": True}, graha=graha,
        run={"sign_idx": 2, "start_date": p_in, "end_date": p_out},
        house=3, vedha_house=9, vedha_sign_idx=8,
        rule={"phala": "gain"}, uncited=False, intervals=ivs, excepted=[],
        horizon_start=date.fromisoformat(horizon[0]),
        horizon_end=date.fromisoformat(horizon[1]))
    row = {"vedha_kind": "house_vedha", "graha": graha, "window_start": res_start,
           "window_end": res_end, "classical_citation": "Phaladipika Adh. XXVI, Sloka 3",
           "detail": detail, "formula_version": W.FORMULA_VERSION}
    if as_vedha_row:
        return VedhaRow(**row)
    return row


def _engine_gate(rows, iso):
    ctx = type("Ctx", (), {"vedha_rows": tuple(rows), "malefic_scale": ()})()
    return E._compute_quality_gates_from_context(ctx, iso, iso, instant_date_iso=iso)


def test_engine_clean_writer_row_is_one_not_0_85():
    q, d = _engine_gate([_writer_row("Sun", "2025-01-01", "2025-06-01")], "2025-02-01")
    assert q == 1.0 and d["state"] == "clear" and d["factor"] == 1.0
    assert d["vedha_fired_count"] == 0 and d["fired_vedha"] == []
    assert d["fired_vedha"] == d["fired"]


def test_engine_expired_obstruction_is_clear_on_april_first_not_0_70():
    row = _writer_row("Sun", "2025-01-01", "2025-06-01",
                      occupants=[("Mars", "2025-01-01", "2025-03-01")])
    assert row.detail["vedha_intervals"][0]["state"] == "active"
    assert _engine_gate([row], "2025-02-01")[1]["state"] == "obstructed"
    assert _engine_gate([row], "2025-03-01")[1]["state"] == "clear"
    q, d = _engine_gate([row], "2025-04-01")
    assert q == 1.0 and d["state"] == "clear" and d["factor"] == 1.0
    # the obstructed instant: structure with identity, factor None, product 1.0
    q2, d2 = _engine_gate([row], "2025-02-01")
    assert q2 == 1.0 and d2["factor"] is None and d2["null_state"] == "omit"
    f = d2["fired_vedha"][0]
    assert f["primary_contact"] == {"graha": "Sun", "primary_house": 3,
                                    "primary_sign_name": "Gemini",
                                    "residence": ["2025-01-01", "2025-06-01"]}
    assert f["rule"]["formula_version"] == W.FORMULA_VERSION
    assert f["rule"]["classical_citation"].startswith("Phaladipika")
    assert f["fired"][0]["obstructor_body"] == "Mars"


def test_engine_duplicate_roots_attenuate_once_never_0_49():
    row = _writer_row("Sun", "2025-01-01", "2025-06-01",
                      occupants=[("Mars", "2025-01-01", "2025-03-01"),
                                 ("Mars", "2025-01-01", "2025-03-01")])
    ctx = type("Ctx", (), {"vedha_rows": (row,), "malefic_scale": ()})()
    g = VG.make_gate(list(ctx.vedha_rows), cited_scale=lambda iv: 0.7)(date(2025, 2, 1))
    assert g["factor_by_body"]["Sun"] == pytest.approx(0.7)
    # and without a cited scale the engine applies NO number at all
    q, d = _engine_gate([row], "2025-02-01")
    assert q == 1.0 and d["factor"] is None and d["factor_by_body"] == {}


def test_engine_vipareeta_carve_and_testimony_honoured():
    row = _writer_row("Sun", "2025-01-01", "2025-06-01",
                      occupants=[("Mars", "2025-01-01", "2025-06-01")],
                      companions=[("Jupiter", "2025-02-15", "2025-03-15")])
    seg_states = [s["state"] for s in row.detail["vedha_intervals"][0]["segments"]]
    assert seg_states == ["active", "cancelled_vipareeta", "active"]
    assert _engine_gate([row], "2025-03-01")[1]["state"] == "clear"   # inside the carve
    assert _engine_gate([row], "2025-04-01")[1]["state"] == "obstructed"
    moon = _writer_row("Moon", "2025-01-01", "2025-06-01",
                       occupants=[("Saturn", "2025-01-01", "2025-06-01")])
    assert moon.detail["operator_role"] == "testimony"
    q, d = _engine_gate([moon], "2025-02-01")
    assert d["state"] == "clear" and d["fired_vedha"] == []
    assert d["annotations"][0]["operator_role"] == "testimony"


def test_engine_coverage_gap_between_horizons_is_unavailable():
    a = _writer_row("Sun", "2025-01-01", "2025-02-01", horizon=("2025-01-01", "2025-02-01"))
    b = _writer_row("Sun", "2025-04-01", "2025-05-01", horizon=("2025-04-01", "2025-05-01"))
    q, d = _engine_gate([a, b], "2025-03-01")
    assert d["state"] == "unavailable" and d["factor"] is None and "gap" in d["reason"]
    assert d["coverage_horizons"] == [["2025-01-01", "2025-02-01"], ["2025-04-01", "2025-05-01"]]
    assert _engine_gate([a, b], "2025-01-15")[1]["state"] == "clear"
    # the projection gate shares the evaluator: same verdict on the gap
    pg = w.make_vedha_gate([dataclasses.asdict(a), dataclasses.asdict(b)])
    assert pg(_jd("2025-03-01"))["state"] == "unavailable"
    assert pg(_jd("2025-04-15"))["state"] == "clear"


def test_engine_legacy_shape_rows_and_latta_rows_never_a_number():
    legacy = VedhaRow(vedha_kind="house_vedha", graha="Sun", window_start="2025-01-01",
                      window_end="2025-06-01", classical_citation=None,
                      detail={"malefic_count": 2})
    q, d = _engine_gate([legacy], "2025-02-01")
    assert q == 1.0 and d["state"] == "unavailable" and d["legacy_shape_rows_ignored"] == 1
    latta = VedhaRow(vedha_kind="latta", graha="Saturn", window_start="2025-01-01",
                     window_end="2025-06-01", classical_citation="Phaladipika PG338",
                     detail={"latta_nakshatra_idx": 4})
    q, d = _engine_gate([latta, _writer_row("Sun", "2025-01-01", "2025-06-01")], "2025-02-01")
    assert q == 1.0 and d["state"] == "clear"
    assert d["annotations"][0]["vedha_kind"] == "latta" and d["factor_by_body"] == {}


def test_engine_scoped_application_reaches_only_the_primarys_sentences():
    from services.gochara_grammar.models import ConfigurationSentence
    mk = lambda planet: ConfigurationSentence(  # noqa: E731
        primitive="degree_contact", chart_id="c", event_class="marriage",
        target_type="karaka", target_ref="Venus", transit_planet=planet,
        secondary_planet=None, event_jd=0.0, event_datetime_ist="x",
        temporal_shape="point", uncited_extension=True,
        detail={"orb_strength": 0.8})
    out, applied = VG.apply_scoped_factors([mk("Sun"), mk("Saturn")], {"Sun": 0.5})
    assert out[0].detail["orb_strength"] == pytest.approx(0.4)
    assert out[1].detail["orb_strength"] == pytest.approx(0.8)
    assert [a["transit_planet"] for a in applied] == ["Sun"]
    # the engine wires the gate BEFORE activity and applies it to sentences
    import inspect
    src = inspect.getsource(E._evaluate_single_from_context)
    assert src.index("_compute_quality_gates_from_context(") < src.index("_compute_activity_v3(")
    assert "apply_scoped_factors" in src


# ── the two evaluators that never reach '4.x' / '5.0' scoring ────────────────

def _production_sources():
    root = Path(__file__).resolve().parents[3]
    for sub in ("services", "scripts", "pipeline", "ga_writers"):
        for f in (root / sub).rglob("*.py"):
            if "/tests/" in str(f) or f.name.startswith("test_"):
                continue
            yield f


def test_legacy_semantics_quality_gates_has_no_production_caller():
    """legacy_semantics.compute_quality_gates is the pinned classification
    MIRROR of the retired engine multiplier; it is legacy-only — no
    production module calls it (the projection and the engine use the
    shared ka_vedha_gochara.gate). Proven by source scan; it is therefore
    not rewritten."""
    callers = [str(f) for f in _production_sources()
               if "compute_quality_gates(" in f.read_text()
               and not f.name == "legacy_semantics.py"]
    assert callers == [], callers


def test_kernel_overlays_quality_gates_at_has_no_production_caller():
    """gochara_kernel.overlays.quality_gates_at / OverlayInterval is the
    WP2 kernel design projection; production imports only its date_to_jd.
    Legacy-only by source scan — not rewritten."""
    users = []
    for f in _production_sources():
        if f.name == "overlays.py":
            continue
        txt = f.read_text()
        if "quality_gates_at(" in txt or "OverlayInterval(" in txt or "coverage_gaps(" in txt:
            users.append(str(f))
    assert users == [], users
