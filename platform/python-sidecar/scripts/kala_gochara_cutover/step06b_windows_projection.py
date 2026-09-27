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

import importlib.util
import json
import sys
import time
import uuid as _uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import connect, step_parser, write_evidence  # noqa: E402

SIDECAR = Path(__file__).resolve().parents[2]
_LEDGER_PATH = SIDECAR / "services" / "gochara_kernel" / "ledger.py"
_LEGACY_PATH = SIDECAR / "services" / "gochara_kernel" / "legacy_semantics.py"

UTC = timezone.utc
JD_UNIX_EPOCH = 2440588.0  # _dt.date(1970,1,1) anchor, resolution_hierarchy.py convention

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
    "kakshya_cell": "kakshya_cell_crossing",
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
    # resolution_hierarchy.py's own conversion (int() floor toward zero on the
    # day count from the 1970 anchor).
    return date(1970, 1, 1) + timedelta(days=int(jd - JD_UNIX_EPOCH))


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


def project_class_windows(class_ctx: ClassContext, contacts: list[dict],
                          horizon_jd: tuple[float, float],
                          quality_gate_for_date, *,
                          min_lambda: float = MIN_LAMBDA_DEFAULT,
                          coarse_step_days: float = COARSE_STEP_DAYS_DEFAULT,
                          day_stride_days: float = 1.0) -> tuple[list[dict], dict]:
    """Era -> month -> day window rows for one event class. Returns
    (window_row_dicts, class_report). Window rows carry logical
    window_key/parent_key; the writer resolves them to parent_window_id at
    INSERT time."""
    evaluate = make_eval_fn(class_ctx, contacts, quality_gate_for_date)
    eval_lambda = lambda t: evaluate(t)["lambda_raw"]  # noqa: E731

    breakpoints = sorted({b for c in contacts
                          for b in (c["_t_in_jd"], c["_t_exact_jd"], c["_t_out_jd"])
                          if b is not None and horizon_jd[0] <= b <= horizon_jd[1]})
    grid = []
    t = horizon_jd[0]
    while t <= horizon_jd[1]:
        grid.append(t)
        t += coarse_step_days
    series = sorted(set(grid) | set(breakpoints))
    if not series:
        return [], {"event_class": class_ctx.event_class,
                    **class_ctx.factors_record(),
                    "components": 0, "peaks_admitted": 0, "peaks_retained": 0,
                    "era_windows": 0, "month_windows": 0, "day_windows": 0}

    rows: list[dict] = []
    admitted_total = 0
    retained_total = 0
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
            # calendar-month bounds of the refined peak, clipped to the era
            # (build_resolution_hierarchy, rh:621-632 + R8.6 clip).
            d = date_of_jd(peak_jd_true)
            month_start = date(d.year, d.month, 1)
            next_month = (date(d.year + 1, 1, 1) if d.month == 12
                          else date(d.year, d.month + 1, 1))
            month_end = next_month - timedelta(days=1)

            def _jd_of_date(dd: date) -> float:
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
        "era_windows": len(components),
        "month_windows": retained_total,
        "day_windows": retained_total,
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


def fetch_contacts(conn, chart_id: str, generation: str) -> list[dict]:
    rows = conn.execute(
        "SELECT contact_id, body, relation, target_type, target_ref,"
        " t_in, t_exact, t_out, orb_max_deg, completeness_state"
        " FROM kala_gochara_contacts"
        " WHERE chart_id = %s AND generation = %s",
        (chart_id, generation)).fetchall()
    out = []
    for (cid, body, relation, ttype, tref, t_in, t_exact, t_out,
         orb_max, completeness) in rows:
        out.append({
            "contact_id": cid, "body": body, "relation": relation,
            "target_type": ttype, "target_ref": tref,
            "orb_max_deg": float(orb_max) if orb_max is not None else None,
            "completeness_state": completeness,
            "_t_in_jd": jd_of(t_in),
            "_t_exact_jd": jd_of(t_exact) if t_exact is not None else None,
            "_t_out_jd": jd_of(t_out),
        })
    return out


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


def write_windows(conn, chart_id: str, generation: str,
                  rows: list[dict], *, source: str,
                  window_columns: set[str]) -> int:
    """Plan §4.7 idempotent rebuild: scoped DELETE (chart_id × generation)
    then INSERT, parents before children so parent_window_id resolves to the
    containing row's id. Never touches another generation. The caller holds
    the transaction."""
    ledger._require_not_published(conn, chart_id, generation, "write_windows")
    conn.execute(
        "DELETE FROM kala_gochara_windows WHERE chart_id = %s AND generation = %s",
        (chart_id, generation))
    computed_at = datetime.now(UTC)
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
    id_by_key: dict[str, int] = {}

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
    with conn.cursor() as cur:
        for row in ordered:
            cur.execute(
                f"INSERT INTO kala_gochara_windows ({', '.join(cols)})"
                f" VALUES ({placeholders}) RETURNING id",
                _values(row))
            id_by_key[row["window_key"]] = cur.fetchone()[0]
    return len(ordered)


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


def build_delta_report(*, chart_id: str, generation: str, baseline: str,
                       class_reports: list[dict], window_rows: list[dict],
                       baseline_rows: list[dict], flags: dict,
                       fingerprints: dict | None, run_meta: dict) -> str:
    """Factor-level delta report vs the baseline generation's served rows.

    The baseline ('3.0') rows carry intensities only — every factor cell for
    the baseline is an honest '—' (null), never a back-filled number."""
    lines = [
        f"# Windows factor delta report — {generation} vs {baseline}",
        "",
        f"- chart_id: `{chart_id}`",
        f"- generated: {run_meta.get('generated_at')}",
        f"- writer: `step06b_windows_projection.py` (build {run_meta.get('build_id')})",
        f"- horizon: {run_meta.get('horizon')}",
        f"- flags: `{json.dumps(flags, sort_keys=True)}`",
        f"- §12.9 fingerprints: `{json.dumps(fingerprints, sort_keys=True, default=str)}`",
        "",
        "Baseline factor cells are '—' where the baseline row set carries no",
        "such factor (the '3.0' rows store intensities, not the v3 term",
        "breakdown) — an honest null, never a 0.0 stand-in.",
        "",
        "## Per-class factors",
        "",
        "| event_class | windows 4.0 (era/month/day) | promise | permission | tārā | w30 | quality_gates | peaks admitted→retained | mean raw 4.0 | windows 3.0 | mean raw 3.0 | Δ mean raw |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    baseline_by_class: dict[str, list[dict]] = {}
    for r in baseline_rows:
        baseline_by_class.setdefault(r["event_class"], []).append(r)
    raw_by_class: dict[str, list[float]] = {}
    for r in window_rows:
        if r["resolution"] == "era":
            raw_by_class.setdefault(r["event_class"], []).append(r["raw_intensity"])
    for rep in class_reports:
        cls = rep["event_class"]
        base = baseline_by_class.get(cls, [])
        mean4 = (sum(raw_by_class.get(cls, [])) / len(raw_by_class[cls])
                 if raw_by_class.get(cls) else None)
        mean3 = (sum(float(b["raw_intensity"]) for b in base) / len(base)
                 if base else None)
        delta = (mean4 - mean3) if (mean4 is not None and mean3 is not None) else None
        fmt = lambda v: f"{v:.6f}" if isinstance(v, float) else "—"  # noqa: E731
        lines.append(
            f"| {cls} | {rep['era_windows']}/{rep['month_windows']}/{rep['day_windows']}"
            f" | {rep['promise']:.6f} | {rep['permission']:.6f}"
            f" | {rep['tara_modifier']:.3f} (skip) | {rep['w30_modifier']:.3f} (N-14)"
            f" | {fmt(rep.get('mean_quality_gates'))}"
            f" | {rep['peaks_admitted']}→{rep['peaks_retained']} (H-5 uncapped)"
            f" | {fmt(mean4)} | {len(base)} | {fmt(mean3)} | {fmt(delta)} |")
    lines += [
        "",
        "## Per-window deltas (era tier)",
        "",
        "| event_class | peak_date | raw 4.0 | signed 4.0 | valence | nearest 3.0 peak | raw 3.0 | Δ raw |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in sorted((w for w in window_rows if w["resolution"] == "era"),
                    key=lambda w: (w["event_class"], w["peak_date"])):
        base = baseline_by_class.get(r["event_class"], [])
        nearest = min(base, key=lambda b: abs((b["peak_date"] - r["peak_date"]).days),
                      default=None)
        lines.append(
            f"| {r['event_class']} | {r['peak_date']} | {r['raw_intensity']:.6f}"
            f" | {r['signed_intensity']:.6f} | {r['valence']}"
            f" | {nearest['peak_date'] if nearest else '—'}"
            f" | {float(nearest['raw_intensity']) if nearest else '—'}"
            f" | {r['raw_intensity'] - float(nearest['raw_intensity']) if nearest else '—'} |")
    lines += [
        "",
        "## Notes",
        "",
        "- PROMISE is the pinned noisy-OR over the class's resolved resonance-map weights.",
        "- PERMISSION comes from the class context input "
        f"({run_meta.get('class_context_source')}); the L1 timing-system wiring is part of the",
        "  escalated production set (ADK-0012).",
        "- tārā reports the pinned honest skip (M-3 separate Moon channel not wired here);",
        "  w30 is N-14-removed (1.0). quality_gates reproduces the F-11 no-rows path where the",
        "  overlay is absent — disclosed on every row's suppression_state.",
        "- Peak storage is H-5-uncapped (the pre-H-5 cap of 3/era is removed; the pinned 90-day",
        "  separation is retained).",
        "- '—' is an honest null: no baseline counterpart exists.",
        "",
    ]
    return "\n".join(lines)


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

        contacts = fetch_contacts(conn, args.chart_id, args.generation)
        if not contacts:
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
        for m in map_rows:
            weight_by_class.setdefault(m["event_class"], {})[m["target_ref"]] = m["weight"]
            weights_all_by_class.setdefault(m["event_class"], []).append(m["weight"])
        contacts_by_class: dict[str, list[dict]] = {}
        unmapped = 0
        unmapped_relation = 0
        for c in contacts:
            primitive = RELATION_TO_PRIMITIVE.get(c["relation"])
            if primitive is None:
                unmapped_relation += 1
                continue
            joined = False
            for m in map_rows:
                if (m["target_type"] == c["target_type"]
                        and m["target_ref"] == c["target_ref"]):
                    c2 = dict(c, _primitive=primitive)
                    contacts_by_class.setdefault(m["event_class"], []).append(c2)
                    joined = True
            if not joined:
                unmapped += 1

        gate_for_date = make_quality_gate_for_date(vedha_rows, malefic_scale)
        all_rows: list[dict] = []
        class_reports: list[dict] = []
        skipped_classes: list[dict] = []
        for cls in sorted(weights_all_by_class):
            cls_contacts = contacts_by_class.get(cls, [])
            if not cls_contacts:
                continue  # a class with no contacts honestly yields zero windows
            ctx_dict = (class_contexts.get(cls) if class_contexts
                        else _rehearsal_class_context(cls))
            if ctx_dict is None:
                skipped_classes.append({
                    "event_class": cls,
                    "reason": "no class context (permission systems) — honest "
                              "skip, never a 0.0 stand-in (plan §4.6)",
                    "contacts_matched": len(cls_contacts),
                })
                continue
            class_ctx = ClassContext(
                cls, weights_all_by_class[cls], ctx_dict["permission_systems"],
                weight_by_target_ref=weight_by_class[cls],
                class_valence=ctx_dict.get("class_valence", "mixed"),
                class_is_adverse=ctx_dict.get("class_is_adverse", False),
                context_source=ctx_dict.get("context_source", context_source))
            rows, rep = project_class_windows(
                class_ctx, cls_contacts, horizon_jd, gate_for_date,
                min_lambda=args.min_lambda,
                coarse_step_days=args.coarse_step_days)
            if rows:
                gates_mean = sum(
                    r["suppression_state"]["quality_gates"] for r in rows
                    if r["resolution"] == "era") / max(1, sum(
                        1 for r in rows if r["resolution"] == "era"))
                rep["mean_quality_gates"] = gates_mean
            all_rows.extend(rows)
            class_reports.append(rep)

        source = SOURCE_REHEARSAL if args.rehearse_synthetic else SOURCE_LIVE
        n_written = write_windows(conn, args.chart_id, args.generation,
                                  all_rows, source=source,
                                  window_columns=window_columns)
        update_manifest_windows_count(conn, args.chart_id, args.generation,
                                      n_written)
        conn.commit()
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

    flags = {**CANDIDATE_FLAGS, "orb_max_deg": args.orb_deg,
             "min_lambda": args.min_lambda,
             "coarse_step_days": args.coarse_step_days}
    run_meta = {
        "build_id": build_id,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "horizon": f"[{args.horizon_start},{args.horizon_end})",
        "class_context_source": context_source,
    }
    delta_report = build_delta_report(
        chart_id=args.chart_id, generation=args.generation,
        baseline=args.baseline_generation, class_reports=class_reports,
        window_rows=all_rows, baseline_rows=baseline_rows, flags=flags,
        fingerprints=fingerprints, run_meta=run_meta)
    if args.delta_report_out:
        Path(args.delta_report_out).write_text(delta_report)

    report = {
        "writer": "step06b_windows_projection",
        "chart_id": args.chart_id, "generation": args.generation,
        "build_id": build_id,
        "source": source,
        "flags": flags,
        "upstream_fingerprints": fingerprints,
        "contacts_read": len(contacts),
        "contacts_unmapped_no_class": unmapped,
        "contacts_unmapped_relation": unmapped_relation,
        "classes_projected": len(class_reports),
        "skipped_classes": skipped_classes,
        "windows_written": n_written,
        "windows_by_tier": {
            tier: sum(1 for r in all_rows if r["resolution"] == tier)
            for tier in ("era", "month", "day")},
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
    sys.exit(main())
