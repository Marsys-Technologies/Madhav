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
  * PERMISSION — T0-6 (FABLE #2/#3; ASTRA P1-2): evaluated AT EACH
    PROJECTION INSTANT as the FROZEN C5 object (GOCHARA_DESIGN_SPECS_v1_4
    §4.1): per-level MD/AD/PD lord, row id, licence ∈ {scored, testimony,
    none} and relation from the B5.1 relation-kind evaluator
    (services.gochara_rules.permission.period_lord_relation) over the
    document's `_dasha_periods` (L1 rows pinned to `_dasha_read_contract`
    build/tier, parent-linked, §4.0 duplicate rules), class licence = union
    over levels, Aṣṭottarī applicability named; composed into the λ factor
    with the other DR-14 generators (Vimśottarī active iff the class
    licence is `scored`; sade-sāti testimony and inapplicable systems leave
    numerator AND denominator). Memoized by the exact instant, never by
    date. Installed by main() through build_projection_class_context. When
    the context document carries no `_dasha_periods` (old documents,
    --rehearse-synthetic) the pinned static per-class constant is used
    exactly as pre-repair and the class report records
    permission_mode='static_systems_active'; a document with
    `_dasha_periods` but no `_chart` is refused. A class with matching
    contacts but NO context is skipped and recorded (skipped_classes) —
    never a 0.0 stand-in (plan §4.6).
  * ACTIVITY — the pinned noisy-OR of legacy_semantics.compute_activity_v3,
    with per-contact orb_strength = the M-1 `linear_no_box` ANGULAR kernel
    (D-RQ2, sealed doctrine FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0 finding
    N1): activity(t) = 1 − min(|Δλ(t)| / orb, 1), where Δλ(t) is the
    shortest-arc separation between the contact's ASPECT POINT at t — the
    transiting body's longitude AT t (Swiss ephemeris, engine.py's
    _get_planet_pos accessor pattern) plus the ledger's aspect_deg
    (§6.2 inv 6 forward count; 0 for non-dṛṣṭi relations) — and the
    contact's target_longitude_deg, and orb is the contact's orb_max_deg.
    A contact contributes only inside its own episode [t_in, t_out]
    (a later pass is a different contact), and role aliases of one physical
    root (same ledger independence_group) contribute once, by max (§2.1
    shared-root rule) — ASTRA_REVIEW_A5_4 P1-1. orb is the contact's orb_max_deg
    (fallback 5.0°, the --orb-deg / ACTIVITY_MAX_ORB_DEG default, when the
    column is NULL). This is exactly the algebra engine.py's
    _compute_activity_v3 applies under activity_shape='linear_no_box'
    (engine.py:1147-1155) — the flag label stays truthful; the previous
    TIME-triangle over [t_in, t_exact, t_out] was the N1 defect (it
    coincides with the angular kernel only under constant angular speed and
    is badly wrong around stations). NO ±5-day box — that is the F-08 step
    the flag retires. The span edges are the enumeration's orb crossings,
    so for monotone motion the kernel reaches 0 at t_in/t_out physically,
    not by time construction.
  * tārā — P6 TESTIMONY (S-04, O-P6-TARA; ASTRA P1-6): the λ product's
    tara term is pinned to 1.0; the nine-fold class (gochara_rules.p6.tara
    over the document's natal Moon and the transit Moon at the row's peak)
    annotates DAY rows only — P6 is the sole day-resolution source. λ is
    identical with and without the annotation; no natal Moon in _chart ⇒
    an honest skip record, never a fabricated class.
  * w30 — N-14 removed: pinned w30_modifier(enabled=False) (1.0, recorded).
  * VEDHA (quality gates) — the §5 interval gate (ASTRA P1-3) over the
    chart's T0-8 kala_vedha_gochara rows through the shared
    ka_vedha_gochara.logic.attenuation_at: active segments only (half-open),
    coverage → `unavailable` with the coverage object (null_state omit,
    never a clean 1.0), one root attenuates once, no generalised PG353
    number (D-PG353; an active obstruction is `obstructed` structure with
    factor None unless a cited scale is supplied), scoped to the primary
    graha's own contacts, Moon-primary rows testimony (day-row annotations
    only). The legacy whole-row DATE-grain multiplier is retired.
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
    len(admitted) and min_separation_days = 0: the pre-H-5 cap of 3
    (MAX_PEAKS_PER_ERA_WINDOW) is REMOVED per H-5, and the 90-day minimum
    separation is NOT applied at write time — per N5 that trim is a
    SERVE-time concern (resolution_hierarchy.py:117-127), so every admitted
    peak is stored, however closely spaced. This choice is recorded in the
    run report.
  * Era -> month -> day rows mirror build_resolution_hierarchy (calendar
    month of the refined peak clipped to the era; day row at the refined
    peak), parent_window_id wired to the containing row's id at INSERT time
    (migration 567's documentary linkage, parents inserted first).
  * valence/is_adverse — DERIVED from the three-field outcome at each row's
    own peak instant (valence := outcome_valence_for_native, is_adverse :=
    outcome == 'adverse'); the pinned netted resolve_valence_v3 verdict is
    computed for the review trail only (suppression_state.legacy_netted_
    valence). The class fallback valence comes from the class context
    (default 'mixed', disclosed).
  * THREE-FIELD VALENCE — T0-7 (FABLE #11/#12, GOCHARA_DESIGN_SPECS_v1_4 §3):
    every evaluated window row additionally carries
    evidence_for_occurrence / evidence_against_occurrence /
    outcome_valence_for_native / severity, computed AT THE ROW'S PEAK
    INSTANT from the class polarity (the class context's class_valence /
    class_is_adverse — the brahma_event_ontology declaration, reused, never
    redeclared) plus the signed channels. The three fields are INDEPENDENT:
    evidence_for is never netted against evidence_against; a contested
    occurrence (both > 0) stands as both fields positive and does NOT
    relabel the outcome 'mixed' — 'mixed' is a valence verdict from class
    polarity only. An unresolved operand (class polarity absent from the
    context document, an in-orb contact with no map weight, or — for a
    kakṣyā-crossing contact ONLY — its P5c donor row absent from the
    document's `_av_donor_matrix.available_keys`, resolved per
    '{GRAHA}-CONTRIBUTOR_{DONOR}-SIGN_{N}' key: the O-TV-3 case under
    D-SPECS C4, where a missing contributor matrix disables P5c alone and
    never disqualifies a window that consumes no P5c operand) yields
    outcome 'unqualified' with the operand NAMED in the breakdown — never
    a silent 1.0 / 'favourable' default (finding #12's E5 regression is
    what this prevents). ACTIVITY is fed |weight| so negative-only
    evidence (an adverse-class affliction) produces a window; the sign is
    consumed by the channels alone. The served valence / is_adverse
    columns and the sign of signed_intensity DERIVE from
    outcome_valence_for_native (the netted legacy verdict is kept in
    suppression_state.legacy_netted_valence for the review trail only).
    The three fields ride inside suppression_state (the served table has no
    columns for them and migrations are out of scope here); derivation is
    disclosed in suppression_state.three_field_valence on every row and in
    the class factors record.
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
from common import connect, resolve_dsn, step_parser, write_evidence  # noqa: E402

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
# N5 (FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0): the 90-day minimum peak
# separation is a SERVE-TIME trim, owned by the serving layer
# (services/gochara_v3/resolution_hierarchy.py:117-127,
# MIN_PEAK_SEPARATION_DAYS, applied per-query). This writer is
# enumeration/write-time: it must retain EVERY admitted peak so that
# closer-than-90-day peaks exist in the data and can be served (or trimmed)
# per query. The write-time separation is therefore 0 — only the H-5 count
# cap removal and retain_candidates' deterministic ranking (λ DESC, jd ASC;
# jd-sorted emission) are load-bearing here.
WRITE_TIME_MIN_PEAK_SEPARATION_DAYS = 0.0
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


# ── M-1 angular orb kernel (D-RQ2; activity_shape='linear_no_box') ──────────

# M-1 fallback orb when the ledger's orb_max_deg is NULL — the same default
# the legacy semantics (legacy_semantics.ACTIVITY_MAX_ORB_DEG) and this
# file's --orb-deg flag use.
ORB_MAX_DEG_FALLBACK = 5.0


def angular_orb_decay(body_lon_deg: float, target_lon_deg: float,
                      orb_deg: float) -> float:
    """The ruled angular kernel (D-RQ2): activity = 1 − min(|Δλ|/orb, 1.0).

    Δλ is the shortest-arc separation between the transiting body's
    longitude at the evaluation instant and the contact's target longitude
    (the engine.py:1119 idiom, abs(((lon − target + 180) % 360) − 180));
    identical to the algebra engine.py's _compute_activity_v3 applies for
    activity_shape='linear_no_box' (orb_decay_i = 1 − min(|Δ|_i /
    orb_max_deg, 1.0), engine.py:1147-1155). Pure arithmetic in longitude —
    no time interpolation anywhere; the result is in [0, 1] by the min().
    """
    orb = float(orb_deg)
    if orb <= 0.0:
        raise ValueError(f"orb_deg must be positive, got {orb_deg!r}")
    delta = abs(((float(body_lon_deg) - float(target_lon_deg) + 180.0)
                 % 360.0) - 180.0)
    return 1.0 - min(delta / orb, 1.0)


_PLANET_POS_FN = None


def _default_planet_pos_fn():
    """(body, jd) -> sidereal longitude deg, via the same Swiss-ephemeris
    accessor the engine uses (pipeline.transit_search._get_planet_pos,
    engine.py:1116). Lazily imported so the projection's pure-arithmetic
    tests need no ephemeris; memoized per (body, jd) on this projection
    object (no century-long precomputation)."""
    global _PLANET_POS_FN
    if _PLANET_POS_FN is None:
        if str(SIDECAR) not in sys.path:
            sys.path.insert(0, str(SIDECAR))
        import swisseph as swe
        from pipeline.transit_search import _get_planet_pos
        cache: dict[tuple[str, float], float] = {}

        def pos(body: str, jd: float) -> float:
            key = (body, float(jd))
            if key not in cache:
                cache[key] = float(_get_planet_pos(swe, body, float(jd))[0])
            return cache[key]

        _PLANET_POS_FN = pos
    return _PLANET_POS_FN


# ── T0-6 per-instant permission (FABLE #2/#3) ────────────────────────────────


def _sade_sati_testimony_renormalize(permission: float, detail: dict):
    """N-15 (candidate flag sade_sati_mode='testimony', mirrored from
    engine.py:1900-1902): sade sāti ANNOTATES, never weights — its weight
    leaves both the numerator (when active) and the denominator. The
    pre-renormalization value is kept in the detail for the review trail.
    No sade-sati term is introduced by this wiring: the generator was
    already one of the twelve in permission.compute_permission; this strips
    its weight so the projection honours the flag it declares."""
    systems = detail.get("systems") or []
    ss = next((s for s in systems if s.get("system_id") == "sade_sati"), None)
    if ss is None:
        return permission, detail
    w_ss = float(ss.get("weight") or 0.0)
    active_weight = sum(float(s["weight"]) for s in systems if s.get("active"))
    if ss.get("active"):
        active_weight -= w_ss
    total = sum(float(s["weight"]) for s in systems) - w_ss
    newp = active_weight / total if total else 0.0
    d2 = dict(detail)
    d2["systems_active"] = [s for s in detail.get("systems_active", [])
                            if s != "sade_sati"]
    d2["sade_sati_mode"] = "testimony"
    d2["sade_sati_testimony"] = {
        "active": bool(ss.get("active")),
        "detail": ss.get("detail"),
        "legacy_permission_including_sade_sati": permission,
        "note": "N-15: testimony, never weight (mirrors engine.py:1900-1902)",
    }
    return newp, d2


# ── frozen C5 permission (GOCHARA_DESIGN_SPECS_v1_4 §4, D-SPECS C5) ─────────
#
# ASTRA_REVIEW_A5_4 P1-2: the per-instant licence is the FROZEN §4.1 object,
# evaluated from the L1 chart_dashas rows the class-context document carries
# (`_dasha_periods`, read per §4.0) and the chart operands it carries
# (`_chart`): per level (MD/AD/PD) the lord, its row id, its licence ∈
# {scored, testimony, none} from the P1 relation-kind table
# (services.gochara_rules.permission.period_lord_relation — the B5.1
# implementation, reused, never duplicated) and the relation; class-level
# licence = union over levels (licensed iff some level is `scored`;
# testimony annotates and never licenses); Aṣṭottarī applicability with both
# failed conditions named. Rows are pinned to the document's read contract
# (build_id, tier two_pass_verified), parent-linked (an AD only under its MD,
# a PD only under its AD — an orphan is ignored and reported, never
# accepted), and a conflicting duplicate (same level/parent/start, any
# contract field differing) raises DashaReadConflict — never silently
# picked. Memoization is by the EXACT instant: a date bucket would put the
# half-open boundary instant 2020-02-14T11:47:23Z (Rahu) and 00:00 of the
# same day (Mars) in one cell.

VIMSHOTTARI = "vimshottari"
PERMISSION_CONTRACT = "frozen_c5:GOCHARA_DESIGN_SPECS_v1_4 §4.1 (D-SPECS C5)"
# N-15: testimony systems annotate, never weight — out of the fraction.
TESTIMONY_SYSTEMS = frozenset({"sade_sati"})
def utc_iso_of_jd(t_jd: float) -> str:
    """The UTC instant the licence is evaluated at (§4.0 instant rule: the
    read prints the UTC instant it evaluated) — the JD converted EXACTLY
    (microsecond precision, never rounded: a 10 ms rounding advanced
    2020-02-14T11:47:22.999Z into the Rahu AD — ASTRA v1.1). A JD float
    carries ~40 µs of slack; a caller holding the exact instant passes it
    as `t_iso` to select_period_rows / frozen_c5_permission_context and it
    is used verbatim."""
    secs = (float(t_jd) - JD_UNIX_EPOCH) * 86400.0
    return datetime.fromtimestamp(secs, tz=UTC).isoformat(timespec="microseconds")


def _rowv(row: dict, key: str):
    v = row.get(key)
    return None if v is None else str(v)


def select_period_rows(dasha_rows: list[dict], t_jd: float, *,
                       system: str = VIMSHOTTARI,
                       pinned_build_id: str | None = None,
                       tier: str | None = None,
                       t_iso: str | None = None) -> dict:
    """§4.0 row selection at t: PIN first (build / tier — under an explicit
    pin a row with a NULL pin field is REJECTED, never accepted), then the
    duplicate rules (dasha_data.canonicalize_multilevel_rows: identical
    collapse with parent-alias canonicalization, sibling `index`, and the
    `(level, parent, index)` overlap conflict over the WHOLE pinned set —
    not only the rows covering t), then half-open [start_iso, end_iso)
    parent-linked selection per level at the EXACT instant."""
    from services.gochara_grammar import dasha_data as DD
    t_iso = t_iso or utc_iso_of_jd(t_jd)
    excluded = {"other_system": 0, "other_build": 0, "other_tier": 0,
                "missing_build_id": 0, "missing_tier": 0}
    rows = []
    for r in dasha_rows:
        if _rowv(r, "system_id") != system:
            excluded["other_system"] += 1
            continue
        if pinned_build_id:
            b = _rowv(r, "build_id")
            if b is None:
                excluded["missing_build_id"] += 1
                continue
            if b != str(pinned_build_id):
                excluded["other_build"] += 1
                continue
        if tier:
            tr = _rowv(r, "verification_pass_status")
            if tr is None:
                excluded["missing_tier"] += 1
                continue
            if tr != tier:
                excluded["other_tier"] += 1
                continue
        rows.append(dict(r))
    rows = DD.canonicalize_multilevel_rows(rows)

    orphans: list[dict] = []

    def covering(level: int, parent_id: str | None):
        hits = []
        for r in rows:
            if int(r.get("level_n") or 0) != level:
                continue
            if not DD.period_contains(r, t_iso):
                continue
            if level > 1 and _rowv(r, "parent_row_id") != parent_id:
                orphans.append({"level_n": level,
                                "dasha_row_id": _rowv(r, "dasha_row_id"),
                                "parent_row_id": _rowv(r, "parent_row_id"),
                                "lord": r.get("lord_graha"),
                                "reason": "parent is not the selected "
                                          f"level-{level - 1} row {parent_id}"})
                continue
            hits.append(r)
        if not hits:
            return None
        if len(hits) > 1:
            # cannot happen after canonicalize_multilevel_rows (identical
            # duplicates collapsed; overlapping siblings raised) — defensive
            raise DD.DashaReadConflict(
                f"chart_dashas §4.0: {len(hits)} rows cover {t_iso} at level "
                f"{level} under parent {parent_id} — both rejected")
        return dict(hits[0])

    md = covering(1, None)
    ad = covering(2, _rowv(md, "dasha_row_id")) if md else None
    pd = covering(3, _rowv(ad, "dasha_row_id")) if ad else None
    return {"t_utc": t_iso, "md": md, "ad": ad, "pd": pd,
            "orphans_ignored": orphans, "rows_excluded": excluded,
            "rows_considered": len(rows)}


def c5_relation_record_id(lord: str, relation: str, event_class: str,
                          chart: dict, licence: str) -> str | None:
    """The C5 relation IDENTITY (§4.1: `relation` names the natal relation
    kind AND its record id): the §1 relationship_record for the period
    lord's natal relation to the class, built with the B5.1 record type
    (deterministic record_id over the natural key). None when the relation
    is `none`/`unknown`."""
    from services.gochara_rules.frames import SIGN_LORDS, sign_of
    from services.gochara_rules.records import RelationshipRecord
    from services.gochara_rules.registry import RULE_VERSION, signature_houses
    if relation in ("none", "unknown"):
        return None
    natal = chart["natal"]
    houses = signature_houses(event_class, chart) or frozenset()
    if relation == "occupancy":
        obj_sign = sign_of(natal[lord])
        agent, role = lord, "occupant"
    elif relation == "ownership":
        owned = sorted(s for s in houses if SIGN_LORDS[s] == lord)
        obj_sign, agent, role = owned[0], lord, "lord"
    elif relation == "dispositorship":
        disp = SIGN_LORDS[sign_of(natal[lord])]
        if disp in natal and sign_of(natal[disp]) in houses:
            obj_sign = sign_of(natal[disp])
        else:
            owned = sorted(s for s in houses if SIGN_LORDS[s] == disp)
            obj_sign = owned[0] if owned else sign_of(natal[lord])
        agent, role = disp, "dispositor"
    else:
        return None
    rec = RelationshipRecord(
        chart_id=str(chart.get("chart_id", "")), generation="4.0",
        event_class=event_class, affected_person="native", frame="lagna",
        agent=agent, relation=relation, object_id=f"obj:sign:{obj_sign}",
        object_kind="sign_span", object_role=role, contact_id=None,
        path_id="P1", rule_version=RULE_VERSION, prerequisites=[],
        provenance="verse_cited" if licence == "scored" else "uncited_extension",
        operator_role=licence if licence in ("scored", "testimony") else "testimony",
        ruling_ref=None if licence == "scored" else "D-PADMIT",
        source_text="Phaladīpikā", source_page="PG249-250 (XX.34-38)")
    return rec.record_id


def frozen_c5_permission_context(dasha_rows: list[dict], t_jd: float,
                                 event_class: str, chart: dict, *,
                                 pinned_build_id: str | None = None,
                                 tier: str | None = None,
                                 t_iso: str | None = None) -> dict:
    """§4.1: permission(chart_id, t, event_class) → {admitted_paths,
    period_context{system, build_id, md/ad/pd{lord, row_id, index, licence,
    relation, relation_record_id}, applicability}, class_licence}.
    Per-level licences via the B5.1 relation-kind evaluator; levels never
    collapsed into one boolean; the relation identity is the §1 record id."""
    from brahmagyan.graha_vocabulary import to_title
    from services.gochara_rules.permission import (
        applicability, period_lord_relation)
    sel = select_period_rows(dasha_rows, t_jd, pinned_build_id=pinned_build_id,
                             tier=tier, t_iso=t_iso)
    period_context: dict = {"system": VIMSHOTTARI, "build_id": pinned_build_id,
                            "tier": tier, "t_utc": sel["t_utc"]}
    licences = []
    for level in ("md", "ad", "pd"):
        row = sel[level]
        if row is None:
            period_context[level] = {"lord": None, "row_id": None,
                                     "licence": "none", "relation": "none",
                                     "detail": "no covering row"}
            continue
        lord = to_title(row.get("lord_graha")) or str(row.get("lord_graha"))
        rel = period_lord_relation(lord, event_class, chart)
        period_context[level] = {
            "lord": lord, "row_id": _rowv(row, "dasha_row_id"),
            "index": row.get("index"),
            "merged_row_ids": row.get("merged_row_ids"),
            "parent_row_id": _rowv(row, "parent_row_id"),
            "start_iso": _rowv(row, "start_iso"), "end_iso": _rowv(row, "end_iso"),
            "licence": rel["licence"], "relation": rel["relation"],
            "relation_record_id": c5_relation_record_id(
                lord, rel["relation"], event_class, chart, rel["licence"]),
            "detail": rel["detail"]}
        licences.append(rel["licence"])
    class_licence = ("scored" if "scored" in licences
                     else "testimony" if "testimony" in licences else "none")
    period_context["applicability"] = applicability(chart)
    period_context["orphans_ignored"] = sel["orphans_ignored"]
    period_context["rows_excluded"] = sel["rows_excluded"]
    return {"contract": PERMISSION_CONTRACT,
            "admitted_paths": ["P1"] if class_licence == "scored" else [],
            "period_context": period_context,
            "class_licence": class_licence}


def frozen_permission_value(legacy_detail: dict, c5: dict) -> tuple[float, dict]:
    """The λ PERMISSION factor under the frozen contract, composed from the
    DR-14 generator table the legacy evaluator produced:
      * Vimśottarī is active iff the C5 class licence is `scored` (the
        per-level union; testimony never licenses) — the legacy any-row
        lord match is replaced, not supplemented;
      * testimony systems (N-15 sade_sati) leave numerator AND denominator;
      * a system whose applicability is `absent` (Aṣṭottarī on this chart,
        D-RQ7) leaves numerator AND denominator — absent, not false-weighted.
    Everything excluded is listed with its reason; the legacy value is kept
    for the review trail."""
    systems = [dict(sx) for sx in (legacy_detail.get("systems") or [])]
    excluded = []
    applicability = c5["period_context"].get("applicability") or {}
    absent_systems = ({applicability.get("system")}
                      if applicability.get("state") == "absent" else set())
    included = []
    for sx in systems:
        sid = sx.get("system_id")
        if sid == VIMSHOTTARI:
            sx["active"] = c5["class_licence"] == "scored"
            sx["licence_source"] = PERMISSION_CONTRACT
            sx["class_licence"] = c5["class_licence"]
            sx["detail"] = {lvl: c5["period_context"][lvl]
                            for lvl in ("md", "ad", "pd")}
        if sid in TESTIMONY_SYSTEMS:
            excluded.append({"system_id": sid, "reason": "testimony (N-15) — "
                             "annotates, never weights", "active": sx.get("active"),
                             "detail": sx.get("detail")})
            continue
        if sid in absent_systems:
            excluded.append({"system_id": sid, "reason": "inapplicable — "
                             f"{applicability.get('failed_conditions')}",
                             "active": sx.get("active")})
            continue
        included.append(sx)
    total = sum(float(sx.get("weight") or 0.0) for sx in included)
    active_w = sum(float(sx.get("weight") or 0.0) for sx in included if sx.get("active"))
    value = active_w / total if total else 0.0
    detail = {
        **legacy_detail,
        "systems": included,
        "systems_active": [sx["system_id"] for sx in included if sx.get("active")],
        "systems_considered": [sx["system_id"] for sx in included],
        "system_count_active": sum(1 for sx in included if sx.get("active")),
        "systems_excluded": excluded,
        "permission_contract": PERMISSION_CONTRACT,
        "class_licence": c5["class_licence"],
        "admitted_paths": c5["admitted_paths"],
        "period_context": c5["period_context"],
        "sade_sati_mode": "testimony",
        "legacy_permission_value": legacy_detail.get("_legacy_permission"),
    }
    return value, detail


def make_per_instant_permission_fn(conn, chart_id: str, event_class: str,
                                   dasha_periods: list[dict], chart: dict, *,
                                   pinned_build_id: str | None = None,
                                   tier: str | None = None):
    """permission_fn(t_jd) -> (permission, detail) for one event class:
    the frozen C5 licence (frozen_c5_permission_context) composed with the
    other DR-14 generators (gochara_intensity.permission.compute_permission
    — the legacy evaluator supplies the non-Vimśottarī generator rows) via
    frozen_permission_value. Returns None when the class's targets do not
    resolve (the caller records the class as skipped, never a fabricated
    context). Memoized by the EXACT instant (never by date)."""
    if str(SIDECAR) not in sys.path:
        sys.path.insert(0, str(SIDECAR))
    import swisseph as swe
    from services.gochara_grammar.resonance_map import fetch_resonance_targets
    from services.gochara_intensity import enrichment
    from services.gochara_intensity import permission as perm

    targets = enrichment.enrich_targets(
        conn, fetch_resonance_targets(conn, chart_id, event_class))
    if not targets:
        return None
    cache: dict[float, tuple[float, dict]] = {}

    def at(t_jd: float):
        key = float(t_jd)
        if key not in cache:
            c5 = frozen_c5_permission_context(
                dasha_periods, t_jd, event_class, chart,
                pinned_build_id=pinned_build_id, tier=tier)
            raw, detail = perm.compute_permission(
                swe, conn, chart_id, event_class, targets, t_jd,
                dasha_periods=dasha_periods)
            detail = {**detail, "_legacy_permission": raw}
            cache[key] = frozen_permission_value(detail, c5)
        return cache[key]

    return at


def build_projection_class_context(conn, chart_id: str, event_class: str,
                                   ctx_dict: dict, doc: dict | None, *,
                                   weights: list[float],
                                   weight_by_target_ref: dict[str, float],
                                   context_source: str,
                                   permission_factory=None):
    """The ONE constructor path main() uses for a class's ClassContext
    (ASTRA P1-2: the per-instant permission function must be INSTALLED on
    the executable path, not merely defined). When the document carries
    `_dasha_periods` AND `_chart`, the frozen C5 per-instant function is
    built by `permission_factory` (default make_per_instant_permission_fn)
    and installed; a factory result of None means the class's targets did
    not resolve → returns None (caller skips the class). A document with
    `_dasha_periods` but no `_chart` is refused (ValueError): the frozen
    licence cannot be evaluated without the chart operands — never a silent
    static fallback. Documents without `_dasha_periods` (old documents,
    --rehearse-synthetic) keep the pinned static fallback, disclosed."""
    factory = permission_factory or make_per_instant_permission_fn
    doc = doc or {}
    permission_fn = None
    dasha_rows = doc.get("_dasha_periods")
    if dasha_rows is not None:
        chart = doc.get("_chart")
        if not chart:
            raise ValueError(
                "class-context document carries _dasha_periods but no _chart "
                "operands — the frozen C5 licence (GOCHARA_DESIGN_SPECS_v1_4 "
                "§4.1) cannot be evaluated; regenerate the document with the "
                "repaired step06a_class_context.py")
        contract = doc.get("_dasha_read_contract") or {}
        permission_fn = factory(
            conn, chart_id, event_class, dasha_rows, chart,
            pinned_build_id=contract.get("build_id"),
            tier=contract.get("tier"))
        if permission_fn is None:
            return None
    return ClassContext(
        event_class, weights, ctx_dict["permission_systems"],
        weight_by_target_ref=weight_by_target_ref,
        class_valence=ctx_dict.get("class_valence", "mixed"),
        class_is_adverse=ctx_dict.get("class_is_adverse", False),
        context_source=ctx_dict.get("context_source", context_source),
        permission_fn=permission_fn,
        unresolved_valence_operands=ctx_dict.get(
            "valence_unresolved_operands", ()),
        av_donor_keys=(doc.get("_av_donor_matrix") or {}).get("available_keys"),
        natal_moon_deg=((doc.get("_chart") or {}).get("natal") or {}).get("Moon"))


# ── T0-7 three-field valence (FABLE #11/#12; GOCHARA_DESIGN_SPECS_v1_4 §3) ───

# The §3.1 enum, verbatim. 'unqualified' is a first-class verdict — the
# honest state when an operand is unresolved (ADK-0026), never a
# favourable-sounding default.
OUTCOME_VALENCE_ENUM = ("favourable", "adverse", "mixed", "unqualified")
VALENCE_CONTRACT = "three_field_valence:v1 (GOCHARA_DESIGN_SPECS_v1_4 §3)"

# The class-polarity declaration vocabulary, exactly as declared by
# brahma_event_ontology.evidence_requirements->>'valence' (the live field
# gochara_intensity.valence reads; VALENCE_MAP is its documented fixture).
# A context document carrying anything outside this set (or nothing) leaves
# the polarity operand UNRESOLVED — the channels cannot be oriented
# class-relatively without it.
_CLASS_VALENCE_KNOWN = frozenset({"gain", "loss", "neutral", "mixed"})

# T0-7 / O-TV-3 operand name for the P5c per-contributor BAV matrix. D-SPECS
# C4 (GOCHARA_DESIGN_SPECS_v1_4 §2.2 missing-input matrix, §8.2 inv 4): a
# missing contributor matrix disables **P5c alone** — it never disqualifies
# a window whose evidence rests on no kakṣyā crossing, and it is resolved
# PER KEY ('{GRAHA}-CONTRIBUTOR_{DONOR}-SIGN_{N}', the ga_strength_writer
# scheme), never chart-wide from one unrelated row (ASTRA P1-4).
AV_DONOR_OPERAND = "av_donor_matrix"
P5C_RELATION = "kakshya_cell_crossing"


def kakshya_donor_key(body: str, target_lon_deg: float) -> tuple[str, dict]:
    """The P5c donor row a kakṣyā crossing consumes (Phaladīpikā XXIII,
    PG301: fruit delivered in the cell owned by the mark-donor). The crossed
    boundary's cell is the one it opens (division order Saturn → Lagna,
    primitives._KAKSHYA_LORD_ORDER); sign N is the absolute rāśi 1–12 of
    the boundary degree. Returns (writer-scheme key, detail)."""
    from brahmagyan.graha_vocabulary import norm_graha
    from services.gochara_grammar.primitives import (
        kakshya_index_for_degree_in_sign, kakshya_lord_for_index)
    lon = float(target_lon_deg) % 360.0
    sign_n = int(lon // 30.0) + 1
    idx = kakshya_index_for_degree_in_sign(lon)
    lord = kakshya_lord_for_index(idx)
    key = f"{norm_graha(body)}-CONTRIBUTOR_{norm_graha(lord)}-SIGN_{sign_n}"
    return key, {"sign_number": sign_n, "kakshya_index": idx,
                 "kakshya_lord": lord, "donor_row_key": key}


def three_field_valence(supportive_channel: float, afflicting_channel: float,
                        *, class_valence: str | None, class_is_adverse: bool,
                        unresolved_operands=()) -> dict:
    """GOCHARA_DESIGN_SPECS_v1_4 §3 on the '4.0' projection path (T0-7;
    sealed doctrine FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0 findings
    #11/#12). Computed at evaluation time from class polarity + the signed
    channels — never copied class-blind from a rule row (§3.2 inv 4).

    Semantic choices (each disclosed, none improvised):

      * EVIDENCE ORIENTATION IS CLASS-RELATIVE (§3.1): for an ADVERSE class
        (class_is_adverse — the loss classes plus the documented
        psychological_arc override in gochara_intensity.valence) the
        afflicting channel is evidence FOR occurrence and the supportive
        channel evidence AGAINST (the spec's own example: a 7th-house
        affliction is evidence for the separation class, against the
        marriage class). For every other class the direct reading holds:
        supportive → for, afflicting → against. Magnitudes are the D-SPECS
        C2 channel sums (max per root per channel, Σ across roots;
        c2_evidence_channels) — rank-only, never gates; they may exceed 1.
      * NO NETTING (§3.2 inv 1, O-TV-2): the two evidence fields are
        reported as they stand. Nothing anywhere computes
        evidence_for − evidence_against; a contested occurrence (both > 0)
        is reported as contested, never cancelled to neutral.
      * OUTCOME IS A POLARITY VERDICT, not an evidence verdict (S-03):
        unresolved operand → 'unqualified'; else class_is_adverse →
        'adverse'; else class_valence == 'mixed' → 'mixed'; else
        'favourable'. The gain|neutral → 'favourable' reading is pinned by
        O-TV-2 (marriage is 'neutral' in the ontology, and its occurrence —
        even when contested — is favourable for the native): 'neutral' tags
        the class as not-inherently-loss, it is NOT a third outcome. The
        signed-channel balance NEVER enters the verdict, so contested
        occurrence cannot relabel the outcome 'mixed' (the O-TV-2 mutation)
        and the all-favourable era table (#12, E5) cannot reappear — a
        loss-class window is 'adverse' by polarity alone.
      * UNRESOLVED OPERANDS (§3.2 inv 3, O-TV-3, ADK-0026): any entry in
        unresolved_operands — or an out-of-vocabulary/absent class_valence
        (operand 'class_polarity') — makes the outcome 'unqualified' and
        names every unresolved operand in the breakdown. No silent 1.0, no
        'favourable' default. When the polarity itself is unresolved the
        channels cannot be oriented, so both evidence fields are honest
        nulls (None), not 0.0 stand-ins; otherwise the evidence fields are
        still reported (the occurrence evidence is computable; only the
        verdict is withheld).
      * SEVERITY (§1.1: interpretive, rank-only, never a gate) is the
        occurrence-strength reading evidence_for_occurrence — how strongly
        the event itself is evidenced, independent of whether that
        occurrence is good for the native (signed_intensity already carries
        the sign). None when the evidence fields are null.
    """
    unresolved = list(unresolved_operands)
    polarity_known = class_valence in _CLASS_VALENCE_KNOWN
    if not polarity_known:
        unresolved.append("class_polarity")
    if polarity_known:
        # class-relative orientation (see docstring)
        if class_is_adverse:
            ev_for, ev_against = afflicting_channel, supportive_channel
            orientation = "adverse_class:afflicting=for,supportive=against"
        else:
            ev_for, ev_against = supportive_channel, afflicting_channel
            orientation = "non_adverse_class:supportive=for,afflicting=against"
    else:
        ev_for = ev_against = None
        orientation = "unoriented:class_polarity unresolved"
    if unresolved:
        outcome = "unqualified"
    elif class_is_adverse:
        outcome = "adverse"
    elif class_valence == "mixed":
        outcome = "mixed"
    else:
        outcome = "favourable"
    return {
        "evidence_for_occurrence": ev_for,
        "evidence_against_occurrence": ev_against,
        "outcome_valence_for_native": outcome,
        "severity": ev_for,
        "breakdown": {
            "contract": VALENCE_CONTRACT,
            "class_valence": class_valence,
            "class_is_adverse": class_is_adverse,
            "supportive_channel": supportive_channel,
            "afflicting_channel": afflicting_channel,
            "orientation": orientation,
            "unresolved_operands": unresolved,
            "derivation": (
                "evidence fields = signed channels oriented by class "
                "polarity (never netted); outcome = polarity verdict "
                "(unqualified if any operand unresolved; adverse if "
                "class_is_adverse; mixed iff class_valence=='mixed'; else "
                "favourable); severity = evidence_for_occurrence "
                "(rank-only, never a gate)"),
        },
    }


# ── tārā: P6 testimony annotation on day rows (S-04, O-P6-TARA; ASTRA P1-6) ──

NAKSHATRA_ARC_DEG = 360.0 / 27.0
TARA_CONTRACT = "P6 tārā testimony (GOCHARA_DESIGN_SPECS_v1_4 §2.2 P6; S-04; D-PADMIT)"


def nakshatra_index_1based(longitude_deg: float) -> int:
    """1..27 (Aśvinī = 1) — the gochara_rules.p6.tara index convention."""
    idx = int((float(longitude_deg) % 360.0) // NAKSHATRA_ARC_DEG) + 1
    return max(1, min(27, idx))


def make_tara_annotator(natal_moon_deg, planet_pos_fn):
    """annotator(jd) -> the P6 tārā testimony record for a DAY row: the
    nine-fold class of the transit Moon's nakṣatra counted from the janma
    nakṣatra (services.gochara_rules.p6.tara — reused; weight 0.0, operator
    testimony). It annotates only: the λ product's tara term is pinned to
    1.0 (ClassContext.tara). natal_moon_deg None ⇒ an honest skip record,
    never a fabricated class."""
    from services.gochara_rules.p6 import tara as p6_tara

    def annotate(jd: float) -> dict:
        if natal_moon_deg is None:
            return {"contract": TARA_CONTRACT, "state": "skipped",
                    "operator_role": "testimony",
                    "reason": "natal Moon longitude absent from the context "
                              "document's _chart operands"}
        moon_lon = float(planet_pos_fn("Moon", jd))
        natal_idx = nakshatra_index_1based(natal_moon_deg)
        transit_idx = nakshatra_index_1based(moon_lon)
        term = p6_tara(natal_idx, transit_idx)
        return {"contract": TARA_CONTRACT, "state": "annotated",
                "natal_moon_deg": float(natal_moon_deg),
                "transit_moon_deg": moon_lon,
                "natal_nakshatra_index": natal_idx,
                "transit_nakshatra_index": transit_idx,
                **term}

    return annotate


# ── per-class lambda evaluator ───────────────────────────────────────────────


class ClassContext:
    """The once-per-(chart, class) factor context (plan §4.5)."""

    def __init__(self, event_class: str, weights: list[float],
                 permission_systems: dict[str, bool],
                 *, weight_by_target_ref: dict[str, float],
                 class_valence: str = "mixed", class_is_adverse: bool = False,
                 context_source: str = "class_context_json",
                 permission_fn=None, unresolved_valence_operands=(),
                 av_donor_keys=None, natal_moon_deg=None):
        self.event_class = event_class
        self.weight_by_target_ref = dict(weight_by_target_ref)
        self.abs_weight_by_target_ref = {
            k: abs(float(v)) for k, v in self.weight_by_target_ref.items()}
        # ASTRA_REVIEW_A5_4 v1.1 P1-1: PROMISE is the class's occurrence
        # promise — the MAGNITUDE of each resonance weight. The pinned
        # compute_promise clamps a negative map weight to 0, so a class whose
        # only targets carry negative weights (adverse-class evidence) had
        # PROMISE 0 ⇒ λ 0 ⇒ no window on the production construction path
        # (main() passes the signed map weights). The sign is consumed by
        # the evidence channels alone (§3 class-relative polarity).
        self.promise_weights_signed = [float(w) for w in weights]
        self.promise, self.promise_detail = leg.compute_promise(
            [abs(w) for w in self.promise_weights_signed])
        self.promise_detail = {
            **self.promise_detail,
            "weights_signed": self.promise_weights_signed,
            "magnitude_rule": "PROMISE uses |weight|; sign → evidence channels "
                              "(ASTRA v1.1 P1-1)",
        }
        # T0-6 (FABLE #2/#3): when permission_fn is given, PERMISSION is
        # evaluated AT EACH INSTANT (per-instant MD/AD/PD plurality over the
        # class context's `_dasha_periods`); the constructor constant is then
        # not computed (self.permission is None — never served as a stand-in).
        # Without it (old context documents, --rehearse-synthetic) the pinned
        # static per-class constant is kept exactly as pre-repair.
        self.permission_fn = permission_fn
        self.permission_mode = ("per_instant_md_ad_pd" if permission_fn is not None
                                else "static_systems_active")
        self.permission = (None if permission_fn is not None
                           else leg.compute_permission(permission_systems))
        self.permission_systems = dict(permission_systems)
        self.class_valence = class_valence
        self.class_is_adverse = class_is_adverse
        # T0-7: class-level unresolved valence operands declared by the
        # context document (e.g. 'av_donor_matrix' when the P5c contributor
        # matrix is absent — O-TV-3's exact fixture condition). Every window
        # row of the class then evaluates with these operands unresolved:
        # outcome 'unqualified', operands named in the breakdown.
        self.unresolved_valence_operands = tuple(unresolved_valence_operands)
        # P5c donor matrix (D-SPECS C4 scoping, ASTRA P1-4): the set of
        # contributor-row keys the context document found for the chart
        # (step06a `_av_donor_matrix.available_keys`); None when the document
        # carries no such block (old documents / rehearsal). Consulted ONLY
        # for kakṣyā-crossing contacts — the sole P5c consumer — per key.
        self.av_donor_keys = (None if av_donor_keys is None
                              else frozenset(av_donor_keys))
        self.context_source = context_source
        # tārā (S-04 / O-P6-TARA; ASTRA P1-6): a P6 Moon-channel operator is
        # TESTIMONY — the λ product's tara term is pinned to 1.0 and the
        # nine-fold class annotates DAY rows only (make_tara_annotator over
        # the document's natal Moon; None ⇒ honest skip on the annotation).
        self.natal_moon_deg = (None if natal_moon_deg is None
                               else float(natal_moon_deg))
        self.tara = {
            "modifier": 1.0, "operator_role": "testimony",
            "contract": TARA_CONTRACT,
            "skipped": self.natal_moon_deg is None,
            "skip_reason": (None if self.natal_moon_deg is not None else
                            "natal Moon longitude absent from _chart — "
                            "annotation skipped (never weights either way)"),
            "annotation_path": "day rows only (P6 is the sole day-resolution source)",
        }
        # N-14: nodal dṛṣṭi removed — the pinned disabled path (modifier 1.0).
        self.w30 = leg.w30_modifier(None, [], enabled=False)

    def class_level_unresolved_operands(self) -> tuple:
        """Operands unresolved for EVERY window of the class. The P5c donor
        matrix is excluded here by D-SPECS C4 — it gates P5c consumers only
        (scoped per kakṣyā contact in make_eval_fn), never the class."""
        return tuple(op for op in self.unresolved_valence_operands
                     if op != AV_DONOR_OPERAND)

    def p5c_operand_state(self, contact: dict) -> dict | None:
        """For a kakṣyā-crossing contact: the donor operand's resolution.
        None for every other relation (no P5c operand is consumed). A
        document without the matrix block (av_donor_keys None) resolves the
        operand as unresolved only when the legacy chart-level declaration
        named it — and still only on this P5c consumer, never chart-wide."""
        if contact.get("relation") != P5C_RELATION:
            return None
        key, detail = kakshya_donor_key(contact["body"],
                                        contact["_target_lon_deg"])
        if self.av_donor_keys is None:
            legacy_declared = AV_DONOR_OPERAND in self.unresolved_valence_operands
            return {**detail, "state": ("unresolved" if legacy_declared
                                        else "not_probed"),
                    "operand": f"{AV_DONOR_OPERAND}:{key}"}
        return {**detail,
                "state": "resolved" if key in self.av_donor_keys else "unresolved",
                "operand": f"{AV_DONOR_OPERAND}:{key}"}

    def permission_at(self, t_jd: float):
        """(permission, detail) at the evaluation instant. Per-instant mode
        delegates to permission_fn; static mode returns the pinned constant."""
        if self.permission_fn is not None:
            return self.permission_fn(t_jd)
        return self.permission, {
            "systems_active": sorted(
                s for s, on in self.permission_systems.items() if on),
            "mode": "static_systems_active",
        }

    def factors_record(self) -> dict:
        per_instant = self.permission_fn is not None
        return {
            "event_class": self.event_class,
            "promise": self.promise,
            "promise_target_count": self.promise_detail["target_count"],
            # T0-6: in per-instant mode PERMISSION varies with t — the class
            # record carries None (never a constant stand-in) plus the mode;
            # the licence at each window's own instant is on the row's
            # contributing_systems / suppression_state.permission_detail.
            "permission": None if per_instant else self.permission,
            "permission_mode": self.permission_mode,
            "permission_contract": PERMISSION_CONTRACT if per_instant else None,
            "permission_systems_active": (
                None if per_instant else sorted(
                    s for s, on in self.permission_systems.items() if on)),
            "tara_modifier": self.tara["modifier"],
            "tara_skip_reason": self.tara["skip_reason"],
            "w30_modifier": self.w30["modifier"],
            "w30_skip_reason": self.w30["skip_reason"],
            "class_valence": self.class_valence,
            "class_is_adverse": self.class_is_adverse,
            # T0-7 (FABLE #11/#12, §3): the class factors record carries the
            # three-field contract id and the CLASS-LEVEL polarity verdict
            # (polarity alone — the per-window evaluation-time verdict and
            # evidence fields live on each window row's suppression_state.
            # The evidence/severity quantities are per-instant, so the
            # class-level cells are honest nulls, never stand-ins).
            "valence_contract": VALENCE_CONTRACT,
            "evidence_for_occurrence": None,
            "evidence_against_occurrence": None,
            "outcome_valence_for_native": three_field_valence(
                0.0, 0.0, class_valence=self.class_valence,
                class_is_adverse=self.class_is_adverse,
                unresolved_operands=self.class_level_unresolved_operands()
            )["outcome_valence_for_native"],
            "severity": None,
            "valence_unresolved_operands": sorted(
                self.class_level_unresolved_operands()),
            # D-SPECS C4: the P5c operand is per-window/per-key, never a
            # class-level verdict input; its availability is reported here.
            "av_donor_matrix_keys_available": (
                None if self.av_donor_keys is None else len(self.av_donor_keys)),
            "context_source": self.context_source,
        }


def contact_aspect_point_deg(body_lon_deg: float, aspect_deg: float) -> float:
    """The longitude the contact's relation actually touches (§6.2 inv 6,
    T0-1): a dṛṣṭi from body b falls at (λ_b + aspect_deg) mod 360 — the
    FORWARD count (Mars 4th/8th +90°/+210°, Saturn 3rd/10th +60°/+270°,
    Jupiter 5th/9th +120°/+240°, the 7th +180°). A conjunction/return/
    ingress carries aspect_deg 0 (the ledger stores 0 for every non-dṛṣṭi
    relation, step06_enumerate_episodes._episode_to_dict) so the point is
    the body itself. Reading Δλ from the bare body longitude for a dṛṣṭi
    contact scored every exact aspect 0 (ASTRA_REVIEW_A5_4 P1-1)."""
    return (float(body_lon_deg) + float(aspect_deg or 0.0)) % 360.0


def contact_supports(c: dict, t_jd: float) -> bool:
    """Episode support (§6.1 occurrence identity; ASTRA P1-1): a contact is
    ONE solved crossing with its own in-orb interval [t_in, t_out]; outside
    it the contact is absent — a later pass of the same body over the same
    target is a DIFFERENT contact (its own occurrence ordinal) and must not
    contribute at the first pass's instants. Closed on both ends: the span
    edges are the enumeration's orb crossings where the kernel is 0 anyway
    for monotone motion."""
    t_in, t_out = c.get("_t_in_jd"), c.get("_t_out_jd")
    if t_in is not None and t_jd < t_in:
        return False
    if t_out is not None and t_jd > t_out:
        return False
    return True


def contact_root_key(c: dict):
    """The physical-root key for the §2.1 shared-root reduction: the
    ledger's independence_group (gochara_kernel.ids.independence_group —
    body, relation, aspect_deg, target_deg, t_exact) when carried; else the
    same tuple rebuilt locally. Role aliases of one physical contact (7L
    Venus and kāraka Venus both at natal Venus) share one root."""
    ig = c.get("_independence_group")
    if ig:
        return ig
    return ("root", c.get("body"), c.get("relation"),
            round(float(c.get("_aspect_deg") or 0.0), 4),
            round(float(c.get("_target_lon_deg") or 0.0), 4),
            c.get("_t_exact_jd"))


def reduce_shared_roots(scored: list[dict], weight_by_target_ref: dict) -> dict:
    """§2.1 (amendment 2, R4-S01): contribution(root, channel) := MAX over
    the records sharing the root of that record's channel value; roots then
    combine (here: the pinned noisy-OR). No other reduction — first row, sum
    across roles, noisy-OR ACROSS role aliases — is permitted. `scored` are
    {contact, decay, weight} records already restricted to supporting,
    in-orb contacts. Returns {"activity": [records], "channels": [records]}:
    one record per root for the unsigned occurrence term, and per root the
    best positive- and best negative-weight record for the signed channels
    (a root's aliases may sit on different channels; each channel keeps its
    own max). Annotation of the non-contributing aliases is in `dropped`."""
    by_root: dict = {}
    for rec in scored:
        by_root.setdefault(contact_root_key(rec["contact"]), []).append(rec)
    activity_recs, channel_recs, dropped = [], [], []
    for root, recs in by_root.items():
        best = max(recs, key=lambda r: r["decay"] * abs(r["weight"]))
        activity_recs.append(best)
        pos = [r for r in recs if r["weight"] > 0.0]
        neg = [r for r in recs if r["weight"] < 0.0]
        keep_ids = {id(best)}
        if pos:
            bp = max(pos, key=lambda r: r["decay"] * r["weight"])
            channel_recs.append(bp)
            keep_ids.add(id(bp))
        if neg:
            bn = max(neg, key=lambda r: r["decay"] * -r["weight"])
            channel_recs.append(bn)
            keep_ids.add(id(bn))
        for r in recs:
            if id(r) not in keep_ids:
                dropped.append({"contact_id": r["contact"]["contact_id"],
                                "root": str(root),
                                "reason": "role alias of a contributing root "
                                          "(§2.1 max-per-root; annotation only)"})
    return {"activity": activity_recs, "channels": channel_recs,
            "dropped": dropped, "roots": len(by_root)}


def c2_evidence_channels(scored: list[dict]) -> dict:
    """D-SPECS C2 (GOCHARA_DESIGN_SPECS_v1_4 §2.1 amendment 2, R4-S01) —
    evidence accumulation and shared roots, on the '4.0' projection path
    (ASTRA v1.1 P1-5):

        root_id := contact_id on transit rows (here: the ledger's
                   independence_group / the local physical tuple —
                   contact_root_key);
        contribution(root, c) := MAX over the records sharing the root of
                                 that record's value in channel c;
        path.c := Σ over roots of contribution(root, c).

    A record's value in its assigned channel is its within-path factor
    product — here orb strength × |weight| (both in [0, 1]); its other
    channel is 0; the channel is assigned by the weight's sign (class-
    relative polarity is applied afterwards by three_field_valence). The
    reduction is order-independent and channel-preserving; no other
    reduction — first row, sum across roles, noisy-OR — is permitted. Two
    distinct roots contributing 0.5 each therefore yield 1.0 (the legacy
    noisy-OR gave 0.75); two aliases of one root yield 0.5. The sums are
    rank-only and may exceed 1 (the codomain rule is on FACTORS, not on the
    accumulated evidence; §1.1 evidence_* are 'rank-only; scale set at L5').
    """
    positive: dict = {}
    negative: dict = {}
    breakdown = []
    for rec in scored:
        root = str(contact_root_key(rec["contact"]))
        w = float(rec["weight"])
        value = float(rec["decay"]) * abs(w)
        entry = {"contact_id": rec["contact"]["contact_id"], "root": root,
                 "target_ref": rec["contact"]["target_ref"],
                 "weight": w, "orb_strength": rec["decay"], "value": value,
                 "channel": ("positive" if w > 0 else "negative" if w < 0 else "none")}
        breakdown.append(entry)
        if w > 0:
            positive[root] = max(positive.get(root, 0.0), value)
        elif w < 0:
            negative[root] = max(negative.get(root, 0.0), value)
    return {
        "positive": sum(positive.values()),
        "negative": sum(negative.values()),
        "roots_positive": len(positive), "roots_negative": len(negative),
        "per_root": {"positive": positive, "negative": negative},
        "records": sorted(breakdown, key=lambda e: (e["root"], e["contact_id"])),
        "reduction": "C2: max per root per channel, sum across roots (order-independent)",
    }


def _sentence_for(rec: dict) -> "leg.Sentence":
    c = rec["contact"]
    return leg.Sentence(
        primitive=c["_primitive"], target_ref=c["target_ref"],
        transit_planet=c["body"], event_jd=c["_t_exact_jd"],
        detail={"orb_strength": rec["decay"]},
    )


def make_eval_fn(class_ctx: ClassContext, contacts: list[dict],
                 quality_gate_for_date, *, planet_pos_fn=None):
    """eval_fn(t_jd) -> (lambda_raw, active_contact_ids, signed_channels).

    The pinned assemble_lambda_v3 algebra over the M-1 ANGULAR in-orb
    activity (D-RQ2): each contact's orb_strength is 1 − min(|Δλ(t)|/orb, 1)
    with Δλ from the contact's ASPECT POINT at t — the body's ephemeris
    longitude plus the contact's aspect_deg (contact_aspect_point_deg; 0
    for non-dṛṣṭi relations) — never a time triangle. A contact
    contributes only inside its own episode [t_in, t_out]
    (contact_supports), and role aliases of one physical root contribute
    once (reduce_shared_roots) — ASTRA_REVIEW_A5_4 P1-1. A contact without
    a target longitude aborts the run (the F-08 exception-swallow is NOT
    reproduced — errors propagate; a silent 0.0 or fallback stand-in would
    fabricate activity). `planet_pos_fn` is (body, jd) -> longitude deg;
    default: the Swiss accessor (lazy)."""
    if planet_pos_fn is None:
        planet_pos_fn = _default_planet_pos_fn()

    def evaluate(t_jd: float):
        # §5 vedha qualifier at THIS instant, scoped per primary graha
        # (ASTRA P1-3): attenuates only the primary's own contacts.
        gate = quality_gate_for_date(t_jd)
        factor_by_body = gate.get("factor_by_body") or {}
        applied = []
        scored = []
        for c in contacts:
            target_lon = c.get("_target_lon_deg")
            if target_lon is None:
                raise ValueError(
                    f"contact {c.get('contact_id')} has no target_longitude_deg "
                    "— the angular kernel cannot score it honestly")
            if not contact_supports(c, t_jd):
                continue
            orb_deg = c.get("_orb_deg") or ORB_MAX_DEG_FALLBACK
            point = contact_aspect_point_deg(
                planet_pos_fn(c["body"], t_jd), c.get("_aspect_deg") or 0.0)
            decay = angular_orb_decay(point, target_lon, orb_deg)
            if decay <= 0.0:
                continue
            vf = factor_by_body.get(c["body"])
            if vf is not None and vf != 1.0:
                applied.append({"contact_id": c["contact_id"], "body": c["body"],
                                "factor": vf, "decay_before": decay})
                decay *= vf
            scored.append({
                "contact": c, "decay": decay,
                "weight": float(class_ctx.weight_by_target_ref.get(
                    c["target_ref"], 0.0)),
            })
        reduced = reduce_shared_roots(scored, class_ctx.weight_by_target_ref)
        # in-orb supporting contacts BEFORE the root reduction: the operand
        # check below must see every alias — an alias with no map weight
        # leaves its root's true max unknown even when a weighted alias of
        # the same root contributes (O-TV-3).
        in_orb_ids = [r["contact"]["contact_id"] for r in scored]
        active_ids = [r["contact"]["contact_id"] for r in reduced["activity"]]
        sentences = [_sentence_for(r) for r in reduced["activity"]]
        channel_sentences = [_sentence_for(r) for r in reduced["channels"]]
        # T0-7 (ASTRA P1-4): ACTIVITY is occurrence strength — the
        # magnitude of the evidence regardless of its sign. The pinned
        # compute_activity_v3 clamps a negative map weight to 0 (the legacy
        # engine's #11 defect: negatives reach only the afflicting channel),
        # so negative-only evidence (a bereavement-class Saturn on the 9L)
        # produced activity 0, λ 0 and NO window. The activity term is
        # therefore fed |weight|; the SIGN is consumed only by the channels.
        activity, _act_detail, _tb = leg.compute_activity_v3(
            sentences, class_ctx.abs_weight_by_target_ref)
        # LEGACY signed channels (noisy-OR per channel) — retained ONLY for
        # the legacy netted verdict (suppression_state.legacy_netted_valence);
        # the §3 evidence fields use the C2 reduction below.
        supportive, afflicting, _ch = leg.compute_signed_channels_v3(
            channel_sentences, class_ctx.weight_by_target_ref)
        # D-SPECS C2 (ASTRA v1.1 P1-5): the evidence channels are max per
        # root per channel, SUMMED across distinct roots.
        c2 = c2_evidence_channels(scored)
        # The class-wide multiplier is RETIRED: λ receives 1.0 here; the
        # vedha qualification already entered the primaries' orb strengths
        # above (scoped), and its state/provenance is disclosed per row.
        applied_product = 1.0
        for a in applied:
            applied_product *= a["factor"]
        gates = 1.0
        gates_detail = {**gate, "scoped_application": applied,
                        "applied_product_on_primaries": applied_product,
                        "class_multiplier": "retired (scoped per primary; §5.2 inv 1)"}
        # T0-7 (FABLE #11/#12): the three-field valence at THIS instant.
        # Per-operand resolution: a contributing contact whose target_ref has
        # NO weight in the class's map-weight dict would be silently scored
        # 0.0 by compute_signed_channels_v3 (weight_by_target_ref.get(...,
        # 0.0)) — the same silent-default shape as finding #12. Such a
        # contact's channel contribution is genuinely UNKNOWN, so its operand
        # is named unresolved instead of defaulted. Class-level unresolved
        # operands (context-declared, e.g. 'av_donor_matrix' — O-TV-3) always
        # apply.
        unresolved = list(class_ctx.class_level_unresolved_operands())
        p5c_operands = []
        for c in contacts:
            if c["contact_id"] not in in_orb_ids:
                continue
            if c["target_ref"] not in class_ctx.weight_by_target_ref:
                unresolved.append(f"map_weight:{c['target_ref']}")
            # D-SPECS C4 / ASTRA P1-4: the P5c donor operand is consumed
            # ONLY by kakṣyā crossings, resolved per donor-row key.
            p5c = class_ctx.p5c_operand_state(c)
            if p5c is not None:
                p5c_operands.append({"contact_id": c["contact_id"], **p5c})
                if p5c["state"] == "unresolved":
                    unresolved.append(p5c["operand"])
        tv = three_field_valence(
            c2["positive"], c2["negative"], class_valence=class_ctx.class_valence,
            class_is_adverse=class_ctx.class_is_adverse,
            unresolved_operands=unresolved)
        tv["breakdown"]["c2_reduction"] = {
            k: c2[k] for k in ("positive", "negative", "roots_positive",
                               "roots_negative", "per_root", "reduction")}
        tv["breakdown"]["c2_records"] = c2["records"]
        # T0-6: PERMISSION at THIS instant (per-instant MD/AD/PD plurality),
        # never a per-class constant, when the class context carries one.
        permission, permission_detail = class_ctx.permission_at(t_jd)
        assembled = leg.assemble_lambda_v3(
            promise=class_ctx.promise, permission=permission,
            activity=activity, tara_modifier=class_ctx.tara["modifier"],
            w30_modifier=class_ctx.w30["modifier"], quality_gates=gates)
        return {
            "lambda_raw": assembled["lambda_raw"],
            "lambda_signed": assembled["lambda_signed"],
            "activity": activity,
            "permission": permission,
            "permission_detail": permission_detail,
            "permission_systems_active": permission_detail["systems_active"],
            "supportive": supportive,
            "afflicting": afflicting,
            "c2_positive": c2["positive"],
            "c2_negative": c2["negative"],
            "quality_gates": applied_product,
            "quality_gates_detail": gates_detail,
            "active_contact_ids": active_ids,
            "shared_roots": {"roots": reduced["roots"],
                             "dropped_aliases": reduced["dropped"]},
            "p5c_operands": p5c_operands,
            "three_field_valence": tv,
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
                          day_stride_days: float = 1.0,
                          planet_pos_fn=None) -> tuple[list[dict], dict]:
    """Era -> month -> day window rows for one event class. Returns
    (window_row_dicts, class_report). Window rows carry logical
    window_key/parent_key; the writer resolves them to parent_window_id at
    INSERT time. `planet_pos_fn` is forwarded to make_eval_fn (the angular
    kernel's ephemeris accessor; default: Swiss, lazy)."""
    if planet_pos_fn is None:
        planet_pos_fn = _default_planet_pos_fn()
    evaluate = make_eval_fn(class_ctx, contacts, quality_gate_for_date,
                            planet_pos_fn=planet_pos_fn)
    eval_lambda = lambda t: evaluate(t)["lambda_raw"]  # noqa: E731
    tara_annotator = make_tara_annotator(class_ctx.natal_moon_deg, planet_pos_fn)

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
        # series; H-5 — the count cap is removed (max_peaks=len(admitted));
        # N5 — the 90-day separation trim is NOT applied here: it is a
        # serve-time trim (resolution_hierarchy.py:117-127), so every
        # admitted peak is persisted regardless of spacing.
        era_cands = leg.find_local_maxima(era_series, era_values)
        admitted = leg.admit_candidates(era_cands, era_values)
        retained = leg.retain_candidates(
            admitted, max_peaks=len(admitted) if admitted else 0,
            min_separation_days=WRITE_TIME_MIN_PEAK_SEPARATION_DAYS)
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
                peak_jd=peak_jd_true, tara_annotator=tara_annotator))

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
            len(g.get("fired") or []) for g in gate_details_seen.values()),
    }
    return rows, report


def _window_row(class_ctx: ClassContext, evaluate, *, window_key: str,
                parent_key: str | None, tier: str, enter_jd: float,
                exit_jd: float, peak_jd: float, tara_annotator=None) -> dict:
    peak = evaluate(peak_jd)
    # P6 tārā testimony: DAY rows only (P6 is the sole day-resolution
    # source, §2.3 inv 6); era/month rows carry the not-applicable record.
    if tier == "day" and tara_annotator is not None:
        tara_record = {**class_ctx.tara, "annotation": tara_annotator(peak_jd)}
    else:
        tara_record = {**class_ctx.tara, "annotation": None,
                       "annotation_state": f"not_applicable({tier} row; P6 annotates day rows)"}
    tv = peak["three_field_valence"]
    raw = peak["lambda_raw"]
    # The served single-axis columns (valence / is_adverse / the sign of
    # signed_intensity) are DERIVED FROM THE THREE-FIELD CONTRACT (ASTRA
    # P1-4: "ensure consumers use the three independent fields"): valence
    # := outcome_valence_for_native, is_adverse := outcome == 'adverse'. The
    # legacy netted verdict (resolve_valence_v3: imbalance_ratio → 'mixed',
    # the #11/#12 shape) is computed only for the review trail and kept in
    # suppression_state.legacy_netted_valence — it no longer reaches a served
    # column.
    valence = tv["outcome_valence_for_native"]
    is_adverse = valence == "adverse"
    legacy_valence, legacy_is_adverse, tension = leg.resolve_valence_v3(
        peak["supportive"], peak["afflicting"],
        class_valence=class_ctx.class_valence,
        class_is_adverse=class_ctx.class_is_adverse)
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
        # T0-7 (FABLE #11/#12, §3): the three-field valence contract,
        # computed at this row's own peak instant. The served table has no
        # columns for these (migrations out of scope) — they ride inside
        # suppression_state.three_field_valence (written as jsonb) and are
        # top-level here for the class report / tests.
        "evidence_for_occurrence": tv["evidence_for_occurrence"],
        "evidence_against_occurrence": tv["evidence_against_occurrence"],
        "outcome_valence_for_native": tv["outcome_valence_for_native"],
        "severity": tv["severity"],
        "active_sentences": sorted(peak["active_contact_ids"]),
        "contributing_systems": [
            # T0-6: the licence at THIS row's own peak instant (per-instant
            # mode) — not the per-class unioned constant.
            *peak["permission_systems_active"],
            "promise:gochara_resonance_map",
            "activity:kala_gochara_contacts@m1_linear_no_box",
            ("tara:testimony(P6 day annotation; never weights)" if tier == "day"
             else f"tara:not_applicable({tier} row; P6 testimony annotates day rows)"),
            "w30:removed(N-14)",
            f"vedha:{peak['quality_gates_detail'].get('state')}"
            "(kala_vedha_gochara §5 interval gate; scoped per primary)",
            f"valence:{VALENCE_CONTRACT}",
        ],
        "suppression_state": {
            "quality_gates": peak["quality_gates"],
            "quality_gates_detail": {
                **peak["quality_gates_detail"],
                # P6 Moon-vedha testimony annotates DAY rows only (§5.2 inv
                # 3 / S-04); era/month rows carry none.
                "annotations": (peak["quality_gates_detail"].get("annotations") or []
                                if tier == "day" else []),
                "annotations_withheld_for_tier": (
                    None if tier == "day" else
                    len(peak["quality_gates_detail"].get("annotations") or []))},
            "permission_at_peak": peak["permission"],
            "permission_detail": peak["permission_detail"],
            "tara": tara_record,
            "w30": class_ctx.w30,
            "valence_tension": tension,
            "legacy_netted_valence": {
                "valence": legacy_valence, "is_adverse": legacy_is_adverse,
                "note": "resolve_valence_v3 (netted) — review trail only; "
                        "the served valence/is_adverse derive from "
                        "three_field_valence.outcome_valence_for_native"},
            "p5c_operands": peak["p5c_operands"],
            "shared_roots": peak["shared_roots"],
            # T0-7: full derivation disclosure (fields + breakdown, incl.
            # every named unresolved operand).
            "three_field_valence": tv,
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
    # aspect_deg + independence_group (ASTRA P1-1): the dṛṣṭi angle the
    # kernel must add to the body longitude, and the physical-root key for
    # the shared-root reduction. Both are ledger columns (WP1 §3); read
    # explicitly, never defaulted from the relation label.
    rows = conn.execute(
        "SELECT contact_id, body, relation, target_type, target_ref,"
        " target_longitude_deg, t_in, t_exact, t_out, orb_max_deg,"
        " completeness_state, aspect_deg, independence_group"
        " FROM kala_gochara_contacts"
        " WHERE chart_id = %s AND generation = %s",
        (chart_id, generation)).fetchall()
    out = []
    for (cid, body, relation, ttype, tref, tlon, t_in, t_exact, t_out,
         orb_max, completeness, aspect_deg, independence_group) in rows:
        out.append({
            "contact_id": cid, "body": body, "relation": relation,
            "target_type": ttype, "target_ref": tref,
            "target_longitude_deg": float(tlon) if tlon is not None else None,
            "orb_max_deg": float(orb_max) if orb_max is not None else None,
            "completeness_state": completeness,
            "aspect_deg": float(aspect_deg) if aspect_deg is not None else 0.0,
            "independence_group": independence_group,
            "_target_lon_deg": float(tlon) if tlon is not None else None,
            "_orb_deg": (float(orb_max) if orb_max is not None
                         else ORB_MAX_DEG_FALLBACK),
            "_aspect_deg": float(aspect_deg) if aspect_deg is not None else 0.0,
            "_independence_group": independence_group,
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


# ── vedha interval gate (GOCHARA_DESIGN_SPECS_v1_4 §5; ASTRA P1-3) ───────────
#
# The projection previously called legacy_semantics.compute_quality_gates: a
# DATE-grain whole-row multiplier applying the PG353 battle-scale grade to
# every overlay row overlapping the day, regardless of interval state,
# cancellation, coverage, independence or operator role — the reviewer's
# probes: a clean row still yielded 0.85; an obstruction ending March 1
# still yielded 0.70 on April 1; duplicate roots yielded 0.49. The gate
# below consumes the T0-8 writer payload (detail.vedha_intervals with
# per-segment states, detail.coverage, operator_role, rule provenance)
# through the SHARED evaluator services.ka_vedha_gochara.logic.attenuation_at
# (reused, not duplicated):
#   * attenuation only where an ACTIVE segment covers t (half-open; #17,
#     O-VI-1/2/4);
#   * coverage: t outside the overlay's computed horizon, or no T0-8 rows at
#     all, reads `unavailable` with the coverage object — the factor is
#     None and takes the §2.1 null_state `omit` (dropped from the λ product,
#     disclosed as unavailable, never reported as a clean 1.0; #25, O-VI-5);
#   * one root attenuates once (independence_group; §5.1);
#   * NO generalised PG353 number: with no cited suppression scale
#     (D-PG353) an active obstruction is reported as `obstructed` structure
#     with factor None (omit) — the state, the fired intervals and the rule
#     provenance reach every row; a caller holding a CITED scale passes
#     cited_scale(interval) -> float and it multiplies once per root;
#   * scoped to the PRIMARY transit: a row for graha G attenuates only G's
#     own contacts (per-body factor applied to the contact's orb strength),
#     never the whole class λ;
#   * Moon-primary rows are P6 testimony (S-04): never a factor; they
#     annotate day rows only (_window_row filters by tier);
#   * pre-T0-8 rows (no detail.vedha_intervals) are counted as legacy shape
#     and contribute nothing — never the PG353 multiplier.

VEDHA_NULL_STATE = "omit"  # §2.1 factor null_state for an unresolved qualifier


def parse_vedha_overlay_rows(vedha_rows: list[dict]) -> dict:
    """Delegates to the ONE evaluator of the writer's payload
    (services.ka_vedha_gochara.gate.parse_overlay_rows); returned shape is
    that module's, with `coverage` = the list of per-row horizons."""
    from services.ka_vedha_gochara import gate as VG
    parsed = VG.parse_overlay_rows(vedha_rows)
    return {**parsed, "coverage": parsed["horizons"] or None}


def make_vedha_gate(vedha_rows: list[dict], *, cited_scale=None):
    """gate(t_jd) -> the §5 qualifier at t's UTC date — the shared
    ka_vedha_gochara.gate evaluator (also wired into the v3 engine), keyed
    here by JD for the projection's evaluate()."""
    from services.ka_vedha_gochara import gate as VG
    inner = VG.make_gate(vedha_rows, cited_scale=cited_scale)

    def gate(t_jd: float) -> dict:
        return inner(date_of_jd(t_jd))

    return gate


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
    # Adjacent components can each retain a peak whose refine_peak_to_day
    # lands on the same calendar day (and, clipped to era bounds, the same
    # month), producing rows identical under uq_kala_gochara_windows_natural_key
    # (chart, class, window_start, peak_date, milestone_id, resolution,
    # generation). Keep the first in insert order; children of a skipped row
    # re-point to the retained row's id.
    seen_natural: dict[tuple, int] = {}
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
        print(f"write_windows: {skipped_dupes} projected row(s) shared a "
              "natural key with an already-written row (adjacent-component "
              "peak collapse to the same date); first occurrence kept, "
              "children re-pointed", file=sys.stderr)
    return len(ordered) - skipped_dupes, skipped_dupes


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
        perm_cell = (f"{rep['permission']:.6f}"
                     if isinstance(rep.get("permission"), float)
                     else (rep.get("permission_mode") or "—"))
        lines.append(
            f"| {cls} | {rep['era_windows']}/{rep['month_windows']}/{rep['day_windows']}"
            f" | {rep['promise']:.6f} | {perm_cell}"
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
        "- PERMISSION context input: "
        f"{run_meta.get('class_context_source')}.",
        "- PERMISSION is per-instant when the class context carries `_dasha_periods` (T0-6;",
        "  MD/AD/PD, memoized per class×day, sade-sāti testimony-renormalized per N-15); the",
        "  per-class column then reads the mode, not a constant. Otherwise it is the pinned",
        "  static systems_active fraction (old documents, rehearsal).",
        "- tārā reports the pinned honest skip (M-3 separate Moon channel not wired here);",
        "  w30 is N-14-removed (1.0). quality_gates reproduces the F-11 no-rows path where the",
        "  overlay is absent — disclosed on every row's suppression_state.",
        "- T0-7 (FABLE #11/#12, §3): every row's suppression_state.three_field_valence carries",
        "  evidence_for_occurrence / evidence_against_occurrence (independent, never netted),",
        "  outcome_valence_for_native (polarity verdict; 'unqualified' with named operands when",
        "  any operand is unresolved) and severity. The valence/is_adverse columns are the",
        "  legacy single-axis fields, retained for serving compatibility.",
        "- Peak storage is H-5-uncapped and N5-untrimmed (the pre-H-5 cap of 3/era is removed;",
        "  the 90-day minimum separation is a SERVE-time trim in resolution_hierarchy.py,",
        "  not applied at write time — every admitted peak is stored).",
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
        # T0-7: rehearsal declares no unresolved valence operands (a known
        # polarity, no AV-donor absence) so rehearsal rows behave exactly as
        # pre-repair apart from carrying the new fields.
        "valence_unresolved_operands": [],
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

    conn = connect(resolve_dsn(args), step=6, autocommit=False)
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

        # §5 interval gate (ASTRA P1-3). bg_vedha_malefic_scale is read only
        # for the run report — D-PG353: it is not a general grade source and
        # no longer feeds scoring.
        gate_for_date = make_vedha_gate(vedha_rows)
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
            # T0-6 / ASTRA P1-2: the frozen C5 per-instant permission is
            # INSTALLED here (build_projection_class_context) whenever the
            # document carries _dasha_periods + _chart; None ⇒ the class's
            # targets did not resolve ⇒ honest skip.
            class_ctx = build_projection_class_context(
                conn, args.chart_id, cls, ctx_dict,
                class_contexts if class_contexts else None,
                weights=weights_all_by_class[cls],
                weight_by_target_ref=weight_by_class[cls],
                context_source=context_source)
            if class_ctx is None:
                skipped_classes.append({
                    "event_class": cls,
                    "reason": "targets did not resolve for the per-instant "
                              "permission (fetch_resonance_targets/"
                              "enrich_targets empty) — honest skip",
                    "contacts_matched": len(cls_contacts),
                })
                continue
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
        n_written, skipped_dupes = write_windows(
            conn, args.chart_id, args.generation,
            all_rows, source=source, window_columns=window_columns)
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
        "contacts_read": len(contacts),
        "vedha_overlay": {
            "rows_read": len(vedha_rows),
            "t0_8_rows": parse_vedha_overlay_rows(vedha_rows)["rows_total"]
            - parse_vedha_overlay_rows(vedha_rows)["legacy_rows"],
            "legacy_shape_rows_ignored": parse_vedha_overlay_rows(vedha_rows)["legacy_rows"],
            "malefic_scale_rows": len(malefic_scale),
            "malefic_scale_role": "report only — D-PG353 (no generalised PG353 attenuation)",
        },
        "contacts_unmapped_no_class": unmapped,
        "contacts_unmapped_relation": unmapped_relation,
        "classes_projected": len(class_reports),
        "skipped_classes": skipped_classes,
        "windows_written": n_written,
        "windows_collapsed_dupes": skipped_dupes,
        "windows_by_tier": {
            tier: sum(1 for r in all_rows if r["resolution"] == tier)
            for tier in ("era", "month", "day")},
        "windows_by_tier_basis": "pre-dedupe projection counts; "
            "windows_written is post-dedupe, so "
            "sum(windows_by_tier) = windows_written + windows_collapsed_dupes",
        "class_reports": class_reports,
        "baseline_generation": args.baseline_generation,
        "baseline_windows_read": len(baseline_rows),
        "delta_report_out": args.delta_report_out,
        "peak_retention": "H-5: count cap removed (all admitted peaks "
                          "stored); N5: 90-day separation trim is serve-time "
                          "(resolution_hierarchy.py), not applied at write",
    }
    print(json.dumps(report, indent=2, default=str))
    if args.evidence:
        write_evidence(6, "WINDOWS-PROJECTION",
                       f"```json\n{json.dumps(report, indent=2, default=str)}\n```")
    return 0


if __name__ == "__main__":
    sys.exit(main())
