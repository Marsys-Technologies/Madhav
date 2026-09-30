"""A5.4 vedha_interval_relation — proof battery for the T0-8 repair of the
ka_vedha_gochara writer (FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0 N4, #16/#17/#25,
D-PG353; GOCHARA_DESIGN_SPECS_v1_4 §5).

Unit mirrors of oracles O-VI-1…O-VI-5 (GOCHARA_TEST_ORACLES_v1_3.json). The
literal-kind oracles (O-VI-2, O-VI-4) are mirrored on their exact literal
timestamps; the executable_at_A5.5 kinds (O-VI-1, O-VI-3, O-VI-5) are mirrored
here as pure-function mechanism checks — full-fixture execution is the later
A5.5 rehearsal.

Every test is pure-python (dates and dicts) or a direct call into the writer's
pure detail builder — no Swiss, no real DB. Each test names the pre-repair
mutation it would catch: whole-residence attenuation (N4), flag-flip
cancellation (O-VI-4), first-only obstruction (N4), attenuation on a
non-active state (#17), exception-pair obstruction (M-8 / O-VI-3), default-1.0
on missing coverage (#25 / O-VI-5), and the removed PG353 grade (D-PG353).
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.ka_vedha_gochara import logic as L  # noqa: E402
from services.ka_vedha_gochara import writer as W  # noqa: E402

D = date


def _day(iso: str) -> date:
    return date.fromisoformat(iso)


# ── O-VI-2 (literal): partial overlap → partial interval, half-open boundary ──

def test_ov2_partial_overlap_is_interval_not_residence_flag():
    """Primary residence [2025-01-01, 2025-06-01); obstruction covering
    [2025-01-01, 2025-03-01) only. Mutation caught: whole-residence
    attenuation (the N4 collapse)."""
    intervals = L.build_obstruction_intervals(
        _day("2025-01-01"), _day("2025-06-01"),
        [("Mars", _day("2025-01-01"), _day("2025-03-01"))],
    )
    assert len(intervals) == 1
    iv = intervals[0]
    assert (iv["t_in"], iv["t_out"]) == (_day("2025-01-01"), _day("2025-03-01"))
    assert iv["t_out"] < _day("2025-06-01")  # partial, NOT the whole residence
    assert iv["state"] == L.STATE_ACTIVE


def test_ov2_boundary_day_is_clean_half_open():
    """The boundary day 2025-03-01 belongs to the CLEAN interval (R3 half-open
    convention). Mutation caught: attenuating the boundary day."""
    intervals = L.build_obstruction_intervals(
        _day("2025-01-01"), _day("2025-06-01"),
        [("Mars", _day("2025-01-01"), _day("2025-03-01"))],
    )
    coverage = {"start": _day("2025-01-01"), "end": _day("2025-06-01")}
    scale = lambda _iv: 0.5  # noqa: E731 — synthetic cited-scale stand-in
    inside = L.attenuation_at(_day("2025-02-15"), intervals,
                              coverage=coverage, scale=scale)
    boundary = L.attenuation_at(_day("2025-03-01"), intervals,
                                coverage=coverage, scale=scale)
    after = L.attenuation_at(_day("2025-04-01"), intervals,
                             coverage=coverage, scale=scale)
    assert inside["state"] == "obstructed" and inside["factor"] == 0.5
    assert boundary["state"] == "clear" and boundary["factor"] == 1.0
    assert after["state"] == "clear" and after["factor"] == 1.0


# ── O-VI-4 (literal): vipareeta carves a sub-interval, remainder stays active ──

def test_ov4_vipareeta_carves_sub_interval():
    """Obstruction [2025-01-01, 2025-06-01); vipareeta companionship
    [2025-02-15, 2025-03-15) strictly inside. Mutation caught: flag-flip
    cancellation (whole row inactive/cancelled)."""
    intervals = L.build_obstruction_intervals(
        _day("2025-01-01"), _day("2025-06-01"),
        [("Mars", _day("2025-01-01"), _day("2025-06-01"))],
    )
    companions = L.carve_vipareeta(
        intervals[0], [("Jupiter", _day("2025-02-15"), _day("2025-03-15"))])
    assert companions == ["Jupiter"]
    iv = intervals[0]
    assert iv["state"] == L.STATE_ACTIVE  # NOT fully cancelled
    assert iv["segments"] == [
        {"start": _day("2025-01-01"), "end": _day("2025-02-15"),
         "state": L.STATE_ACTIVE},
        {"start": _day("2025-02-15"), "end": _day("2025-03-15"),
         "state": L.STATE_CANCELLED_VIPAREETA},
        {"start": _day("2025-03-15"), "end": _day("2025-06-01"),
         "state": L.STATE_ACTIVE},
    ]
    coverage = {"start": _day("2025-01-01"), "end": _day("2025-06-01")}
    scale = lambda _iv: 0.5  # noqa: E731
    # attenuation outside the carve, none inside it
    assert L.attenuation_at(_day("2025-02-01"), intervals,
                            coverage=coverage, scale=scale)["factor"] == 0.5
    carved = L.attenuation_at(_day("2025-03-01"), intervals,
                              coverage=coverage, scale=scale)
    assert carved["state"] == "clear" and carved["factor"] == 1.0
    assert L.attenuation_at(_day("2025-04-01"), intervals,
                            coverage=coverage, scale=scale)["factor"] == 0.5


def test_ov4_fully_carved_interval_reports_cancelled_vipareeta():
    intervals = L.build_obstruction_intervals(
        _day("2025-01-01"), _day("2025-06-01"),
        [("Mars", _day("2025-01-01"), _day("2025-06-01"))],
    )
    L.carve_vipareeta(
        intervals[0],
        [("Jupiter", _day("2024-12-01"), _day("2025-07-01"))])  # swallows it
    iv = intervals[0]
    assert iv["state"] == L.STATE_CANCELLED_VIPAREETA
    assert iv["segments"] == [
        {"start": _day("2025-01-01"), "end": _day("2025-06-01"),
         "state": L.STATE_CANCELLED_VIPAREETA},
    ]


# ── N4: a second obstructor yields a SECOND interval relation ────────────────

def test_n4_second_obstructor_not_dropped():
    """Mutation caught: first-obstruction-only recording."""
    intervals = L.build_obstruction_intervals(
        _day("2025-01-01"), _day("2025-06-01"),
        [("Mars", _day("2025-01-01"), _day("2025-03-01")),
         ("Saturn", _day("2025-02-01"), _day("2025-04-01"))],
    )
    assert [iv["obstructor_body"] for iv in intervals] == ["Mars", "Saturn"]
    assert (intervals[0]["t_in"], intervals[0]["t_out"]) == (
        _day("2025-01-01"), _day("2025-03-01"))
    assert (intervals[1]["t_in"], intervals[1]["t_out"]) == (
        _day("2025-02-01"), _day("2025-04-01"))


def test_n4_two_roots_one_independence_group_each_attenuate_once():
    """independence_group: one root attenuates once; duplicates never multiply.
    Two intervals sharing one group contribute ONE factor; two distinct groups
    contribute two."""
    intervals = L.build_obstruction_intervals(
        _day("2025-01-01"), _day("2025-06-01"),
        [("Mars", _day("2025-01-01"), _day("2025-06-01")),
         ("Saturn", _day("2025-01-01"), _day("2025-06-01"))],
    )
    coverage = {"start": _day("2025-01-01"), "end": _day("2025-06-01")}
    scale = lambda _iv: 0.5  # noqa: E731
    # distinct groups → 0.5 * 0.5
    intervals[0]["independence_group"] = "g1"
    intervals[1]["independence_group"] = "g2"
    assert L.attenuation_at(_day("2025-03-01"), intervals,
                            coverage=coverage, scale=scale)["factor"] == 0.25
    # same physical root (duplicated row) → attenuates ONCE, not twice
    intervals[1]["independence_group"] = "g1"
    assert L.attenuation_at(_day("2025-03-01"), intervals,
                            coverage=coverage, scale=scale)["factor"] == 0.5


# ── O-VI-1 / #17: attenuation requires state='active' at t ───────────────────

def test_ov1_inactive_and_cancelled_never_attenuate():
    """Mutation caught: attenuating on the inactive/cancelled row (#17's
    'inactive and cancelled vedhas still suppress')."""
    cancelled = L.build_obstruction_intervals(
        _day("2025-01-01"), _day("2025-06-01"),
        [("Mars", _day("2025-01-01"), _day("2025-06-01"))])[0]
    L.carve_vipareeta(cancelled, [("Jupiter", _day("2024-01-01"),
                                   _day("2026-01-01"))])
    inactive = dict(cancelled)
    inactive["state"] = L.STATE_INACTIVE
    active = L.build_obstruction_intervals(
        _day("2025-01-01"), _day("2025-06-01"),
        [("Saturn", _day("2025-01-01"), _day("2025-06-01"))])[0]
    coverage = {"start": _day("2025-01-01"), "end": _day("2025-06-01")}
    scale = lambda _iv: 0.5  # noqa: E731
    for iv in (cancelled, inactive):
        r = L.attenuation_at(_day("2025-03-01"), [iv],
                             coverage=coverage, scale=scale)
        assert r["state"] == "clear" and r["factor"] == 1.0
    control = L.attenuation_at(_day("2025-03-01"), [active],
                               coverage=coverage, scale=scale)
    assert control["state"] == "obstructed" and control["factor"] < 1.0


def test_17_no_obstruction_no_attenuation():
    """No active obstruction → no attenuation at all."""
    coverage = {"start": _day("2025-01-01"), "end": _day("2025-06-01")}
    r = L.attenuation_at(_day("2025-03-01"), [], coverage=coverage,
                         scale=lambda _iv: 0.5)
    assert r["state"] == "clear" and r["factor"] == 1.0


# ── O-VI-3 / M-8: exception pairs never obstruct ─────────────────────────────

def test_ov3_exception_pairs_produce_no_interval():
    assert L.exception_for_pair("Sun", "Saturn") == L.EXCEPTION_SUN_SATURN
    assert L.exception_for_pair("Saturn", "Sun") == L.EXCEPTION_SUN_SATURN
    assert L.exception_for_pair("Moon", "Mercury") == L.EXCEPTION_MOON_MERCURY
    assert L.exception_for_pair("Mercury", "Moon") == L.EXCEPTION_MOON_MERCURY
    assert L.exception_for_pair("Sun", "Mars") == L.EXCEPTION_NONE
    # The writer exception-filters BEFORE interval construction (M-8 order:
    # exceptions first, then vipareeta); an exception-pair occupancy therefore
    # yields no interval and no malefic count. Mirror that partition:
    occupants = [("Saturn", {"start": _day("2025-01-01"), "end": _day("2025-03-01")}),
                 ("Mars", {"start": _day("2025-02-01"), "end": _day("2025-04-01")})]
    effective = [(g, ov) for g, ov in occupants
                 if not L.is_mutual_exclusion("Sun", g)]
    excepted = [g for g, _ in occupants if L.is_mutual_exclusion("Sun", g)]
    assert excepted == ["Saturn"]
    intervals = L.build_obstruction_intervals(
        _day("2025-01-01"), _day("2025-06-01"),
        [(g, ov["start"], ov["end"] + timedelta(days=1))
         for g, ov in effective])
    assert [iv["obstructor_body"] for iv in intervals] == ["Mars"]  # control


# ── O-VI-5 / #25: absent overlay coverage reads unavailable, never 1.0 ───────

def test_ov5_absent_coverage_is_unavailable_not_1():
    """Mutation caught: default 1.0 on missing overlay."""
    intervals = L.build_obstruction_intervals(
        _day("2025-01-01"), _day("2025-06-01"),
        [("Mars", _day("2025-01-01"), _day("2025-06-01"))])
    r = L.attenuation_at(_day("2025-03-01"), intervals, coverage=None)
    assert r["state"] == "unavailable"
    assert r["factor"] is None
    assert r["factor"] != 1.0
    assert "coverage" in r  # coverage object, echoed (None when never computed)


def test_ov5_coverage_not_containing_t_is_unavailable():
    intervals = L.build_obstruction_intervals(
        _day("2025-01-01"), _day("2025-06-01"),
        [("Mars", _day("2025-01-01"), _day("2025-06-01"))])
    cov = {"start": _day("2026-07-29"), "end": _day("2027-11-01")}  # E2 window
    r = L.attenuation_at(_day("2025-03-01"), intervals, coverage=cov)
    assert r["state"] == "unavailable" and r["factor"] is None
    assert r["coverage"] is cov


def test_obstructed_without_cited_scale_reports_structure_not_number():
    """D-PG353: with no cited suppression scale, an active obstruction is
    reported as obstructed with factor=None — never an uncited 0.35."""
    intervals = L.build_obstruction_intervals(
        _day("2025-01-01"), _day("2025-06-01"),
        [("Mars", _day("2025-01-01"), _day("2025-06-01"))])
    r = L.attenuation_at(_day("2025-03-01"), intervals,
                         coverage={"start": _day("2025-01-01"),
                                   "end": _day("2025-06-01")})
    assert r["state"] == "obstructed" and r["factor"] is None
    assert r["fired"][0]["obstructor_body"] == "Mars"


# ── Writer-level: interval construction, detail payload, D-PG353 removal ─────

def _sign_run(sign_idx, start, end):
    return {"sign_idx": sign_idx, "start_date": start, "end_date": end,
            "start_truncated": False, "end_truncated": False}


def test_writer_builds_half_open_intervals_from_inclusive_runs():
    """The writer's sign runs are inclusive day ranges; the served interval is
    half-open [t_in, t_out) with t_out = last obstructed day + 1 (O-VI-2
    boundary at date grain)."""
    primary = _sign_run(2, _day("2025-01-01"), _day("2025-05-31"))
    runs = {
        "Sun": [primary],
        "Mars": [_sign_run(8, _day("2025-01-10"), _day("2025-02-20"))],
        "Saturn": [_sign_run(0, _day("2025-01-01"), _day("2025-06-01"))],
        "Jupiter": [_sign_run(2, _day("2025-02-01"), _day("2025-02-10"))],
    }
    effective = [("Mars", {"start": _day("2025-01-10"),
                           "end": _day("2025-02-20")})]
    intervals = W._build_house_vedha_intervals(
        graha="Sun", run=primary, vedha_sign_idx=8, effective=effective,
        sign_runs_by_graha=runs, retro_dates={})
    assert len(intervals) == 1
    iv = intervals[0]
    assert iv["t_in"] == _day("2025-01-10")
    assert iv["t_out"] == _day("2025-02-21")  # inclusive end + 1 day
    # Jupiter's companionship [02-01, 02-11) carves a sub-interval (N4: not
    # first-only — ALL companions carve; here the single companion suffices).
    assert iv["vipareeta_companions"] == ["Jupiter"]
    assert [s["state"] for s in iv["segments"]] == [
        L.STATE_ACTIVE, L.STATE_CANCELLED_VIPAREETA, L.STATE_ACTIVE]
    assert iv["segments"][1]["start"] == _day("2025-02-01")
    assert iv["segments"][1]["end"] == _day("2025-02-11")
    assert iv["independence_group"].startswith("sha256:")


def test_writer_multiple_companions_all_carve():
    primary = _sign_run(2, _day("2025-01-01"), _day("2025-05-31"))
    runs = {
        "Sun": [primary],
        "Jupiter": [_sign_run(2, _day("2025-02-01"), _day("2025-02-10"))],
        "Venus": [_sign_run(2, _day("2025-03-01"), _day("2025-03-10"))],
    }
    intervals = W._build_house_vedha_intervals(
        graha="Sun", run=primary, vedha_sign_idx=8,
        effective=[("Mars", {"start": _day("2025-01-01"),
                             "end": _day("2025-05-31")})],
        sign_runs_by_graha=runs, retro_dates={})
    iv = intervals[0]
    assert iv["vipareeta_companions"] == ["Jupiter", "Venus"]
    assert [s["state"] for s in iv["segments"]] == [
        L.STATE_ACTIVE, L.STATE_CANCELLED_VIPAREETA, L.STATE_ACTIVE,
        L.STATE_CANCELLED_VIPAREETA, L.STATE_ACTIVE]


def test_writer_retrograde_qualifier_per_interval_preserved():
    """M-8 (c) semantics preserved, now per interval (not first-obstructor)."""
    primary = _sign_run(2, _day("2025-01-01"), _day("2025-05-31"))
    runs = {"Sun": [primary]}
    intervals = W._build_house_vedha_intervals(
        graha="Sun", run=primary, vedha_sign_idx=8,
        effective=[("Mars", {"start": _day("2025-01-10"),
                             "end": _day("2025-02-20")})],
        sign_runs_by_graha=runs,
        retro_dates={"Mars": {_day("2025-02-01")}})  # inside the interval
    assert intervals[0]["intensity_qualifier"] == "retrograde_malefic"
    intervals = W._build_house_vedha_intervals(
        graha="Sun", run=primary, vedha_sign_idx=8,
        effective=[("Mars", {"start": _day("2025-01-10"),
                             "end": _day("2025-02-20")})],
        sign_runs_by_graha=runs,
        retro_dates={"Mars": {_day("2025-04-01")}})  # outside the interval
    assert intervals[0]["intensity_qualifier"] is None


def _detail(graha="Sun", intervals=None, citation="Phaladipika Adh. XXVI, Sloka 6"):
    return W._house_vedha_detail(
        upstream_fp={"algorithm": "sha256"},
        graha=graha,
        run=_sign_run(2, _day("2025-01-01"), _day("2025-05-31")),
        house=3, vedha_house=9, vedha_sign_idx=8,
        rule={"phala": "x", "classical_citation": citation},
        uncited=L.house_vedha_uncited_extension(citation),
        intervals=intervals or [],
        excepted=[],
        horizon_start=_day("2025-01-01"), horizon_end=_day("2025-06-01"),
    )


def test_detail_pg353_grade_removed_with_disclosure():
    """D-PG353: no grade application; the removal itself is recorded as data.
    Mutation caught: re-emitting malefic_effect_grade from the scale."""
    intervals = W._build_house_vedha_intervals(
        graha="Sun",
        run=_sign_run(2, _day("2025-01-01"), _day("2025-05-31")),
        vedha_sign_idx=8,
        effective=[("Mars", {"start": _day("2025-01-10"),
                             "end": _day("2025-02-20")})],
        sign_runs_by_graha={"Sun": []}, retro_dates={})
    detail = _detail(intervals=intervals)
    assert detail["malefic_count"] == 1
    assert detail["malefic_obstructing_grahas"] == ["Mars"]
    assert detail["malefic_effect_grade"] is None
    assert detail["malefic_scale_citation"] is None
    assert "malefic_grade_uncited_extension" not in detail
    assert detail["d_pg353"]["applied"] is False
    assert detail["d_pg353"]["ruling_ref"] == "D-PG353"


def test_detail_no_active_obstruction_no_attenuation():
    detail = _detail()  # no intervals at all
    assert detail["obstruction_active"] is False
    assert detail["attenuation"]["state_at_build"] == "clear"
    assert detail["attenuation"]["factor"] is None
    assert detail["suppression_factor"] is None
    assert detail["cancelled"] is False
    assert detail["independence_group"] is None


def test_detail_intervals_shape_and_single_root_group():
    intervals = W._build_house_vedha_intervals(
        graha="Sun",
        run=_sign_run(2, _day("2025-01-01"), _day("2025-05-31")),
        vedha_sign_idx=8,
        effective=[("Mars", {"start": _day("2025-01-10"),
                             "end": _day("2025-02-20")})],
        sign_runs_by_graha={"Sun": []}, retro_dates={})
    detail = _detail(intervals=intervals)
    iv = detail["vedha_intervals"][0]
    assert iv["t_in"] == "2025-01-10" and iv["t_out"] == "2025-02-21"
    assert iv["half_open"] is True and iv["exception"] == "none"
    assert iv["state"] == "active"
    assert iv["provenance"] == "verse_cited" and iv["operator_role"] == "scored"
    # one physical root → the row-level aggregate group is present
    assert detail["independence_group"] == iv["independence_group"]
    assert detail["coverage"]["state"] == "computed"
    # #25: the coverage object exists so absence can never read as 1.0
    assert detail["coverage"]["horizon_start"] == "2025-01-01"


def test_detail_two_roots_row_group_none_per_interval_authoritative():
    intervals = W._build_house_vedha_intervals(
        graha="Sun",
        run=_sign_run(2, _day("2025-01-01"), _day("2025-05-31")),
        vedha_sign_idx=8,
        effective=[("Mars", {"start": _day("2025-01-10"),
                             "end": _day("2025-02-20")}),
                   ("Rahu", {"start": _day("2025-03-01"),
                             "end": _day("2025-04-01")})],
        sign_runs_by_graha={"Sun": []}, retro_dates={})
    detail = _detail(intervals=intervals)
    assert len(detail["vedha_intervals"]) == 2
    assert detail["independence_group"] is None
    groups = {iv["independence_group"] for iv in detail["vedha_intervals"]}
    assert len(groups) == 2 and all(g.startswith("sha256:") for g in groups)


def test_detail_moon_primary_is_testimony_only():
    """S-04: Moon vedha is annotation-only (P6 testimony) — never scored."""
    detail = _detail(graha="Moon")
    assert detail["operator_role"] == "testimony"
    assert detail["ruling_ref"] == "S-04"
    sun = _detail(graha="Sun")
    assert sun["operator_role"] == "scored" and sun["ruling_ref"] is None


def test_detail_unsourced_rule_provenance_carries_ruling_ref():
    detail = _detail(citation="UNSOURCED — node house transit")
    assert detail["provenance"] == "uncited_extension"
    assert detail["ruling_ref"] == "N-14/F-29"


def test_grade_key_mapping_is_data_not_prose():
    """#16: the grade→key mapping is the served table's own primary key —
    an exact int-keyed dict lookup, not a prose name match. Retained as the
    key map only; NOT applied post-D-PG353."""
    scale = {1: {"effect_grade": "fear"}, 5: {"effect_grade": "ignominy"}}
    assert L.malefic_count_grade(1, scale)["effect_grade"] == "fear"
    assert L.malefic_count_grade(5, scale)["effect_grade"] == "ignominy"
    assert L.malefic_count_grade(3, scale) is None  # honest gap, never guessed
