"""
gochara_v3.threshold — Self-normalizing activation threshold (W1.4).

The v1 pathology: gochara windows are emitted approximately every 9 days
(astronomically impossible — Jupiter alone takes ~12 years per sign). Root
cause: v1 uses a fixed beta×X crossing threshold that every chart with any
activity crosses constantly, regardless of the event class's realistic
base-rate.

W1.4 fix: for each (chart_id, event_class) pair, compute an activation
threshold as the Pth percentile of that chart's own λ_v3 distribution over a
century-scale horizon. The percentile P is derived from the event class's
age-appropriate base_rate_by_age read from brahma_event_ontology, so the
implied window density (windows/year) approximates the classical base rate
rather than the v1 constant-threshold density.

Architecture:
  - _compute_century_lambda_distribution: pure function, no DB — accepts the
    pre-fetched ClassContext and evaluates evaluate_lambda_vector over ~5200
    weekly JDs spanning a century.  Designed to be stubbed in unit tests.
  - fetch_base_rate_for_class: single DB read from brahma_event_ontology.
    Honest degrade (logs + returns default) when the class is absent.
  - compute_threshold_config: top-level entry — orchestrates the above two
    helpers and returns a ThresholdConfig with all provenance fields.
  - is_above_threshold: pure predicate used by engine.py to gate window
    emission.

Pathology guards:
  - >52 windows/year implied by the computed threshold → density_flag:
    'pathological_dense' (the v1 pathology, now detected and named).
  - 0 windows/century for a nonzero base-rate class → density_flag: 'starved'.
  Both are stored honestly, never silently suppressed.

I2 compliance: no gochara_grammar/*.py files are modified or imported by name
here — only gochara_v3.engine (our own module) is called.

v1_parity_mode=True: ThresholdConfig is still computed (provenance on every
row is an AC4 requirement), but engine.py's window-emission logic is
completely unaffected (the v1 path does not gate on lambda_v3 at all).
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from services.gochara_intensity._dbutil import savepoint_scope
from services.ph_nimitta.base_rate import (
    AGE_BANDS,
    BAND_KEYS,
    UNIFORM_BASE_RATE,
    age_band_for_years,
    normalize_age_vector,
    years_between,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Sentinel age for the native (Abhisek Mohanty, born 1984-02-05, age ~42 in 2026).
# The caller should supply the real native age; this is used only as the
# honest fallback when birth date is unavailable.
_DEFAULT_AGE_YEARS: int = 42

# Age bracket 35–50 maps to band_41_60 (inclusive 41–60). At age 42 this is
# band_41_60, per AGE_BANDS.
_DEFAULT_BAND: str = "band_41_60"

# Weekly sampling for the century-scale distribution (52 samples/year × 100 years).
# In tests, pass step_days=365 (annual) to keep the mock fast.
CENTURY_STEP_DAYS: float = 7.0

# Julian Day reference: 2026-01-01 noon UTC ≈ JD 2461042.0.
# Used as a sane default start when no explicit start is supplied.
_JD_2026_JAN_01: float = 2461042.0

# Default fallback percentile when brahma_event_ontology lookup fails.
_FALLBACK_PERCENTILE: float = 0.50

# Density pathology bounds (windows/year).
MAX_SANE_WINDOWS_PER_YEAR: float = 52.0   # more than one per week → v1 pathology
MIN_SANE_WINDOWS_PER_YEAR: float = 0.0    # 0 windows/century → starvation (nonzero base-rate)

# Weekly sampling window in years (used for the percentile formula).
_DELTA_T_YEARS: float = 1.0 / 52.0


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class ThresholdConfig:
    """Provenance record for the self-normalizing activation threshold.

    Carried on every window row (AC4). Constructed ONCE per
    (chart_id × event_class) pair and re-used across the full JD sweep.

    Fields
    ------
    percentile_used     P ∈ [0, 1]: the percentile of the λ_v3 distribution
                        used as the activation threshold.
    lambda_thresh       λ_thresh = percentile P of the century-scale distribution.
                        A JD is considered "active" iff λ_v3 ≥ λ_thresh.
    implied_density     Windows/year implied by this threshold, estimated from
                        the century sample itself (fraction of active samples × 52).
    base_rate_cited     The normalized age-band base rate from
                        brahma_event_ontology.base_rate_by_age that drove P.
    age_band_used       Which BAND_KEY was used for the lookup.
    density_flag        'ok' | 'pathological_dense' | 'starved' | 'no_base_rate'.
    fallback_used       True when brahma_event_ontology had no row for this class
                        and the 50th-percentile default was applied.
    sample_count        Number of weekly JDs in the century distribution.
    """
    percentile_used: float
    lambda_thresh: float
    implied_density: float
    base_rate_cited: float
    age_band_used: str
    density_flag: str
    fallback_used: bool
    sample_count: int

    def to_dict(self) -> dict:
        return {
            "threshold_percentile": self.percentile_used,
            "threshold_lambda": self.lambda_thresh,
            "implied_density": self.implied_density,
            "base_rate_cited": self.base_rate_cited,
            "age_band_used": self.age_band_used,
            "density_flag": self.density_flag,
            "fallback_used": self.fallback_used,
            "sample_count": self.sample_count,
        }


# ---------------------------------------------------------------------------
# DB read: brahma_event_ontology.base_rate_by_age
# ---------------------------------------------------------------------------

def fetch_base_rate_for_class(
    conn,
    event_class: str,
    age_years: int = _DEFAULT_AGE_YEARS,
) -> tuple[float, str, bool]:
    """Read base_rate_by_age from brahma_event_ontology and return the
    normalized rate for the given age bracket.

    Returns
    -------
    (normalized_rate, age_band_key, fallback_used)
        normalized_rate : float in (0, 1] — the normalized age-band weight.
        age_band_key    : str — the BAND_KEY used.
        fallback_used   : True when the DB read failed or the class was absent.
    """
    band = age_band_for_years(age_years)
    if conn is None:
        logger.info(
            "[gochara_v3.threshold] no DB connection — using fallback percentile "
            "for event_class=%s", event_class,
        )
        return UNIFORM_BASE_RATE, band, True

    try:
        with savepoint_scope(conn, "v3_threshold_base_rate"):
            cur = conn.execute(
                "SELECT base_rate_by_age FROM brahma_event_ontology "
                "WHERE event_class_id = %s",
                [event_class],
            )
            row = cur.fetchone()
    except Exception as exc:  # noqa: BLE001
        logger.info(
            "[gochara_v3.threshold] brahma_event_ontology read failed for "
            "event_class=%s: %s — using fallback percentile.", event_class, exc,
        )
        return UNIFORM_BASE_RATE, band, True

    if row is None:
        logger.info(
            "[gochara_v3.threshold] no brahma_event_ontology row for event_class=%s "
            "— using fallback percentile.", event_class,
        )
        return UNIFORM_BASE_RATE, band, True

    raw_vector = (row if isinstance(row, dict) else dict(
        zip(["base_rate_by_age"], row)
    )).get("base_rate_by_age") or {}

    if isinstance(raw_vector, str):
        import json as _json
        try:
            raw_vector = _json.loads(raw_vector)
        except Exception:  # noqa: BLE001
            raw_vector = {}

    norm = normalize_age_vector(raw_vector)
    rate = norm.get(band, UNIFORM_BASE_RATE)
    if rate <= 0.0:
        # Theoretically possible (zero weight for this band); treat like missing.
        logger.info(
            "[gochara_v3.threshold] zero base_rate for band=%s event_class=%s "
            "— using fallback percentile.", band, event_class,
        )
        return UNIFORM_BASE_RATE, band, True

    return rate, band, False


# ---------------------------------------------------------------------------
# Pure helper: century-scale λ distribution
# ---------------------------------------------------------------------------

def _compute_century_lambda_distribution(
    swe,
    context,
    jd_start: float,
    jd_end: float,
    step_days: float = CENTURY_STEP_DAYS,
) -> np.ndarray:
    """Evaluate λ_v3 over [jd_start, jd_end] at weekly intervals.

    This is a PURE function of ClassContext — zero DB access. It calls
    evaluate_lambda_vector from engine.py (our own v3 module) with
    v1_parity_mode=False.

    In unit tests, stub this function to return a synthetic distribution
    rather than running ~5200 ephemeris calls.

    Returns
    -------
    np.ndarray of float, shape (N,), each value in [0, 1].
    """
    # Import here (not at module level) to avoid circular import with engine.py.
    from services.gochara_v3.engine import evaluate_lambda_vector

    jd_vector = np.arange(jd_start, jd_end, step_days)
    if len(jd_vector) == 0:
        return np.array([], dtype=float)

    results = evaluate_lambda_vector(
        swe, context, jd_vector, v1_parity_mode=False,
    )
    return np.array([r.raw_lambda for r in results], dtype=float)


# ---------------------------------------------------------------------------
# Top-level: compute ThresholdConfig
# ---------------------------------------------------------------------------

def compute_threshold_config(
    swe,
    context,
    conn=None,
    age_years: int = _DEFAULT_AGE_YEARS,
    jd_start: Optional[float] = None,
    jd_end: Optional[float] = None,
    step_days: float = CENTURY_STEP_DAYS,
    _lambda_distribution: Optional[np.ndarray] = None,
) -> ThresholdConfig:
    """Compute the self-normalizing threshold for (chart × class).

    Parameters
    ----------
    swe             Swiss Ephemeris handle.
    context         ClassContext (pre-fetched, immutable).
    conn            DB connection for brahma_event_ontology read (None → fallback).
    age_years       Native's age at the evaluation anchor (default 42).
    jd_start        Start of century horizon (default: JD 2026-01-01).
    jd_end          End of century horizon (default: jd_start + 100 years).
    step_days       Sampling interval in days (default 7 = weekly).
    _lambda_distribution
                    Pre-computed λ array for testing — when supplied, skips
                    the century evaluation entirely.

    Returns
    -------
    ThresholdConfig with all provenance fields populated.
    """
    event_class = context.event_class

    # 1. Age-appropriate base rate from brahma_event_ontology.
    base_rate, age_band, fallback_used = fetch_base_rate_for_class(
        conn, event_class, age_years,
    )

    # 2. Percentile formula:
    #    P = 1 - base_rate × Δt
    #    where Δt = 1/52 year (weekly sampling).
    #
    #    Derivation: if λ_v3 is above the Pth percentile, the fraction of
    #    active weeks is (1 - P). The expected windows/year = (1 - P) × 52.
    #    We want this to equal base_rate, so:
    #       base_rate = (1 - P) × 52 × Δt = (1 - P) × (52 × 1/52) = (1 - P)
    #    Therefore P = 1 - base_rate.
    #    Clamp P to [0.05, 0.999] to avoid degenerate thresholds.
    raw_p = 1.0 - base_rate
    percentile = max(0.05, min(0.999, raw_p))

    # 3. Evaluate century-scale λ distribution.
    if _lambda_distribution is not None:
        lambda_dist = np.asarray(_lambda_distribution, dtype=float)
    else:
        if jd_start is None:
            jd_start = _JD_2026_JAN_01
        if jd_end is None:
            jd_end = jd_start + 100.0 * 365.25
        lambda_dist = _compute_century_lambda_distribution(
            swe, context, jd_start, jd_end, step_days=step_days,
        )

    sample_count = len(lambda_dist)

    # 4. Compute λ_thresh as the Pth percentile of the distribution.
    if sample_count == 0:
        lambda_thresh = 0.0
    else:
        lambda_thresh = float(np.percentile(lambda_dist, percentile * 100.0))
        # Clamp to [0, 1] (should be guaranteed by λ_v3 ∈ [0,1], but defensive).
        lambda_thresh = max(0.0, min(1.0, lambda_thresh))

    # 5. Compute implied density from the sample itself.
    #    implied_density = (fraction of samples ≥ λ_thresh) × (365.25 / step_days).
    if sample_count == 0 or step_days <= 0:
        implied_density = 0.0
    else:
        active_count = int(np.sum(lambda_dist >= lambda_thresh))
        active_fraction = active_count / sample_count
        windows_per_year = active_fraction * (365.25 / step_days)
        implied_density = windows_per_year

    # 6. Density pathology guards.
    #
    #    Priority order (highest → lowest):
    #      a. pathological_dense: >52 w/yr is always a pathology, regardless
    #         of whether we have a real base rate. Even a fallback-rate threshold
    #         that produces >52 w/yr is the v1 density pathology.
    #      b. starved: 0 windows for a class with a KNOWN nonzero base rate
    #         (fallback_used=False only — we can't diagnose starvation without
    #         a real base rate to compare against).
    #      c. no_base_rate: fallback was used and density is in the sane range;
    #         we record the fallback honestly without further classification.
    #      d. ok: sane density + real base rate.
    density_flag = "ok"
    if implied_density > MAX_SANE_WINDOWS_PER_YEAR:
        density_flag = "pathological_dense"
        logger.warning(
            "[gochara_v3.threshold] DENSITY PATHOLOGY: event_class=%s implies "
            "%.1f windows/year (threshold > %.0f/year). "
            "percentile=%.4f, lambda_thresh=%.6f, base_rate=%.4f, fallback=%s. "
            "This is the v1 density pathology — threshold did not suppress enough.",
            event_class, implied_density, MAX_SANE_WINDOWS_PER_YEAR,
            percentile, lambda_thresh, base_rate, fallback_used,
        )
    elif implied_density == 0.0 and not fallback_used and base_rate > UNIFORM_BASE_RATE:
        density_flag = "starved"
        logger.warning(
            "[gochara_v3.threshold] STARVATION: event_class=%s implies 0 windows/century "
            "despite nonzero base_rate=%.4f. "
            "percentile=%.4f, lambda_thresh=%.6f. "
            "All λ_v3 values fell below the threshold for this chart×class.",
            event_class, base_rate, percentile, lambda_thresh,
        )
    elif fallback_used:
        # No real base rate — record the fallback honestly.
        density_flag = "no_base_rate"

    return ThresholdConfig(
        percentile_used=round(percentile, 6),
        lambda_thresh=round(lambda_thresh, 8),
        implied_density=round(implied_density, 4),
        base_rate_cited=round(base_rate, 6),
        age_band_used=age_band,
        density_flag=density_flag,
        fallback_used=fallback_used,
        sample_count=sample_count,
    )


def is_above_threshold(lambda_v3: float, config: ThresholdConfig) -> bool:
    """Return True iff lambda_v3 >= config.lambda_thresh.

    This is the sole gating predicate for window emission in W1.4.
    v1_parity_mode callers MUST NOT use this predicate — v1 has its own
    crossing logic (fixed beta×X threshold) that is frozen and untouched.
    """
    return lambda_v3 >= config.lambda_thresh


__all__ = [
    "ThresholdConfig",
    "fetch_base_rate_for_class",
    "compute_threshold_config",
    "is_above_threshold",
    "_compute_century_lambda_distribution",
    "CENTURY_STEP_DAYS",
    "MAX_SANE_WINDOWS_PER_YEAR",
]
