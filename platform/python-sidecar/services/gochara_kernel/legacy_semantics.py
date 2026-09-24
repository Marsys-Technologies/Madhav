"""WP3b — Span-aware reproduction of the gochara_v3 legacy scoring algebra.

This module is the WP3b equivalence baseline: a pure-Python, span-aware
reproduction of the EXACT semantics the served `services/gochara_v3` engine
computes today (pre-WP5-fix semantics, captured before engine.py is touched
by H-1..H-6). It is what WP4 diffs the kernel-based projection against.

Fidelity rules (WP3b spec):
  * NO database access anywhere in this module.
  * NO Swiss Ephemeris at import time (in fact none at all — every function
    takes explicit values or an injected `eval_fn(jd) -> float` evaluator).
  * NO runtime imports from services.* (one-way dependency R2: the kernel
    never depends on the legacy engine; the semantics are copied here with
    per-function attribution comments citing the reproduced file:line).
  * Every ACCIDENTAL BUG in the legacy algebra is REPRODUCED here (the
    baseline must equal the legacy behavior bit-for-bit on the pre-fix
    semantics) and labelled with a `# ARTIFACT:` comment naming the finding
    id (F-08, F-09, F-10, F-11, ...) — classification details live in
    00_ARCHITECTURE/briefs/nirmana/l3_autonomous/gochara_wp0_7/WP3b_CLASSIFICATION.md.

Pinned legacy formula (engine.py:632, the executing line; hoisted string at
engine.py:135-138; persisted string at engine.py:143-145):

    lambda_v3   = PROMISE * PERMISSION * activity * tara_modifier
                  * w30_modifier * quality_gates        (then clamped to [0,1])
    lambda_sign = -lambda_v3 if is_adverse else +lambda_v3   (engine.py:637)

"Span-aware" means: the legacy per-JD gather window (activity sentences are
gathered over [t-5d, t+5d], engine.py:499-501 with window_days_activity=5.0)
is restated as explicit contribution spans — each sentence contributes over
the JD interval [event_jd - 5d, event_jd + 5d] clipped to its episode
[t_in, t_out] and to the horizon — so that a query over any interval
collects exactly the contributions the legacy engine would have gathered at
each instant of that interval. The legacy contribution value itself is a
STEP (constant over the whole box; the orb decay is evaluated AT the event,
not at the query instant) — that step is F-08's "lambda_v3 is a step
function on the served path" and is reproduced faithfully here.

Times are Julian Day floats throughout (mirroring the engine); ISO-8601
handling appears only where the legacy system itself uses date strings
(the quality-gates vedha overlap check, engine.py:259-269 / :307-315).
"""

from __future__ import annotations

import datetime as _dt
import math
import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional

# ---------------------------------------------------------------------------
# Pinned constants (all copied with attribution; see WP3b_CLASSIFICATION.md)
# ---------------------------------------------------------------------------

# engine.py:135-145 — canonical formula strings (also persisted verbatim into
# every served row's term_breakdown.formula).
LAMBDA_V3_FORMULA: str = (
    "lambda_v3 = PROMISE * PERMISSION * activity * tara_modifier "
    "* w30_modifier * quality_gates"
)
TERM_BREAKDOWN_FORMULA: str = (
    "PROMISE × PERMISSION × activity × tara_modifier × w30_modifier × quality_gates"
)

# engine.py:154 — linear-decay bound for activity orb decay.
# M-1 (L3 §4.5): mirror of engine.py::_ACTIVITY_MAX_ORB_DEG — RETAINED for
# the legacy_box default; retired by the M-1 value ratification step that
# follows the WP8 orb battery (GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0 §4.6).
# Do not remove before that ruling.
ACTIVITY_MAX_ORB_DEG: float = 5.0

# engine.py:183-192 — primitives whose sentences feed the v3 activity term.
# NOTE: `sarvatobhadra_vedha` is deliberately absent (IR-6 removal, documented
# at engine.py:162-182); `av_threshold_state`, `sign_occupation`,
# `planetary_return`, `sade_sati_phase` are not activity primitives either.
ACTIVITY_PRIMITIVES: frozenset[str] = frozenset({
    "degree_contact",
    "drishti_contact",
    "sign_ingress",
    "nakshatra_ingress_tara",
    "kakshya_cell_crossing",
    "station_retro_loop",
    "eclipse_degree",
    "gochara_vedha_pair",
})

# engine.py:202 — valence tension threshold (W1.2).
VALENCE_TENSION_THRESHOLD: float = 0.1

# engine.py:228-250 — W1.3 vedha suppression schedule (Phaladeepika PG353
# battle scale per engine.py:209-210; structural prior per engine.py:219-227).
VEDHA_GRADE_SUPPRESSION: dict[str, float] = {
    "no_grade": 0.85,
    "fear": 0.75,
    "grade_2": 0.65,
    "grade_3": 0.55,
    "grade_4": 0.45,
    "ignominy": 0.35,
}
VEDHA_WORST_SUPPRESSION: float = 0.35
VEDHA_NO_SCALE_ROW_FACTOR: float = 0.70
VEDHA_ZERO_MALEFIC_FACTOR: float = 0.85
LATTA_EFFECTIVE_MALEFIC_COUNT: int = 3

# permission.py:100-121 — SYSTEM_WEIGHTS (sum == 1.0) and the 12-system
# generator id list (8 dasha systems, DASHA_SYSTEM_IDS at permission.py:120-121,
# plus sade_sati / guru_shani_double_transit / av_threshold / planetary_return).
SYSTEM_WEIGHTS: dict[str, float] = {
    "vimshottari": 0.16,
    "chara_karaka": 0.10,
    "narayana": 0.08,
    "mudda": 0.09,
    "yogini": 0.07,
    "ashtottari": 0.07,
    "naisargika": 0.05,
    "kalachakra": 0.05,
    "sade_sati": 0.10,
    "guru_shani_double_transit": 0.10,
    "av_threshold": 0.06,
    "planetary_return": 0.07,
}
DASHA_SYSTEM_IDS: tuple[str, ...] = (
    "vimshottari", "yogini", "ashtottari", "chara_karaka",
    "naisargika", "mudda", "kalachakra", "narayana",
)
PERMISSION_SYSTEM_IDS: tuple[str, ...] = DASHA_SYSTEM_IDS + (
    "sade_sati", "guru_shani_double_transit", "av_threshold", "planetary_return",
)

# engine.py:107, engine.py:118 — mechanism toggles as served (BOTH enabled).
W30_NODAL_DRISHTI_ENABLED: bool = True
W23_TARA_BALA_ENABLED: bool = True

# w23_tara_bala.py:73-97 — 9-Tara cycle tables (1-based position 1-9).
TARA_QUALITY: dict[int, str] = {
    1: "janma", 2: "sampat", 3: "vipat", 4: "kshema", 5: "pratyak",
    6: "sadhana", 7: "naidhana", 8: "mitra", 9: "paramamitra",
}
TARA_MODIFIERS: dict[str, float] = {
    "janma": 1.00, "sampat": 1.15, "vipat": 0.75, "kshema": 1.10,
    "pratyak": 0.80, "sadhana": 1.05, "naidhana": 0.70, "mitra": 1.15,
    "paramamitra": 1.20,
}
NAKSHATRA_ARC_DEG: float = 360.0 / 27.0

# w30_nodal_drishti.py:75-97 — sign vocabulary and 5/7/9 aspect tables.
W30_SIGN_NAMES: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
W30_SIGN_TO_INDEX: dict[str, int] = {name: idx for idx, name in enumerate(W30_SIGN_NAMES)}
W30_ASPECT_OFFSETS: tuple[int, ...] = (4, 6, 8)
W30_ASPECT_MODIFIERS: dict[int, float] = {4: 1.05, 6: 0.95, 8: 1.05}

# resolution_hierarchy.py:94-109 — PK-R-8 peak-anchoring constants (pre-H-5).
PEAK_SCAN_STRIDE_DAYS: float = 7.0
ADMISSION_PERCENTILE: float = 90.0
MIN_PEAK_SEPARATION_DAYS: float = 90.0
MAX_PEAKS_PER_ERA_WINDOW: int = 3
DAY_REFINEMENT_HALF_WINDOW_DAYS: float = 7.0
DAY_REFINEMENT_STEP_DAYS: float = 1.0

# interval_solver.py:37-40 — bisection / dense-scan constants.
BISECT_TOL_DAYS: float = 0.1
PEAK_SAMPLE_COUNT: int = 50

# threshold.py:77,84,87-88,91 — W1.4 threshold constants.
CENTURY_STEP_DAYS: float = 7.0
FALLBACK_PERCENTILE: float = 0.50
MAX_SANE_WINDOWS_PER_YEAR: float = 52.0
MIN_SANE_WINDOWS_PER_YEAR: float = 0.0
_DELTA_T_YEARS: float = 1.0 / 52.0
UNIFORM_BASE_RATE: float = 0.20  # ph_nimitta/base_rate.py:35

# ka_gochara_v3_century_materialize.py:475,478,652-683 — decade grid.
DECADE_COUNT: int = 10
DAYS_PER_YEAR: float = 365.25

# The legacy ±5-day activity box (WP1_CONTRACTS.md §7 orb_legacy_box;
# engine.py:424/477 window_days_activity default 5.0).
# M-1 (L3 §4.5): RETAINED for the legacy_box default; retired by the M-1
# value ratification step that follows the WP8 orb battery
# (GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0 §4.6). Do not remove before that
# ruling.
BOX_HALF_DAYS_DEFAULT: float = 5.0


# ---------------------------------------------------------------------------
# Pure data mirrors
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Sentence:
    """Pure mirror of the fields of `services.gochara_grammar.models.
    ConfigurationSentence` that the v3 scoring algebra actually reads
    (primitive, target_ref, transit_planet, event_jd, detail). The engine
    reads exactly these (engine.py:849-896); everything else on the real
    dataclass is carried through untouched by the algebra."""

    primitive: str
    target_ref: Optional[str] = None
    transit_planet: Optional[str] = None
    event_jd: Optional[float] = None
    detail: dict = field(default_factory=dict)
    event_datetime_ist: Optional[str] = None


@dataclass(frozen=True)
class ThresholdConfig:
    """Pure mirror of services/gochara_v3/threshold.py:98-140 ThresholdConfig
    (the provenance record carried on every served window row)."""

    percentile_used: float
    lambda_thresh: float
    implied_density: float
    base_rate_cited: float
    age_band_used: str
    density_flag: str
    fallback_used: bool
    sample_count: int


@dataclass(frozen=True)
class IntervalBoundary:
    """Pure mirror of services/gochara_v3/interval_solver.py:47-77
    IntervalBoundary."""

    enter_jd: float
    exit_jd: float
    peak_jd: float
    peak_lambda: float
    era_slice_key: str = "g3_utkarsha"  # interval_solver.py:34


@dataclass(frozen=True)
class PeakCandidate:
    """Pure mirror of services/gochara_v3/resolution_hierarchy.py:179-183."""

    jd: float
    lam: float


@dataclass(frozen=True)
class WindowRecord:
    """Pure mirror of services/gochara_v3/resolution_hierarchy.py:133-176
    WindowResolutionRecord (fields the algebra/writer consume)."""

    window_id: str
    parent_window_id: Optional[str]
    resolution_tier: str  # "era" | "month" | "day"
    enter_jd: float
    exit_jd: float
    peak_jd: float
    peak_lambda: float


@dataclass(frozen=True)
class DecadeSlice:
    """Pure mirror of the century writer's DecadeSlice
    (ka_gochara_v3_century_materialize.py:652-683)."""

    era_slice_key: str
    start_jd: float
    end_jd: float
    year_start: int
    year_end: int


# ---------------------------------------------------------------------------
# PROMISE — noisy-OR over target weights
# ---------------------------------------------------------------------------

def compute_promise(target_weights: list[float]) -> tuple[float, dict]:
    """Reproduces gochara_intensity/promise.py:42-81 compute_promise.

    PROMISE = 1 - PROD_i (1 - clamp(w_i, 0, 1)); empty target list is an
    honest 0.0 (promise.py:51-59). Time-invariant; computed once per
    (chart, event_class) in ClassContext.fetch (engine.py:488-490).
    """
    if not target_weights:
        return 0.0, {
            "target_count": 0,
            "aggregation": "noisy_or",
            "calibration_state": "structural_prior",
            "note": "no targets -- honest PROMISE=0.0, not a fabricated default.",
        }
    product_complement = 1.0
    per_target = []
    for w in target_weights:
        wc = max(0.0, min(1.0, float(w)))
        product_complement *= (1.0 - wc)
        per_target.append({"weight": wc})
    return 1.0 - product_complement, {
        "target_count": len(target_weights),
        "targets": per_target,
        "aggregation": "noisy_or",
        "calibration_state": "structural_prior",
    }


# ---------------------------------------------------------------------------
# PERMISSION — weighted fraction of active timing systems
# ---------------------------------------------------------------------------

def compute_permission(systems_active: dict[str, bool]) -> float:
    """Reproduces engine.py:1241-1243 (which mirrors permission.py:362-364).

    permission = sum(SYSTEM_WEIGHTS[s] for s active) / sum(SYSTEM_WEIGHTS).
    The denominator is the full 12-system table (sums to 1.0,
    permission.py:100-114), so PERMISSION is a weighted fraction in [0,1].
    Unknown system ids in `systems_active` are ignored (the legacy engine
    only ever iterates the 12 pinned ids, engine.py:1187-1239).
    """
    active_weight = sum(
        SYSTEM_WEIGHTS[s] for s in PERMISSION_SYSTEM_IDS if systems_active.get(s, False)
    )
    total_weight = sum(SYSTEM_WEIGHTS.values())
    return active_weight / total_weight if total_weight else 0.0


# ---------------------------------------------------------------------------
# Activity — orb-decayed noisy-OR over sentences (the W1.1 term)
# ---------------------------------------------------------------------------

def orb_decay_from_detail(detail: dict) -> float:
    """Reproduces engine.py:863-876 (the orb-strength selection inside
    _compute_activity_v3):

      detail['orb_strength'] present -> clamp to [0,1]
      else detail['orb_degrees'] present -> 1 - min(|deg| / 5.0, 1.0)
      else -> 0.5   ("present but unorbed" conservative fallback,
                      engine.py:872-876)

    ARTIFACT (F-09 companion, classified DELIBERATE-fallback): the 0.5
    fallback is documented intent ("not flat 1.0", engine.py:158-160).
    """
    orb_strength_raw = detail.get("orb_strength")
    if orb_strength_raw is not None:
        return float(max(0.0, min(1.0, float(orb_strength_raw))))
    orb_degrees_raw = detail.get("orb_degrees")
    if orb_degrees_raw is not None:
        orb_degrees = abs(float(orb_degrees_raw))
        return 1.0 - min(orb_degrees / ACTIVITY_MAX_ORB_DEG, 1.0)
    return 0.5


def compute_activity_v3(
    sentences: list[Sentence],
    weight_by_target_ref: dict[str, float],
) -> tuple[float, dict, dict]:
    """Reproduces engine.py:821-917 _compute_activity_v3 exactly.

    Per sentence in ACTIVITY_PRIMITIVES (cancelled gochara_vedha_pair
    excluded, engine.py:852-853):
        target_weight = clamp(weight_by_target_ref.get(target_ref, 0.5), 0, 1)
        p_i             = orb_decay(detail) * target_weight
        activity        = 1 - PROD_i (1 - p_i)      (noisy-OR)

    ARTIFACT (F-08a, classified ACCIDENTAL — step function): the orb decay
    is evaluated AT THE EVENT and is constant across the whole ±5-day
    gather window; there is no decay by |t - event_jd|. lambda_v3 therefore
    jumps to its full value for every instant in [event-5d, event+5d] and
    drops to 0 outside it. Reproduced faithfully (see
    legacy_activity_at / contribution_box).
    """
    product_complement = 1.0
    contributions = []
    term_breakdown: dict[str, float] = {}

    for s in sentences:
        if s.primitive not in ACTIVITY_PRIMITIVES:
            continue
        if s.primitive == "gochara_vedha_pair" and s.detail.get("cancelled"):
            continue

        target_weight = max(
            0.0, min(1.0, weight_by_target_ref.get(s.target_ref or "", 0.5))
        )
        orb_decay = orb_decay_from_detail(s.detail)
        p_i = orb_decay * target_weight

        product_complement *= (1.0 - p_i)
        contributions.append({
            "primitive": s.primitive,
            "target_ref": s.target_ref,
            "transit_planet": s.transit_planet,
            "event_datetime_ist": s.event_datetime_ist,
            "target_weight": round(target_weight, 6),
            "orb_decay": round(orb_decay, 6),
            "p_i": round(p_i, 6),
        })
        term_breakdown[s.primitive] = term_breakdown.get(s.primitive, 0.0) + p_i

    activity = 1.0 - product_complement
    activity = max(0.0, min(1.0, activity))
    detail = {
        "activity": round(activity, 8),
        "aggregation": "noisy_or",
        "sentence_count_active": len(contributions),
        "sentence_count_total_gathered": len(sentences),
        "max_orb_deg": ACTIVITY_MAX_ORB_DEG,
        "contributions": contributions,
        "calibration_state": "structural_prior",
    }
    return activity, detail, term_breakdown


def contribution_box(
    sentence: Sentence,
    box_half_days: float = BOX_HALF_DAYS_DEFAULT,
    t_in: Optional[float] = None,
    t_out: Optional[float] = None,
    horizon: Optional[tuple[float, float]] = None,
) -> Optional[tuple[float, float]]:
    """Span-aware statement of the legacy gather window (engine.py:499-501:
    sentences are gathered over [t_jd - 5d, t_jd + 5d]).

    The contribution of one sentence lives over
        [event_jd - B, event_jd + B]
    clipped to the episode span [t_in, t_out] when given and to the
    `horizon` (start_jd, end_jd) when given. Returns None when the clipped
    box is empty (the sentence would never be gathered). This restatement
    is exactly equivalent to the per-instant gather: instant t receives the
    contribution iff t lies in the box.
    """
    if sentence.event_jd is None:
        return None
    lo = sentence.event_jd - box_half_days
    hi = sentence.event_jd + box_half_days
    if t_in is not None:
        lo = max(lo, t_in)
    if t_out is not None:
        hi = min(hi, t_out)
    if horizon is not None:
        lo = max(lo, horizon[0])
        hi = min(hi, horizon[1])
    if hi < lo:
        return None
    return (lo, hi)


def legacy_activity_at(
    sentences: list[Sentence],
    weight_by_target_ref: dict[str, float],
    t_jd: float,
    box_half_days: float = BOX_HALF_DAYS_DEFAULT,
    episode_spans: Optional[dict[int, tuple[float, float]]] = None,
    horizon: Optional[tuple[float, float]] = None,
) -> tuple[float, list[dict]]:
    """Legacy activity at one instant, restated span-aware.

    Collects every sentence whose contribution box (see contribution_box)
    contains t_jd and combines with the same noisy-OR as
    compute_activity_v3. This is bit-equivalent to what the served engine
    computes at t_jd: it gathers sentences with event_jd in
    [t_jd - 5d, t_jd + 5d] (engine.py:499-501, 1063-1154) and each
    contributes its full event-time p_i (the F-08 STEP — no decay by
    |t_jd - event_jd|).
    """
    active: list[Sentence] = []
    for idx, s in enumerate(sentences):
        span = episode_spans.get(idx) if episode_spans else None
        box = contribution_box(
            s, box_half_days,
            t_in=span[0] if span else None,
            t_out=span[1] if span else None,
            horizon=horizon,
        )
        if box is not None and box[0] <= t_jd <= box[1]:
            active.append(s)
    activity, detail, _ = compute_activity_v3(active, weight_by_target_ref)
    return activity, detail["contributions"]


# ---------------------------------------------------------------------------
# W1.2 signed channels + valence (engine.py:920-1060)
# ---------------------------------------------------------------------------

def compute_signed_channels_v3(
    sentences: list[Sentence],
    weight_by_target_ref: dict[str, float],
) -> tuple[float, float, dict]:
    """Reproduces engine.py:920-1015 _compute_signed_channels_v3.

    raw_weight > 0 -> supportive channel; < 0 -> afflicting; == 0 -> skipped.
    p_i = orb_decay * |raw_weight|, clamped to [0,1] (engine.py:977-979).
    Each channel is an independent noisy-OR.
    """
    supportive_complement = 1.0
    afflicting_complement = 1.0
    supportive_contributions = []
    afflicting_contributions = []

    for s in sentences:
        if s.primitive not in ACTIVITY_PRIMITIVES:
            continue
        if s.primitive == "gochara_vedha_pair" and s.detail.get("cancelled"):
            continue
        raw_weight = weight_by_target_ref.get(s.target_ref or "", 0.0)
        if raw_weight == 0.0:
            continue
        orb_decay = orb_decay_from_detail(s.detail)
        p_i = min(1.0, orb_decay * abs(raw_weight))
        record = {
            "primitive": s.primitive,
            "target_ref": s.target_ref,
            "transit_planet": s.transit_planet,
            "event_datetime_ist": s.event_datetime_ist,
            "raw_weight": round(raw_weight, 6),
            "orb_decay": round(orb_decay, 6),
            "p_i": round(p_i, 6),
        }
        if raw_weight > 0.0:
            supportive_complement *= (1.0 - p_i)
            supportive_contributions.append(record)
        else:
            afflicting_complement *= (1.0 - p_i)
            afflicting_contributions.append(record)

    supportive = max(0.0, min(1.0, 1.0 - supportive_complement))
    afflicting = max(0.0, min(1.0, 1.0 - afflicting_complement))
    return supportive, afflicting, {
        "supportive_channel": round(supportive, 8),
        "afflicting_channel": round(afflicting, 8),
        "supportive_sentence_count": len(supportive_contributions),
        "afflicting_sentence_count": len(afflicting_contributions),
        "supportive_contributions": supportive_contributions,
        "afflicting_contributions": afflicting_contributions,
        "aggregation": "noisy_or_per_channel",
    }


def resolve_valence_v3(
    supportive_channel: float,
    afflicting_channel: float,
    *,
    class_valence: str,
    class_is_adverse: bool,
) -> tuple[str, bool, bool]:
    """Reproduces engine.py:1018-1060 _resolve_valence_v3 (rules in
    docstring order)."""
    total = supportive_channel + afflicting_channel
    if total < 1e-10:
        return class_valence, class_is_adverse, False
    imbalance_ratio = abs(supportive_channel - afflicting_channel) / total
    if imbalance_ratio < VALENCE_TENSION_THRESHOLD:
        return "mixed", False, True
    if supportive_channel > afflicting_channel:
        return "favourable", False, False
    return "adverse", True, False


# ---------------------------------------------------------------------------
# W2.3 tara bala modifier (w23_tara_bala.py, wired at engine.py:598-612)
# ---------------------------------------------------------------------------

def longitude_to_nakshatra_index(longitude_deg: float) -> int:
    """w23_tara_bala.py:150-156: floor(lon / (360/27)) + 1, clamped [1,27]."""
    idx = int(longitude_deg / NAKSHATRA_ARC_DEG) + 1
    return max(1, min(27, idx))


def compute_tara(transit_nak_index: int, natal_nak_index: int) -> tuple[str, float]:
    """w23_tara_bala.py:131-147: position = ((transit - natal) % 27) % 9 + 1."""
    position = ((transit_nak_index - natal_nak_index) % 27) % 9 + 1
    tara = TARA_QUALITY[position]
    return tara, TARA_MODIFIERS[tara]


def tara_modifier(
    natal_moon_longitude_deg: Optional[float],
    transit_moon_longitude_deg: Optional[float],
    *,
    enabled: bool = W23_TARA_BALA_ENABLED,
) -> dict:
    """Reproduces w23_tara_bala.compute (w23_tara_bala.py:162-268) as wired
    at engine.py:598-612.

    ARTIFACT NOTE (engine.py:602-606): the engine computes the transit Moon
    longitude inside a bare `except Exception: pass`; on any Swiss failure
    the modifier silently defaults to 1.0 via the mechanism's honest-skip
    path. The skip itself is DOCUMENTED intent ("honest skip: modifier
    defaults to 1.0 via mechanism", engine.py:606); reproduced here as
    transit_moon_longitude_deg=None -> modifier 1.0, skipped=True.
    """
    if not enabled:
        return {"modifier": 1.0, "tara_name": None, "tara_position": None,
                "skipped": True, "skip_reason": "mechanism disabled via toggle"}
    if natal_moon_longitude_deg is None:
        return {"modifier": 1.0, "tara_name": None, "tara_position": None,
                "skipped": True, "skip_reason": "natal_facts not available in context"}
    if transit_moon_longitude_deg is None:
        return {"modifier": 1.0, "tara_name": None, "tara_position": None,
                "skipped": True, "skip_reason": "transit_body_longitude_deg not supplied"}
    natal_nak = longitude_to_nakshatra_index(natal_moon_longitude_deg)
    transit_nak = longitude_to_nakshatra_index(transit_moon_longitude_deg)
    tara_name, modifier = compute_tara(transit_nak, natal_nak)
    position = ((transit_nak - natal_nak) % 27) % 9 + 1
    return {"modifier": modifier, "tara_name": tara_name, "tara_position": position,
            "skipped": False, "skip_reason": None}


# ---------------------------------------------------------------------------
# W3.0 nodal drishti modifier (w30_nodal_drishti.py, wired at engine.py:624-629)
# ---------------------------------------------------------------------------

def w30_aspected_signs(rahu_sign: int) -> frozenset[int]:
    """w30_nodal_drishti.py:147-159: Rahu and Ketu (= rahu+6) each aspect
    their 5th (+4), 7th (+6), 9th (+8) signs."""
    ketu_sign = (rahu_sign + 6) % 12
    aspected: set[int] = set()
    for base in (rahu_sign, ketu_sign):
        for offset in W30_ASPECT_OFFSETS:
            aspected.add((base + offset) % 12)
    return frozenset(aspected)


def w30_modifier(
    rahu_longitude_deg: Optional[float],
    target_sign_names: list[str],
    *,
    enabled: bool = W30_NODAL_DRISHTI_ENABLED,
    natal_facts_available: bool = True,
) -> dict:
    """Reproduces w30_nodal_drishti.compute (w30_nodal_drishti.py:165-310)
    as wired at engine.py:624-629.

    ARTIFACT (F-28/F-29, classified ACCIDENTAL — enabled candidate with a
    REFUTED citation): the engine toggle W30_NODAL_DRISHTI_ENABLED is True
    (engine.py:107) while the module's own docstring calls the 5/7/9 nodal
    aspect "NOT found in the original BPHS" (w30_nodal_drishti.py:11-12)
    and the primitives.py:193-194 BPHS Ch.26 citation is corpus-refuted.
    N-14 will remove this factor; the baseline documents its live semantics:
    geometric mean over per-target aspect contributions (Rahu preferred over
    Ketu when both aspect the same sign), 1.0 when nothing is aspected.

    `rahu_longitude_deg=None` reproduces the engine's swe-failure honest
    skip (w30:226-243).
    """
    if not enabled:
        return {"modifier": 1.0, "aspected_sign_indices": (), "rahu_sign": None,
                "ketu_sign": None, "skipped": True,
                "skip_reason": "mechanism disabled via toggle"}
    if not natal_facts_available:
        return {"modifier": 1.0, "aspected_sign_indices": (), "rahu_sign": None,
                "ketu_sign": None, "skipped": True,
                "skip_reason": "natal_facts not available in context"}
    if rahu_longitude_deg is None:
        return {"modifier": 1.0, "aspected_sign_indices": (), "rahu_sign": None,
                "ketu_sign": None, "skipped": True,
                "skip_reason": "swe.calc_ut failed"}

    rahu_sign = int(rahu_longitude_deg / 30.0) % 12
    ketu_sign = (rahu_sign + 6) % 12
    aspected = w30_aspected_signs(rahu_sign)

    contributions: list[float] = []
    for sign_name in target_sign_names:
        target_idx = W30_SIGN_TO_INDEX.get(sign_name)
        if target_idx is None or target_idx not in aspected:
            continue
        contribution_modifier: Optional[float] = None
        for base_sign in (rahu_sign, ketu_sign):
            for offset in W30_ASPECT_OFFSETS:
                if (base_sign + offset) % 12 == target_idx:
                    contribution_modifier = W30_ASPECT_MODIFIERS[offset]
                    break
            if contribution_modifier is not None:
                break
        if contribution_modifier is not None:
            contributions.append(contribution_modifier)

    if not contributions:
        modifier = 1.0
    else:
        log_sum = sum(math.log(c) for c in contributions)
        modifier = math.exp(log_sum / len(contributions))

    return {"modifier": modifier, "aspected_sign_indices": tuple(sorted(aspected)),
            "rahu_sign": rahu_sign, "ketu_sign": ketu_sign, "skipped": False,
            "skip_reason": None}


# ---------------------------------------------------------------------------
# W1.3 quality gates (engine.py:272-415)
# ---------------------------------------------------------------------------

def _suppression_factor_for_grade(effect_grade: str) -> float:
    """engine.py:253-256."""
    key = (effect_grade or "").strip().lower().replace(" ", "_")
    return VEDHA_GRADE_SUPPRESSION.get(key, VEDHA_WORST_SUPPRESSION)


def compute_quality_gates(
    vedha_rows: list[dict],
    window_start_iso: str,
    window_end_iso: str,
    malefic_scale_by_count: Optional[dict[int, str]] = None,
) -> tuple[float, dict]:
    """Reproduces engine.py:272-415 _compute_quality_gates_from_context.

    vedha_rows: list of dicts with keys window_start, window_end (ISO
    DATE strings, lexicographic overlap per engine.py:307-315), vedha_kind,
    graha, detail (dict with malefic_count), classical_citation.
    malefic_scale_by_count: malefic_count int -> effect_grade str (the
    bg_vedha_malefic_scale rows; None/{} reproduces the empty-table path).

    Overlap semantics (engine.py:307-315): row overlaps iff
    row.window_start <= window_end_iso AND row.window_end >= window_start_iso
    (DATE-string lexicographic comparison — DATE-grain, not instant-grain;
    classification WP3b_CLASSIFICATION.md row Q-3).

    ARTIFACT (F-11, classified ACCIDENTAL — unknown-as-clear): when NO
    vedha row overlaps, the product stays 1.0 (engine.py:287 "AC1", :400) —
    an interval where the overlay simply was never built is served as fully
    gated. The honest 'unavailable' state does not exist on this path.
    """
    scale_by_count = malefic_scale_by_count or {}
    fired_vedha: list[dict] = []
    product = 1.0

    for vrow in vedha_rows:
        if vrow["window_start"] > window_end_iso:
            continue
        if vrow["window_end"] < window_start_iso:
            continue

        detail = vrow.get("detail") or {}

        # B3 latta path (engine.py:328-354)
        if vrow.get("vedha_kind") == "latta":
            if scale_by_count:
                scale_grade = scale_by_count.get(
                    LATTA_EFFECTIVE_MALEFIC_COUNT,
                    scale_by_count.get(max(scale_by_count)),
                )
                suppression_factor = _suppression_factor_for_grade(scale_grade)
            else:
                suppression_factor = VEDHA_NO_SCALE_ROW_FACTOR
            product *= suppression_factor
            fired_vedha.append({"vedha_kind": "latta", "suppression_factor": suppression_factor})
            continue

        malefic_count = detail.get("malefic_count", 0)
        try:
            malefic_count = int(malefic_count)
        except (TypeError, ValueError):
            malefic_count = 0

        if malefic_count == 0:
            suppression_factor = VEDHA_ZERO_MALEFIC_FACTOR
            effect_grade = "no_grade"
        elif malefic_count > 0 and scale_by_count:
            scale_grade = scale_by_count.get(malefic_count)
            if scale_grade is None:
                scale_grade = scale_by_count.get(max(scale_by_count))
            effect_grade = scale_grade if scale_grade else "unknown"
            suppression_factor = _suppression_factor_for_grade(effect_grade)
        else:
            suppression_factor = VEDHA_NO_SCALE_ROW_FACTOR
            effect_grade = "unknown_no_scale_table"

        product *= suppression_factor
        fired_vedha.append({
            "vedha_kind": vrow.get("vedha_kind"),
            "graha": vrow.get("graha"),
            "malefic_count": malefic_count,
            "effect_grade": effect_grade,
            "suppression_factor": round(suppression_factor, 6),
        })

    quality_gates = product
    detail_out = {
        "quality_gates": round(quality_gates, 8),
        "vedha_fired_count": len(fired_vedha),
        "vedha_rows_total": len(vedha_rows),
        "aggregation": "multiplicative",
        "fired_vedha": fired_vedha,
        "calibration_state": "structural_prior",
    }
    return quality_gates, detail_out


# ---------------------------------------------------------------------------
# lambda_v3 assembly (engine.py:631-637, 773-788)
# ---------------------------------------------------------------------------

def assemble_lambda_v3(
    *,
    promise: float,
    permission: float,
    activity: float,
    tara_modifier: float,
    w30_modifier: float,
    quality_gates: float,
    is_adverse: bool = False,
) -> dict:
    """Reproduces engine.py:631-637 (the product + clamp), engine.py:637
    (sign), engine.py:773-783 (W1.5 term_breakdown) and engine.py:787-788
    (structural-prior CI band).

    NOTE: the legacy engine never receives quality_gates=None (the W1.3
    path always returns a float, defaulting to 1.0 — F-11). The honest
    'unavailable' contract is the WP2 oracle's rule, not the legacy engine's;
    passing None here raises, matching the oracle's "an unknown input is
    never silently treated as empty".
    """
    if quality_gates is None:
        raise ValueError(
            "quality_gates=None has no legacy-engine meaning (W1.3 always "
            "returns a float; the honest-unavailable state is the WP2 "
            "oracle's contract, reproduced only in the classification)."
        )
    raw_lambda = promise * permission * activity * tara_modifier * w30_modifier * quality_gates
    raw_lambda = max(0.0, min(1.0, raw_lambda))
    signed_lambda = raw_lambda * (-1.0 if is_adverse else 1.0)
    ci_low = max(0.0, raw_lambda * 0.8)
    ci_high = min(1.0, raw_lambda * 1.2)
    term_breakdown = {
        "promise": round(promise, 8),
        "permission": round(permission, 8),
        "activity": round(activity, 8),
        "tara_modifier": round(tara_modifier, 8),
        "w30_modifier": round(w30_modifier, 8),
        "quality_gates": round(quality_gates, 8),
        "lambda_v3": round(raw_lambda, 8),
        "formula": TERM_BREAKDOWN_FORMULA,
    }
    return {
        "lambda_raw": raw_lambda,
        "lambda_signed": signed_lambda,
        "term_breakdown": term_breakdown,
        "lambda_v3_ci_low": ci_low,
        "lambda_v3_ci_high": ci_high,
        "ci_source": "structural_prior",
        "formula": LAMBDA_V3_FORMULA,
    }


# ---------------------------------------------------------------------------
# W1.4 threshold certification (threshold.py:257-404)
# ---------------------------------------------------------------------------

def _percentile_linear(values: list[float], percentile: float) -> float:
    """numpy.percentile(..., method='linear') equivalent (numpy's default).

    rank = (n - 1) * p / 100; interpolate between floor/ceil sorted values.
    """
    if not values:
        raise ValueError("percentile of empty distribution")
    vs = sorted(float(v) for v in values)
    p = float(percentile)
    if p <= 0:
        return vs[0]
    if p >= 100:
        return vs[-1]
    rank = (len(vs) - 1) * (p / 100.0)
    lo = int(math.floor(rank))
    hi = int(math.ceil(rank))
    if lo == hi:
        return vs[lo]
    frac = rank - lo
    return vs[lo] * (1.0 - frac) + vs[hi] * frac


def compute_threshold_config(
    lambda_distribution: list[float],
    *,
    base_rate: Optional[float] = None,
    age_band_used: str = "band_41_60",
    step_days: float = CENTURY_STEP_DAYS,
) -> ThresholdConfig:
    """Reproduces threshold.py:257-383 compute_threshold_config, with the
    century evaluation itself EXTERNALIZED (the caller supplies the lambda
    distribution — the same separation threshold.py's own
    `_lambda_distribution` test hook provides, threshold.py:265/307-309).

    base_rate=None reproduces the fallback path (threshold.py:163-168:
    UNIFORM_BASE_RATE, fallback_used=True, density_flag 'no_base_rate').

    Percentile formula (threshold.py:293-304): P = 1 - base_rate, clamped
    to [0.05, 0.999]; lambda_thresh = P-th percentile of the distribution;
    empty distribution -> lambda_thresh = 0.0 (threshold.py:321-322).

    ARTIFACT (F-08 companion, classified ACCIDENTAL): an all-zero (or
    empty) century distribution yields lambda_thresh = 0.0, and the gating
    predicate is `lambda_v3 >= lambda_thresh` (threshold.py:386-393) — so a
    JD whose evaluation FAILED (0.0 via the exception path) is certified
    'active'. See eval_single_legacy / is_above_threshold below.
    """
    if base_rate is None:
        base_rate_eff = UNIFORM_BASE_RATE
        fallback_used = True
    else:
        base_rate_eff = float(base_rate)
        fallback_used = False

    raw_p = 1.0 - base_rate_eff
    percentile = max(0.05, min(0.999, raw_p))

    dist = [float(v) for v in lambda_distribution]
    sample_count = len(dist)

    if sample_count == 0:
        lambda_thresh = 0.0
    else:
        lambda_thresh = _percentile_linear(dist, percentile * 100.0)
        lambda_thresh = max(0.0, min(1.0, lambda_thresh))

    if sample_count == 0 or step_days <= 0:
        implied_density = 0.0
    else:
        active_count = sum(1 for v in dist if v >= lambda_thresh)
        implied_density = (active_count / sample_count) * (365.25 / step_days)

    density_flag = "ok"
    if implied_density > MAX_SANE_WINDOWS_PER_YEAR:
        density_flag = "pathological_dense"
    elif implied_density == 0.0 and not fallback_used and base_rate_eff > UNIFORM_BASE_RATE:
        density_flag = "starved"
    elif fallback_used:
        density_flag = "no_base_rate"

    return ThresholdConfig(
        percentile_used=round(percentile, 6),
        lambda_thresh=round(lambda_thresh, 8),
        implied_density=round(implied_density, 4),
        base_rate_cited=round(base_rate_eff, 6),
        age_band_used=age_band_used,
        density_flag=density_flag,
        fallback_used=fallback_used,
        sample_count=sample_count,
    )


def is_above_threshold(lambda_v3: float, config: ThresholdConfig) -> bool:
    """Reproduces threshold.py:386-393 — `lambda_v3 >= config.lambda_thresh`.

    The `>=` (not `>`) is load-bearing in the legacy defect: with
    lambda_thresh = 0.0, a FAILED evaluation (0.0 via eval_single_legacy's
    exception swallow) is certified 'active'. ARTIFACT F-08, reproduced.
    """
    return lambda_v3 >= config.lambda_thresh


def eval_single_legacy(eval_fn: Callable[[float], float], jd: float) -> float:
    """Reproduces interval_solver.py:116-136 _eval_single.

    ARTIFACT (F-08 / H-2, classified ACCIDENTAL): ANY exception from the
    evaluation (including a genuine solver failure) is swallowed
    (`except Exception ... return 0.0`, interval_solver.py:132-136) and the
    scalar 0.0 flows into the coarse sweep, the bisection, the dense peak
    scan AND the threshold predicate — where, with lambda_thresh = 0.0, it
    is certified 'active'. Reproduced faithfully; WP5/H-2 fixes the engine,
    not this baseline.
    """
    try:
        return float(eval_fn(float(jd)))
    except Exception:  # noqa: BLE001 — faithful reproduction of interval_solver.py:132
        return 0.0


# ---------------------------------------------------------------------------
# W3.2 interval solver (interval_solver.py:162-393), evaluator-injected
# ---------------------------------------------------------------------------

def _bisect_crossing(
    eval_fn: Callable[[float], float],
    jd_low: float,
    jd_high: float,
    lambda_thresh: float,
    *,
    tol_days: float = BISECT_TOL_DAYS,
    target_above: bool,
) -> float:
    """interval_solver.py:162-195 _bisect_crossing (with _eval_single's
    exception->0.0 semantics via eval_single_legacy)."""
    lo, hi = jd_low, jd_high
    max_iters = 100
    for _ in range(max_iters):
        if (hi - lo) < tol_days:
            break
        mid = 0.5 * (lo + hi)
        mid_lambda = eval_single_legacy(eval_fn, mid)
        mid_above = mid_lambda >= lambda_thresh
        if mid_above == target_above:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def _find_peak(
    eval_fn: Callable[[float], float],
    enter_jd: float,
    exit_jd: float,
    *,
    sample_count: int = PEAK_SAMPLE_COUNT,
) -> tuple[float, float]:
    """interval_solver.py:372-393 _find_peak. np.argmax returns the FIRST
    index attaining the max — reproduced with strict `>`."""
    if exit_jd <= enter_jd:
        lam = eval_single_legacy(eval_fn, enter_jd)
        return enter_jd, lam
    n = max(2, sample_count)
    step = (exit_jd - enter_jd) / (n - 1)
    best_idx = 0
    best_lam = eval_single_legacy(eval_fn, enter_jd)
    for i in range(1, n):
        lam = eval_single_legacy(eval_fn, enter_jd + i * step)
        if lam > best_lam:
            best_lam = lam
            best_idx = i
    return enter_jd + best_idx * step, best_lam


def find_threshold_crossings(
    eval_fn: Callable[[float], float],
    start_jd: float,
    end_jd: float,
    lambda_thresh: float,
    *,
    coarse_step_days: float = 7.0,
    bisect_tol_days: float = BISECT_TOL_DAYS,
    return_series: bool = False,
):
    """Reproduces interval_solver.py:202-369 find_threshold_crossings.

    ARTIFACT (F-10/H-3, classified ACCIDENTAL — zero-score ranges declared):
    when the coarse series STARTS above threshold, enter_jd is set to
    jd_series[0] = the sweep start (interval_solver.py:304-306) with no
    check that the crossing actually occurs there; symmetrically exit_jd =
    jd_series[-1] when the series ends above (interval_solver.py:324-326).
    An era window is thereby declared over a range whose underlying score is
    below threshold (the true crossing lying outside the swept range).
    Reproduced faithfully.
    """
    if end_jd <= start_jd:
        if return_series:
            return [], [], []
        return []

    jd_series = []
    jd = start_jd
    while jd < end_jd:
        jd_series.append(jd)
        jd += coarse_step_days
    if not jd_series:
        if return_series:
            return [], [], []
        return []

    lambdas = [eval_single_legacy(eval_fn, t) for t in jd_series]
    above_flags = [lam >= lambda_thresh for lam in lambdas]

    intervals: list[IntervalBoundary] = []
    i = 0
    n = len(above_flags)
    while i < n:
        if not above_flags[i]:
            i += 1
            continue
        if i > 0:
            enter_jd = _bisect_crossing(
                eval_fn, jd_series[i - 1], jd_series[i], lambda_thresh,
                tol_days=bisect_tol_days, target_above=True,
            )
        else:
            enter_jd = float(jd_series[0])  # ARTIFACT F-10/H-3 (see docstring)
        j = i
        while j < n and above_flags[j]:
            j += 1
        if j < n:
            exit_jd = _bisect_crossing(
                eval_fn, jd_series[j - 1], jd_series[j], lambda_thresh,
                tol_days=bisect_tol_days, target_above=False,
            )
        else:
            exit_jd = float(jd_series[-1])  # ARTIFACT F-10/H-3 (see docstring)

        peak_jd, peak_lambda = _find_peak(eval_fn, enter_jd, exit_jd)
        intervals.append(IntervalBoundary(
            enter_jd=enter_jd, exit_jd=exit_jd,
            peak_jd=peak_jd, peak_lambda=peak_lambda,
        ))
        i = j

    if return_series:
        return intervals, jd_series, lambdas
    return intervals


# ---------------------------------------------------------------------------
# W3.3 resolution hierarchy (resolution_hierarchy.py), evaluator-injected
# ---------------------------------------------------------------------------

def build_decade_slices(
    birth_jd: float,
    birth_year: int,
    count: int = DECADE_COUNT,
    days_per_year: float = DAYS_PER_YEAR,
) -> list[DecadeSlice]:
    """ka_gochara_v3_century_materialize.py:652-683 build_decade_slices:
    slice i spans [birth_jd + i*10*DAYS_PER_YEAR, birth_jd + (i+1)*10*
    DAYS_PER_YEAR), labeled g3_{birth_year + 10i}_{birth_year + 10(i+1)}.

    These whole-decade ranges are the era-window sweep spans (F-10's "era
    window = whole decade range" — each (event_class, decade) substep calls
    build_resolution_hierarchy over exactly one of these).
    """
    slices: list[DecadeSlice] = []
    for i in range(count):
        year_start = birth_year + i * 10
        year_end = birth_year + (i + 1) * 10
        slices.append(DecadeSlice(
            era_slice_key=f"g3_{year_start}_{year_end}",
            start_jd=birth_jd + i * 10 * days_per_year,
            end_jd=birth_jd + (i + 1) * 10 * days_per_year,
            year_start=year_start,
            year_end=year_end,
        ))
    return slices


def find_local_maxima(jds: list[float], lambdas: list[float]) -> list[PeakCandidate]:
    """resolution_hierarchy.py:370-405 find_local_maxima.

    Interior candidate: strict rise AND non-increase after (s[i] > s[i-1]
    and s[i] >= s[i+1]) — the flat top of a plateau is admitted EXACTLY
    ONCE, at its FIRST point (documented at resolution_hierarchy.py:374-376;
    in tension with WP2 case 12's pinned tie-break, which admits ALL tied
    maxima — classified DELIBERATE-legacy, see WP3b_CLASSIFICATION.md P-1).
    """
    n = len(lambdas)
    if n < 2:
        return []
    candidates: list[PeakCandidate] = []
    for i in range(n):
        if i == 0:
            if lambdas[0] > lambdas[1]:
                candidates.append(PeakCandidate(float(jds[0]), float(lambdas[0])))
        elif i == n - 1:
            if lambdas[i] > lambdas[i - 1]:
                candidates.append(PeakCandidate(float(jds[i]), float(lambdas[i])))
        else:
            if lambdas[i] > lambdas[i - 1] and lambdas[i] >= lambdas[i + 1]:
                candidates.append(PeakCandidate(float(jds[i]), float(lambdas[i])))
    return candidates


def admit_candidates(
    candidates: list[PeakCandidate],
    series_lambdas: list[float],
    *,
    percentile: float = ADMISSION_PERCENTILE,
) -> list[PeakCandidate]:
    """resolution_hierarchy.py:413-439 admit_candidates: candidate.lam >=
    P90 of the era window's OWN coarse series; flat series (max <= min)
    admits nothing."""
    if len(series_lambdas) == 0 or not candidates:
        return []
    lo = min(series_lambdas)
    hi = max(series_lambdas)
    if hi <= lo:
        return []
    p90 = _percentile_linear(series_lambdas, percentile)
    return [c for c in candidates if c.lam >= p90]


def retain_candidates(
    admitted: list[PeakCandidate],
    *,
    max_peaks: int = MAX_PEAKS_PER_ERA_WINDOW,
    min_separation_days: float = MIN_PEAK_SEPARATION_DAYS,
) -> list[PeakCandidate]:
    """resolution_hierarchy.py:446-465 retain_candidates: rank (lambda DESC,
    jd ASC), greedy-retain enforcing min_separation, capped at max_peaks.

    ARTIFACT (F-10/H-5, classified ACCIDENTAL — truncation as absence):
    the MAX_PEAKS_PER_ERA_WINDOW=3 cap drops every admitted peak beyond the
    third BEFORE persistence; nothing downstream can recover them. Pre-H-5
    behavior, reproduced faithfully.
    """
    ranked = sorted(admitted, key=lambda c: (-c.lam, c.jd))
    retained: list[PeakCandidate] = []
    for c in ranked:
        if len(retained) >= max_peaks:
            break
        if all(abs(c.jd - r.jd) >= min_separation_days for r in retained):
            retained.append(c)
    return sorted(retained, key=lambda c: c.jd)


def retain_candidates_pooled(
    admitted_by_era: list[list[PeakCandidate]],
    *,
    max_peaks_per_era: int = MAX_PEAKS_PER_ERA_WINDOW,
    min_separation_days: float = MIN_PEAK_SEPARATION_DAYS,
) -> list[list[PeakCandidate]]:
    """resolution_hierarchy.py:474-544 retain_candidates_pooled (MR-44):
    one pooled retention pass across ALL era windows of a call; the cap
    stays per-era-window, the separation check is global."""
    tagged = [
        (era_idx, c)
        for era_idx, candidates in enumerate(admitted_by_era)
        for c in candidates
    ]
    ranked = sorted(tagged, key=lambda t: (-t[1].lam, t[1].jd))
    retained: list[tuple[int, PeakCandidate]] = []
    per_era_count: dict[int, int] = {}
    for era_idx, c in ranked:
        if per_era_count.get(era_idx, 0) >= max_peaks_per_era:
            continue
        if all(abs(c.jd - r.jd) >= min_separation_days for _, r in retained):
            retained.append((era_idx, c))
            per_era_count[era_idx] = per_era_count.get(era_idx, 0) + 1
    result: list[list[PeakCandidate]] = [[] for _ in admitted_by_era]
    for era_idx, c in retained:
        result[era_idx].append(c)
    for bucket in result:
        bucket.sort(key=lambda c: c.jd)
    return result


def refine_peak_to_day(
    eval_fn: Callable[[float], float],
    candidate_jd: float,
    *,
    half_window_days: float = DAY_REFINEMENT_HALF_WINDOW_DAYS,
    step_days: float = DAY_REFINEMENT_STEP_DAYS,
) -> tuple[float, float]:
    """resolution_hierarchy.py:551-598 refine_peak_to_day: 1-day-resolution
    argmax over [candidate - 7d, candidate + 7d]; the candidate's own value
    seeds the running best (with the same exception->0.0 semantics)."""
    start = candidate_jd - half_window_days
    end = candidate_jd + half_window_days
    n_steps = int(round((end - start) / step_days)) + 1

    best_jd = candidate_jd
    best_lam = eval_single_legacy(eval_fn, candidate_jd)

    jd = start
    for _ in range(n_steps):
        lam = eval_single_legacy(eval_fn, jd)
        if lam > best_lam:
            best_lam = lam
            best_jd = jd
        jd += step_days
    return best_jd, best_lam


def build_resolution_hierarchy(
    eval_fn: Callable[[float], float],
    start_jd: float,
    end_jd: float,
    lambda_thresh: float,
    *,
    coarse_step_days: float = PEAK_SCAN_STRIDE_DAYS,
) -> dict:
    """Reproduces resolution_hierarchy.py:850-1043 build_resolution_hierarchy
    (era windows + peak-anchored month/day children + pooled retention).

    Returns a dict with keys: era_windows, month_windows, day_windows
    (lists of WindowRecord), resolution_facet, era_window_count,
    peaks_scanned, peaks_admitted, peaks_retained.

    ERA WINDOWS (F-10, pre-H-3/H-5 semantics): every find_threshold_crossings
    interval becomes one era-tier window over the WHOLE-DECADE sweep range
    this was called with; peaks are admitted at the era window's own P90,
    retained with the pooled per-era cap of 3 (MAX_PEAKS_PER_ERA_WINDOW),
    day-refined at 1-day resolution over +/-7 days. Zero retained peaks ->
    zero month/day rows, no fabrication (R8.6).
    """
    empty = {
        "era_windows": [], "month_windows": [], "day_windows": [],
        "resolution_facet": {"era": 0, "month": 0, "day": 0},
        "era_window_count": 0, "peaks_scanned": 0,
        "peaks_admitted": 0, "peaks_retained": 0,
    }
    if end_jd <= start_jd:
        return empty

    intervals, series_jds, series_lambdas = find_threshold_crossings(
        eval_fn, start_jd, end_jd, lambda_thresh,
        coarse_step_days=coarse_step_days, return_series=True,
    )

    era_windows: list[WindowRecord] = []
    admitted_by_era: list[list[PeakCandidate]] = []
    total_scanned = 0
    total_admitted = 0

    for interval in intervals:
        era_windows.append(WindowRecord(
            window_id=str(uuid.uuid4()),
            parent_window_id=None,
            resolution_tier="era",
            enter_jd=interval.enter_jd,
            exit_jd=interval.exit_jd,
            peak_jd=interval.peak_jd,
            peak_lambda=interval.peak_lambda,
        ))
        sliced = [
            (t, lam) for t, lam in zip(series_jds, series_lambdas)
            if interval.enter_jd <= t <= interval.exit_jd
        ]
        sliced_jds = [t for t, _ in sliced]
        sliced_lams = [lam for _, lam in sliced]
        if len(sliced_jds) < 3:
            admitted: list[PeakCandidate] = []
            total_scanned += 0
        else:
            candidates = find_local_maxima(sliced_jds, sliced_lams)
            total_scanned += len(candidates)
            admitted = admit_candidates(candidates, sliced_lams)
        total_admitted += len(admitted)
        admitted_by_era.append(admitted)

    retained_by_era = retain_candidates_pooled(admitted_by_era)

    all_month: list[WindowRecord] = []
    all_day: list[WindowRecord] = []
    total_retained = 0
    for era_record, retained in zip(era_windows, retained_by_era):
        total_retained += len(retained)
        for cand in retained:
            peak_jd_true, peak_lambda_true = refine_peak_to_day(eval_fn, cand.jd)
            # calendar-month bounds of the refined peak (rh:621-632)
            days_since_epoch = int(peak_jd_true - 2440588.0)
            # month clipping to the era window (R8.6, rh:705-707)
            d = _dt.date(1970, 1, 1) + _dt.timedelta(days=days_since_epoch)
            month_start = _dt.date(d.year, d.month, 1)
            if d.month == 12:
                next_month = _dt.date(d.year + 1, 1, 1)
            else:
                next_month = _dt.date(d.year, d.month + 1, 1)
            month_end = next_month - _dt.timedelta(days=1)

            def _pydate_to_jd(dd: _dt.date) -> float:
                return 2440588.0 + (dd - _dt.date(1970, 1, 1)).days

            month_start_jd = max(_pydate_to_jd(month_start), era_record.enter_jd)
            month_end_jd = min(_pydate_to_jd(month_end), era_record.exit_jd)

            month_id = str(uuid.uuid4())
            all_month.append(WindowRecord(
                window_id=month_id, parent_window_id=era_record.window_id,
                resolution_tier="month", enter_jd=month_start_jd,
                exit_jd=month_end_jd, peak_jd=peak_jd_true,
                peak_lambda=peak_lambda_true,
            ))
            all_day.append(WindowRecord(
                window_id=str(uuid.uuid4()), parent_window_id=month_id,
                resolution_tier="day", enter_jd=peak_jd_true,
                exit_jd=peak_jd_true, peak_jd=peak_jd_true,
                peak_lambda=peak_lambda_true,
            ))

    return {
        "era_windows": era_windows,
        "month_windows": all_month,
        "day_windows": all_day,
        "resolution_facet": {"era": len(era_windows), "month": len(all_month), "day": len(all_day)},
        "era_window_count": len(era_windows),
        "peaks_scanned": total_scanned,
        "peaks_admitted": total_admitted,
        "peaks_retained": total_retained,
    }


__all__ = [
    # constants
    "LAMBDA_V3_FORMULA", "TERM_BREAKDOWN_FORMULA", "ACTIVITY_MAX_ORB_DEG",
    "ACTIVITY_PRIMITIVES", "VALENCE_TENSION_THRESHOLD",
    "VEDHA_GRADE_SUPPRESSION", "SYSTEM_WEIGHTS", "PERMISSION_SYSTEM_IDS",
    "W30_NODAL_DRISHTI_ENABLED", "W23_TARA_BALA_ENABLED",
    "TARA_QUALITY", "TARA_MODIFIERS", "W30_SIGN_NAMES", "W30_ASPECT_MODIFIERS",
    "PEAK_SCAN_STRIDE_DAYS", "ADMISSION_PERCENTILE", "MIN_PEAK_SEPARATION_DAYS",
    "MAX_PEAKS_PER_ERA_WINDOW", "DAY_REFINEMENT_HALF_WINDOW_DAYS",
    "DAY_REFINEMENT_STEP_DAYS", "BISECT_TOL_DAYS", "PEAK_SAMPLE_COUNT",
    "CENTURY_STEP_DAYS", "UNIFORM_BASE_RATE", "DECADE_COUNT", "DAYS_PER_YEAR",
    "BOX_HALF_DAYS_DEFAULT",
    # data mirrors
    "Sentence", "ThresholdConfig", "IntervalBoundary", "PeakCandidate",
    "WindowRecord", "DecadeSlice",
    # factors
    "compute_promise", "compute_permission", "orb_decay_from_detail",
    "compute_activity_v3", "contribution_box", "legacy_activity_at",
    "compute_signed_channels_v3", "resolve_valence_v3",
    "tara_modifier", "compute_tara", "longitude_to_nakshatra_index",
    "w30_modifier", "w30_aspected_signs",
    "compute_quality_gates", "assemble_lambda_v3",
    # threshold + windows
    "compute_threshold_config", "is_above_threshold", "eval_single_legacy",
    "find_threshold_crossings", "build_decade_slices", "find_local_maxima",
    "admit_candidates", "retain_candidates", "retain_candidates_pooled",
    "refine_peak_to_day", "build_resolution_hierarchy",
]
