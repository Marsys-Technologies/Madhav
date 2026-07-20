"""
gochara_intensity.promise — the PROMISE term of lambda_e = PROMISE * PERMISSION
* exp(beta_e * X(t)) - suppression (BRIEF_D5 §1 G-3 row).

PROMISE is the classical-prior "how much does this chart's own structure
want this event_class" signal, sourced entirely from G-1's
`gochara_resonance_map` (already classical-prior-weighted, already citation-
disciplined per `gochara_grammar.models.ResonanceTarget`'s mechanical
enforcement) -- G-3 does not invent new weights here, it AGGREGATES G-1's
per-target weights into one scalar per chart x event_class.

Aggregation choice (ENGINEERING JUDGMENT, documented): a chart rarely has
just one resonance target for an event_class (BRIEF_D5's own resonance-map
spec lists up to 8 target_type families -- bhava/lord/karaka/mechanism_node/
sensitive_degree/arudha/yoga_constituent/dasha_lord_portfolio). Treating
these as independent-ish corroborating signals, PROMISE uses a "noisy-OR"
combination:

    PROMISE = 1 - PRODUCT_i (1 - w_i)

over each target's disclosed weight w_i (already in [0,1] per G-1's schema).
This has three properties that make it a better fit than a raw sum or mean
for this use: (1) it saturates at 1.0 rather than blowing past it as targets
accumulate (a raw sum of five 0.5-weight targets would hit 2.5, meaningless
as a [0,1] promise fraction); (2) a single very strong target (w=0.95)
already carries most of the signal, matching the classical intuition that
ONE dominant classical marker (e.g. a well-fortified karaka) can carry a
chart's promise for an event_class even with weaker corroborators; (3) it
is monotonically non-decreasing in the number and strength of targets,
unlike a mean (which can be dragged down by adding a weak target) -- more
classical evidence should never LOWER promise. An empty target set
(chart/event_class has no gochara_resonance_map rows yet) is an honest
PROMISE=0.0, not a fabricated default.
"""
from __future__ import annotations

from typing import Any

from services.gochara_grammar.models import ResonanceTarget


def compute_promise(targets: list[ResonanceTarget]) -> tuple[float, dict[str, Any]]:
    """Returns (promise, detail). `detail` carries per-target contributions
    plus `calibration_state` -- PROMISE weights are G-1's own disclosed
    classical-prior weights (already `structural_prior`-equivalent; G-1's
    schema does not carry a `calibration_state` column of its own, but every
    row is either `classical_citation`-backed or explicitly
    `uncited_extension` per G-1/G-2's shared citation discipline, which this
    module's detail dict surfaces per-target so a caller can see exactly
    which targets are cited vs honestly-flagged extensions)."""
    if not targets:
        return 0.0, {
            "target_count": 0,
            "targets": [],
            "aggregation": "noisy_or",
            "calibration_state": "structural_prior",
            "note": "no gochara_resonance_map rows for this chart/event_class -- honest PROMISE=0.0, "
                    "not a fabricated default.",
        }

    product_complement = 1.0
    per_target = []
    for t in targets:
        w = max(0.0, min(1.0, float(t.weight)))
        product_complement *= (1.0 - w)
        per_target.append({
            "target_type": t.target_type,
            "target_ref": t.target_ref,
            "weight": w,
            "classical_citation": t.classical_citation,
            "uncited_extension": t.uncited_extension,
        })

    promise = 1.0 - product_complement
    detail = {
        "target_count": len(targets),
        "targets": per_target,
        "aggregation": "noisy_or",
        "calibration_state": "structural_prior",
    }
    return promise, detail


__all__ = ["compute_promise"]
