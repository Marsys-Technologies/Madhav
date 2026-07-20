"""
services.gochara_intensity — Lane G-3 "Intensity engine" (D-5 Gochara-Chitra
wave).

    lambda_e(t | chart) = PROMISE * PERMISSION * exp(beta_e * X(t)) - suppression

Pure service module -- no orchestrator writer (BRIEF_D5 §9: "G-1/G-2/G-3 are
pure service/schema work consumed at query time, no orchestrator asset").
Consumes G-1's `gochara_resonance_map` (via `gochara_grammar.resonance_map`)
and G-2's contact-primitive/composition-operator grammar
(`gochara_grammar.primitives`/`composition`/`sarvatobhadra`/`dasha_data`)
read-only -- this package never modifies either sibling lane's code.

Every disclosed weight/coefficient (PROMISE target weights inherited from
G-1, PERMISSION's per-system weights, beta_e, suppression's damping
weights) carries `calibration_state='structural_prior'` -- BRIEF_D5 §7
explicitly excludes fitted weights from D-5 (D-4b's job). `IntensityResult`
(`models.py`) enforces this disclosure mechanically at construction time.
"""
from __future__ import annotations

from .models import IntensityResult, SystemContribution, CalibrationDisclosureError
from .engine import compute_lambda_e, compute_lambda_e_series, fetch_temporal_shape, SHAPE_MAP
from .valence import is_adverse, fetch_valence, VALENCE_MAP
from .promise import compute_promise
from .permission import compute_permission, SYSTEM_WEIGHTS, DASHA_SYSTEM_IDS
from .configuration_activity import gather_configuration_sentences, compute_x_t
from .suppression import compute_suppression, SUPPRESSION_WEIGHTS
from .beta_priors import beta_for, BETA_STRUCTURAL_PRIORS, DEFAULT_BETA
from .enrichment import enrich_target, enrich_targets

__all__ = [
    "IntensityResult",
    "SystemContribution",
    "CalibrationDisclosureError",
    "compute_lambda_e",
    "compute_lambda_e_series",
    "fetch_temporal_shape",
    "SHAPE_MAP",
    "is_adverse",
    "fetch_valence",
    "VALENCE_MAP",
    "compute_promise",
    "compute_permission",
    "SYSTEM_WEIGHTS",
    "DASHA_SYSTEM_IDS",
    "gather_configuration_sentences",
    "compute_x_t",
    "compute_suppression",
    "SUPPRESSION_WEIGHTS",
    "beta_for",
    "BETA_STRUCTURAL_PRIORS",
    "DEFAULT_BETA",
    "enrich_target",
    "enrich_targets",
]
