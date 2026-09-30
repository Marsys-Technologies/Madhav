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
  * PERMISSION — T0-6 (FABLE #2/#3): evaluated AT EACH PROJECTION INSTANT by
    gochara_intensity.permission.compute_permission over the class-context
    document's `_dasha_periods` (MD/AD/PD levels 1-3, §4.0 tier), memoized
    per class × UTC day; N-15 testimony renormalization strips the
    sade-sāti weight (it annotates, never licenses). When the context
    document carries no `_dasha_periods` (old documents, --rehearse-synthetic)
    the pinned static per-class constant (compute_permission over the
    context's systems_active map) is used exactly as pre-repair and the
    class report records permission_mode='static_systems_active'. A class
    with matching contacts but NO context is skipped and recorded
    (skipped_classes) — never a 0.0 stand-in (plan §4.6).
  * ACTIVITY — the pinned noisy-OR of legacy_semantics.compute_activity_v3,
    with per-contact orb_strength = the M-1 `linear_no_box` ANGULAR kernel
    (D-RQ2, sealed doctrine FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0 finding
    N1): activity(t) = 1 − min(|Δλ(t)| / orb, 1), where Δλ(t) is the
    shortest-arc separation between the transiting body's longitude AT t
    (Swiss ephemeris, engine.py's _get_planet_pos accessor pattern) and the
    contact's target_longitude_deg, and orb is the contact's orb_max_deg
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
  * valence/is_adverse — pinned resolve_valence_v3 over the signed channels
    at each row's own peak instant; the class fallback valence comes from
    the class context (default 'mixed', disclosed). LEGACY single-axis
    columns, RETAINED unchanged for the serving layer and the delta report.
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
    context document, an active contact with no map weight, or a
    context-declared valence_unresolved_operands entry such as
    'av_donor_matrix' — the O-TV-3 P5c donor-matrix-absent case) yields
    outcome 'unqualified' with the operand NAMED in the breakdown — never
    a silent 1.0 / 'favourable' default (finding #12's E5 regression is
    what this prevents). The new fields ride inside suppression_state (the
    served table has no columns for them and migrations are out of scope
    here); derivation is disclosed in suppression_state.three_field_valence
    on every row and in the class factors record.
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


def make_per_instant_permission_fn(conn, chart_id: str, event_class: str,
                                   dasha_periods: list[dict]):
    """permission_fn(t_jd) -> (permission, detail) for one event class,
    evaluated by the REAL plurality machinery
    (gochara_intensity.permission.compute_permission) at each instant over
    the MULTI-LEVEL (MD/AD/PD) dasha rows from the class-context document —
    the T0-6 repair of the per-class unioned constant.

    Targets come from the same fetch step06a and the served engine use
    (fetch_resonance_targets + enrich_targets — no second wiring to drift).
    Returns None when the class's targets do not resolve: the caller records
    the class as skipped, never a fabricated context.

    Memoization: one plurality evaluation per (class, UTC calendar date) —
    the projection's grids and bisections evaluate the same day repeatedly;
    no century-long curve is precomputed. N-15: the sade-sāti generator's
    weight is stripped (testimony renormalization) after each call."""
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
    cache: dict[str, tuple[float, dict]] = {}

    def at(t_jd: float):
        key = iso_date_of_jd(t_jd)
        if key not in cache:
            raw, detail = perm.compute_permission(
                swe, conn, chart_id, event_class, targets, t_jd,
                dasha_periods=dasha_periods)
            cache[key] = _sade_sati_testimony_renormalize(raw, detail)
        return cache[key]

    return at


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
        supportive → for, afflicting → against. Magnitudes are the pinned
        noisy-OR channel values in [0, 1] — rank-only, never gates.
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


# ── per-class lambda evaluator ───────────────────────────────────────────────


class ClassContext:
    """The once-per-(chart, class) factor context (plan §4.5)."""

    def __init__(self, event_class: str, weights: list[float],
                 permission_systems: dict[str, bool],
                 *, weight_by_target_ref: dict[str, float],
                 class_valence: str = "mixed", class_is_adverse: bool = False,
                 context_source: str = "class_context_json",
                 permission_fn=None, unresolved_valence_operands=()):
        self.event_class = event_class
        self.weight_by_target_ref = dict(weight_by_target_ref)
        self.promise, self.promise_detail = leg.compute_promise(weights)
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
        self.context_source = context_source
        # tārā: the transit-Moon channel is not wired into this projection
        # (M-3 separate channel) — the pinned honest skip (modifier 1.0).
        self.tara = leg.tara_modifier(None, None)
        # N-14: nodal dṛṣṭi removed — the pinned disabled path (modifier 1.0).
        self.w30 = leg.w30_modifier(None, [], enabled=False)

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
                unresolved_operands=self.unresolved_valence_operands
            )["outcome_valence_for_native"],
            "severity": None,
            "valence_unresolved_operands": sorted(
                self.unresolved_valence_operands),
            "context_source": self.context_source,
        }


def make_eval_fn(class_ctx: ClassContext, contacts: list[dict],
                 quality_gate_for_date, *, planet_pos_fn=None):
    """eval_fn(t_jd) -> (lambda_raw, active_contact_ids, signed_channels).

    The pinned assemble_lambda_v3 algebra over the M-1 ANGULAR in-orb
    activity (D-RQ2): each contact's orb_strength is 1 − min(|Δλ(t)|/orb, 1)
    with Δλ from the body's ephemeris longitude at t — never a time
    triangle. A contact without a target longitude aborts the run (the F-08
    exception-swallow is NOT reproduced — errors propagate; a silent 0.0 or
    fallback stand-in would fabricate activity). `planet_pos_fn` is
    (body, jd) -> longitude deg; default: the Swiss accessor (lazy)."""
    if planet_pos_fn is None:
        planet_pos_fn = _default_planet_pos_fn()

    def evaluate(t_jd: float):
        sentences = []
        active_ids = []
        for c in contacts:
            target_lon = c.get("_target_lon_deg")
            if target_lon is None:
                raise ValueError(
                    f"contact {c.get('contact_id')} has no target_longitude_deg "
                    "— the angular kernel cannot score it honestly")
            orb_deg = c.get("_orb_deg") or ORB_MAX_DEG_FALLBACK
            decay = angular_orb_decay(
                planet_pos_fn(c["body"], t_jd), target_lon, orb_deg)
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
        # T0-7 (FABLE #11/#12): the three-field valence at THIS instant.
        # Per-operand resolution: a contributing contact whose target_ref has
        # NO weight in the class's map-weight dict would be silently scored
        # 0.0 by compute_signed_channels_v3 (weight_by_target_ref.get(...,
        # 0.0)) — the same silent-default shape as finding #12. Such a
        # contact's channel contribution is genuinely UNKNOWN, so its operand
        # is named unresolved instead of defaulted. Class-level unresolved
        # operands (context-declared, e.g. 'av_donor_matrix' — O-TV-3) always
        # apply.
        unresolved = list(class_ctx.unresolved_valence_operands)
        for c in contacts:
            if (c["contact_id"] in active_ids
                    and c["target_ref"] not in class_ctx.weight_by_target_ref):
                unresolved.append(f"map_weight:{c['target_ref']}")
        tv = three_field_valence(
            supportive, afflicting, class_valence=class_ctx.class_valence,
            class_is_adverse=class_ctx.class_is_adverse,
            unresolved_operands=unresolved)
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
            "quality_gates": gates,
            "quality_gates_detail": gates_detail,
            "active_contact_ids": active_ids,
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
    evaluate = make_eval_fn(class_ctx, contacts, quality_gate_for_date,
                            planet_pos_fn=planet_pos_fn)
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
    # LEGACY single-axis valence columns (retained unchanged — consumed by
    # the serving layer and the delta report). NOTE: resolve_valence_v3 nets
    # the channels (imbalance_ratio → 'mixed'); that is exactly the #11/#12
    # shape the three-field contract replaces, so the new fields below are
    # authoritative for §3 and these two are legacy compatibility only.
    valence, is_adverse, tension = leg.resolve_valence_v3(
        peak["supportive"], peak["afflicting"],
        class_valence=class_ctx.class_valence,
        class_is_adverse=class_ctx.class_is_adverse)
    tv = peak["three_field_valence"]
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
            f"tara:skipped({class_ctx.tara['skip_reason']})",
            "w30:removed(N-14)",
            ("quality_gates:kala_vedha_gochara"
             if peak["quality_gates_detail"].get("vedha_rows_total")
             else "quality_gates:no_overlay_rows(F-11)"),
            f"valence:{VALENCE_CONTRACT}",
        ],
        "suppression_state": {
            "quality_gates": peak["quality_gates"],
            "quality_gates_detail": peak["quality_gates_detail"],
            "permission_at_peak": peak["permission"],
            "permission_detail": peak["permission_detail"],
            "tara": class_ctx.tara,
            "w30": class_ctx.w30,
            "valence_tension": tension,
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
    rows = conn.execute(
        "SELECT contact_id, body, relation, target_type, target_ref,"
        " target_longitude_deg, t_in, t_exact, t_out, orb_max_deg,"
        " completeness_state"
        " FROM kala_gochara_contacts"
        " WHERE chart_id = %s AND generation = %s",
        (chart_id, generation)).fetchall()
    out = []
    for (cid, body, relation, ttype, tref, tlon, t_in, t_exact, t_out,
         orb_max, completeness) in rows:
        out.append({
            "contact_id": cid, "body": body, "relation": relation,
            "target_type": ttype, "target_ref": tref,
            "target_longitude_deg": float(tlon) if tlon is not None else None,
            "orb_max_deg": float(orb_max) if orb_max is not None else None,
            "completeness_state": completeness,
            "_target_lon_deg": float(tlon) if tlon is not None else None,
            "_orb_deg": (float(orb_max) if orb_max is not None
                         else ORB_MAX_DEG_FALLBACK),
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
                context_source=ctx_dict.get("context_source", context_source),
                # T0-7: old context documents carry no such key -> [] ->
                # behaviour identical to pre-repair apart from the new
                # fields; documents from the repaired step06a declare the
                # O-TV-3 operand ('av_donor_matrix') when the P5c donor
                # matrix is absent.
                unresolved_valence_operands=ctx_dict.get(
                    "valence_unresolved_operands", ()))
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
