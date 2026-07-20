"""
gochara_intensity.configuration_activity — X(t), the "how loud is the sky
right now" scalar feeding exp(beta_e * X(t)) in lambda_e = PROMISE *
PERMISSION * exp(beta_e * X(t)) - suppression (BRIEF_D5 §1 G-3 row).

X(t) is deliberately the INSTANT-GEOMETRY half of the engine, separate from
PERMISSION's period/system-gating half (`permission.py`): it aggregates
G-2's contact-primitive families that fire AT a specific transiting-degree
event -- degree_contact, drishti_contact, sign_ingress,
nakshatra_ingress_tara, kakshya_cell_crossing, station_retro_loop,
eclipse_degree, gochara_vedha_pair, sarvatobhadra_vedha -- within a window
around t, weighted by (a) the resonance target's own PROMISE-side weight
(a contact on a chart-critical target should count for more than one on a
peripheral target) and (b) each fired sentence's own orb_strength where the
primitive reports one (tighter orb = stronger signal), falling back to a
flat per-sentence contribution of 1.0 when no orb_strength is available
(sign_ingress, nakshatra_ingress_tara, eclipse_degree, vedha primitives).

X(t) is intentionally UNBOUNDED non-negative (not normalized to [0,1]) --
it is meant to be fed through exp(beta_e * X(t)), where beta_e (a disclosed
structural-prior coefficient, `beta_priors.py`) does the scaling/damping
job. This mirrors the vision text's own framing (exp(beta*X), not a bare
X) -- clamping X(t) itself would fight beta_e's job.

`gather_configuration_sentences` is the shared sentence-pool builder this
module and `suppression.py` both call, so the "what fired near t" work
happens exactly once per `engine.compute_lambda_e` call.
"""
from __future__ import annotations

import logging
from typing import Any

from services.gochara_grammar import primitives as P
from services.gochara_grammar import sarvatobhadra as SBC
from services.gochara_grammar.models import ConfigurationSentence, ResonanceTarget
from ._dbutil import savepoint_scope

logger = logging.getLogger(__name__)

# The "instant geometry" primitive families X(t) draws on -- deliberately
# excludes av_threshold_state / planetary_return / the Jupiter+Saturn slice
# of drishti_contact+degree_contact, which `permission.py` already counts as
# PERMISSION-side systems; double-counting the same fired sentence in both
# PROMISE-side X(t) AND PERMISSION would conflate the two terms the vision
# text keeps deliberately distinct.
_CONFIG_ACTIVITY_PRIMITIVES = (
    "degree_contact", "drishti_contact", "sign_ingress", "nakshatra_ingress_tara",
    "kakshya_cell_crossing", "station_retro_loop", "eclipse_degree",
    "gochara_vedha_pair", "sarvatobhadra_vedha",
)


def gather_configuration_sentences(
    swe, conn, chart_id: str, targets: list[ResonanceTarget], start_jd: float, end_jd: float,
) -> list[ConfigurationSentence]:
    """Runs every X(t)-relevant contact primitive over every target in the
    window, degrading honestly (skip, log, continue) on any single
    primitive/target failure rather than aborting the whole gather -- same
    discipline the primitives themselves already use internally."""
    out: list[ConfigurationSentence] = []
    for target in targets:
        for fn, needs_conn in (
            (P.degree_contact, False),
            (P.drishti_contact, False),
            (P.sign_ingress, False),
            (P.nakshatra_ingress_tara, False),
            (P.kakshya_cell_crossing, True),
            (P.station_retro_loop, False),
            (P.eclipse_degree, False),
            (P.gochara_vedha_pair, True),
        ):
            try:
                with savepoint_scope(conn, "config_activity_primitive"):
                    if needs_conn:
                        out.extend(fn(swe, chart_id, target, start_jd, end_jd, conn=conn))
                    else:
                        out.extend(fn(swe, chart_id, target, start_jd, end_jd))
            except Exception as exc:  # noqa: BLE001
                logger.info("[configuration_activity] %s failed for target_ref=%s: %s",
                            getattr(fn, "__name__", fn), target.target_ref, exc)
        try:
            with savepoint_scope(conn, "sarvatobhadra_vedha"):
                out.extend(SBC.find_sarvatobhadra_vedha_states(swe, chart_id, target, start_jd, end_jd, conn=conn))
        except Exception as exc:  # noqa: BLE001
            logger.info("[configuration_activity] sarvatobhadra_vedha failed for target_ref=%s: %s",
                        target.target_ref, exc)
    return out


def compute_x_t(
    sentences: list[ConfigurationSentence],
    weight_by_target_ref: dict[str, float],
) -> tuple[float, dict[str, Any]]:
    """Aggregates already-gathered ConfigurationSentences into the scalar
    X(t). `weight_by_target_ref` is target_ref -> PROMISE-side weight (the
    same G-1 weights `promise.py` consumes), used so a contact on a
    chart-critical target contributes more than one on a peripheral target.
    Sentences whose primitive is a cancelled gochara_vedha_pair are EXCLUDED
    from X(t) -- a cancelled primary transit is not "loud sky activity", it
    is the suppression term's job (see `suppression.py`) to represent it.

    `target_weight` is clamped to `[0.0, +inf)` before use (mirrors
    `promise.py`'s own clamp) -- live `gochara_resonance_map` rows CAN carry
    a negative weight (e.g. a `mechanism_node` target tagged
    `unfavourable`, confirmed live: `venus:unfavourable:h7` weight=-1) to
    encode DIRECTION at the resonance-map layer. X(t) is documented as an
    "unbounded NON-NEGATIVE" activity magnitude (see module docstring); a
    negative weight flowing through unclamped would silently violate that
    contract and could drive X(t) negative, which `exp(beta*X(t))` does not
    expect. Direction/valence is handled once, at the whole-lambda_e level
    (`valence.is_adverse`'s final sign flip in `engine.py`), not re-derived
    per-target inside X(t) -- clamping here keeps that separation clean."""
    contributions = []
    x_t = 0.0
    for s in sentences:
        if s.primitive not in _CONFIG_ACTIVITY_PRIMITIVES:
            continue
        if s.primitive == "gochara_vedha_pair" and s.detail.get("cancelled"):
            continue  # suppression.py's job, not X(t)'s
        target_weight = max(0.0, weight_by_target_ref.get(s.target_ref or "", 0.5))  # honest neutral default
        orb_strength = s.detail.get("orb_strength")
        strength = float(orb_strength) if orb_strength is not None else 1.0
        contribution = target_weight * strength
        x_t += contribution
        contributions.append({
            "primitive": s.primitive, "target_ref": s.target_ref, "transit_planet": s.transit_planet,
            "event_datetime_ist": s.event_datetime_ist, "target_weight": target_weight,
            "strength": strength, "contribution": round(contribution, 6),
        })
    detail = {
        "sentence_count_considered": len(contributions),
        "sentence_count_total_gathered": len(sentences),
        "contributions": contributions,
        "note": "unbounded non-negative aggregate; scaling/damping is beta_e's job (see beta_priors.py)",
    }
    return x_t, detail


__all__ = ["gather_configuration_sentences", "compute_x_t"]
