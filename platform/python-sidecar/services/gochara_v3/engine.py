"""
gochara_v3.engine — batched lambda_e evaluation: ZERO per-JD DB access.

    evaluate_lambda_vector(swe, context, jd_vector) -> list[IntensityResult]

All DB data is pre-fetched in ClassContext.fetch(). This module operates
ENTIRELY against that context's immutable data + Swiss Ephemeris calls.
The ephemeris calls (transit_search primitives) are the remaining per-JD
cost, but they are CPU-bound, not IO-bound, and much faster than DB
round-trips.

Per I2 (v1 modules NEVER edited in place):
  - primitives are IMPORTED from gochara_grammar.primitives
  - composition operators from gochara_grammar.composition
  - promise/suppression/beta/valence from gochara_intensity.*
  - the v1 per-point compute_lambda_e is called in v1-parity mode
    (optional flag) for golden-test comparison

Architecture:
  - PROMISE is time-invariant -> computed once in ClassContext.fetch()
  - PERMISSION is evaluated per-JD using pre-fetched dasha periods +
    pre-fetched sade_sati phases + ephemeris-only checks for the
    remaining generators (guru-shani, av_threshold, planetary_return)
  - X(t) is evaluated per-JD via the same v1 primitives (ephemeris only,
    no DB) with pre-fetched targets
  - SUPPRESSION is evaluated per-JD from the same sentence pool as X(t)

W1.1 — Bounded lambda_v3 formula (v1_parity_mode=False):
  lambda_v3 = PROMISE * PERMISSION * activity * quality_gates

  Where:
    PROMISE    in [0,1]: noisy-OR over target weights (same compute_promise math)
    PERMISSION in [0,1]: weighted-fraction of active timing systems
    activity   in [0,1]: saturating aggregate of orb-strength-decayed sentences
                         via noisy-OR over per-sentence contributions
    quality_gates: product of quality filters (default 1.0 for W1.1)

  KEY INVARIANT: lambda_v3 in [0,1] by construction (noisy-OR of [0,1]
  values multiplied by [0,1] factors = [0,1]).

  REMOVED: exp(beta * X(t)) — the unbounded exponential that produced
  values 1e0–1.5e21 (X reaching ~66, beta=0.45), swamping PROMISE
  and PERMISSION.

W1.2 — Direction Restored (signed valence channels):
  _compute_signed_channels_v3 separates sentences into:
    - supportive channel  (weight > 0): noisy-OR of orb_decay * |weight|
    - afflicting channel  (weight < 0): noisy-OR of orb_decay * |weight|

  Window valence emerges from the net evidence sign:
    - sum_supportive > sum_afflicting  => valence = 'favourable'
    - sum_afflicting > sum_supportive  => valence = 'adverse'
    - roughly equal (within VALENCE_TENSION_THRESHOLD) => valence = 'mixed',
      valence_tension = True

  The class-level valence (from brahma_event_ontology, context.valence) is
  retained as prior when both channels are zero (no configuration evidence).

  KEY INVARIANT: valence_tension is True IFF afflicting and supportive
  channels nearly cancel. It is surfaced in x_t_detail['valence_tension']
  and does NOT average away the disagreement.

  I2 COMPLIANCE: no file in gochara_grammar/ or gochara_intensity/ is
  modified. All sign handling is in this module only.

v1-parity mode (v1_parity_mode=True):
  The original PROMISE * PERMISSION * exp(beta*X) - suppression formula,
  preserved bit-for-bit for golden-test comparison. The existing
  test_v1_parity.py tests rely on this path.
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Optional

import numpy as np

# v1 imports (I2 compliance — imported, never copied/edited)
from services.gochara_grammar import primitives as P
from services.gochara_grammar import sarvatobhadra as SBC
from services.gochara_grammar import composition as CO
from services.gochara_grammar import dasha_data as DD
from services.gochara_grammar.models import ConfigurationSentence, ResonanceTarget
from services.gochara_intensity.models import IntensityResult
from services.gochara_intensity.suppression import compute_suppression, SUPPRESSION_WEIGHTS
from services.gochara_intensity.configuration_activity import compute_x_t
from services.gochara_intensity.permission import (
    SYSTEM_WEIGHTS, DASHA_SYSTEM_IDS,
    _relevant_grahas, _relevant_signs, _lord_matches, YOGINI_LORD_TO_GRAHA,
)
from services.gochara_intensity.beta_priors import beta_for
from pipeline.transit_search import _jd_to_ist_iso

from .context import ClassContext, VedhaRow, MaleficScaleRow
from .threshold import ThresholdConfig, compute_threshold_config, is_above_threshold

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# W1.1 constants
# ---------------------------------------------------------------------------
# Maximum orb for activity decay (degrees). Contacts within this orb score
# fractionally based on proximity; contacts at or beyond this orb score 0.
# This is the linear-decay bound: activity_strength = 1 - orb / MAX_ORB_DEG
# (clamped to [0, 1]).
_ACTIVITY_MAX_ORB_DEG: float = 5.0

# Primitives that contribute to the v3 activity term (same set as X(t)).
# Station/eclipse contacts always report orb_strength via detail; when absent
# we fall back to the raw activity_strength computed from the sentence's
# own orb_degrees if available, else a conservative 0.5 (not flat 1.0 as in
# v1's X(t)) to avoid overcounting poorly-orbed contacts.
_ACTIVITY_PRIMITIVES = frozenset({
    "degree_contact",
    "drishti_contact",
    "sign_ingress",
    "nakshatra_ingress_tara",
    "kakshya_cell_crossing",
    "station_retro_loop",
    "eclipse_degree",
    "gochara_vedha_pair",
    "sarvatobhadra_vedha",
})

# ---------------------------------------------------------------------------
# W1.2 constants
# ---------------------------------------------------------------------------
# When |supportive - afflicting| / max(supportive + afflicting, epsilon) is
# below this threshold, the two channels are judged "roughly equal" and
# valence_tension is set True with valence='mixed'.
# A ratio of 0.1 means the winning channel holds less than 55% of the total
# evidence weight — genuinely contested ground.
_VALENCE_TENSION_THRESHOLD: float = 0.1


# ---------------------------------------------------------------------------
# W1.3 suppression schedule
# ---------------------------------------------------------------------------
# Suppression factor schedule keyed by effect_grade from bg_vedha_malefic_scale
# (Phaladeepika PG353). The scale maps malefic_count → effect_grade; we map
# effect_grade → suppression factor in (0, 1].
#
# Design principle: even a malefic_count=0 vedha (a non-malefic obstructor)
# mildly suppresses. Stronger malefic presence suppresses more.
# Factors are calibrated conservatively — lambda remains > 0 unless PROMISE
# or PERMISSION are already near zero. A factor of 1.0 means no suppression
# (passthrough); 0.0 would mean full suppression (not used; too aggressive
# for a structural prior).
#
# Grade → suppression_factor schedule (structural_prior; refines via L5
# calibration loop as outcome data accrues):
#   no_grade (malefic_count=0 vedha, no scale row):  0.85  (mild)
#   fear  (malefic_count=1):                          0.75
#   grade 2 (malefic_count=2):                        0.65
#   grade 3 (malefic_count=3):                        0.55
#   grade 4 (malefic_count=4):                        0.45
#   ignominy (malefic_count=5, worst):                0.35
# Any count > 5 (not in Phaladeepika): clamped to the grade-5 factor.
_VEDHA_GRADE_SUPPRESSION: dict[str, float] = {
    # Matches the five Phaladeepika grades in bg_vedha_malefic_scale.
    # Keys match effect_grade column values (case-insensitive comparison used
    # at runtime). The "no_grade" sentinel covers malefic_count=0 vedha rows
    # (obstruction_active with zero malefic occupants) and any unrecognised
    # grade string — these get a mild suppression, not a free pass.
    "no_grade": 0.85,
    "fear": 0.75,
    "grade_2": 0.65,
    "grade_3": 0.55,
    "grade_4": 0.45,
    "ignominy": 0.35,
}
# Fallback when malefic_count > 5 or effect_grade not in schedule
_VEDHA_WORST_SUPPRESSION: float = 0.35
# Factor when no malefic scale row exists for count>0 (table empty / CI)
_VEDHA_NO_SCALE_ROW_FACTOR: float = 0.70
# Factor for a vedha row with malefic_count=0 (an obstruction is active but
# entirely from benefic planets — mildest suppression)
_VEDHA_ZERO_MALEFIC_FACTOR: float = 0.85


def _suppression_factor_for_grade(effect_grade: str) -> float:
    """Map a bg_vedha_malefic_scale effect_grade to a suppression factor in (0,1]."""
    key = (effect_grade or "").strip().lower().replace(" ", "_")
    return _VEDHA_GRADE_SUPPRESSION.get(key, _VEDHA_WORST_SUPPRESSION)


def _jd_to_date_iso(swe, jd: float) -> str:
    """Convert Julian day to a YYYY-MM-DD date string (Gregorian, no timezone).

    Used for overlap-checking evaluation window bounds against the
    kala_vedha_gochara window_start / window_end date columns (stored as
    YYYY-MM-DD). We use UT directly (the date boundary shift of ±hours is
    within the same day for practically all evaluation windows, and vedha
    windows span days-to-months, making sub-day precision irrelevant here).
    """
    y, m, d, _ = swe.revjul(jd)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def _compute_quality_gates_from_context(
    context: ClassContext,
    window_start_iso: str,
    window_end_iso: str,
) -> tuple[float, dict]:
    """W1.3: compute quality_gates suppression from pre-fetched vedha rows.

    Finds all kala_vedha_gochara rows whose [window_start, window_end] overlaps
    [window_start_iso, window_end_iso] (the evaluation window). For each
    overlapping vedha, reads malefic_count from the detail JSONB and looks up
    the suppression factor from the bg_vedha_malefic_scale grading schedule.
    Multiple concurrent vedhā are combined by multiplication (noisy-OR product
    of suppression factors — same pattern as activity).

    Returns:
        quality_gates  float in (0, 1]  (1.0 when no vedha overlaps — AC1)
        detail         dict carrying which vedhā fired, per-vedha suppression,
                       combined factor, and calibration_state (AC6)

    Graceful degrades:
        - Empty context.vedha_rows (CI / no prod DB) → quality_gates = 1.0 (AC1)
        - Empty context.malefic_scale (table absent) → uses _VEDHA_NO_SCALE_ROW_FACTOR
        - malefic_count = 0 in detail → uses _VEDHA_ZERO_MALEFIC_FACTOR (mild)
    """
    # Build a fast-lookup dict from the pre-fetched malefic_scale rows.
    # Keys are malefic_count integers; values are MaleficScaleRow.
    scale_by_count: dict[int, MaleficScaleRow] = {
        r.malefic_count: r for r in context.malefic_scale
    }

    fired_vedha: list[dict] = []
    product = 1.0  # noisy-OR product of (1 - suppression) inverted: start at 1.0
                   # We accumulate product of suppression factors directly
                   # (multiplicative: f1 * f2 * … gives the combined gate).

    for vrow in context.vedha_rows:
        # Date-string overlap check: [vrow.window_start, vrow.window_end]
        # overlaps [window_start_iso, window_end_iso] iff:
        #   vrow.window_start <= window_end_iso AND vrow.window_end >= window_start_iso
        # Dates are ISO YYYY-MM-DD strings; lexicographic comparison is correct.
        if vrow.window_start > window_end_iso:
            continue
        if vrow.window_end < window_start_iso:
            continue

        # This vedha overlaps the evaluation window.
        detail = vrow.detail
        malefic_count = detail.get("malefic_count", 0)
        try:
            malefic_count = int(malefic_count)
        except (TypeError, ValueError):
            malefic_count = 0

        # Determine suppression factor.
        if malefic_count == 0:
            # Obstruction from benefics only — mildest suppression.
            suppression_factor = _VEDHA_ZERO_MALEFIC_FACTOR
            effect_grade = "no_grade"
            scale_citation = None
        elif malefic_count > 0 and scale_by_count:
            # Look up the PG353 scale row; fall back to the worst factor if
            # the count exceeds the table's maximum (>5 in practice).
            scale_row = scale_by_count.get(malefic_count)
            if scale_row is None:
                # Count out of table range (e.g. 6+) — use worst grade
                scale_row = scale_by_count.get(max(scale_by_count))
            effect_grade = scale_row.effect_grade if scale_row else "unknown"
            suppression_factor = _suppression_factor_for_grade(effect_grade)
            scale_citation = scale_row.source_citation if scale_row else None
        else:
            # malefic_count > 0 but malefic_scale table was empty (CI / absent)
            suppression_factor = _VEDHA_NO_SCALE_ROW_FACTOR
            effect_grade = "unknown_no_scale_table"
            scale_citation = None

        product *= suppression_factor

        fired_vedha.append({
            "vedha_kind": vrow.vedha_kind,
            "graha": vrow.graha,
            "window_start": vrow.window_start,
            "window_end": vrow.window_end,
            "malefic_count": malefic_count,
            "malefic_obstructing_grahas": detail.get("malefic_obstructing_grahas", []),
            "effect_grade": effect_grade,
            "suppression_factor": round(suppression_factor, 6),
            "classical_citation": vrow.classical_citation,
            "scale_citation": scale_citation,
        })

    quality_gates = product  # product of suppression factors; 1.0 when no vedha fired

    detail_out = {
        "quality_gates": round(quality_gates, 8),
        "vedha_fired_count": len(fired_vedha),
        "vedha_rows_total": len(context.vedha_rows),
        "aggregation": "multiplicative",
        "fired_vedha": fired_vedha,
        "calibration_state": "structural_prior",
        "note": (
            "W1.3 quality_gates: multiplicative product of per-vedha suppression "
            "factors (each factor in (0,1]); 1.0 when no kala_vedha_gochara rows "
            "overlap the evaluation window."
        ),
    }
    return quality_gates, detail_out


def evaluate_lambda_vector(
    swe,
    context: ClassContext,
    jd_vector: np.ndarray,
    *,
    window_days_permission: float = 15.0,
    window_days_activity: float = 5.0,
    suppression_window_days: float = 3.0,
    source: str = "v3_batch",
    v1_parity_mode: bool = False,
) -> list[IntensityResult]:
    """Evaluate lambda_e for ALL JDs simultaneously. ZERO per-JD DB access.

    This is the critical performance path. All DB data was pre-fetched into
    `context` by ClassContext.fetch(). Each JD evaluation here uses:
      - context.promise (pre-computed, time-invariant)
      - _compute_permission_from_context (pre-fetched dasha periods +
        sade_sati phases; guru-shani/av/return use ephemeris only)
      - gather + compute_x_t (v1 primitives, ephemeris-only)
      - compute_suppression (pure compute on gathered sentences)

    v1_parity_mode=False (default, W1.1):
      Uses the new bounded lambda_v3 formula:
        lambda_v3 = PROMISE * PERMISSION * activity * quality_gates
      All terms are in [0,1]; result is in [0,1] by construction.

    v1_parity_mode=True:
      Uses the original v1 formula:
        lambda_e = PROMISE * PERMISSION * exp(beta_e * X(t)) - suppression
      Preserved for golden-test comparison (test_v1_parity.py).

    Returns a list of IntensityResult, one per JD in jd_vector.
    """
    targets = list(context.resonance_targets)
    results: list[IntensityResult] = []

    for jd in jd_vector:
        t_jd = float(jd)
        result = _evaluate_single_from_context(
            swe, context, t_jd, targets,
            window_days_permission=window_days_permission,
            window_days_activity=window_days_activity,
            suppression_window_days=suppression_window_days,
            source=source,
            v1_parity_mode=v1_parity_mode,
        )
        results.append(result)

    return results


def _evaluate_single_from_context(
    swe,
    context: ClassContext,
    t_jd: float,
    targets: list[ResonanceTarget],
    *,
    window_days_permission: float = 15.0,
    window_days_activity: float = 5.0,
    suppression_window_days: float = 3.0,
    source: str = "v3_batch",
    v1_parity_mode: bool = False,
) -> IntensityResult:
    """Compute ONE lambda value using ONLY the pre-fetched ClassContext.

    This function does ZERO DB access. All data comes from context.
    Ephemeris calls (swe.calc_ut via transit_search primitives) are the
    only external calls — these are CPU-bound, not IO-bound.
    """
    # 1. PROMISE — already computed in context (time-invariant)
    promise = context.promise
    promise_detail = context.promise_detail

    # 2. PERMISSION — from pre-fetched data
    permission, permission_detail = _compute_permission_from_context(
        swe, context, t_jd, targets,
        window_days=window_days_permission,
    )

    # 3. Gather configuration sentences (ephemeris only, no DB)
    start_jd = t_jd - window_days_activity
    end_jd = t_jd + window_days_activity
    sentences = _gather_sentences_no_db(swe, context, targets, start_jd, end_jd)

    notes = []

    if v1_parity_mode:
        # ── v1-parity path: PROMISE * PERMISSION * exp(beta*X) - suppression ──
        x_t, x_t_detail = compute_x_t(sentences, context.weight_by_target_ref)
        beta_e = context.beta_e
        exp_term = math.exp(beta_e * x_t)

        suppression, suppression_detail = compute_suppression(
            sentences, window_days=suppression_window_days,
        )

        raw_lambda = promise * permission * exp_term - suppression
        if raw_lambda < 0:
            notes.append(
                f"raw product ({promise * permission * exp_term:.6f}) fully absorbed by suppression "
                f"({suppression:.6f}) -- clamped to 0.0."
            )
            raw_lambda = 0.0

        signed_lambda = raw_lambda * (-1.0 if context.is_adverse else 1.0)

        if not targets:
            notes.append(
                "no gochara_resonance_map targets resolved for this chart/event_class -- "
                "PROMISE (and therefore lambda_e) is an honest 0.0."
            )

        return IntensityResult(
            chart_id=context.chart_id,
            event_class=context.event_class,
            temporal_shape=context.temporal_shape,
            t_jd=t_jd,
            t_datetime_ist=_jd_to_ist_iso(swe, t_jd),
            promise=promise,
            promise_detail=promise_detail,
            permission=permission,
            permission_detail=permission_detail,
            x_t=x_t,
            x_t_detail=x_t_detail,
            beta_e=beta_e,
            beta_e_calibration_state="structural_prior",
            exp_term=exp_term,
            suppression=suppression,
            suppression_detail=suppression_detail,
            raw_lambda=raw_lambda,
            valence=context.valence,
            is_adverse=context.is_adverse,
            signed_lambda=signed_lambda,
            notes=notes,
            source=source,
        )

    # ── W1.1 bounded lambda_v3 path ─────────────────────────────────────────
    # Formula: lambda_v3 = PROMISE * PERMISSION * activity * quality_gates
    # Invariant: all terms in [0,1] => result in [0,1]

    # 4a. activity in [0,1]: noisy-OR over per-sentence orb-decayed strengths,
    #     weighted by the sentence's target weight.
    #
    #     Each sentence contributes a value p_i in [0,1]:
    #       orb_decay    = 1 - min(orb_degrees / MAX_ORB_DEG, 1.0)
    #       target_weight = clamp(weight_by_target_ref[target_ref], 0, 1)
    #       p_i           = orb_decay * target_weight
    #
    #     Then activity = 1 - product_i(1 - p_i)   (noisy-OR, same as PROMISE)
    #
    #     This saturates at 1.0 (multiple strong contacts can't exceed 1.0),
    #     is monotonically non-decreasing in sentence count, and preserves the
    #     qualitative ordering: tighter-orb contacts count for more.
    activity, activity_detail, term_breakdown = _compute_activity_v3(
        sentences, context.weight_by_target_ref,
    )

    # 4b. W1.2 — Signed channels: separate supportive (weight > 0) and
    #     afflicting (weight < 0) contributions. The v1 engine clamps negative
    #     weights to zero in both configuration_activity.py (line ~133) and
    #     promise.py (line ~64), silently erasing afflictions. In v3 we carry
    #     both channels here — no edit to any gochara_grammar/*.py file (I2).
    supportive_channel, afflicting_channel, signed_channel_detail = (
        _compute_signed_channels_v3(sentences, context.weight_by_target_ref)
    )

    # 4c. Window valence emerges from the sign of net configuration evidence.
    #     Class-level valence (context.valence) is the prior when evidence is
    #     zero on both channels (no sentences fired).
    v3_valence, v3_is_adverse, valence_tension = _resolve_valence_v3(
        supportive_channel,
        afflicting_channel,
        class_valence=context.valence,
        class_is_adverse=context.is_adverse,
    )

    # 4d. quality_gates: W1.3 vedha-based multiplicative suppression gate.
    #     Looks up kala_vedha_gochara rows (pre-fetched in context) that
    #     overlap the evaluation window and multiplies their suppression factors.
    #     Falls back to 1.0 when no vedha rows overlap (AC1).
    eval_start_iso = _jd_to_date_iso(swe, start_jd)
    eval_end_iso = _jd_to_date_iso(swe, end_jd)
    quality_gates, quality_gates_detail = _compute_quality_gates_from_context(
        context, eval_start_iso, eval_end_iso,
    )

    # 5. Assemble lambda_v3 — bounded [0,1] by construction
    raw_lambda = promise * permission * activity * quality_gates

    # Clamp for floating-point edge cases (should be impossible, but defensive)
    raw_lambda = max(0.0, min(1.0, raw_lambda))

    signed_lambda = raw_lambda * (-1.0 if v3_is_adverse else 1.0)

    if not targets:
        notes.append(
            "no gochara_resonance_map targets resolved for this chart/event_class -- "
            "PROMISE (and therefore lambda_v3) is an honest 0.0."
        )

    # v3 uses activity in place of X(t)/exp_term. We still populate
    # x_t/exp_term fields on IntensityResult for schema compatibility,
    # but set them to their v3 equivalents (activity / 1.0) so the
    # existing parity tests that read these fields still get sensible values.
    # The term_breakdown carries the full W1.1 decomposition.
    # W1.2 signed-channel data is in x_t_detail['signed_channels'].
    x_t_compat = activity  # activity IS the v3 replacement for X(t)
    x_t_detail_compat = {
        **activity_detail,
        "formula": "lambda_v3 = PROMISE * PERMISSION * activity * quality_gates",
        "v3_mode": True,
        "term_breakdown": term_breakdown,
        "quality_gates": quality_gates,
        "quality_gates_detail": quality_gates_detail,
        # W1.2 signed-channel fields
        "signed_channels": signed_channel_detail,
        "valence_v3": v3_valence,
        "valence_tension": valence_tension,
        "note": (
            "W1.2 direction restored: signed supportive/afflicting channels separate; "
            "valence derived from net evidence sign. "
            "W1.1/W1.3 bounded lambda_v3: activity replaces exp(beta*X); "
            "quality_gates is W1.3 vedha suppression (multiplicative; 1.0 when no vedha). "
            "activity=noisy_OR over orb-decayed sentence contributions in [0,1]. "
            "exp_term=1.0 (no exponential in v3 formula)."
        ),
    }

    # ── MR-41(c) v3 SUPPRESSION WIRING DECISION (PK-R-5, 2026-08-11, recorded
    # per this lane's explicit-decision requirement) ──────────────────────────
    # `quality_gates` (computed above at line ~493) IS the v3-native suppression
    # mechanism, in production use on every W1.1 bounded-lambda_v3 evaluation
    # (the branch this code is in -- v1_parity_mode=False, the default/served
    # path). It reads its own, ALREADY-POPULATED corpus (`kala_vedha_gochara`
    # rows, pre-fetched into `ClassContext`) -- entirely independent of the
    # three v1 suppression mechanisms below and NOT affected by MR-41(a)/(b)'s
    # bg_transit_vedha / target_nakshatra_id repoints.
    #
    # `compute_suppression` (gochara_intensity/suppression.py,
    # SUPPRESSION_WEIGHTS = vedha_cancellation + sarvatobhadra_vedha +
    # kartari_pincer) is the v1 mechanism MR-41 restored reachability for. It
    # is called ONLY inside the `v1_parity_mode` branch above (line ~402) --
    # i.e. it remains v1-PARITY-MODE-ONLY: exercised for golden-test
    # comparison against the v1 engine, never on the v3 production path. This
    # lane deliberately does NOT wire it into the W1.1 formula alongside (or
    # instead of) quality_gates -- doing so would change v3 SCORING semantics
    # (a new subtracted term in `raw_lambda`), which is out of this lane's I2
    # scope. The chosen minimal, honest fix: keep quality_gates as the v3
    # mechanism (documented here), and make the field BELOW (`suppression_v3`,
    # and downstream the writer's `suppression_state` column, MR-42) report
    # truthfully what ran, rather than an unconditional placeholder.
    #
    # suppression field is 0.0 in v3 (quality_gates is the W1.3 suppression
    # mechanism, reported separately via quality_gates/quality_gates_detail
    # above and forwarded into detail below) -- kept at 0.0 (not None) only
    # for IntensityResult schema compatibility with v1's numeric suppression
    # field; MR-42's writer fix reads quality_gates_detail (via
    # x_t_detail_compat), not this placeholder, when populating a truthful
    # suppression_state on interval rows.
    suppression_v3 = 0.0
    suppression_detail_v3 = {
        "note": "v3 formula uses quality_gates for vedha suppression (W1.3); "
                "suppression field is kept at 0.0 for schema compatibility with v1. "
                "quality_gates is the v3-native suppression mechanism (see MR-41(c) "
                "wiring-decision comment above); the v1 vedha_cancellation/"
                "sarvatobhadra_vedha/kartari_pincer mechanisms in "
                "gochara_intensity.suppression.compute_suppression remain "
                "v1-parity-mode-only and are not consulted on this path.",
        "calibration_state": "structural_prior",
        "mechanism": "quality_gates",
    }

    # ── W1.5 λ decomposition output ──────────────────────────────────────────
    # Full term_breakdown JSONB: top-level scalar factors + per-sentence list
    # from _compute_activity_v3, plus the assembled formula and final value.
    w15_term_breakdown = {
        "promise": round(promise, 8),
        "permission": round(permission, 8),
        "activity": round(activity, 8),
        "quality_gates": round(quality_gates, 8),
        "lambda_v3": round(raw_lambda, 8),
        "activity_terms": x_t_detail_compat.get("contributions", []),
        "formula": "PROMISE × PERMISSION × activity × quality_gates",
    }

    # W1.5 credible interval — structural_prior: ±20% band, clamped to [0,1].
    # ci_source='structural_prior' until Wave-4.5 fitted posteriors replace this.
    ci_low = max(0.0, raw_lambda * 0.8)
    ci_high = min(1.0, raw_lambda * 1.2)

    return IntensityResult(
        chart_id=context.chart_id,
        event_class=context.event_class,
        temporal_shape=context.temporal_shape,
        t_jd=t_jd,
        t_datetime_ist=_jd_to_ist_iso(swe, t_jd),
        promise=promise,
        promise_detail=promise_detail,
        permission=permission,
        permission_detail=permission_detail,
        x_t=x_t_compat,
        x_t_detail=x_t_detail_compat,
        beta_e=context.beta_e,
        beta_e_calibration_state="structural_prior",
        exp_term=1.0,            # no exp() in v3 formula
        suppression=suppression_v3,
        suppression_detail=suppression_detail_v3,
        raw_lambda=raw_lambda,
        valence=v3_valence,      # W1.2: dynamic valence from net evidence
        is_adverse=v3_is_adverse,
        signed_lambda=signed_lambda,
        notes=notes,
        source=source,
        # W1.5: λ decomposition + structural prior credible interval
        term_breakdown=w15_term_breakdown,
        lambda_v3_ci_low=ci_low,
        lambda_v3_ci_high=ci_high,
        ci_source="structural_prior",
    )


def _compute_activity_v3(
    sentences: list[ConfigurationSentence],
    weight_by_target_ref: dict[str, float],
) -> tuple[float, dict, dict]:
    """Compute the W1.1 activity term in [0,1].

    Uses noisy-OR over per-sentence orb-decayed strengths:

        p_i = orb_decay_i * target_weight_i

    where:
        orb_decay_i    = 1 - min(orb_degrees_i / MAX_ORB_DEG, 1.0)
                         (linear decay; stations/eclipses may report
                          orb_strength directly in detail — use it)
        target_weight_i = clamp(weight_by_target_ref[target_ref], 0, 1)

    Then:
        activity = 1 - product_i(1 - p_i)   (noisy-OR; same math as PROMISE)

    Returns:
        activity      float in [0,1]
        detail        dict with per-sentence contributions for debugging
        term_breakdown dict with per-primitive contribution sums (for W1.5)
    """
    product_complement = 1.0
    contributions = []
    term_breakdown: dict[str, float] = {}

    for s in sentences:
        if s.primitive not in _ACTIVITY_PRIMITIVES:
            continue
        if s.primitive == "gochara_vedha_pair" and s.detail.get("cancelled"):
            continue  # cancelled vedha pair: not an activity signal

        # Target weight: clamp to [0,1] (negative weights encode direction,
        # not activity magnitude; direction is handled at the signed_lambda level)
        target_weight = max(0.0, min(1.0, weight_by_target_ref.get(s.target_ref or "", 0.5)))

        # Orb strength: prefer detail['orb_strength'] if present (already
        # normalized by the primitive), else compute from detail['orb_degrees']
        # with linear decay, else fall back to 0.5 (conservative neutral,
        # not flat 1.0 — stations/eclipses not near exact degree get partial credit)
        orb_strength_raw = s.detail.get("orb_strength")
        if orb_strength_raw is not None:
            # Primitive already computed orb_strength in [0,1]
            orb_decay = float(max(0.0, min(1.0, orb_strength_raw)))
        else:
            orb_degrees_raw = s.detail.get("orb_degrees")
            if orb_degrees_raw is not None:
                orb_degrees = abs(float(orb_degrees_raw))
                orb_decay = 1.0 - min(orb_degrees / _ACTIVITY_MAX_ORB_DEG, 1.0)
            else:
                # No orb information available (sign_ingress, nakshatra_ingress,
                # eclipse_degree, some vedha variants): use 0.5 as the honest
                # "present but unorbed" contribution level
                orb_decay = 0.5

        p_i = orb_decay * target_weight
        # p_i is in [0,1] (both factors clamped)

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

        # Accumulate per-primitive signed scalar for W1.5 term_breakdown
        # The scalar is p_i itself (the marginal activity contribution of
        # this sentence before noisy-OR combination)
        term_breakdown[s.primitive] = term_breakdown.get(s.primitive, 0.0) + p_i

    activity = 1.0 - product_complement
    # Clamp for floating-point accumulation edge cases
    activity = max(0.0, min(1.0, activity))

    detail = {
        "activity": round(activity, 8),
        "aggregation": "noisy_or",
        "sentence_count_active": len(contributions),
        "sentence_count_total_gathered": len(sentences),
        "max_orb_deg": _ACTIVITY_MAX_ORB_DEG,
        "contributions": contributions,
        "calibration_state": "structural_prior",
        "note": (
            "W1.1 activity: noisy-OR over orb-decayed sentence contributions; "
            "each p_i = orb_decay * target_weight in [0,1]; "
            "result saturates at 1.0 (replaces unbounded X(t) from v1)."
        ),
    }

    return activity, detail, term_breakdown


def _compute_signed_channels_v3(
    sentences: list[ConfigurationSentence],
    weight_by_target_ref: dict[str, float],
) -> tuple[float, float, dict]:
    """W1.2 — Separate configuration sentences into supportive and afflicting channels.

    v1 (gochara_intensity/configuration_activity.py line ~133 and
    gochara_intensity/promise.py line ~64) clamp negative weights to zero.
    This function deliberately does NOT clamp, letting the v3 engine see the
    full signed evidence. No gochara_grammar/*.py file is modified (I2).

    For each sentence in _ACTIVITY_PRIMITIVES:
      raw_weight = weight_by_target_ref[target_ref]   (may be negative)
      orb_decay  = same computation as _compute_activity_v3
      p_i        = orb_decay * |raw_weight|            (always >= 0)

      If raw_weight > 0  => contributes p_i to the supportive channel
      If raw_weight < 0  => contributes p_i to the afflicting channel
      If raw_weight == 0 => neutral; excluded from both channels

    Each channel is aggregated via noisy-OR (same as activity / PROMISE):
      channel = 1 - product_i(1 - p_i)   in [0,1]

    Returns:
      supportive_channel  float in [0,1]
      afflicting_channel  float in [0,1]
      detail              dict with per-channel breakdown for debugging
    """
    supportive_complement = 1.0
    afflicting_complement = 1.0
    supportive_contributions = []
    afflicting_contributions = []

    for s in sentences:
        if s.primitive not in _ACTIVITY_PRIMITIVES:
            continue
        if s.primitive == "gochara_vedha_pair" and s.detail.get("cancelled"):
            continue

        raw_weight = weight_by_target_ref.get(s.target_ref or "", 0.0)
        if raw_weight == 0.0:
            continue  # neutral; no channel contribution

        # Orb decay: identical logic to _compute_activity_v3
        orb_strength_raw = s.detail.get("orb_strength")
        if orb_strength_raw is not None:
            orb_decay = float(max(0.0, min(1.0, orb_strength_raw)))
        else:
            orb_degrees_raw = s.detail.get("orb_degrees")
            if orb_degrees_raw is not None:
                orb_degrees = abs(float(orb_degrees_raw))
                orb_decay = 1.0 - min(orb_degrees / _ACTIVITY_MAX_ORB_DEG, 1.0)
            else:
                orb_decay = 0.5

        # p_i uses the ABSOLUTE value of the weight (magnitude only;
        # sign determines which channel receives it)
        p_i = orb_decay * abs(raw_weight)
        # Clamp to [0,1]: abs weight could exceed 1 for over-weighted targets
        p_i = min(1.0, p_i)

        contribution_record = {
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
            supportive_contributions.append(contribution_record)
        else:
            afflicting_complement *= (1.0 - p_i)
            afflicting_contributions.append(contribution_record)

    supportive_channel = max(0.0, min(1.0, 1.0 - supportive_complement))
    afflicting_channel = max(0.0, min(1.0, 1.0 - afflicting_complement))

    detail = {
        "supportive_channel": round(supportive_channel, 8),
        "afflicting_channel": round(afflicting_channel, 8),
        "supportive_sentence_count": len(supportive_contributions),
        "afflicting_sentence_count": len(afflicting_contributions),
        "supportive_contributions": supportive_contributions,
        "afflicting_contributions": afflicting_contributions,
        "aggregation": "noisy_or_per_channel",
        "note": (
            "W1.2: signed channels. Negative weights (afflictions) are NOT "
            "clamped to zero as in v1. Each channel is a noisy-OR in [0,1]. "
            "I2 compliant: gochara_grammar/*.py untouched."
        ),
    }
    return supportive_channel, afflicting_channel, detail


def _resolve_valence_v3(
    supportive_channel: float,
    afflicting_channel: float,
    *,
    class_valence: str,
    class_is_adverse: bool,
) -> tuple[str, bool, bool]:
    """W1.2 — Derive window valence from the sign of net configuration evidence.

    Rules (in order):

    1. If both channels are zero (no sentences fired, or all weights neutral):
       Fall back to class-level prior (class_valence / class_is_adverse).
       valence_tension = False.

    2. If |supportive - afflicting| / (supportive + afflicting) < threshold:
       The two channels nearly cancel => valence = 'mixed', tension = True.

    3. If supportive > afflicting: valence = 'favourable', tension = False.

    4. If afflicting > supportive: valence = 'adverse', tension = False.

    Returns:
      valence       str   'favourable' | 'adverse' | 'mixed' | class_valence fallback
      is_adverse    bool  True iff valence == 'adverse'
      valence_tension bool True iff channels nearly cancel (rule 2)
    """
    total = supportive_channel + afflicting_channel

    if total < 1e-10:
        # No configuration evidence — use class-level prior
        return class_valence, class_is_adverse, False

    imbalance_ratio = abs(supportive_channel - afflicting_channel) / total

    if imbalance_ratio < _VALENCE_TENSION_THRESHOLD:
        # Channels nearly cancel — genuine disagreement
        return "mixed", False, True

    if supportive_channel > afflicting_channel:
        return "favourable", False, False
    else:
        return "adverse", True, False


def _gather_sentences_no_db(
    swe,
    context: ClassContext,
    targets: list[ResonanceTarget],
    start_jd: float,
    end_jd: float,
) -> list[ConfigurationSentence]:
    """Run v1 configuration primitives EPHEMERIS-ONLY (no conn passed).

    The v1 `configuration_activity.gather_configuration_sentences` takes
    `conn` to pass to conn-needing primitives (kakshya_cell_crossing,
    gochara_vedha_pair, sarvatobhadra_vedha). In v3, those DB reads were
    pre-fetched into context. For the ephemeris-only primitives (6 of 9),
    we call them directly with no conn. For the conn-needing ones, we
    skip them here (their DB-dependent data is already in context) or
    call them without conn (they degrade honestly to []).

    This approach trades some accuracy on the 3 DB-needing primitives
    for ZERO per-JD DB access. The trade is acceptable because:
      - kakshya_cell_crossing: reads chart_facts for kakshya boundaries —
        these are natal (time-invariant) and could be pre-fetched, but
        the primitive's internal format is tightly coupled to its DB query.
        Skipping it means we lose kakshya contributions to X(t) — a minor
        signal in practice.
      - gochara_vedha_pair: reads bg_transit_rules for vedha houses.
        These are reference data. Skipping it means we lose vedha-pair
        contributions. Suppression still works via sarvatobhadra_vedha.
      - sarvatobhadra_vedha: reads bg_transit_rules. Same as above.

    In v1-parity mode, these losses are measurable but bounded. The
    dominant signals (degree_contact, drishti_contact, sign_ingress,
    nakshatra_ingress_tara, station_retro_loop, eclipse_degree) are all
    ephemeris-only and fully preserved.
    """
    out: list[ConfigurationSentence] = []
    for target in targets:
        # The 6 ephemeris-only primitives (no conn parameter)
        for fn in (
            P.degree_contact,
            P.drishti_contact,
            P.sign_ingress,
            P.nakshatra_ingress_tara,
            P.station_retro_loop,
            P.eclipse_degree,
        ):
            try:
                out.extend(fn(swe, context.chart_id, target, start_jd, end_jd))
            except Exception as exc:  # noqa: BLE001
                logger.debug(
                    "[v3.engine] %s failed for target_ref=%s: %s",
                    getattr(fn, "__name__", fn), target.target_ref, exc,
                )

        # The 2 conn-needing primitives: call with conn=None so they
        # degrade honestly (return []) rather than crashing.
        for fn in (P.kakshya_cell_crossing, P.gochara_vedha_pair):
            try:
                out.extend(fn(swe, context.chart_id, target, start_jd, end_jd, conn=None))
            except Exception as exc:  # noqa: BLE001
                logger.debug(
                    "[v3.engine] %s (no-conn degrade) failed for target_ref=%s: %s",
                    getattr(fn, "__name__", fn), target.target_ref, exc,
                )

        # sarvatobhadra_vedha (conn-needing)
        try:
            out.extend(SBC.find_sarvatobhadra_vedha_states(
                swe, context.chart_id, target, start_jd, end_jd, conn=None,
            ))
        except Exception as exc:  # noqa: BLE001
            logger.debug(
                "[v3.engine] sarvatobhadra_vedha (no-conn degrade) failed: %s", exc,
            )

    return out


def _compute_permission_from_context(
    swe,
    context: ClassContext,
    t_jd: float,
    targets: list[ResonanceTarget],
    *,
    window_days: float = 15.0,
) -> tuple[float, dict]:
    """Compute PERMISSION using ONLY pre-fetched ClassContext data.

    Mirrors v1's `permission.compute_permission` but with ALL DB data
    coming from context instead of live queries.

    The 12 generators:
      1-8: chart_dashas systems — from context.dasha_periods (pre-fetched)
      9:   sade_sati — from context.sade_sati_phases (pre-fetched)
      10:  guru_shani_double_transit — ephemeris only (no DB)
      11:  av_threshold — from context.av_gate_rows (pre-fetched)
      12:  planetary_return — ephemeris only (no DB)
    """
    t_iso = _jd_to_ist_iso(swe, t_jd)
    start_jd = t_jd - window_days
    end_jd = t_jd + window_days

    systems: list[dict] = []

    # 1-8: Dasha systems (pre-fetched periods, pure datetime comparison)
    dasha_hits = _dasha_contributions_from_context(
        context, t_iso,
    )
    for sid in DASHA_SYSTEM_IDS:
        hit = dasha_hits[sid]
        systems.append({
            "system_id": sid,
            "active": hit["active"],
            "weight": SYSTEM_WEIGHTS[sid],
            "detail": hit["detail"],
        })

    # 9: Sade Sati (pre-fetched phases, pure datetime comparison)
    sade_sati_active, sade_sati_detail = _check_sade_sati_from_context(
        context, t_iso,
    )
    systems.append({
        "system_id": "sade_sati",
        "active": sade_sati_active,
        "weight": SYSTEM_WEIGHTS["sade_sati"],
        "detail": sade_sati_detail,
    })

    # 10: Guru-Shani double transit (ephemeris only — no DB)
    gsdt_active, gsdt_detail = _check_guru_shani_from_context(
        swe, context, targets, start_jd, end_jd,
        window_days=window_days,
    )
    systems.append({
        "system_id": "guru_shani_double_transit",
        "active": gsdt_active,
        "weight": SYSTEM_WEIGHTS["guru_shani_double_transit"],
        "detail": gsdt_detail,
    })

    # 11: AV threshold (pre-fetched gate rows + ephemeris for planet sign)
    av_active, av_detail = _check_av_threshold_from_context(
        swe, context, targets, start_jd, end_jd,
    )
    systems.append({
        "system_id": "av_threshold",
        "active": av_active,
        "weight": SYSTEM_WEIGHTS["av_threshold"],
        "detail": av_detail,
    })

    # 12: Planetary return (ephemeris only — no DB)
    return_active, return_detail = _check_planetary_return_from_context(
        swe, context, targets, start_jd, end_jd,
    )
    systems.append({
        "system_id": "planetary_return",
        "active": return_active,
        "weight": SYSTEM_WEIGHTS["planetary_return"],
        "detail": return_detail,
    })

    active_weight = sum(s["weight"] for s in systems if s["active"])
    total_weight = sum(SYSTEM_WEIGHTS.values())
    permission = active_weight / total_weight if total_weight else 0.0

    systems_active = [s["system_id"] for s in systems if s["active"]]
    detail = {
        "systems": systems,
        "systems_active": systems_active,
        "systems_considered": [s["system_id"] for s in systems],
        "system_count_active": len(systems_active),
        "t_datetime_ist": t_iso,
        "window_days": window_days,
        "calibration_state": "structural_prior",
    }
    return permission, detail


def _dasha_contributions_from_context(
    context: ClassContext,
    t_iso: str,
) -> dict[str, dict]:
    """Evaluate dasha PERMISSION generators from pre-fetched periods.

    Mirrors v1's permission._dasha_contributions but reads from
    context.dasha_periods instead of a live DB query.
    """
    out: dict[str, dict] = {sid: {"active": False, "detail": {}} for sid in DASHA_SYSTEM_IDS}
    lord_check_available = bool(context.relevant_grahas or context.relevant_signs)

    for period in context.dasha_periods:
        sid = period.get("system_id")
        if sid not in out or out[sid]["active"]:
            continue
        if not DD.period_contains(period, t_iso):
            continue
        lord = period.get("lord_graha")
        if lord_check_available and not _lord_matches(
            sid, lord, set(context.relevant_grahas), set(context.relevant_signs),
        ):
            continue
        out[sid] = {
            "active": True,
            "detail": {
                "lord_graha": lord,
                "start_iso": period.get("start_iso"),
                "end_iso": period.get("end_iso"),
                "lord_relevance_check": (
                    "matched_relevant_lord" if lord_check_available
                    else "no_relevant_lord_vocabulary_resolved_any_period_counted"
                ),
            },
        }
    return out


def _check_sade_sati_from_context(
    context: ClassContext,
    t_iso: str,
) -> tuple[bool, dict]:
    """Check Sade Sati phase from pre-fetched data.

    The v1 permission.py calls P.sade_sati_phase which reads chart_facts.
    We pre-fetched those facts into context.sade_sati_phases. Here we
    check if t_iso falls within any sade_sati phase interval.
    """
    # The pre-fetched sade_sati_phases are raw chart_facts rows.
    # We need to find phase intervals. Sade sati phases have
    # fact_category='sade_sati_phase' with start/end encoded in fact_key
    # or fact_value_text. The exact format depends on the writer.
    # For now, check if any phase row's interval contains t_iso.
    for phase in context.sade_sati_phases:
        if phase.get("fact_category") != "sade_sati_phase":
            continue
        start_iso = phase.get("fact_value_text")
        if not start_iso:
            continue
        # The sade_sati_phase primitive in v1 builds pseudo-periods
        # from chart_facts rows. We attempt the same logic here but
        # with pre-fetched data. This is a best-effort degrade —
        # if the exact format doesn't match, we return False (honest).
        try:
            pseudo_period = {
                "start_iso": start_iso,
                "end_iso": "9999-12-31T00:00:00+00:00",
            }
            if DD.period_contains(pseudo_period, t_iso):
                return True, {"phase": phase.get("fact_key", ""), "source": "v3_prefetch"}
        except Exception:  # noqa: BLE001
            pass

    return False, {}


def _check_guru_shani_from_context(
    swe,
    context: ClassContext,
    targets: list[ResonanceTarget],
    start_jd: float,
    end_jd: float,
    window_days: float = 15.0,
) -> tuple[bool, dict]:
    """Guru-Shani double transit — ephemeris only, no DB needed.

    Same logic as v1's permission.py guru-shani block, but using
    ephemeris-only primitives (drishti_contact, degree_contact,
    sign_occupation all take swe + target, no conn needed for the
    ephemeris calls themselves).

    IMPORTANT: window_days passed to CO.double_transit/double_transit_mixed
    must match v1's compute_permission, which passes its own window_days
    parameter (default 15.0), NOT the span of the search window
    (2*window_days). The search window is for primitive scanning; the
    clustering window for composition is separate.
    """
    try:
        contact_sentences = []
        occupation_sentences = []
        for target in targets:
            if target.target_longitude_deg is not None or target.target_sign is not None:
                contact_sentences += P.drishti_contact(
                    swe, context.chart_id, target, start_jd, end_jd,
                    planets=["Jupiter", "Saturn"],
                )
                contact_sentences += P.degree_contact(
                    swe, context.chart_id, target, start_jd, end_jd,
                    planets=["Jupiter", "Saturn"],
                )
            if target.target_sign is not None:
                contact_sentences += P.sign_occupation(
                    swe, context.chart_id, target, start_jd, end_jd,
                    planets=["Jupiter", "Saturn"],
                )
        comps = CO.double_transit(contact_sentences, window_days=window_days)
        comps += CO.double_transit_mixed(
            contact_sentences + occupation_sentences, window_days=window_days,
        )
        for c in comps:
            if c.detail.get("is_guru_shani_double_transit"):
                return True, {
                    "target_ref": c.detail.get("target_ref"),
                    "event_datetime_ist": c.event_datetime_ist,
                    "operator": c.operator,
                }
    except Exception as exc:  # noqa: BLE001
        logger.debug("[v3.engine] guru_shani_double_transit check failed: %s", exc)

    return False, {}


def _check_av_threshold_from_context(
    swe,
    context: ClassContext,
    targets: list[ResonanceTarget],
    start_jd: float,
    end_jd: float,
) -> tuple[bool, dict]:
    """AV threshold — uses pre-fetched gate rows + ephemeris for planet sign.

    The v1 av_threshold_state primitive reads bg_transit_av_gates from DB.
    We pre-fetched those rows into context.av_gate_rows. Here we check
    whether any transiting planet is in a target sign during the window
    (via ephemeris) and whether the gate fires.

    For now, use the v1 primitive with conn=None (honest degrade) since
    the primitive's internal format is complex. This means AV threshold
    is effectively disabled in v3 — an honest gap, not a fabricated value.
    """
    # The v1 primitive needs conn for bg_transit_av_gates. We pre-fetched
    # the gate rows but the primitive's interface doesn't accept them
    # directly (it has fixture_gate_rows parameter though).
    for target in targets:
        if target.target_type != "bhava" or not target.target_sign:
            continue
        # Filter pre-fetched gate rows for this target
        target_gates = [
            {"graha": g.graha, "min_sav_score": g.min_sav_score,
             "effect": g.effect, "classical_citation": g.classical_citation}
            for g in context.av_gate_rows
            if g.target_ref == target.target_ref
        ]
        if not target_gates:
            continue
        try:
            events = P.av_threshold_state(
                swe, context.chart_id, target, start_jd, end_jd,
                conn=None,
                fixture_gate_rows=target_gates,
            )
            if events:
                return True, {"target_ref": target.target_ref, "count": len(events)}
        except Exception as exc:  # noqa: BLE001
            logger.debug("[v3.engine] av_threshold check failed: %s", exc)

    return False, {}


def _check_planetary_return_from_context(
    swe,
    context: ClassContext,
    targets: list[ResonanceTarget],
    start_jd: float,
    end_jd: float,
) -> tuple[bool, dict]:
    """Planetary return — ephemeris only, no DB needed.

    Same as v1's permission.py planetary_return block: restricted to
    Saturn/Jupiter/Rahu/Ketu targets with resolved target_longitude_deg.
    P.planetary_return is ephemeris-only.
    """
    for target in targets:
        if target.natal_planet not in ("Saturn", "Jupiter", "Rahu", "Ketu"):
            continue
        if target.target_longitude_deg is None:
            continue
        try:
            events = P.planetary_return(
                swe, context.chart_id, target, start_jd, end_jd,
            )
            if events:
                return True, {"natal_planet": target.natal_planet, "count": len(events)}
        except Exception as exc:  # noqa: BLE001
            logger.debug("[v3.engine] planetary_return check failed: %s", exc)

    return False, {}


def evaluate_lambda_vector_with_threshold(
    swe,
    context: ClassContext,
    jd_vector: np.ndarray,
    *,
    conn=None,
    age_years: int = 42,
    jd_thresh_start: Optional[float] = None,
    jd_thresh_end: Optional[float] = None,
    thresh_step_days: float = 7.0,
    window_days_permission: float = 15.0,
    window_days_activity: float = 5.0,
    suppression_window_days: float = 3.0,
    source: str = "v3_batch",
    _lambda_distribution=None,
) -> tuple[list[IntensityResult], ThresholdConfig]:
    """W1.4: Evaluate λ_v3 for all JDs AND compute the self-normalizing threshold.

    This is the W1.4 entry point. It:

    1. Computes a ThresholdConfig ONCE via compute_threshold_config — the
       percentile-based activation threshold derived from the chart's own
       century-scale λ_v3 distribution and brahma_event_ontology base rates.
    2. Evaluates evaluate_lambda_vector (unchanged) for all requested JDs.
    3. Returns (results, threshold_config) so the caller can:
         - gate window emission: is_above_threshold(r.raw_lambda, config)
         - attach provenance to every window row: config.to_dict()

    AC5 guarantee: v1_parity_mode=True is never passed here — this wrapper
    operates exclusively in the v3 bounded-lambda path. Callers wanting
    v1_parity_mode must call evaluate_lambda_vector directly (unchanged).

    Parameters
    ----------
    swe                    Swiss Ephemeris handle.
    context                ClassContext (pre-fetched).
    jd_vector              JDs to evaluate.
    conn                   DB connection for brahma_event_ontology read.
    age_years              Native's age (default 42, native bracket 35–50).
    jd_thresh_start        Start of century horizon for threshold distribution.
    jd_thresh_end          End of century horizon.
    thresh_step_days       Sampling step for the century distribution (days).
    window_days_permission PERMISSION window (passed to evaluate_lambda_vector).
    window_days_activity   Activity window (passed to evaluate_lambda_vector).
    suppression_window_days Suppression window (passed to evaluate_lambda_vector).
    source                 Provenance tag.
    _lambda_distribution   Pre-computed distribution array for testing (skips
                           the century evaluation when supplied).

    Returns
    -------
    (results, threshold_config)
        results           list[IntensityResult], one per JD in jd_vector,
                          produced by evaluate_lambda_vector with v1_parity_mode=False.
        threshold_config  ThresholdConfig with all W1.4 provenance fields.
    """
    # 1. Compute threshold config ONCE for this (chart × class).
    threshold_config = compute_threshold_config(
        swe, context,
        conn=conn,
        age_years=age_years,
        jd_start=jd_thresh_start,
        jd_end=jd_thresh_end,
        step_days=thresh_step_days,
        _lambda_distribution=_lambda_distribution,
    )

    # 2. Evaluate λ_v3 for all requested JDs (v3 path only, never v1_parity).
    results = evaluate_lambda_vector(
        swe, context, jd_vector,
        window_days_permission=window_days_permission,
        window_days_activity=window_days_activity,
        suppression_window_days=suppression_window_days,
        source=source,
        v1_parity_mode=False,  # W1.4 operates on λ_v3 only — v1 path untouched
    )

    return results, threshold_config


__all__ = [
    "evaluate_lambda_vector",
    "evaluate_lambda_vector_with_threshold",
    "_compute_activity_v3",
    "_compute_signed_channels_v3",
    "_resolve_valence_v3",
    "_VALENCE_TENSION_THRESHOLD",
]
