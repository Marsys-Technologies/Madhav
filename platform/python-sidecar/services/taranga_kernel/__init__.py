"""
services.taranga_kernel — shared, pure activation-curve computation (L3 Kāla).

Doctrine-Waves D-3, lane wave/D-3/T-3.

Extracted from the batch writer `pipeline/orchestrator/writers/ka_taranga.py`
(monthly dasha × transit × promise convolution) so BOTH:
  (a) ka_taranga (batch, monthly-grain, persists to kala_taranga), and
  (b) a live on-demand caller (sibling lane wave/D-3/T-2's serving-layer
      Taraṅga service — imports this module once T-2 merges)
can compute activation values with an IDENTICAL formula, with NO writer-side
I/O (no db_conn, no orchestrator coupling) inside the pure computation itself.

See `kernel.py` for the public interface (harmonic_mean / combine_activation /
GRAHA_DOMAINS / month_range / ChartStaticSubstrate / compute_activation_curve).
See `promise.py` for the PROMISE lock formula (CR-88).

NEVER calls conn.commit()/rollback(). NEVER writes to any DB table. NEVER
imports psycopg or anything DB-shaped — I/O is entirely the caller's job.
"""
from __future__ import annotations

from services.taranga_kernel.kernel import (
    GRAHA_DOMAINS,
    ActivationPoint,
    ChartStaticSubstrate,
    combine_activation,
    compute_activation_curve,
    dasha_lord_at,
    harmonic_mean,
    month_range,
)
from services.taranga_kernel.promise import (
    PromiseInputs,
    compute_promise,
    nbry_deferral_semantics,
)

__all__ = [
    "GRAHA_DOMAINS",
    "ActivationPoint",
    "ChartStaticSubstrate",
    "combine_activation",
    "compute_activation_curve",
    "dasha_lord_at",
    "harmonic_mean",
    "month_range",
    "PromiseInputs",
    "compute_promise",
    "nbry_deferral_semantics",
]
