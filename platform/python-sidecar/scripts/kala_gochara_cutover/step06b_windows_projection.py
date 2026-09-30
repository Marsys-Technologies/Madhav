#!/usr/bin/env python3
"""step06b_windows_projection.py — E-012 '4.0' windows projection writer (ADK-0012).

Projects the '4.0' candidate contact ledger (kala_gochara_contacts, written by
step06_candidate_build.py) into the SERVED window table kala_gochara_windows
under generation '4.0' — plan §2.2/§4.5/§4.7, the writer whose absence steps 7
and 8 refuse on (E-012). Branch-local lane work under ADK-0012: design,
implementation, tests and disposable-DB rehearsal ONLY; the production
application set (overlay rebuild + candidate build + flip) stays
native-escalated and is not attempted here.

Semantics (every choice disclosed, none improvised):

  * Contact -> event_class: a '4.0' contact joins every gochara_resonance_map
    row matching (chart_id, target_type, target_ref); the map's UNIQUE(chart,
    class, type, ref) constraint makes the per-class weight unambiguous. A
    contact matching no map row contributes to NO class (counted in the
    report as contacts_unmapped, never silently dropped).
  * PROMISE — pinned legacy_semantics.compute_promise over the class's map
    weights (noisy-OR; computed once per (chart, class), plan §4.5).
  * PERMISSION — pinned compute_permission over the class context's
    systems_active map. The per-class timing-system context is an INPUT
    (--class-context-json, or the disclosed synthetic context under
    --rehearse-synthetic): wiring it to the L1 dasha facts is part of the
    escalated production set. A class with matching contacts but NO context
    is skipped and recorded (skipped_classes) — never a 0.0 stand-in
    (plan §4.6).
  * ACTIVITY — the pinned noisy-OR of legacy_semantics.compute_activity_v3,
    with per-contact orb_strength = the M-1 `linear_no_box` decay across the
    contact's own in-orb span [t_in, t_out] (orb = orb_max_deg at the span
    edges, 0 at t_exact, linear between; NO ±5-day box — that is the F-08
    step the flag retires). The span edges are exactly the enumeration orb
    (--orb-deg), so decay hits 0 at t_in/t_out by construction.
  * tārā — pinned honest skip (modifier 1.0, skipped=True): the M-3 separate
    Moon channel is not wired into this projection, so the transit-Moon
    input is genuinely unavailable; the skip is recorded on every row.
  * w30 — N-14 removed: pinned w30_modifier(enabled=False) (1.0, recorded).
  * QUALITY GATES — pinned compute_quality_gates over the chart's
    kala_vedha_gochara rows (DATE-grain overlap) when the overlay columns
    exist; the F-11 no-rows path (1.0) is reproduced and disclosed per row.
  * lambda_v3 — pinned assemble_lambda_v3 (product + clamp + term breakdown).
  * Windows — components of {t : lambda(t) >= --min-lambda} over the horizon.
    The sampler evaluates on the union of the daily grid AND every contact
    breakpoint (t_in/t_exact/t_out): under M-1 the activity function is
    piecewise-defined with breakpoints exactly there, so no positive-activity
    component — however narrow, including sub-day spans the pinned uniform
    7-day sweep would miss — can fall between samples. Component boundaries
    are bisected (same _bisect discipline as the pinned solver, WITHOUT the
    F-08 exception-swallow: an evaluation error aborts the run, it is never
    served as 0.0). --min-lambda defaults to 1e-9: the degenerate
    threshold.py fallback (lambda_thresh=0.0 certifying failed evaluations as
    active, F-08) is NOT reproduced — a window exists only where lambda is
    genuinely positive.
  * Peaks — pinned find_local_maxima + admit_candidates (era's own P90) +
    refine_peak_to_day, with retain_candidates called at max_peaks =
    len(admitted): the pre-H-5 cap of 3 (MAX_PEAKS_PER_ERA_WINDOW) is REMOVED
    per H-5 — every admitted peak is stored; the pinned 90-day minimum
    separation is retained. This choice is recorded in the run report.
  * Era -> month -> day rows mirror build_resolution_hierarchy (calendar
    month of the refined peak clipped to the era; day row at the refined
    peak), parent_window_id wired to the containing row's id at INSERT time
    (migration 567's documentary linkage, parents inserted first).
  * valence/is_adverse — pinned resolve_valence_v3 over the signed channels
    at each row's own peak instant; the class fallback valence comes from
    the class context (default 'mixed', disclosed).
  * active_sentences — the contributing contacts' contact_ids at the row's
    peak instant (plan §4.6). contributing_systems — the active permission
    systems plus per-factor provenance strings. suppression_state — the
    quality-gates detail plus the tārā/w30 skip records and the §12.9
    freshness states.

Idempotency (plan §4.7): DELETE ... WHERE chart_id AND generation='<gen>'
then INSERT, inside ONE transaction with the candidate-manifest check
(ledger._require_not_published / _candidate_manifest_id) — a published
generation refuses (exit 6); 'v1'/'3.0' rows are never touched (the
cross-generation test proves it). The candidate manifest's row_counts gains
the real windows count.

§12.9: before any write the overlay freshness gate runs exactly as in
step06_enumerate_episodes / step06_candidate_build (exit 7 on stale); under
--rehearse-synthetic it is skipped and recorded NOT_RUN, mirroring step06.

Delta report: --delta-report-out writes the factor-level delta report vs the
baseline generation ('3.0'): per-class factors and per-era-window intensity
deltas, honest '—' (null) wherever the '3.0' row set has no counterpart
factor (it carries intensities only — never back-filled).

Usage:
    python3 step06b_windows_projection.py --dsn postgresql://... \
        --chart-id <uuid> [--generation 4.0] \
        [--horizon-start 2020-01-01T00:00:00+00:00 \
         --horizon-end 2030-01-01T00:00:00+00:00] \
        [--orb-deg 5.0] [--min-lambda 1e-9] [--coarse-step-days 1.0] \
        [--class-context-json ctx.json | --rehearse-synthetic] \
        [--delta-report-out PATH] [--evidence]

Exit codes: 0 written; 3 cannot proceed (no candidate manifest, no contacts,
bad args); 4 production refusal; 6 published-generation refusal; 7 §12.9
stale-overlay refusal.
"""
from __future__ import annotations

import heapq
import importlib.util
import json
import sys
import time
import uuid as _uuid
from array import array
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import connect, run_main_guarded, step_parser, write_evidence  # noqa: E402

SIDECAR = Path(__file__).resolve().parents[2]
_LEDGER_PATH = SIDECAR / "services" / "gochara_kernel" / "ledger.py"
_LEGACY_PATH = SIDECAR / "services" / "gochara_kernel" / "legacy_semantics.py"

UTC = timezone.utc
# E-020 / ADK-0026: the Unix-epoch JD anchor is 2440587.5 (1970-01-01T00:00Z,
# midnight UTC) — matching overlays.py:34. The previous 2440588.0 (noon UTC)
# made date_of_jd not the true inverse of jd_of: instants 00:00–11:59 UTC
# (05:30–17:29 IST) were dated one day early (the 39 horizon-edge rows of
# the conjunct-(e) RED).
JD_UNIX_EPOCH = 2440587.5

GENERATION_DEFAULT = "4.0"
BASELINE_DEFAULT = "3.0"
MIN_LAMBDA_DEFAULT = 1e-9   # positive-activity floor; NOT the threshold.py 0.0 fallback (F-08)
COARSE_STEP_DAYS_DEFAULT = 1.0
MIN_PEAK_SEPARATION_DAYS = 90.0  # pinned (resolution_hierarchy.py); H-5 removes only the count cap
PEAK_BASIS = "gochara_lambda_v3:m1_linear_no_box:step06b"
SOURCE_LIVE = "live"
SOURCE_REHEARSAL = "fixture"  # migration 460 CHECK: 'live' | 'fixture'

# The candidate flag set this projection is built under (E-018/ADK-0012 —
# recorded verbatim in the run report and the delta report header).
CANDIDATE_FLAGS = {
    "activity_shape": "linear_no_box",     # M-1 candidate 1
    "moon_channel": "separate",            # M-3 (tārā transit-Moon input not wired -> honest skip)
    "nodal_drishti": "removed",            # N-14 (w30 = 1.0, pinned disabled path)
    "sade_sati_mode": "testimony",         # N-15
    "kakshya_bindu_interim": True,         # N-22
    "overlay_stamps": True,                # N-17
    "vedha_exceptions": "m8_rows",         # M-8
}

# ledger relation -> legacy ACTIVITY_PRIMITIVES vocabulary. A return is a
# degree contact with the body's own natal longitude (disclosed); relations
# outside this map are excluded from activity and counted (never silently
# scored under a wrong primitive).
RELATION_TO_PRIMITIVE = {
    "conjunction": "degree_contact",
    "return": "degree_contact",
    "drishti_contact": "drishti_contact",
    "sign_ingress": "sign_ingress",
    "nakshatra_ingress": "nakshatra_ingress_tara",
    "kakshya_cell_crossing": "kakshya_cell_crossing",
    "station_retro_loop": "station_retro_loop",
    "eclipse_degree": "eclipse_degree",
}

# Optional columns the window row carries when the target table has them
# (migration 567's hierarchy columns). era_slice_key is deliberately NOT
# written: the re-pinned ka_gochara integrity contract (migration 1091,
# conjunct (g)) reads a non-null era_slice_key inside generation '4.0' as
# the century writer's stamp on this writer's rows — it belongs to the
# g3_% generations only.
OPTIONAL_COLUMNS = ("parent_window_id", "resolution")


def _load_module(path: Path, name: str):
    """Import-by-path (the step06/ledger precedent: the kernel package
    __init__ is a sibling workstream's surface)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ledger = _load_module(_LEDGER_PATH, "step06b_ledger")
leg = _load_module(_LEGACY_PATH, "step06b_legacy_semantics")


# ── time helpers ─────────────────────────────────────────────────────────────


def jd_of(dt: datetime) -> float:
    if dt.tzinfo is None:
        raise ValueError("naive datetime has no jd (B1: tz-aware only)")
    return dt.timestamp() / 86400.0 + 2440587.5


def date_of_jd(jd: float) -> date:
    # E-020 / ADK-0026: the true inverse of jd_of — the UTC calendar date of
    # the instant (overlays.py:49-52 jd_to_date shape). The prior
    # int(jd - 2440588.0) day-count floored at the noon-UTC boundary.
    return datetime.fromtimestamp(
        (jd - JD_UNIX_EPOCH) * 86400.0, tz=UTC).date()


def iso_date_of_jd(jd: float) -> str:
    return date_of_jd(jd).isoformat()


# ── M-1 linear_no_box decay ─────────────────────────────────────────────────


def linear_no_box_decay(t_jd: float, t_in_jd: float, t_exact_jd: float,
                        t_out_jd: float) -> float:
    """M-1 `linear_no_box`: orb = orb_max at the in-orb span edges, 0 at
    t_exact, linear in between; the contribution is 0 outside [t_in, t_out]
    and at the edges themselves. This replaces the legacy ±5-day box (the
    F-08 step) — the span IS the enumeration's in-orb region, so the decay
    reaches exactly 0 where the contact ceases to exist."""
    if t_exact_jd is None:
        return 0.0
    if t_jd <= t_in_jd or t_jd >= t_out_jd:
        return 0.0
    if t_jd <= t_exact_jd:
        span = t_exact_jd - t_in_jd
        if span <= 0:
            return 1.0 if t_jd == t_exact_jd else 0.0
        return (t_jd - t_in_jd) / span
    span = t_out_jd - t_exact_jd
    if span <= 0:
        return 0.0
    return (t_out_jd - t_jd) / span


# ── per-class lambda evaluator ───────────────────────────────────────────────


class ClassContext:
    """The once-per-(chart, class) factor context (plan §4.5)."""

    def __init__(self, event_class: str, weights: list[float],
                 permission_systems: dict[str, bool],
                 *, weight_by_target_ref: dict[str, float],
                 class_valence: str = "mixed", class_is_adverse: bool = False,
                 context_source: str = "class_context_json"):
        self.event_class = event_class
        self.weight_by_target_ref = dict(weight_by_target_ref)
        self.promise, self.promise_detail = leg.compute_promise(weights)
        self.permission = leg.compute_permission(permission_systems)
        self.permission_systems = dict(permission_systems)
        self.class_valence = class_valence
        self.class_is_adverse = class_is_adverse
        self.context_source = context_source
        # tārā: the transit-Moon channel is not wired into this projection
        # (M-3 separate channel) — the pinned honest skip (modifier 1.0).
        self.tara = leg.tara_modifier(None, None)
        # N-14: nodal dṛṣṭi removed — the pinned disabled path (modifier 1.0).
        self.w30 = leg.w30_modifier(None, [], enabled=False)

    def factors_record(self) -> dict:
        return {
            "event_class": self.event_class,
            "promise": self.promise,
            "promise_target_count": self.promise_detail["target_count"],
            "permission": self.permission,
            "permission_systems_active": sorted(
                s for s, on in self.permission_systems.items() if on),
            "tara_modifier": self.tara["modifier"],
            "tara_skip_reason": self.tara["skip_reason"],
            "w30_modifier": self.w30["modifier"],
            "w30_skip_reason": self.w30["skip_reason"],
            "class_valence": self.class_valence,
            "class_is_adverse": self.class_is_adverse,
            "context_source": self.context_source,
        }


def make_eval_fn(class_ctx: ClassContext, contacts: list[dict],
                 quality_gate_for_date):
    """eval_fn(t_jd) -> (lambda_raw, active_contact_ids, signed_channels).

    The pinned assemble_lambda_v3 algebra over the M-1 in-orb activity; the
    F-08 exception-swallow is NOT reproduced — errors propagate."""

    def evaluate(t_jd: float):
        sentences = []
        active_ids = []
        for c in contacts:
            decay = linear_no_box_decay(t_jd, c["_t_in_jd"], c["_t_exact_jd"],
                                        c["_t_out_jd"])
            if decay <= 0.0:
                continue
            sentences.append(leg.Sentence(
                primitive=c["_primitive"], target_ref=c["target_ref"],
                transit_planet=c["body"], event_jd=c["_t_exact_jd"],
                detail={"orb_strength": decay},
            ))
            active_ids.append(c["contact_id"])
        activity, _act_detail, _tb = leg.compute_activity_v3(
            sentences, class_ctx.weight_by_target_ref)
        supportive, afflicting, _ch = leg.compute_signed_channels_v3(
            sentences, class_ctx.weight_by_target_ref)
        gates, gates_detail = quality_gate_for_date(iso_date_of_jd(t_jd))
        assembled = leg.assemble_lambda_v3(
            promise=class_ctx.promise, permission=class_ctx.permission,
            activity=activity, tara_modifier=class_ctx.tara["modifier"],
            w30_modifier=class_ctx.w30["modifier"], quality_gates=gates)
        return {
            "lambda_raw": assembled["lambda_raw"],
            "lambda_signed": assembled["lambda_signed"],
            "activity": activity,
            "supportive": supportive,
            "afflicting": afflicting,
            "quality_gates": gates,
            "quality_gates_detail": gates_detail,
            "active_contact_ids": active_ids,
        }

    return evaluate


# ── component + peak machinery (pinned primitives, F-08 swallow removed) ────


def _bisect_above(eval_lambda, lo: float, hi: float, thresh: float,
                  tol_days: float = 1e-4) -> float:
    """Boundary between a below point (lo) and an above point (hi). Same
    bisection discipline as the pinned solver's _bisect_crossing; evaluation
    errors propagate (the F-08 0.0-swallow is not reproduced)."""
    while hi - lo > tol_days:
        mid = (lo + hi) / 2.0
        if eval_lambda(mid) >= thresh:
            hi = mid
        else:
            lo = mid
    return hi


def _bisect_below(eval_lambda, lo: float, hi: float, thresh: float,
                  tol_days: float = 1e-4) -> float:
    """Boundary between an above point (lo) and a below point (hi)."""
    while hi - lo > tol_days:
        mid = (lo + hi) / 2.0
        if eval_lambda(mid) >= thresh:
            lo = mid
        else:
            hi = mid
    return lo


def find_components(eval_lambda, points: list[float], min_lambda: float):
    """Maximal above-threshold runs over the (sorted) augmented series, with
    bisected boundaries. `points` MUST include every contact breakpoint —
    under M-1 that is where activity components begin and end, so no
    positive-activity interval can be missed regardless of width."""
    components = []
    n = len(points)
    i = 0
    while i < n:
        if eval_lambda(points[i]) < min_lambda:
            i += 1
            continue
        enter = (_bisect_above(eval_lambda, points[i - 1], points[i], min_lambda)
                 if i > 0 else points[0])
        j = i
        while j < n and eval_lambda(points[j]) >= min_lambda:
            j += 1
        exit_jd = (_bisect_below(eval_lambda, points[j - 1], points[j], min_lambda)
                   if j < n else points[-1])
        components.append((enter, exit_jd, i, j - 1))  # series index range incl.
        i = j
    return components


def iter_grid(horizon_jd: tuple[float, float], coarse_step_days: float):
    """The daily evaluation grid, lazily — the SAME accumulation
    (t += coarse_step_days from horizon start) the whole-class projection
    used, so every grid float is bit-identical whether the class is
    projected whole or cluster by cluster."""
    t = horizon_jd[0]
    while t <= horizon_jd[1]:
        yield t
        t += coarse_step_days


def contact_span(c: dict) -> tuple[float, float]:
    """The instants a contact can contribute to or break the series at:
    [min(t_in, t_exact), max(t_out, t_exact)] (t_exact is inside the in-orb
    span by construction; taken defensively so a malformed row can never
    place a breakpoint outside its own cluster)."""
    lo, hi = c["_t_in_jd"], c["_t_out_jd"]
    te = c["_t_exact_jd"]
    if te is not None:
        lo, hi = min(lo, te), max(hi, te)
    return lo, hi


def project_class_windows(class_ctx: ClassContext, contacts: list[dict],
                          horizon_jd: tuple[float, float],
                          quality_gate_for_date, *,
                          min_lambda: float = MIN_LAMBDA_DEFAULT,
                          coarse_step_days: float = COARSE_STEP_DAYS_DEFAULT,
                          day_stride_days: float = 1.0) -> tuple[list[dict], dict]:
    """Era -> month -> day window rows for one event class from an in-memory
    contact list — the rehearsal-scale (and equivalence-oracle) shape; the
    century path runs project_class_streamed, which is exactly this
    computation as a bounded sweep. Returns (window_row_dicts,
    class_report). Window rows carry logical window_key/parent_key; the
    writer resolves them to parent_window_id at INSERT time."""
    evaluate = make_eval_fn(class_ctx, contacts, quality_gate_for_date)
    eval_lambda = lambda t: evaluate(t)["lambda_raw"]  # noqa: E731

    breakpoints = sorted({b for c in contacts
                          for b in (c["_t_in_jd"], c["_t_exact_jd"], c["_t_out_jd"])
                          if b is not None and horizon_jd[0] <= b <= horizon_jd[1]})
    grid = list(iter_grid(horizon_jd, coarse_step_days))
    series = sorted(set(grid) | set(breakpoints))
    if not series:
        return [], {"event_class": class_ctx.event_class,
                    **class_ctx.factors_record(),
                    "components": 0, "peaks_admitted": 0, "peaks_retained": 0,
                    "peaks_refined_outside_era": 0,
                    "era_windows": 0, "month_windows": 0, "day_windows": 0}

    rows: list[dict] = []
    admitted_total = 0
    retained_total = 0
    refined_outside_era = 0
    components = find_components(eval_lambda, series, min_lambda)
    gate_details_seen: dict[str, dict] = {}

    for enter_jd, exit_jd, i0, i1 in components:
        era_series = series[i0:i1 + 1]
        era_values = [eval_lambda(t) for t in era_series]
        peak_idx = max(range(len(era_series)), key=lambda k: era_values[k])
        era_peak_jd = era_series[peak_idx]
        era_peak = evaluate(era_peak_jd)
        era_key = f"era-{_uuid.uuid4()}"
        for gd in (era_peak["quality_gates_detail"],):
            gate_details_seen[era_key] = gd

        # Peaks: pinned find_local_maxima + P90 admission over the era's own
        # series; H-5 — the count cap is removed (max_peaks=len(admitted)),
        # the pinned 90-day minimum separation is retained.
        era_cands = leg.find_local_maxima(era_series, era_values)
        admitted = leg.admit_candidates(era_cands, era_values)
        retained = leg.retain_candidates(
            admitted, max_peaks=len(admitted) if admitted else 0,
            min_separation_days=MIN_PEAK_SEPARATION_DAYS)
        admitted_total += len(admitted)
        retained_total += len(retained)

        rows.append(_window_row(
            class_ctx, evaluate, window_key=era_key, parent_key=None,
            tier="era", enter_jd=enter_jd, exit_jd=exit_jd,
            peak_jd=era_peak_jd))

        for cand in retained:
            peak_jd_true, _lam = leg.refine_peak_to_day(eval_lambda, cand.jd)
            # E-020 rehearsal finding: refine_peak_to_day scans ±42 days around the
            # coarse candidate and can land OUTSIDE this era component (the peak
            # then belongs to the adjacent component, where it is emitted with its
            # own family). Emitting month/day rows for such a peak clips the
            # calendar month against a non-overlapping era and produces an inverted
            # (window_end < window_start) or peak-escaped (peak_date > window_end)
            # row — a conjunct-(d) violation. Skip the month/day family; the peak
            # is not lost, it is represented in the era it actually falls in.
            if not (enter_jd <= peak_jd_true <= exit_jd):
                refined_outside_era += 1
                continue
            # calendar-month bounds of the refined peak, clipped to the era
            # (build_resolution_hierarchy, rh:621-632 + R8.6 clip — with the
            # E-020/ADK-0026 correction: bounds are midnight-UTC JDs, the true
            # inverse of date_of_jd, not rh's noon-UTC anchor).
            d = date_of_jd(peak_jd_true)
            month_start = date(d.year, d.month, 1)
            next_month = (date(d.year + 1, 1, 1) if d.month == 12
                          else date(d.year, d.month + 1, 1))
            month_end = next_month - timedelta(days=1)

            def _jd_of_date(dd: date) -> float:
                # midnight-UTC JD of the civil date (jd_of(datetime(dd, UTC)))
                return JD_UNIX_EPOCH + (dd - date(1970, 1, 1)).days

            month_key = f"month-{_uuid.uuid4()}"
            rows.append(_window_row(
                class_ctx, evaluate, window_key=month_key, parent_key=era_key,
                tier="month",
                enter_jd=max(_jd_of_date(month_start), enter_jd),
                exit_jd=min(_jd_of_date(month_end), exit_jd),
                peak_jd=peak_jd_true))
            rows.append(_window_row(
                class_ctx, evaluate, window_key=f"day-{_uuid.uuid4()}",
                parent_key=month_key, tier="day",
                enter_jd=peak_jd_true, exit_jd=peak_jd_true,
                peak_jd=peak_jd_true))

    report = {
        "event_class": class_ctx.event_class,
        **class_ctx.factors_record(),
        "components": len(components),
        "peaks_admitted": admitted_total,
        "peaks_retained": retained_total,
        "peaks_refined_outside_era": refined_outside_era,
        "era_windows": len(components),
        "month_windows": retained_total - refined_outside_era,
        "day_windows": retained_total - refined_outside_era,
        "quality_gates_fired": sum(
            g.get("vedha_fired_count", 0) for g in gate_details_seen.values()),
    }
    return rows, report


def _window_row(class_ctx: ClassContext, evaluate, *, window_key: str,
                parent_key: str | None, tier: str, enter_jd: float,
                exit_jd: float, peak_jd: float) -> dict:
    peak = evaluate(peak_jd)
    valence, is_adverse, tension = leg.resolve_valence_v3(
        peak["supportive"], peak["afflicting"],
        class_valence=class_ctx.class_valence,
        class_is_adverse=class_ctx.class_is_adverse)
    raw = peak["lambda_raw"]
    return {
        "window_key": window_key,
        "parent_key": parent_key,
        "event_class": class_ctx.event_class,
        "temporal_shape": "point" if tier == "day" else "interval",
        "window_start": date_of_jd(enter_jd),
        "window_end": date_of_jd(exit_jd),
        "peak_date": date_of_jd(peak_jd),
        "milestone_id": None,
        "is_irreversibility_milestone": False,
        "signed_intensity": raw * (-1.0 if is_adverse else 1.0),
        "raw_intensity": raw,
        "valence": valence,
        "is_adverse": is_adverse,
        "active_sentences": sorted(peak["active_contact_ids"]),
        "contributing_systems": [
            *sorted(s for s, on in class_ctx.permission_systems.items() if on),
            "promise:gochara_resonance_map",
            "activity:kala_gochara_contacts@m1_linear_no_box",
            f"tara:skipped({class_ctx.tara['skip_reason']})",
            "w30:removed(N-14)",
            ("quality_gates:kala_vedha_gochara"
             if peak["quality_gates_detail"].get("vedha_rows_total")
             else "quality_gates:no_overlay_rows(F-11)"),
        ],
        "suppression_state": {
            "quality_gates": peak["quality_gates"],
            "quality_gates_detail": peak["quality_gates_detail"],
            "tara": class_ctx.tara,
            "w30": class_ctx.w30,
            "valence_tension": tension,
        },
        "peak_basis": PEAK_BASIS,
        "calibration_state": "structural_prior",
        "resolution": tier,
    }


# ── DB surface ───────────────────────────────────────────────────────────────


def _table_columns(conn, table: str) -> set[str]:
    return {r[0] for r in conn.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = %s", (table,)).fetchall()}


def _contact_row_to_dict(row) -> dict:
    (cid, body, relation, ttype, tref, t_in, t_exact, t_out,
     orb_max, completeness) = row
    d = {
        "contact_id": cid, "body": body, "relation": relation,
        "target_type": ttype, "target_ref": tref,
        "orb_max_deg": float(orb_max) if orb_max is not None else None,
        "completeness_state": completeness,
        "_t_in_jd": jd_of(t_in),
        "_t_exact_jd": jd_of(t_exact) if t_exact is not None else None,
        "_t_out_jd": jd_of(t_out),
    }
    d["_span_lo"], d["_span_hi"] = contact_span(d)
    return d


_CONTACT_COLUMNS_SQL = (
    "contact_id, body, relation, target_type, target_ref,"
    " t_in, t_exact, t_out, orb_max_deg, completeness_state")


def _class_pair_conditions(target_pairs) -> tuple[str, list]:
    pairs = sorted(target_pairs)
    conds = " OR ".join(["(target_type = %s AND target_ref = %s)"] * len(pairs))
    params: list = []
    for ttype, tref in pairs:
        params += [ttype, tref]
    return conds, params


def count_class_contacts(conn, chart_id: str, generation: str,
                         target_pairs: set[tuple[str, str]],
                         relations: list[str]) -> int:
    """SQL COUNT of one class's contacts with a scorable relation — the
    per-class accounting (contacts_matched / no-contact short-circuit)
    without materializing the class."""
    if not target_pairs:
        return 0
    conds, params = _class_pair_conditions(target_pairs)
    return int(conn.execute(
        "SELECT count(*) FROM kala_gochara_contacts"
        " WHERE chart_id = %s AND generation = %s AND relation = ANY(%s)"
        f" AND ({conds})",
        [chart_id, generation, relations, *params]).fetchone()[0])


def iter_class_contacts(conn, chart_id: str, generation: str,
                        target_pairs: set[tuple[str, str]]):
    """Stream ONE event class's contacts via a server-side cursor (ASTRA A2.5
    review amendment 1), ORDERED by span start (LEAST(t_in, t_exact)) so
    iter_series_points / sweep_class_components can consume them as a
    sliding window — the projection never holds more than the contacts
    active around the sweep point (round-2 amendment 1). `target_pairs` is the class's (target_type,
    target_ref) set from gochara_resonance_map (map UNIQUE(chart, class,
    type, ref) makes the per-class join unambiguous)."""
    if not target_pairs:
        return
    conds, params = _class_pair_conditions(target_pairs)
    with conn.cursor(name="step06b_class_contacts") as cur:
        cur.itersize = 10000
        cur.execute(
            f"SELECT {_CONTACT_COLUMNS_SQL} FROM kala_gochara_contacts"
            f" WHERE chart_id = %s AND generation = %s AND ({conds})"
            " ORDER BY LEAST(t_in, COALESCE(t_exact, t_in)), contact_id",
            [chart_id, generation, *params])
        for row in cur:
            yield _contact_row_to_dict(row)


def _dt_of_jd(jd: float) -> datetime:
    return datetime.fromtimestamp((jd - JD_UNIX_EPOCH) * 86400.0, tz=UTC)


def fetch_class_contacts_intersecting(conn, chart_id: str, generation: str,
                                      target_pairs: set[tuple[str, str]],
                                      relations: list[str],
                                      lo_jd: float, hi_jd: float) -> list[dict]:
    """Pass-2 bounded re-read: the class's scorable contacts whose span
    intersects [lo, hi], in the stream's (span start, contact_id) order,
    with _primitive set. The range is a peak's refinement window (about
    two weeks) or a single instant — never the class."""
    if not target_pairs:
        return []
    conds, params = _class_pair_conditions(target_pairs)
    rows = conn.execute(
        f"SELECT {_CONTACT_COLUMNS_SQL} FROM kala_gochara_contacts"
        f" WHERE chart_id = %s AND generation = %s AND relation = ANY(%s)"
        f" AND ({conds})"
        " AND LEAST(t_in, COALESCE(t_exact, t_in)) <= %s"
        " AND GREATEST(t_out, COALESCE(t_exact, t_out)) >= %s"
        " ORDER BY LEAST(t_in, COALESCE(t_exact, t_in)), contact_id",
        [chart_id, generation, relations, *params,
         _dt_of_jd(hi_jd), _dt_of_jd(lo_jd)]).fetchall()
    out = []
    for row in rows:
        c = _contact_row_to_dict(row)
        c["_primitive"] = RELATION_TO_PRIMITIVE[c["relation"]]
        out.append(c)
    return out


def iter_era_rows(conn, chart_id: str, generation: str):
    """Stream the written era-tier rows back for the delta report (round-2
    amendment 1: report data is read from the relation after commit, never
    retained across classes), ordered the way the report prints them."""
    with conn.cursor(name="step06b_era_rows") as cur:
        cur.itersize = 5000
        cur.execute(
            "SELECT event_class, peak_date, raw_intensity, signed_intensity,"
            " valence FROM kala_gochara_windows"
            " WHERE chart_id = %s AND generation = %s AND resolution = 'era'"
            " ORDER BY event_class, peak_date",
            (chart_id, generation))
        for cls, peak_date, raw, signed, val in cur:
            yield {"resolution": "era", "event_class": cls,
                   "peak_date": peak_date, "raw_intensity": float(raw),
                   "signed_intensity": float(signed), "valence": val}


def fetch_map_rows(conn, chart_id: str) -> list[dict]:
    return [
        {"event_class": r[0], "target_type": r[1], "target_ref": r[2],
         "weight": float(r[3])}
        for r in conn.execute(
            "SELECT event_class, target_type, target_ref, weight"
            " FROM gochara_resonance_map WHERE chart_id = %s"
            " AND target_resolution_state = 'resolved'",
            (chart_id,)).fetchall()
    ]


def fetch_vedha_rows(conn, chart_id: str) -> list[dict]:
    """Overlay rows for the W1.3 quality gates; empty when the overlay
    columns are absent (the F-11 no-rows path, disclosed on every row)."""
    cols = _table_columns(conn, "kala_vedha_gochara") \
        if _table_exists(conn, "kala_vedha_gochara") else set()
    needed = {"window_start", "window_end", "vedha_kind", "graha", "detail"}
    if not needed <= cols:
        return []
    return [
        {"window_start": str(r[0]), "window_end": str(r[1]),
         "vedha_kind": r[2], "graha": r[3],
         "detail": r[4] if isinstance(r[4], dict) else {},
         "classical_citation": r[5]}
        for r in conn.execute(
            "SELECT window_start, window_end, vedha_kind, graha, detail,"
            " classical_citation FROM kala_vedha_gochara WHERE chart_id = %s",
            (chart_id,)).fetchall()
    ]


def fetch_malefic_scale(conn) -> dict[int, str]:
    if not _table_exists(conn, "bg_vedha_malefic_scale"):
        return {}
    return {int(r[0]): r[1] for r in conn.execute(
        "SELECT malefic_count, effect_grade FROM bg_vedha_malefic_scale").fetchall()}


def _table_exists(conn, table: str) -> bool:
    return conn.execute("SELECT to_regclass(%s)", (table,)).fetchone()[0] is not None


def make_quality_gate_for_date(vedha_rows: list[dict],
                               malefic_scale: dict[int, str]):
    cache: dict[str, tuple[float, dict]] = {}

    def for_date(date_iso: str):
        if date_iso not in cache:
            cache[date_iso] = leg.compute_quality_gates(
                vedha_rows, date_iso, date_iso, malefic_scale)
        return cache[date_iso]

    return for_date


class WindowWriteState:
    """Cross-call state for per-cluster write_windows calls within one
    projection run: the natural-key collapse map and the window_key → id map
    must persist across the clusters of a class exactly as they did within
    the single per-class call (adjacent clusters can still retain peaks that
    land on the same calendar day). One computed_at for the run."""

    def __init__(self):
        self.id_by_key: dict[str, int] = {}
        self.seen_natural: dict[tuple, int] = {}
        self.skipped_dupes = 0
        self.computed_at = datetime.now(UTC)


def write_windows(conn, chart_id: str, generation: str,
                  rows: list[dict], *, source: str,
                  window_columns: set[str], delete: bool = True,
                  state: WindowWriteState | None = None) -> tuple[int, int]:
    """Plan §4.7 idempotent rebuild: scoped DELETE (chart_id × generation)
    then INSERT, parents before children so parent_window_id resolves to the
    containing row's id. Never touches another generation. The caller holds
    the transaction.

    `delete=False` (the streamed century shape, ASTRA A2.5 review amendment
    1): the caller already issued the scoped DELETE once, and each overlap
    cluster's rows are INSERTed as the cluster is projected — window rows
    for the whole century never accumulate in this process. Parent linkage
    is cluster-internal (a month/day window's parent era is in the same
    cluster), and `state` carries the natural-key collapse across clusters
    so a per-cluster call resolves parent_window_id and duplicate collapse
    exactly as the whole-set call. Returns (written, skipped) for THIS call."""
    ledger._require_not_published(conn, chart_id, generation, "write_windows")
    if delete:
        conn.execute(
            "DELETE FROM kala_gochara_windows WHERE chart_id = %s AND generation = %s",
            (chart_id, generation))
    if state is None:
        state = WindowWriteState()
    computed_at = state.computed_at
    optional = [c for c in OPTIONAL_COLUMNS if c in window_columns]
    base_cols = ["chart_id", "event_class", "temporal_shape", "window_start",
                 "window_end", "peak_date", "milestone_id",
                 "is_irreversibility_milestone", "signed_intensity",
                 "raw_intensity", "valence", "is_adverse", "active_sentences",
                 "contributing_systems", "suppression_state", "peak_basis",
                 "calibration_state", "source", "computed_at", "generation"]
    cols = base_cols + optional
    jsonb_cols = {"active_sentences", "contributing_systems", "suppression_state"}
    placeholders = ", ".join(
        f"%s::jsonb" if c in jsonb_cols else "%s" for c in cols)
    id_by_key = state.id_by_key

    def _values(row: dict) -> tuple:
        vals = {
            "chart_id": chart_id, "generation": generation,
            "source": source, "computed_at": computed_at,
            "parent_window_id": (id_by_key.get(row["parent_key"])
                                 if row["parent_key"] else None),
        }
        vals.update({k: row[k] for k in (
            "event_class", "temporal_shape", "window_start", "window_end",
            "peak_date", "milestone_id", "is_irreversibility_milestone",
            "signed_intensity", "raw_intensity", "valence", "is_adverse",
            "peak_basis", "calibration_state", "resolution")})
        for jc in jsonb_cols:
            vals[jc] = json.dumps(row[jc], default=str)
        return tuple(vals[c] for c in cols)

    # parents (era) first, then month, then day — the insert order resolves
    # the documentary parent linkage (migration 567).
    ordered = sorted(rows, key=lambda r: {"era": 0, "month": 1, "day": 2}[r["resolution"]])
    # Adjacent components can each retain a peak whose refine_peak_to_day
    # lands on the same calendar day (and, clipped to era bounds, the same
    # month), producing rows identical under uq_kala_gochara_windows_natural_key
    # (chart, class, window_start, peak_date, milestone_id, resolution,
    # generation). Keep the first in insert order; children of a skipped row
    # re-point to the retained row's id.
    seen_natural = state.seen_natural
    skipped_dupes = 0
    with conn.cursor() as cur:
        for row in ordered:
            natural = (row["event_class"], row["window_start"],
                       row["peak_date"], row["milestone_id"] or "",
                       row["resolution"] or "")
            if natural in seen_natural:
                id_by_key[row["window_key"]] = seen_natural[natural]
                skipped_dupes += 1
                continue
            cur.execute(
                f"INSERT INTO kala_gochara_windows ({', '.join(cols)})"
                f" VALUES ({placeholders}) RETURNING id",
                _values(row))
            rid = cur.fetchone()[0]
            id_by_key[row["window_key"]] = rid
            seen_natural[natural] = rid
    if skipped_dupes:
        state.skipped_dupes += skipped_dupes
        print(f"write_windows: {skipped_dupes} projected row(s) shared a "
              "natural key with an already-written row (adjacent-component "
              "peak collapse to the same date); first occurrence kept, "
              "children re-pointed", file=sys.stderr)
    return len(ordered) - skipped_dupes, skipped_dupes


# ── per-class streamed projection: the component sweep (round-2 amendment 1) ─
#
# project_class_windows needs the class's whole contact list. The century
# path cannot hold it (a class is input-sized). project_class_streamed is the
# SAME computation — the same series, the same find_components runs and
# bisected boundaries, the same pinned peak admission/retention/refinement,
# the same rows in the same order — arranged so that nothing input-sized
# is retained:
#
#   pass 1 (sweep_class_components): the evaluation series (daily grid ∪
#     in-horizon contact breakpoints) is generated lazily in order by
#     merging the grid with a heap of breakpoints fed from the span-ordered
#     contact stream; lambda at each point is evaluated over a SLIDING
#     WINDOW holding only the contacts whose span has not yet ended (M-1
#     decay is 0 outside (t_in, t_out), so an ended contact can never
#     contribute again); each lambda >= min_lambda run is kept as two
#     compact float arrays (jd, lambda) until it closes, exactly the
#     era_series/era_values the whole-class code builds for that component.
#   pass 2 (per component, as it closes): the pinned peak machinery runs on
#     the arrays; the era-peak evaluation, each retained peak's
#     refine_peak_to_day (±DAY_REFINEMENT_HALF_WINDOW_DAYS) and the
#     month/day rows re-evaluate lambda over the contacts intersecting that
#     small range, re-fetched from the relation (fetch_contacts_in) — the
#     retained-peak count is bounded by the pinned 90-day separation, so
#     this is at most a few hundred bounded fetches per component.
#
# Retained memory per class: the sliding window (overlap depth), one
# component's compact series (16 bytes per series point — the one residual
# that is inherently proportional to a continuously-active component,
# because the pinned P90 admission needs the run's whole value distribution;
# for a 1M-contact component ≈ 50 MB) plus its PeakCandidate list, and the
# scalar class report. Never the class's contacts, never the century's rows.
# Where a run is so long that even the compact residual matters, the
# driver's RLIMIT_AS guard turns the overrun into a loud exit 3.

_SUMMED_REPORT_KEYS = ("components", "peaks_admitted", "peaks_retained",
                       "peaks_refined_outside_era", "era_windows",
                       "month_windows", "day_windows", "quality_gates_fired")


class ContactWindow:
    """The contacts that can still contribute at or after the sweep point,
    kept in the stream's (span start, contact_id) order — pass 1's ONLY
    contact retention. make_eval_fn iterates it afresh per evaluation, so
    the noisy-OR runs over the same contact sequence (minus the zero-decay
    ones it skips anyway) as the whole-class evaluator."""

    __slots__ = ("_items", "peak_size")

    def __init__(self):
        self._items: list[dict] = []
        self.peak_size = 0

    def add(self, c: dict) -> None:
        self._items.append(c)
        if len(self._items) > self.peak_size:
            self.peak_size = len(self._items)

    def evict_through(self, t: float) -> None:
        """Drop every contact whose span ends at or before t: decay is 0 at
        and after t_out, so it cannot affect any later point or bisection."""
        self._items = [c for c in self._items if c["_span_hi"] > t]

    def __iter__(self):
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)


def iter_series_points(contacts, horizon_jd: tuple[float, float],
                       coarse_step_days: float, window: ContactWindow):
    """Yield the whole-class evaluation series — sorted(set(grid) |
    set(in-horizon breakpoints)) — one point at a time without building
    it: the lazy grid is merged with a heap of breakpoints pushed as the
    span-ordered contact stream is read. Invariant on every yielded point
    p: every contact whose span starts at or before p has been added to
    `window` (so lambda over the window at p, and at any bisection point
    between p and its successor, equals the whole-class lambda)."""
    h0, h1 = horizon_jd
    grid = iter_grid(horizon_jd, coarse_step_days)
    g = next(grid, None)
    heap: list[float] = []
    it = iter(contacts)
    c = next(it, None)
    last = None
    while True:
        cand = g
        if heap and (cand is None or heap[0] < cand):
            cand = heap[0]
        while c is not None and (cand is None or c["_span_lo"] <= cand):
            window.add(c)
            for b in (c["_t_in_jd"], c["_t_exact_jd"], c["_t_out_jd"]):
                if b is not None and h0 <= b <= h1:
                    heapq.heappush(heap, b)
            c = next(it, None)
            if heap and (cand is None or heap[0] < cand):
                cand = heap[0]
        if cand is None:
            return
        if g is not None and g == cand:
            g = next(grid, None)
        while heap and heap[0] == cand:
            heapq.heappop(heap)
        if last is None or cand > last:
            yield cand
            last = cand


def sweep_class_components(class_ctx: ClassContext, contacts, horizon_jd,
                           quality_gate_for_date, *,
                           min_lambda: float = MIN_LAMBDA_DEFAULT,
                           coarse_step_days: float = COARSE_STEP_DAYS_DEFAULT):
    """Pass 1: find_components as a sweep. Yields, per component,
    (enter_jd, exit_jd, jds, lams, era_peak_jd, window_peak_size) where
    jds/lams are the component's series and values as compact arrays and
    era_peak_jd is the FIRST maximum (max(range(n), key=...) semantics)."""
    window = ContactWindow()
    evaluate = make_eval_fn(class_ctx, window, quality_gate_for_date)
    eval_lambda = lambda t: evaluate(t)["lambda_raw"]  # noqa: E731
    prev = None
    run_jds = run_lams = None
    enter = best = best_jd = None
    for p in iter_series_points(contacts, horizon_jd, coarse_step_days,
                                window):
        v = eval_lambda(p)
        if run_jds is None and v >= min_lambda:
            enter = (_bisect_above(eval_lambda, prev, p, min_lambda)
                     if prev is not None else p)
            run_jds, run_lams = array("d"), array("d")
            best, best_jd = None, None
        if run_jds is not None:
            if v >= min_lambda:
                run_jds.append(p)
                run_lams.append(v)
                if best is None or v > best:
                    best, best_jd = v, p
            else:
                exit_jd = _bisect_below(eval_lambda, run_jds[-1], p, min_lambda)
                yield enter, exit_jd, run_jds, run_lams, best_jd, window.peak_size
                run_jds = run_lams = None
        window.evict_through(p)
        prev = p
    if run_jds is not None:
        yield enter, prev, run_jds, run_lams, best_jd, window.peak_size


def project_class_streamed(class_ctx: ClassContext, contacts, horizon_jd,
                           quality_gate_for_date, write_rows,
                           fetch_contacts_in, *,
                           min_lambda: float = MIN_LAMBDA_DEFAULT,
                           coarse_step_days: float = COARSE_STEP_DAYS_DEFAULT
                           ) -> tuple[dict, dict, int, int]:
    """Project one class from a span-ordered contact STREAM, component by
    component, writing each component's rows (write_rows(rows) ->
    (written, skipped)) before the next component closes.
    `fetch_contacts_in(lo_jd, hi_jd)` returns the class's scorable contacts
    whose span intersects [lo, hi], in (span start, contact_id) order —
    pass 2's bounded re-read. The class report is the SUM of the
    per-component figures (every summed key is per-component) plus the
    era-tier aggregates the delta report needs, accumulated as scalars.
    Returns (class_report, tier_counts, n_written, n_skipped)."""
    acc = {"event_class": class_ctx.event_class, **class_ctx.factors_record()}
    for k in _SUMMED_REPORT_KEYS:
        acc[k] = 0
    tier_counts = {"era": 0, "month": 0, "day": 0}
    n_written = n_skipped = 0
    gates_sum = 0.0
    gates_n = 0
    raw_sum = 0.0
    window_peak = 0
    longest_component = 0
    half = leg.DAY_REFINEMENT_HALF_WINDOW_DAYS
    margin = leg.DAY_REFINEMENT_STEP_DAYS

    def _evaluator_for(lo: float, hi: float):
        return make_eval_fn(class_ctx, fetch_contacts_in(lo, hi),
                            quality_gate_for_date)

    for enter_jd, exit_jd, jds, lams, era_peak_jd, win_peak in \
            sweep_class_components(class_ctx, contacts, horizon_jd,
                                   quality_gate_for_date, min_lambda=min_lambda,
                                   coarse_step_days=coarse_step_days):
        window_peak = max(window_peak, win_peak)
        longest_component = max(longest_component, len(jds))
        rows: list[dict] = []
        era_eval = _evaluator_for(era_peak_jd, era_peak_jd)
        era_peak = era_eval(era_peak_jd)
        era_key = f"era-{_uuid.uuid4()}"
        acc["quality_gates_fired"] += era_peak["quality_gates_detail"].get(
            "vedha_fired_count", 0)

        era_cands = leg.find_local_maxima(jds, lams)
        admitted = leg.admit_candidates(era_cands, lams)
        retained = leg.retain_candidates(
            admitted, max_peaks=len(admitted) if admitted else 0,
            min_separation_days=MIN_PEAK_SEPARATION_DAYS)
        acc["peaks_admitted"] += len(admitted)
        acc["peaks_retained"] += len(retained)
        acc["components"] += 1
        acc["era_windows"] += 1

        rows.append(_window_row(
            class_ctx, era_eval, window_key=era_key, parent_key=None,
            tier="era", enter_jd=enter_jd, exit_jd=exit_jd,
            peak_jd=era_peak_jd))

        for cand in retained:
            ev = _evaluator_for(cand.jd - half - margin, cand.jd + half + margin)
            peak_jd_true, _lam = leg.refine_peak_to_day(
                lambda t, _ev=ev: _ev(t)["lambda_raw"], cand.jd)
            if not (enter_jd <= peak_jd_true <= exit_jd):
                acc["peaks_refined_outside_era"] += 1
                continue
            d = date_of_jd(peak_jd_true)
            month_start = date(d.year, d.month, 1)
            next_month = (date(d.year + 1, 1, 1) if d.month == 12
                          else date(d.year, d.month + 1, 1))
            month_end = next_month - timedelta(days=1)

            def _jd_of_date(dd: date) -> float:
                return JD_UNIX_EPOCH + (dd - date(1970, 1, 1)).days

            month_key = f"month-{_uuid.uuid4()}"
            rows.append(_window_row(
                class_ctx, ev, window_key=month_key, parent_key=era_key,
                tier="month",
                enter_jd=max(_jd_of_date(month_start), enter_jd),
                exit_jd=min(_jd_of_date(month_end), exit_jd),
                peak_jd=peak_jd_true))
            rows.append(_window_row(
                class_ctx, ev, window_key=f"day-{_uuid.uuid4()}",
                parent_key=month_key, tier="day",
                enter_jd=peak_jd_true, exit_jd=peak_jd_true,
                peak_jd=peak_jd_true))
            acc["month_windows"] += 1
            acc["day_windows"] += 1

        for r in rows:
            tier_counts[r["resolution"]] += 1
            if r["resolution"] == "era":
                gates_sum += r["suppression_state"]["quality_gates"]
                gates_n += 1
                raw_sum += r["raw_intensity"]
        w, s = write_rows(rows)
        n_written += w
        n_skipped += s
    if gates_n:
        acc["mean_quality_gates"] = gates_sum / gates_n
    acc["era_raw_intensity_sum"] = raw_sum
    acc["contact_window_peak"] = window_peak
    acc["longest_component_points"] = longest_component
    return acc, tier_counts, n_written, n_skipped


def update_manifest_windows_count(conn, chart_id: str, generation: str,
                                  n_windows: int) -> None:
    """The candidate manifest records the real windows count (publish()
    recomputes the full row set at the flip)."""
    conn.execute(
        "UPDATE kala_gochara_publication"
        " SET row_counts = jsonb_set(row_counts, '{windows}', to_jsonb(%s))"
        " WHERE chart_id = %s AND generation = %s AND status = 'candidate'",
        (n_windows, chart_id, generation))


# ── delta report vs the baseline generation ──────────────────────────────────


def iter_delta_report_lines(*, chart_id: str, generation: str, baseline: str,
                            class_reports: list[dict], era_rows,
                            baseline_rows: list[dict], flags: dict,
                            fingerprints: dict | None, run_meta: dict):
    """The factor-level delta report vs the baseline generation, as a LINE
    STREAM: the per-class table comes from the class reports (one row per
    class, carrying `era_raw_intensity_sum`/`era_windows` so no window row
    is needed for the mean), and the per-window section consumes `era_rows`
    — an iterable of era-tier rows ALREADY sorted by (event_class,
    peak_date), e.g. iter_era_rows' cursor — one row at a time (round-2
    amendment 1: report data is never retained across the century).

    The baseline ('3.0') rows carry intensities only — every factor cell for
    the baseline is an honest '—' (null), never a back-filled number."""
    yield f"# Windows factor delta report — {generation} vs {baseline}"
    yield ""
    yield f"- chart_id: `{chart_id}`"
    yield f"- generated: {run_meta.get('generated_at')}"
    yield f"- writer: `step06b_windows_projection.py` (build {run_meta.get('build_id')})"
    yield f"- horizon: {run_meta.get('horizon')}"
    yield f"- flags: `{json.dumps(flags, sort_keys=True)}`"
    yield f"- §12.9 fingerprints: `{json.dumps(fingerprints, sort_keys=True, default=str)}`"
    yield ""
    yield "Baseline factor cells are '—' where the baseline row set carries no"
    yield "such factor (the '3.0' rows store intensities, not the v3 term"
    yield "breakdown) — an honest null, never a 0.0 stand-in."
    yield ""
    yield "## Per-class factors"
    yield ""
    yield ("| event_class | windows 4.0 (era/month/day) | promise | permission | tārā | w30 | quality_gates | peaks admitted→retained | mean raw 4.0 | windows 3.0 | mean raw 3.0 | Δ mean raw |")
    yield "|---|---|---|---|---|---|---|---|---|---|---|---|"
    baseline_by_class: dict[str, list[dict]] = {}
    for r in baseline_rows:
        baseline_by_class.setdefault(r["event_class"], []).append(r)
    fmt = lambda v: f"{v:.6f}" if isinstance(v, float) else "—"  # noqa: E731
    for rep in class_reports:
        cls = rep["event_class"]
        base = baseline_by_class.get(cls, [])
        n_era = rep.get("era_windows") or 0
        mean4 = (rep["era_raw_intensity_sum"] / n_era
                 if n_era and rep.get("era_raw_intensity_sum") is not None else None)
        mean3 = (sum(float(b["raw_intensity"]) for b in base) / len(base)
                 if base else None)
        delta = (mean4 - mean3) if (mean4 is not None and mean3 is not None) else None
        yield (
            f"| {cls} | {rep['era_windows']}/{rep['month_windows']}/{rep['day_windows']}"
            f" | {rep['promise']:.6f} | {rep['permission']:.6f}"
            f" | {rep['tara_modifier']:.3f} (skip) | {rep['w30_modifier']:.3f} (N-14)"
            f" | {fmt(rep.get('mean_quality_gates'))}"
            f" | {rep['peaks_admitted']}→{rep['peaks_retained']} (H-5 uncapped)"
            f" | {fmt(mean4)} | {len(base)} | {fmt(mean3)} | {fmt(delta)} |")
    yield ""
    yield "## Per-window deltas (era tier)"
    yield ""
    yield ("| event_class | peak_date | raw 4.0 | signed 4.0 | valence | nearest 3.0 peak | raw 3.0 | Δ raw |")
    yield "|---|---|---|---|---|---|---|---|"
    for r in era_rows:
        base = baseline_by_class.get(r["event_class"], [])
        nearest = min(base, key=lambda b: abs((b["peak_date"] - r["peak_date"]).days),
                      default=None)
        yield (
            f"| {r['event_class']} | {r['peak_date']} | {r['raw_intensity']:.6f}"
            f" | {r['signed_intensity']:.6f} | {r['valence']}"
            f" | {nearest['peak_date'] if nearest else '—'}"
            f" | {float(nearest['raw_intensity']) if nearest else '—'}"
            f" | {r['raw_intensity'] - float(nearest['raw_intensity']) if nearest else '—'} |")
    yield ""
    yield "## Notes"
    yield ""
    yield "- PROMISE is the pinned noisy-OR over the class's resolved resonance-map weights."
    yield ("- PERMISSION comes from the class context input "
           f"({run_meta.get('class_context_source')}); the L1 timing-system wiring is part of the")
    yield "  escalated production set (ADK-0012)."
    yield "- tārā reports the pinned honest skip (M-3 separate Moon channel not wired here);"
    yield "  w30 is N-14-removed (1.0). quality_gates reproduces the F-11 no-rows path where the"
    yield "  overlay is absent — disclosed on every row's suppression_state."
    yield "- Peak storage is H-5-uncapped (the pre-H-5 cap of 3/era is removed; the pinned 90-day"
    yield "  separation is retained)."
    yield "- '—' is an honest null: no baseline counterpart exists."
    yield ""


def build_delta_report(*, chart_id: str, generation: str, baseline: str,
                       class_reports: list[dict], window_rows: list[dict],
                       baseline_rows: list[dict], flags: dict,
                       fingerprints: dict | None, run_meta: dict) -> str:
    """Materialized (rehearsal-scale) form of iter_delta_report_lines over an
    in-memory window row list: era rows are selected and sorted here, and a
    class report lacking `era_raw_intensity_sum` gets it from the rows."""
    era = sorted((w for w in window_rows if w["resolution"] == "era"),
                 key=lambda w: (w["event_class"], w["peak_date"]))
    raw_by_class: dict[str, float] = {}
    for r in era:
        raw_by_class[r["event_class"]] = raw_by_class.get(r["event_class"], 0.0) \
            + r["raw_intensity"]
    reports = []
    for rep in class_reports:
        if "era_raw_intensity_sum" not in rep:
            rep = dict(rep, era_raw_intensity_sum=raw_by_class.get(rep["event_class"], 0.0))
        reports.append(rep)
    return "\n".join(iter_delta_report_lines(
        chart_id=chart_id, generation=generation, baseline=baseline,
        class_reports=reports, era_rows=era, baseline_rows=baseline_rows,
        flags=flags, fingerprints=fingerprints, run_meta=run_meta))


# ── main ─────────────────────────────────────────────────────────────────────


def _rehearsal_class_context(event_class: str) -> dict:
    """Disclosed synthetic class context for rehearsal ONLY: a fixed
    permission-system set (recorded as rehearsal-synthetic on every row and
    in the run report), mixed class valence."""
    return {
        "permission_systems": {"vimshottari": True, "sade_sati": True},
        "class_valence": "mixed",
        "class_is_adverse": False,
        "context_source": "REHEARSAL-SYNTHETIC (not chart data)",
    }


def main(argv: list[str] | None = None) -> int:
    parser = step_parser(6, __doc__)
    parser.add_argument("--chart-id", required=True)
    parser.add_argument("--generation", default=GENERATION_DEFAULT)
    parser.add_argument("--baseline-generation", default=BASELINE_DEFAULT)
    parser.add_argument("--horizon-start", default="2020-01-01T00:00:00+00:00")
    parser.add_argument("--horizon-end", default="2030-01-01T00:00:00+00:00")
    parser.add_argument("--orb-deg", type=float, default=5.0,
                        help="M-1 candidate-1 in-orb reference (linear_no_box × "
                             "5.0°); 1.0° is candidate 2, unratified (E-018/ADK-0012)")
    parser.add_argument("--min-lambda", type=float, default=MIN_LAMBDA_DEFAULT,
                        help="window-membership floor; the threshold.py 0.0 "
                             "fallback (F-08) is deliberately NOT reproduced")
    parser.add_argument("--coarse-step-days", type=float, default=COARSE_STEP_DAYS_DEFAULT,
                        help="daily evaluation grid stride; contact breakpoints "
                             "are always added to the series")
    parser.add_argument("--class-context-json",
                        help="per-event-class context: {class: {permission_systems: "
                             "{system: bool}, class_valence, class_is_adverse}}")
    parser.add_argument("--rehearse-synthetic", action="store_true",
                        help="synthetic class context for every map class; the "
                             "§12.9 gate is skipped and recorded NOT_RUN "
                             "(mirrors step06 --rehearse-synthetic)")
    parser.add_argument("--delta-report-out",
                        help="write the factor-level delta report vs the "
                             "baseline generation to this path")
    args = parser.parse_args(argv)

    if not (args.rehearse_synthetic or args.class_context_json):
        print("ERROR: provide --class-context-json, or --rehearse-synthetic "
              "for rehearsal", file=sys.stderr)
        return 3

    h_start = datetime.fromisoformat(args.horizon_start)
    h_end = datetime.fromisoformat(args.horizon_end)
    if h_start.tzinfo is None or h_end.tzinfo is None or h_end <= h_start:
        print("ERROR: horizon bounds must be tz-aware with end > start (B1)",
              file=sys.stderr)
        return 3
    horizon_jd = (jd_of(h_start), jd_of(h_end))

    class_contexts: dict[str, dict] = {}
    context_source = "REHEARSAL-SYNTHETIC (not chart data)"
    if args.class_context_json:
        class_contexts = json.loads(Path(args.class_context_json).read_text())
        context_source = "--class-context-json"

    conn = connect(args.dsn, step=6, autocommit=False)
    build_id = f"wp10-step6b-windows-{int(time.time())}"
    fingerprints = None
    try:
        # §12.9 gate — BEFORE reading anything for the build. Same refusal the
        # enumerator and step06 apply; skipped (NOT_RUN) under rehearsal.
        if args.rehearse_synthetic:
            fingerprints = {"house_vedha": "NOT_RUN: --rehearse-synthetic",
                            "moorti": "NOT_RUN: --rehearse-synthetic"}
        else:
            if str(SIDECAR) not in sys.path:
                sys.path.insert(0, str(SIDECAR))
            from services.ka_vedha_gochara.freshness import (
                check_overlay_freshness, gate_allows_overlays)
            reports = check_overlay_freshness(conn, args.chart_id)
            conn.rollback()  # the checks only read
            fingerprints = {
                "house_vedha": reports["house_vedha"].current,
                "moorti": reports["moorti"].current,
                "house_vedha_state": reports["house_vedha"].state,
                "moorti_state": reports["moorti"].state,
            }
            if not gate_allows_overlays(reports):
                detail = "; ".join(f"{n}: {r.summary()}" for n, r in reports.items())
                print(f"REFUSED (§12.9): {detail}. A windows projection must not "
                      "be built on stale overlay rows — rebuild ka_vedha_gochara "
                      "and ka_moorti_nirnaya first.", file=sys.stderr)
                conn.close()
                return 7

        # Plan §4.7 discipline: a candidate manifest must exist; published
        # refuses (exit 6), missing means step 6 has not run (exit 3).
        try:
            ledger._candidate_manifest_id(conn, args.chart_id, args.generation)
        except ledger.PublishedGenerationRefusal as exc:
            conn.rollback()
            print(f"REFUSED: {exc}", file=sys.stderr)
            conn.close()
            return 6
        except ValueError as exc:
            conn.rollback()
            print(f"ERROR: {exc} — run step06_candidate_build.py first",
                  file=sys.stderr)
            conn.close()
            return 3

        n_contacts_total = conn.execute(
            "SELECT count(*) FROM kala_gochara_contacts"
            " WHERE chart_id = %s AND generation = %s",
            (args.chart_id, args.generation)).fetchone()[0]
        if not n_contacts_total:
            conn.rollback()
            print(f"ERROR: no kala_gochara_contacts rows for chart "
                  f"{args.chart_id} generation {args.generation!r} — run "
                  "step06_candidate_build.py first", file=sys.stderr)
            conn.close()
            return 3
        map_rows = fetch_map_rows(conn, args.chart_id)
        if not map_rows:
            conn.rollback()
            print(f"ERROR: no resolved gochara_resonance_map rows for chart "
                  f"{args.chart_id} — run ka_gochara_resonance first",
                  file=sys.stderr)
            conn.close()
            return 3
        vedha_rows = fetch_vedha_rows(conn, args.chart_id)
        malefic_scale = fetch_malefic_scale(conn)
        baseline_rows = [
            {"event_class": r[0], "peak_date": r[1], "raw_intensity": float(r[2]),
             "signed_intensity": float(r[3])}
            for r in conn.execute(
                "SELECT event_class, peak_date, raw_intensity, signed_intensity"
                " FROM kala_gochara_windows WHERE chart_id = %s AND generation = %s",
                (args.chart_id, args.baseline_generation)).fetchall()
        ] if _table_exists(conn, "kala_gochara_windows") else []
        window_columns = _table_columns(conn, "kala_gochara_windows")

        # contact -> classes join (map UNIQUE(chart, class, type, ref) makes
        # the per-class weight unambiguous)
        weight_by_class: dict[str, dict[str, float]] = {}
        weights_all_by_class: dict[str, list[float]] = {}
        targets_by_class: dict[str, set[tuple[str, str]]] = {}
        for m in map_rows:
            weight_by_class.setdefault(m["event_class"], {})[m["target_ref"]] = m["weight"]
            weights_all_by_class.setdefault(m["event_class"], []).append(m["weight"])
            targets_by_class.setdefault(m["event_class"], set()).add(
                (m["target_type"], m["target_ref"]))
        all_pairs = sorted({p for pairs in targets_by_class.values()
                            for p in pairs})
        known_relations = sorted(RELATION_TO_PRIMITIVE)
        # Unmapped accounting as SQL COUNTs — the century projection never
        # materializes the contact set just to count it (amendment 1).
        n_rel_valid = conn.execute(
            "SELECT count(*) FROM kala_gochara_contacts"
            " WHERE chart_id = %s AND generation = %s AND relation = ANY(%s)",
            (args.chart_id, args.generation, known_relations)).fetchone()[0]
        pair_conds = " OR ".join(
            ["(target_type = %s AND target_ref = %s)"] * len(all_pairs))
        pair_params = [args.chart_id, args.generation, known_relations]
        for ttype, tref in all_pairs:
            pair_params += [ttype, tref]
        n_matched_valid = conn.execute(
            "SELECT count(*) FROM kala_gochara_contacts"
            " WHERE chart_id = %s AND generation = %s AND relation = ANY(%s)"
            f" AND ({pair_conds})",
            pair_params).fetchone()[0]
        unmapped_relation = n_contacts_total - n_rel_valid
        unmapped = n_rel_valid - n_matched_valid

        source = SOURCE_REHEARSAL if args.rehearse_synthetic else SOURCE_LIVE
        # Scoped DELETE once (plan §4.7 idempotent rebuild), then each
        # overlap cluster's windows are INSERTed as the cluster is projected
        # — window rows for the whole century never accumulate in this
        # process (amendment 1 / round-2 amendment 1).
        ledger._require_not_published(conn, args.chart_id, args.generation,
                                      "write_windows")
        conn.execute(
            "DELETE FROM kala_gochara_windows WHERE chart_id = %s AND generation = %s",
            (args.chart_id, args.generation))

        gate_for_date = make_quality_gate_for_date(vedha_rows, malefic_scale)
        write_state = WindowWriteState()
        tier_counts = {"era": 0, "month": 0, "day": 0}
        n_written = 0
        skipped_dupes = 0
        class_reports: list[dict] = []
        skipped_classes: list[dict] = []
        largest_window = 0

        def _write_rows(rows: list[dict]) -> tuple[int, int]:
            return write_windows(conn, args.chart_id, args.generation, rows,
                                 source=source, window_columns=window_columns,
                                 delete=False, state=write_state)

        def _scorable(stream):
            for c in stream:
                primitive = RELATION_TO_PRIMITIVE.get(c["relation"])
                if primitive is None:
                    continue  # counted once, globally, in unmapped_relation
                c["_primitive"] = primitive
                yield c

        for cls in sorted(weights_all_by_class):
            # per-class accounting as an SQL COUNT — the class is never
            # materialized to be counted (round-2 amendment 1)
            n_cls = count_class_contacts(conn, args.chart_id, args.generation,
                                         targets_by_class[cls], known_relations)
            if not n_cls:
                continue  # a class with no contacts honestly yields zero windows
            ctx_dict = (class_contexts.get(cls) if class_contexts
                        else _rehearsal_class_context(cls))
            if ctx_dict is None:
                skipped_classes.append({
                    "event_class": cls,
                    "reason": "no class context (permission systems) — honest "
                              "skip, never a 0.0 stand-in (plan §4.6)",
                    "contacts_matched": n_cls,
                })
                continue
            class_ctx = ClassContext(
                cls, weights_all_by_class[cls], ctx_dict["permission_systems"],
                weight_by_target_ref=weight_by_class[cls],
                class_valence=ctx_dict.get("class_valence", "mixed"),
                class_is_adverse=ctx_dict.get("class_is_adverse", False),
                context_source=ctx_dict.get("context_source", context_source))
            pairs = targets_by_class[cls]
            rep, tiers, w_cls, s_cls = project_class_streamed(
                class_ctx,
                _scorable(iter_class_contacts(conn, args.chart_id,
                                              args.generation, pairs)),
                horizon_jd, gate_for_date, _write_rows,
                lambda lo, hi, _p=pairs: fetch_class_contacts_intersecting(
                    conn, args.chart_id, args.generation, _p,
                    known_relations, lo, hi),
                min_lambda=args.min_lambda,
                coarse_step_days=args.coarse_step_days)
            for k, v in tiers.items():
                tier_counts[k] += v
            n_written += w_cls
            skipped_dupes += s_cls
            largest_window = max(largest_window, rep["contact_window_peak"])
            class_reports.append(rep)

        update_manifest_windows_count(conn, args.chart_id, args.generation,
                                      n_written)
        conn.commit()

        # The delta report's per-window section is streamed back from the
        # relation (era-tier rows, a named cursor) after the commit — no
        # window row is retained across classes for it (round-2 amendment 1).
        flags = {**CANDIDATE_FLAGS, "orb_max_deg": args.orb_deg,
                 "min_lambda": args.min_lambda,
                 "coarse_step_days": args.coarse_step_days}
        run_meta = {
            "build_id": build_id,
            "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "horizon": f"[{args.horizon_start},{args.horizon_end})",
            "class_context_source": context_source,
        }
        if args.delta_report_out:
            if "resolution" in window_columns:
                era_stream = iter_era_rows(conn, args.chart_id, args.generation)
            else:
                # legacy schema without migration 567's resolution column:
                # tiers are indistinguishable in the relation — the per-window
                # section is honestly empty, never reconstructed from memory
                era_stream = iter(())
            with Path(args.delta_report_out).open("w", encoding="utf-8") as fh:
                for line in iter_delta_report_lines(
                        chart_id=args.chart_id, generation=args.generation,
                        baseline=args.baseline_generation,
                        class_reports=class_reports, era_rows=era_stream,
                        baseline_rows=baseline_rows, flags=flags,
                        fingerprints=fingerprints, run_meta=run_meta):
                    fh.write(line)
                    fh.write("\n")
            conn.rollback()  # the report read only; leave no open transaction
    except ledger.PublishedGenerationRefusal as exc:
        conn.rollback()
        print(f"REFUSED: {exc}", file=sys.stderr)
        conn.close()
        return 6
    except Exception:
        conn.rollback()
        conn.close()
        raise
    finally:
        try:
            conn.close()
        except Exception:  # noqa: BLE001
            pass

    if unmapped or unmapped_relation:
        print(f"WARNING: contacts excluded from the activity function — "
              f"contacts_unmapped_relation={unmapped_relation} (relation not in "
              f"RELATION_TO_PRIMITIVE), contacts_unmapped_no_class={unmapped} "
              f"(no resolved gochara_resonance_map row). A non-zero count is a "
              f"reviewable finding — disclose it in the step evidence, never "
              f"leave it silent.", file=sys.stderr)
    report = {
        "writer": "step06b_windows_projection",
        "chart_id": args.chart_id, "generation": args.generation,
        "build_id": build_id,
        "source": source,
        "flags": flags,
        "upstream_fingerprints": fingerprints,
        "contacts_read": n_contacts_total,
        "contacts_unmapped_no_class": unmapped,
        "contacts_unmapped_relation": unmapped_relation,
        "classes_projected": len(class_reports),
        "skipped_classes": skipped_classes,
        "windows_written": n_written,
        "windows_collapsed_dupes": skipped_dupes,
        "windows_by_tier": tier_counts,
        "memory_shape": "component sweep (round-2 amendment 1): each class's "
            "contacts stream through a span-ordered server-side cursor into a "
            "sliding window; the evaluation series is generated lazily; each "
            "lambda>=min run is held as compact float arrays until it closes, "
            "then its peaks are refined against bounded range re-reads and "
            "its windows written before the next component closes; class "
            "reports are scalar aggregates; the delta report's per-window "
            "section is streamed back from the relation after commit. "
            "Retained: O(contact overlap depth) + one component's compact "
            "series + O(classes) + the baseline generation's rows",
        "contact_window_peak": largest_window,
        "memory_guard": getattr(args, "memory_guard", None),
        "windows_by_tier_basis": "pre-dedupe projection counts; "
            "windows_written is post-dedupe, so "
            "sum(windows_by_tier) = windows_written + windows_collapsed_dupes",
        "class_reports": class_reports,
        "baseline_generation": args.baseline_generation,
        "baseline_windows_read": len(baseline_rows),
        "delta_report_out": args.delta_report_out,
        "peak_retention": "H-5: count cap removed (all admitted peaks "
                          "stored); pinned 90-day separation retained",
    }
    print(json.dumps(report, indent=2, default=str))
    if args.evidence:
        write_evidence(6, "WINDOWS-PROJECTION",
                       f"```json\n{json.dumps(report, indent=2, default=str)}\n```")
    return 0


if __name__ == "__main__":
    sys.exit(run_main_guarded(main))
