"""
gochara_intensity.engine — the G-3 entry point:

    lambda_e(t | chart) = PROMISE * PERMISSION * exp(beta_e * X(t)) - suppression

(BRIEF_D5 §1 G-3 row). Ties together `promise.py` (G-1-sourced classical-
prior aggregate), `permission.py` (DR-14 timing-system-plurality gate),
`configuration_activity.py` (G-2-sourced instant-geometry activity scalar
X(t) and its beta_e exponential scaling), and `suppression.py` (G-2's
vedha-cancellation/kartari damping). Every disclosed weight/coefficient
carries `calibration_state='structural_prior'` -- `IntensityResult`
mechanically enforces this (see `models.py`).

Adverse event-classes (BRIEF_D5 §1 G-3 row: "adverse classes get identical
machinery, signed valence per D-2's doctrine") run through the EXACT SAME
PROMISE/PERMISSION/X(t)/suppression pipeline; only the final sign differs
(`valence.is_adverse`). This module never branches its computation on
valence except for that final sign flip -- a fatalistic/cheaper adverse
code path would itself be a DR-16 violation (honest clarity requires the
SAME rigor for adverse windows as auspicious ones).

Shape-aware semantics (BRIEF_D5 §3, binding): `compute_lambda_e` computes
ONE instant's value and always reports `temporal_shape` alongside it, never
implying more precision than that shape supports on its own.
`compute_lambda_e_series` is the ONLY path that produces a multi-point
interval/chain-shaped curve (a caller must explicitly ask for a series to
get interval/chain output) -- this mirrors G-4's eventual sweep serving
layer (out of scope for G-3) while giving THIS lane's own live-verification
step (BRIEF_D5's named interval specimen) a real multi-point curve to show,
not a single point dressed up as an interval.
"""
from __future__ import annotations

import logging
import math
from typing import Optional

from services.gochara_grammar import resonance_map as RM
from services.gochara_grammar import dasha_data as DD
from services.gochara_grammar.models import ResonanceTarget
from pipeline.transit_search import _jd_to_ist_iso

from .models import IntensityResult
from .promise import compute_promise
from .permission import compute_permission
from .configuration_activity import gather_configuration_sentences, compute_x_t
from .suppression import compute_suppression
from .beta_priors import beta_for
from .valence import is_adverse
from .enrichment import enrich_targets
from ._dbutil import savepoint_scope

logger = logging.getLogger(__name__)

# BRIEF_D5 §B.1 — the 27-class ontology's canonical shape, transcribed for
# the same "live-preferred, documented-fallback" honesty discipline as
# `valence.VALENCE_MAP` (a live `brahma_event_ontology.temporal_shape` read
# is preferred when `conn` is available; this is the offline fallback).
SHAPE_MAP: dict[str, str] = {
    **{c: "point" for c in (
        "achievement_recognition", "bereavement", "birth_anchor", "career_advancement",
        "career_entry", "childbirth", "exam_outcome", "illness_acute", "marriage",
        "property_acquisition", "romantic_start", "surgery", "travel_event",
    )},
    **{c: "interval" for c in (
        "career_setback", "chronic_onset", "financial_deception", "major_gain",
        "major_loss", "parental_event", "psychological_arc", "relocation", "spiritual_turn",
    )},
    **{c: "chain" for c in (
        "business_launch", "career_change", "education_milestone",
        "foreign_settlement", "separation",
    )},
}


def fetch_temporal_shape(conn, event_class: str) -> str:
    if conn is not None:
        try:
            with savepoint_scope(conn, "temporal_shape"):
                cur = conn.execute(
                    "SELECT temporal_shape FROM brahma_event_ontology WHERE event_class_id = %s",
                    [event_class],
                )
                row = cur.fetchone()
                if row is not None:
                    v = row["temporal_shape"] if isinstance(row, dict) else row[0]
                    if v:
                        return str(v)
        except Exception as exc:  # noqa: BLE001
            logger.info("[engine] brahma_event_ontology temporal_shape read failed for "
                        "event_class=%s: %s", event_class, exc)
    return SHAPE_MAP.get(event_class, "point")


def compute_lambda_e(
    swe,
    conn,
    chart_id: str,
    event_class: str,
    t_jd: float,
    targets: Optional[list[ResonanceTarget]] = None,
    dasha_periods: Optional[list[dict]] = None,
    temporal_shape: Optional[str] = None,
    window_days_permission: float = 15.0,
    window_days_activity: float = 5.0,
    suppression_window_days: float = 3.0,
    ayanamsha_id: str = "lahiri_chitrapaksha",
    source: str = "live",
) -> IntensityResult:
    """Computes ONE lambda_e(t | chart) value. `targets` lets a caller
    inject an already-fetched/enriched or fixture target list (tests do
    this); when None, live-fetches from `gochara_resonance_map` and
    enriches natal anchors from `chart_facts` (honest empty list on any
    DB-shape surprise, per `resonance_map.fetch_resonance_targets`'s own
    contract)."""
    if targets is None:
        with savepoint_scope(conn, "resonance_targets"):
            raw_targets = RM.fetch_resonance_targets(conn, chart_id, event_class)
        targets = enrich_targets(conn, raw_targets, ayanamsha_id=ayanamsha_id)

    shape = temporal_shape or fetch_temporal_shape(conn, event_class)

    promise, promise_detail = compute_promise(targets)
    permission, permission_detail = compute_permission(
        swe, conn, chart_id, event_class, targets, t_jd,
        dasha_periods=dasha_periods, window_days=window_days_permission, ayanamsha_id=ayanamsha_id,
    )

    start_jd, end_jd = t_jd - window_days_activity, t_jd + window_days_activity
    sentences = gather_configuration_sentences(swe, conn, chart_id, targets, start_jd, end_jd)
    weight_by_target_ref = {t.target_ref: t.weight for t in targets}
    x_t, x_t_detail = compute_x_t(sentences, weight_by_target_ref)

    beta_e = beta_for(event_class)
    exp_term = math.exp(beta_e * x_t)

    suppression, suppression_detail = compute_suppression(sentences, window_days=suppression_window_days)

    raw_lambda = promise * permission * exp_term - suppression
    notes = []
    if raw_lambda < 0:
        notes.append(
            f"raw product ({promise * permission * exp_term:.6f}) fully absorbed by suppression "
            f"({suppression:.6f}) -- clamped to 0.0 (fully-suppressed configuration, not a negative "
            "magnitude; sign is reserved for valence, see IntensityResult.signed_lambda)."
        )
        raw_lambda = 0.0

    adverse, valence = is_adverse(conn, event_class)
    signed_lambda = raw_lambda * (-1.0 if adverse else 1.0)

    if not targets:
        notes.append("no gochara_resonance_map targets resolved for this chart/event_class -- "
                      "PROMISE (and therefore lambda_e) is an honest 0.0, not a fabricated value.")

    return IntensityResult(
        chart_id=chart_id,
        event_class=event_class,
        temporal_shape=shape,
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
        valence=valence,
        is_adverse=adverse,
        signed_lambda=signed_lambda,
        notes=notes,
        source=source,
    )


def compute_lambda_e_series(
    swe,
    conn,
    chart_id: str,
    event_class: str,
    t_start_jd: float,
    t_end_jd: float,
    step_days: float,
    targets: Optional[list[ResonanceTarget]] = None,
    dasha_periods: Optional[list[dict]] = None,
    temporal_shape: Optional[str] = None,
    source: str = "live",
    **kwargs,
) -> list[IntensityResult]:
    """Shape-aware multi-point sweep (BRIEF_D5 §3): the interval/chain
    verification path. Resolves targets/dasha_periods ONCE (rather than
    per-point) so a live series computation does not re-issue the same
    `gochara_resonance_map`/`chart_dashas` queries `len(series)` times."""
    if targets is None:
        with savepoint_scope(conn, "resonance_targets_series"):
            raw_targets = RM.fetch_resonance_targets(conn, chart_id, event_class)
        targets = enrich_targets(conn, raw_targets)
    if dasha_periods is None:
        dasha_periods = DD.fetch_dasha_periods(conn, chart_id)

    shape = temporal_shape or fetch_temporal_shape(conn, event_class)

    results: list[IntensityResult] = []
    t = t_start_jd
    while t <= t_end_jd:
        results.append(compute_lambda_e(
            swe, conn, chart_id, event_class, t,
            targets=targets, dasha_periods=dasha_periods, temporal_shape=shape,
            source=source, **kwargs,
        ))
        t += step_days
    return results


__all__ = ["SHAPE_MAP", "fetch_temporal_shape", "compute_lambda_e", "compute_lambda_e_series"]
