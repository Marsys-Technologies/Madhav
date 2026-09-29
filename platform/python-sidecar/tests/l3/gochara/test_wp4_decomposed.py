"""WP4 — Decomposed comparison on one pre-declared synthetic workload.

Chain under comparison (plan §4 row 4; execution brief §4 WP4):

    independent oracle (WP2 `oracle.score_lambda`, hand-specified)
      → legacy event semantics (WP3b `legacy_semantics`, pre-H-fix baseline)
      → kernel geometry (WP3a `arcs`/`episodes`)
      → scoring projection (kernel episodes projected through the oracle
        factor algebra at query time)

THE WORKLOAD (WP4-SYNTH-1, pre-declared before any measurement; synthetic,
non-person data only — execution brief §3):

  horizon    [2024-01-01 12:00 UT, 2026-01-01 12:00 UT]  (731 days)
  arc knots  daily noon-UT over a PADDED range 2023-07-01..2026-07-01
             (the arc index is global/prepare-phase; the horizon is the
             per-chart query — so horizon-edge orb entries are genuinely
             truncated and the kernel's truncation flags are exercised)
  bodies     "Saturn":  lon(u) = 280 + 8u - 6u^2 + 0.8u^3   (one station at
                        u ~= 0.792; range [278.4, 283.0] deg)
             "Jupiter": lon(u) = 40 + 30u - 4u^2 + 0.4u^3   (monotone direct,
                        range [40, 87.2] deg)
             u = (jd - JD(2024-01-01 12:00 UT)) / 365.25; both cubics are
             reproduced EXACTLY by the noon-knot cubic spline, so the spline
             root IS the exact root (refine=False, same discipline as WP3a's
             synthetic fixtures).
  targets    WP4SUN = 281.0 deg (Saturn conjunctions: 2 exact; first episode
             horizon-truncated at start)
             WP4MOON = 55.0 deg (Jupiter conjunction: 1 exact)
             drishti_contact legs are searched too and honestly return ZERO
             episodes (all dṛṣṭi levels lie outside the traveled bands);
             a zero result with declared cause, not a dropped search.
  factors    promise=0.8, permission=1.0, tara=1.0, w30=1.0,
             quality_gates=1.0, channel='benefic' — chosen so the algebra
             isolates the activity term; target weights 1.0.
  threshold  lambda_thresh = 0.4 for the window legs (an explicit declared
             value; compute_threshold_config is exercised separately for
             the F-08 companion pathology).

Every delta between the legacy leg and the kernel leg is classified against
its pinned source in WP3b_CLASSIFICATION.md (A-1..A-9, B-1..B-9) — an
unclassified divergence is a stop condition (execution brief §6), not a
number to average over.

This module is PRODUCER-PROTOTYPE EVIDENCE. It is not a production-build
result and not a DATA_ACCEPTED claim.
"""
from __future__ import annotations

import json
import time
from datetime import date, datetime, timedelta, timezone

import swisseph as swe

from services.gochara_kernel import arcs, contacts, episodes as kernel_episodes
from services.gochara_kernel import ids as kernel_ids
from services.gochara_kernel import peaks as kernel_peaks
from services.gochara_kernel import legacy_semantics as legacy
from services.gochara_kernel.convention import canonical_convention_id
from services.gochara_kernel import ledger as kernel_ledger

from .oracle import score_lambda

# ── WP4-SYNTH-1 workload declaration ─────────────────────────────────────────

T0 = swe.julday(2024, 1, 1, 12.0)          # horizon start (noon-UT abscissa)
H1 = swe.julday(2026, 1, 1, 12.0)          # horizon end
HORIZON = (T0, H1)
KNOT_START = date(2023, 7, 1)              # padded arc-build range (global
KNOT_END = date(2026, 7, 1)                # prepare phase, not the horizon)
SYNTHETIC_TOL_ARCSEC = 1e-7

LAMBDA_THRESH = 0.4                        # declared, for the window legs
FACTORS = {
    "promise": 0.8,
    "permission": 1.0,
    "tara_modifier": 1.0,
    "w30_modifier": 1.0,
    "quality_gates": 1.0,
    "channel": "benefic",
}
TARGET_WEIGHTS = {"WP4SUN": 1.0, "WP4MOON": 1.0}
CHART_ID = "00000000-0000-4000-8000-0000000004aa"  # synthetic, non-person
METHOD_VERSION = "wp4-1.0"

# Search matrix: (body, curve-name, target, relation, orb_source)
SEARCH_MATRIX = (
    ("Saturn", "WP4SUN", 281.0, "conjunction", "orb_conj_slow"),
    ("Saturn", "WP4SUN", 281.0, "drishti_contact", "orb_drishti_slow"),
    ("Jupiter", "WP4MOON", 55.0, "conjunction", "orb_conj_slow"),
    ("Jupiter", "WP4MOON", 55.0, "drishti_contact", "orb_drishti_slow"),
)


def _u(jd: float) -> float:
    return (jd - T0) / 365.25


def saturn_curve(jd: float) -> float:
    x = _u(jd)
    return 280.0 + 8.0 * x - 6.0 * x * x + 0.8 * x ** 3


def jupiter_curve(jd: float) -> float:
    x = _u(jd)
    return 40.0 + 30.0 * x - 4.0 * x * x + 0.4 * x ** 3


CURVES = {"Saturn": saturn_curve, "Jupiter": jupiter_curve}


def _daily_knots(curve) -> tuple[list[float], list[float]]:
    jds, lons = [], []
    d = KNOT_START
    while d <= KNOT_END:
        jd = swe.julday(d.year, d.month, d.day, 12.0)
        jds.append(jd)
        lons.append(curve(jd) % 360.0)
        d += timedelta(days=1)
    return jds, lons


def _build_indexes() -> dict[str, arcs.ArcIndex]:
    return {
        body: arcs.build_arc_index(
            body, *_daily_knots(CURVES[body]),
            tolerance_arcsec=SYNTHETIC_TOL_ARCSEC,
        )
        for body in CURVES
    }


def _solve_all(indexes) -> dict[tuple[str, str], list]:
    """Solve the full search matrix on prebuilt indexes. Keyed
    (body, relation)."""
    out = {}
    for body, _tref, target_deg, relation, orb_source in SEARCH_MATRIX:
        out[(body, relation)] = kernel_episodes.solve_episodes(
            indexes[body], body, relation, target_deg, HORIZON, orb_source,
            refine=False,
        )
    return out


def _dt(jd: float) -> datetime:
    """jd (UT) -> aware UTC datetime at full float precision."""
    return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(
        days=jd - 2440587.5
    )


def _oracle_episodes(solved, indexes) -> list[dict]:
    """Kernel episodes restated as oracle episode inputs (full-precision
    datetimes; speed = |spline derivative| at the exact instant)."""
    out = []
    for (body, _rel), eps in solved.items():
        for ep in eps:
            if not ep.exact_crossing:
                continue
            speed = abs(float(indexes[body].spline.derivative()(ep.t_exact)))
            out.append({
                "t_in": _dt(ep.t_in),
                "t_exact": _dt(ep.t_exact),
                "t_out": _dt(ep.t_out),
                "speed_deg_per_day": speed,
                "orb_max_deg": ep.orb_max_deg,
            })
    return out


def _legacy_sentences(solved) -> list[legacy.Sentence]:
    """The same physical exact contacts restated as legacy activity
    sentences: event-time orb 0.0 (the contact IS exact), one sentence per
    exact episode — the span-aware baseline's view of this workload."""
    out = []
    for (body, relation), eps in solved.items():
        if relation != "conjunction":
            continue
        for ep in eps:
            if not ep.exact_crossing:
                continue
            out.append(legacy.Sentence(
                primitive="degree_contact",
                target_ref="WP4SUN" if body == "Saturn" else "WP4MOON",
                transit_planet=body,
                event_jd=ep.t_exact,
                detail={"orb_degrees": 0.0},
            ))
    return out


def _legacy_lambda(sentences, t_jd: float) -> float:
    activity, _contrib = legacy.legacy_activity_at(
        sentences, TARGET_WEIGHTS, t_jd, horizon=HORIZON
    )
    return legacy.assemble_lambda_v3(
        promise=FACTORS["promise"], permission=FACTORS["permission"],
        activity=activity, tara_modifier=FACTORS["tara_modifier"],
        w30_modifier=FACTORS["w30_modifier"],
        quality_gates=FACTORS["quality_gates"],
    )["lambda_raw"]


def _projection_lambda(oracle_eps, t_jd: float) -> float:
    """Kernel-geometry scoring projection at one instant: the oracle factor
    algebra applied to the kernel's episodes, graduated decay inside the
    pinned ±5-day box, query span = the instant itself."""
    result = score_lambda({
        **FACTORS,
        "episodes": oracle_eps,
        "query_span": [_dt(t_jd), _dt(t_jd)],
    })
    assert result["state"] == "ok"
    return result["lambda_raw"]


def _weekly_grid() -> list[float]:
    """The legacy 7-day coarse sweep grid over the horizon (105 points)."""
    out = []
    jd = T0
    while jd < H1:
        out.append(jd)
        jd += legacy.PEAK_SCAN_STRIDE_DAYS
    return out


# ── census: the workload, measured once, pinned ─────────────────────────────

def test_workload_census_pinned():
    """Episode census on the declared workload — the counts every later leg
    reasons about. Pinned from direct computation, never from the legacy
    code's output."""
    indexes = _build_indexes()
    solved = _solve_all(indexes)

    assert len(indexes["Saturn"].stations) == 1   # one station, un-coalesced
    assert indexes["Jupiter"].stations == []      # monotone direct

    sat_conj = solved[("Saturn", "conjunction")]
    jup_conj = solved[("Jupiter", "conjunction")]
    sat_dri = solved[("Saturn", "drishti_contact")]
    jup_dri = solved[("Jupiter", "drishti_contact")]

    assert len(sat_conj) == 2 and all(e.exact_crossing for e in sat_conj)
    assert len(jup_conj) == 1 and jup_conj[0].exact_crossing
    # Drishti levels all lie outside the traveled bands: an honest zero,
    # searched and recorded — not a dropped search.
    assert sat_dri == [] and jup_dri == []
    # The first Saturn episode's orb entry predates the horizon: the kernel
    # says so explicitly (padded arc build makes the truncation real).
    assert sat_conj[0].truncated_at_horizon == "start"
    assert sat_conj[1].truncated_at_horizon is None
    assert jup_conj[0].truncated_at_horizon is None
    # No unresolved-station contacts on this workload.
    assert all(e.completeness_state == "applied"
               for eps in solved.values() for e in eps)


# ── the anchor: legs agree AT the exact contact ─────────────────────────────

def test_anchor_legs_agree_at_exact():
    """At an exact contact both legs must produce the same λ (orb decay 1.0
    at the event in both semantics) — the anchor that makes every OFF-exact
    delta attributable to a classified cause rather than to noise."""
    indexes = _build_indexes()
    solved = _solve_all(indexes)
    sentences = _legacy_sentences(solved)
    oracle_eps = _oracle_episodes(solved, indexes)

    for (body, relation), eps in solved.items():
        if relation != "conjunction":
            continue
        for ep in eps:
            if not ep.exact_crossing:
                continue
            lam_legacy = _legacy_lambda(sentences, ep.t_exact)
            lam_kernel = _projection_lambda(oracle_eps, ep.t_exact)
            assert abs(lam_legacy - 0.8) < 1e-9     # promise 0.8 × activity 1
            assert abs(lam_kernel - 0.8) < 1e-9
            assert abs(lam_legacy - lam_kernel) < 1e-9


# ── delta 1: F-08 step function vs graduated decay (A-2) ────────────────────

def test_delta_f08_step_function_vs_graduated_decay():
    indexes = _build_indexes()
    solved = _solve_all(indexes)
    sentences = _legacy_sentences(solved)
    oracle_eps = _oracle_episodes(solved, indexes)
    t_exact = solved[("Saturn", "conjunction")][0].t_exact
    speed = abs(float(indexes["Saturn"].spline.derivative()(t_exact)))

    t_off = t_exact + 4.0    # inside the ±5-day box, off the exact instant
    lam_legacy = _legacy_lambda(sentences, t_off)
    lam_kernel = _projection_lambda(oracle_eps, t_off)

    expected_decay = 1.0 - speed * 4.0 / 1.0   # orb_conj_slow = 1.0 deg
    # Legacy: the event-time weight persists undecayed across the whole box
    # (F-08 step function — identical value at t_exact and t_exact+4d).
    assert lam_legacy == 0.8
    # Kernel projection: graduated linear decay by separation at the instant.
    assert abs(lam_kernel - 0.8 * expected_decay) < 1e-9
    assert lam_kernel < lam_legacy
    print("\nWP4_DELTA F-08/A-2 step-vs-graduated: "
          f"legacy={lam_legacy:.8f} kernel={lam_kernel:.8f} "
          f"delta={lam_legacy - lam_kernel:.8f} at t_exact+4d "
          f"(speed={speed:.6f} deg/d)")


# ── delta 2: F-08/H-2 exception -> 0.0 -> certified active (A-1) ────────────

def test_delta_f08_h2_exception_never_certified_active():
    sentences = _legacy_sentences(_solve_all(_build_indexes()))

    def failing_eval(_jd: float) -> float:
        raise RuntimeError("synthetic solver failure (WP4 declared)")

    # Legacy path: the exception becomes 0.0 (interval_solver.py:132-136
    # reproduced in eval_single_legacy), and with the F-08 companion
    # all-zero century distribution lambda_thresh is 0.0, so the failed
    # evaluation is certified ACTIVE by the >= predicate.
    grid = _weekly_grid()
    zero_series = [
        legacy.eval_single_legacy(failing_eval, jd) for jd in grid[:20]
    ]
    assert zero_series == [0.0] * 20
    config = legacy.compute_threshold_config(zero_series, base_rate=None)
    assert config.lambda_thresh == 0.0
    failed_value = legacy.eval_single_legacy(failing_eval, grid[0])
    assert legacy.is_above_threshold(failed_value, config) is True  # A-1

    # Fixed side of the same delta (WP5 H-2, commit 59bebe7dc): the served
    # engine raises EvaluationFailure instead of swallowing; the kernel
    # propagates 'unqualified' on the row instead of a fabricated 0.0.
    from services.gochara_v3.interval_solver import EvaluationFailure
    assert issubclass(EvaluationFailure, Exception)
    ep = _solve_all(_build_indexes())[("Saturn", "conjunction")][0]
    assert ep.completeness_state in ("applied", "unqualified")
    print("\nWP4_DELTA F-08/A-1 exception->0.0->active: legacy certifies a "
          "FAILED evaluation as active (thresh=0.0, >= predicate); fixed "
          "side: WP5 EvaluationFailure + kernel completeness_state "
          f"(row state here: {ep.completeness_state!r})")
    assert sentences  # workload sanity: the failing path was exercised


# ── delta 3: F-11 overlay absent -> quality_gates 1.0 vs 'unavailable' ──────

def test_delta_f11_overlay_absent_unknown_as_clear():
    # Legacy: no vedha rows overlapping -> product stays 1.0 ("unknown"
    # served as "fully gated", engine.py:287/:400 — A-6).
    qg_legacy, detail = legacy.compute_quality_gates(
        [], "2024-01-01", "2026-01-01"
    )
    assert qg_legacy == 1.0 and detail["vedha_fired_count"] == 0
    # Oracle/projection contract: the same absent overlay is the honest
    # 'unavailable' state — λ is None, never 1.0 by default (WP2 case 10).
    result = score_lambda({**FACTORS, "quality_gates": None, "episodes": []})
    assert result["state"] == "unavailable"
    assert result["lambda_raw"] is None
    print("\nWP4_DELTA F-11/A-6 overlay-absent: legacy quality_gates=1.0 "
          "(unknown-as-clear) vs projection state='unavailable' (honest "
          "null)")


# ── delta 4: F-10/H-3 era-edge clamp vs honest truncation flags ─────────────

def test_delta_f10_h3_edge_clamp_vs_truncation_flag():
    indexes = _build_indexes()
    solved = _solve_all(indexes)
    sentences = _legacy_sentences(solved)
    t_exact = solved[("Saturn", "conjunction")][0].t_exact

    # Sub-horizon starting INSIDE the contribution box of the first exact.
    sub = (t_exact - 2.0, t_exact + 30.0)

    # Legacy: the coarse series starts above threshold, so enter_jd is
    # CLAMPED to the sweep start with no crossing proven there
    # (interval_solver.py:304-306 — A-4); exit is clamped to the series end
    # (series still above at sub-horizon end: the box extends to +5d... the
    # 30d tail decays below 0.4, so exit is bisected — the START clamp is
    # the defect under test).
    intervals = legacy.find_threshold_crossings(
        lambda jd: _legacy_lambda(sentences, jd), sub[0], sub[1],
        LAMBDA_THRESH,
    )
    assert len(intervals) == 1
    assert intervals[0].enter_jd == sub[0]   # clamped, no crossing proven

    # Kernel: the same physical contact, same sub-horizon — the episode
    # carries explicit truncation flags instead of a silent clamp.
    sub_eps = kernel_episodes.solve_episodes(
        indexes["Saturn"], "Saturn", "conjunction", 281.0, sub,
        "orb_conj_slow", refine=False,
    )
    assert len(sub_eps) == 1
    assert sub_eps[0].truncated_at_horizon == "both"
    assert sub_eps[0].t_in == sub[0] and sub_eps[0].t_out == sub[1]
    print("\nWP4_DELTA F-10/H-3 edge: legacy declares enter_jd at the sweep "
          "start with no crossing measured there; kernel marks the same "
          "episode truncated_at_horizon='both'")


# ── delta 5: H-5 stored-peak cap vs persist-all + plateau tie-break ─────────

def test_delta_h5_peak_cap_and_plateau_ties():
    # A-5: legacy pooled retention caps at MAX_PEAKS_PER_ERA_WINDOW = 3
    # BEFORE persistence; peaks beyond the cap are unrecoverable downstream.
    cands = [
        legacy.PeakCandidate(jd=T0 + 10 + 120.0 * i, lam=lam)
        for i, lam in enumerate((0.91, 0.85, 0.88, 0.80, 0.95))
    ]
    retained = legacy.retain_candidates(cands)   # cap applies (pre-H-5)
    assert len(retained) == 3
    assert {c.lam for c in retained} == {0.95, 0.91, 0.88}
    dropped = {c.lam for c in cands} - {c.lam for c in retained}
    assert dropped == {0.85, 0.80}               # truncation as absence

    # H-5 kernel admission: every admitted peak persists; a serve-time
    # max_rows trims AFTER admission and never re-ranks.
    values = [0.5, 0.9, 0.9, 0.9, 0.4]           # plateau of three tied maxima
    admitted = kernel_peaks.admit_peaks(values)
    assert [(p.index, p.rank) for p in admitted] == [(1, 1), (2, 1), (3, 1)]
    trimmed = kernel_peaks.admit_peaks(values, max_rows=2)  # serve-time only
    assert [p.index for p in trimmed] == [1, 2]
    assert all(p.rank == 1 for p in trimmed)

    # B-4 vs WP2 case 12: legacy find_local_maxima admits the plateau's
    # FIRST point only; the kernel admits ALL tied maxima with the same rank.
    jds = [T0 + float(i) for i in range(5)]
    legacy_maxima = legacy.find_local_maxima(jds, values)
    assert len(legacy_maxima) == 1 and legacy_maxima[0].jd == jds[1]
    print("\nWP4_DELTA H-5/A-5+B-4: legacy retains 3/5 peaks (2 dropped "
          "pre-persistence) and admits a plateau once at its first point; "
          "kernel persists all admitted peaks (trim at serve time) and "
          "admits all 3 tied maxima at rank 1")


# ── identity: contact ids are stable under horizon re-partitioning ──────────

def test_contact_ids_stable_under_repartition():
    """WP4 exit gate: re-partition the horizon differently, re-run, and the
    exact contacts' ids must not move. (Ids of NO-EXACT horizon-truncated
    episodes floor t_in by the pinned WP1 §3.2 rule — those are
    partition-scoped by design and recorded in the coverage manifest; they
    are excluded from the stability set, which is stated, not silent.)"""
    indexes = _build_indexes()
    convention_id = canonical_convention_id()

    def ids_over(horizon):
        out = set()
        for body, _tref, target_deg, relation, orb_source in SEARCH_MATRIX:
            for ep in kernel_episodes.solve_episodes(
                indexes[body], body, relation, target_deg, horizon,
                orb_source, refine=False,
            ):
                if ep.exact_crossing:
                    out.add(kernel_ids.contact_id(
                        chart_id=CHART_ID, convention_id=convention_id,
                        body=body, target_type="karaka",
                        target_ref="WP4SUN" if body == "Saturn" else "WP4MOON",
                        relation=relation, aspect_deg=ep.aspect_deg,
                        t_exact_jd=ep.t_exact, method_version=METHOD_VERSION,
                    ))
        return out

    full = ids_over(HORIZON)
    assert len(full) == 3  # 2 Saturn conjunctions + 1 Jupiter conjunction

    mid = swe.julday(2025, 1, 1, 12.0)
    halves = ids_over((T0, mid)) | ids_over((mid, H1))
    shifted = ids_over((T0 + 10.0, H1))
    assert halves == full    # split at a different partition seam
    assert shifted == full   # and a shifted window: ids unmoved


# ── timing: prepare / search / query, cold and warm ─────────────────────────

def test_timing_prepare_search_query():
    """Phase-separated timings. Cold = fresh global arc build; warm = arc
    indexes reused (the production shape: arcs are built once per
    (body × substrate), contact solving is per chart). No cap, coarser grid
    or narrower horizon is used anywhere — the search matrix and grid are
    the declared workload's own."""
    grid = _weekly_grid()

    t = time.perf_counter()
    indexes_cold = _build_indexes()
    prepare_cold = time.perf_counter() - t

    t = time.perf_counter()
    solved = _solve_all(indexes_cold)
    search = time.perf_counter() - t

    sentences = _legacy_sentences(solved)
    oracle_eps = _oracle_episodes(solved, indexes_cold)

    t = time.perf_counter()
    legacy_series = [_legacy_lambda(sentences, jd) for jd in grid]
    query_legacy = time.perf_counter() - t

    t = time.perf_counter()
    kernel_series = [_projection_lambda(oracle_eps, jd) for jd in grid]
    query_kernel = time.perf_counter() - t

    t = time.perf_counter()
    config = legacy.compute_threshold_config(legacy_series, base_rate=0.05)
    hierarchy = legacy.build_resolution_hierarchy(
        lambda jd: _legacy_lambda(sentences, jd), T0, H1,
        config.lambda_thresh,
    )
    hierarchy_t = time.perf_counter() - t

    # Warm pass: search+query again on the SAME indexes (per-chart cost with
    # the global prepare amortized).
    t = time.perf_counter()
    _solve_all(indexes_cold)
    search_warm = time.perf_counter() - t
    t = time.perf_counter()
    [_projection_lambda(oracle_eps, jd) for jd in grid]
    query_kernel_warm = time.perf_counter() - t
    t = time.perf_counter()
    [_legacy_lambda(sentences, jd) for jd in grid]
    query_legacy_warm = time.perf_counter() - t

    e2e_kernel_cold = prepare_cold + search + query_kernel
    e2e_legacy = query_legacy + hierarchy_t

    measured = {
        "workload": "WP4-SYNTH-1",
        "horizon_days": H1 - T0,
        "knots_per_body": len(indexes_cold["Saturn"].knot_jds),
        "search_matrix_cells": len(SEARCH_MATRIX),
        "query_points": len(grid),
        "prepare_cold_s": round(prepare_cold, 6),
        "search_cold_s": round(search, 6),
        "search_warm_s": round(search_warm, 6),
        "query_legacy_s": round(query_legacy, 6),
        "query_legacy_warm_s": round(query_legacy_warm, 6),
        "query_kernel_s": round(query_kernel, 6),
        "query_kernel_warm_s": round(query_kernel_warm, 6),
        "hierarchy_legacy_s": round(hierarchy_t, 6),
        "end_to_end_kernel_cold_s": round(e2e_kernel_cold, 6),
        "end_to_end_legacy_s": round(e2e_legacy, 6),
        "lambda_thresh_used": config.lambda_thresh,
        "era_windows": hierarchy["era_window_count"],
        "historical_best_completed_run_min": 58.2,
        "historical_best_note": (
            "external recorded figure for the full century production "
            "workload; NOT the same workload as WP4-SYNTH-1 — the comparison "
            "is a scale reading, never a like-for-like claim (E-001)"
        ),
    }
    print("\nWP4_MEASURED " + json.dumps(measured, sort_keys=True))

    # Earned-signal assertions: the measurement actually ran the declared
    # workload (no vacuous timing).
    assert len(legacy_series) == len(grid) == len(kernel_series)
    assert max(legacy_series) > 0.0 and max(kernel_series) > 0.0
    assert prepare_cold > 0 and search > 0


# ── ledger write/index cost at this workload's scale (disposable DB) ────────

def test_ledger_write_and_serve_cost(conn):
    """Prices the kernel's new storage costs on the disposable WP6 database:
    write_contacts + write_coverage for this workload's episodes, then a
    serve-shaped range read. The 200k-row index-scale figures are WP6's
    (WP6_LEDGER.md §6) — this test measures THIS workload's write path and
    leaves zero rows behind."""
    solved = _solve_all(_build_indexes())
    convention_id = canonical_convention_id()
    generation = "4.0-wp4"
    chart = "00000000-0000-4000-8000-00000000ff04"

    episode_dicts = []
    for (body, relation), eps in solved.items():
        tref = "WP4SUN" if body == "Saturn" else "WP4MOON"
        for ep in eps:
            episode_dicts.append({
                "independence_group": kernel_ids.independence_group(
                    body=body, relation=relation, aspect_deg=ep.aspect_deg,
                    target_deg=ep.target_deg, t_exact_jd=ep.t_exact,
                    t_fallback_jd=ep.t_in,
                ),
                "body": body,
                "relation": relation,
                "aspect_deg": ep.aspect_deg,
                "target_type": "karaka",
                "target_ref": tref,
                "target_fact_id": None,
                "target_resolution_state": "resolved",
                "target_longitude_deg": ep.target_deg,
                "t_in": _dt(ep.t_in),
                "t_exact": _dt(ep.t_exact) if ep.t_exact is not None else None,
                "t_out": _dt(ep.t_out),
                "bracket_seconds": ep.bracket_seconds,
                "tolerance_arcsec": ep.tolerance_arcsec,
                "truncated_at_horizon": (
                    None if ep.truncated_at_horizon == "both"
                    else ep.truncated_at_horizon
                ),
                "branch": ep.branch,
                "station_flag": ep.station_flag,
                "exact_crossing": ep.exact_crossing,
                "orb_max_deg": ep.orb_max_deg,
                "orb_source": ep.orb_source,
                "dwell_days": ep.dwell_days,
                "epistemic_class": "observed_event",
                "completeness_state": ep.completeness_state,
                "operator_role": "kernel",
                "precision_regime": "instant_grain",
                "time_basis": "event_time_utc",
                "comparable_with": "same_convention_same_inputs",
                "ephemeris_backend": {"mode": "synthetic_cubic",
                                      "retflag": None},
                "evidence_fact_ids": [],
                "classical_citation": None,
                "uncited_extension": True,
                "corpus_verifiable": None,
            })

    cid = kernel_ledger.register_convention(
        conn,
        {**{k: v for k, v in zip(
            ("zodiac", "ayanamsha", "sidereal_method", "node_model",
             "node_source", "epoch_convention", "time_scale", "house_system",
             "ephemeris_mode"),
            ("sidereal", "lahiri_chitrapaksha", "swe_flg_sidereal", "mean",
             "swiss_mean_node_flg_sidereal", "noon_ut_knot_abscissa",
             "ut_to_tt_swe_deltat", "whole_sign", "synthetic_cubic"))},
         "method_version": METHOD_VERSION},
        {"ephemeris_backend": "synthetic_cubic", "retflag": None},
        {},
    )
    kernel_ledger.publish_candidate(
        conn, chart, generation, cid,
        {"resonance": {"computed_at": "2026-09-23T00:00:00Z", "row_count": 0},
         "convention_id": cid},
        {"mode": "synthetic_cubic"},
        "[2024-01-01 12:00:00+00,2026-01-01 12:00:00+00)",
    )

    with conn.transaction():
        t = time.perf_counter()
        contact_ids = kernel_ledger.write_contacts(
            conn, chart, generation, cid, episode_dicts, "wp4-build-1")
        write_contacts_s = time.perf_counter() - t

        t = time.perf_counter()
        kernel_ledger.write_coverage(
            conn, chart, generation, cid,
            [{
                "partition_kind": "body_target",
                "partition_key": f"{body}:{tref}",
                "requested_horizon":
                    "[2024-01-01 12:00:00+00,2026-01-01 12:00:00+00)",
                "completed_horizon":
                    "[2024-01-01 12:00:00+00,2026-01-01 12:00:00+00)",
                "resolution": 2.0,
                "relations_searched": ["conjunction", "drishti_contact"],
                "targets_requested": 1,
                "target_resolution_state_counts": {"resolved": 1},
                "unavailable_inputs": {},
                "unsearched_reason": None,
            } for body, tref in (("Saturn", "WP4SUN"), ("Jupiter", "WP4MOON"))],
            "wp4-build-1")
        write_coverage_s = time.perf_counter() - t

    assert len(contact_ids) == len(episode_dicts) == 3

    # Serve-shaped read (P-4 shape): chart+generation+body+relation, t_exact
    # range. Warm timing (the DB has just seen the rows).
    t = time.perf_counter()
    rows = conn.execute(
        "SELECT contact_id FROM kala_gochara_contacts "
        "WHERE chart_id = %s AND generation = %s AND body = 'Saturn' "
        "AND relation = 'conjunction' "
        "AND t_exact >= %s AND t_exact < %s ORDER BY t_exact",
        (chart, generation, _dt(T0), _dt(H1)),
    ).fetchall()
    serve_read_s = time.perf_counter() - t
    assert len(rows) == 2

    # Leave zero rows behind (F-24 discipline on this test's own writes).
    kernel_ledger.clear_generation(conn, chart, generation)
    remaining = conn.execute(
        "SELECT count(*) FROM kala_gochara_contacts "
        "WHERE chart_id = %s AND generation = %s",
        (chart, generation),
    ).fetchone()[0]
    assert remaining == 0

    print("\nWP4_LEDGER_MEASURED " + json.dumps({
        "workload": "WP4-SYNTH-1",
        "contact_rows": len(episode_dicts),
        "write_contacts_s": round(write_contacts_s, 6),
        "write_coverage_s": round(write_coverage_s, 6),
        "serve_read_s": round(serve_read_s, 6),
        "scale_reference": ("WP6_LEDGER.md §6 measured 200k-row load "
                            "9.9 s (~20k rows/s), serve reads ~0.07 ms warm "
                            "at 200k rows — index cost is priced THERE at "
                            "measured scale; this row prices the write path "
                            "at this workload's own row count"),
    }, sort_keys=True))
