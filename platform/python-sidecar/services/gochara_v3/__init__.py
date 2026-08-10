"""
gochara_v3 — batched-context scoring engine for the GOCHARA-UTKARSHA campaign.

The entire <=15-20 min/chart budget rests on this package. The v1 engine
(`gochara_intensity.engine.compute_lambda_e`) does DB round-trips per
candidate JD (~0.5s each); this package replaces the per-candidate pattern
with a ONE-SHOT context fetch (all DB access in `ClassContext.fetch`) followed
by a ZERO-DB vectorized evaluation (`evaluate_lambda_vector`).

v1 grammar semantics are IMPORTED, not copied (I2 compliance): primitives,
composition operators, promise, suppression weights, beta priors, valence
maps all come from the untouched v1 modules. This package only reorganizes
the DATA ACCESS pattern (batch) and the EVALUATION loop (vectorized), never
the scoring logic itself.
"""

GRAMMAR_VERSION = "v3_utkarsha"

__all__ = ["GRAMMAR_VERSION"]
