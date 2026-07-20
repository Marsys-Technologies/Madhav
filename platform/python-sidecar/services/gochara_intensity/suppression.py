"""
gochara_intensity.suppression — the "- suppression" term of lambda_e =
PROMISE * PERMISSION * exp(beta_e * X(t)) - suppression (BRIEF_D5 §1 G-3
row).

Wires G-2's own cancellation-detecting machinery through rather than
reimplementing vedha/pincer geometry: `composition.cancellation` already
recognizes (a) `gochara_vedha_pair` sentences with `detail['cancelled']`
True (another graha occupying the vedha house at the moment of primary
transit) and (b) EVERY `sarvatobhadra_vedha` sentence (which represents an
active SBC vedha-state window by construction, per `sarvatobhadra.py`'s own
docstring). `composition.kartari` additionally recognizes a two-graha
pincer straddling a target from both sides -- classically a damping/
obstructing configuration, not an amplifying one, hence counted here rather
than in `configuration_activity.py`'s X(t).

Suppression is a disclosed structural-prior DAMPING SCALAR (never fitted,
same BRIEF_D5 §7 discipline as every other coefficient in this package):

    suppression = SUPPRESSION_WEIGHTS['vedha_cancellation'] * n_vedha_cancelled
                 + SUPPRESSION_WEIGHTS['sarvatobhadra_vedha']  * n_sbc_active
                 + SUPPRESSION_WEIGHTS['kartari_pincer']        * n_kartari

subtracted directly from the raw PROMISE*PERMISSION*exp(beta*X) product in
`engine.py` (never multiplied) -- a damping term should be able to fully
cancel a modest raw signal, not just proportionally shrink an unbounded one,
matching the classical vedha doctrine's own framing ("obstructs/cancels the
primary transit's effect", not "reduces it by X%").
"""
from __future__ import annotations

from typing import Any

from services.gochara_grammar import composition as CO
from services.gochara_grammar.models import ConfigurationSentence

SUPPRESSION_WEIGHTS: dict[str, float] = {
    "vedha_cancellation": 0.15,
    "sarvatobhadra_vedha": 0.20,
    "kartari_pincer": 0.10,
}


def compute_suppression(
    sentences: list[ConfigurationSentence],
    window_days: float = 3.0,
) -> tuple[float, dict[str, Any]]:
    """Returns (suppression, detail). `sentences` should be the SAME pool
    `configuration_activity.gather_configuration_sentences` already built
    for X(t) -- suppression is computed from that pool's cancellation/vedha/
    kartari-eligible members, not a second live query."""
    cancellation_sentences = CO.cancellation(sentences)
    n_vedha_cancelled = sum(
        1 for c in cancellation_sentences if c.detail.get("source_primitive") == "gochara_vedha_pair"
    )
    n_sbc = sum(
        1 for c in cancellation_sentences if c.detail.get("source_primitive") == "sarvatobhadra_vedha"
    )

    kartari_source = [s for s in sentences if "signed_offset_from_target_deg" in s.detail]
    kartari_sentences = CO.kartari(kartari_source, window_days=window_days)
    n_kartari = len(kartari_sentences)

    suppression = (
        SUPPRESSION_WEIGHTS["vedha_cancellation"] * n_vedha_cancelled
        + SUPPRESSION_WEIGHTS["sarvatobhadra_vedha"] * n_sbc
        + SUPPRESSION_WEIGHTS["kartari_pincer"] * n_kartari
    )
    detail = {
        "n_vedha_cancelled": n_vedha_cancelled,
        "n_sarvatobhadra_vedha_active": n_sbc,
        "n_kartari_pincer": n_kartari,
        "weights": dict(SUPPRESSION_WEIGHTS),
        "calibration_state": "structural_prior",
        "note": "subtracted directly from the raw product, never multiplied -- see module docstring.",
    }
    return suppression, detail


__all__ = ["SUPPRESSION_WEIGHTS", "compute_suppression"]
