"""
services.w2g_validations — W2G (GOCHARA-2.0) bind-time validations V1–V6.

WAVE ID: **W2G** (ADJUDICATION-3, 2026-07-29 — the operative wave identity is
`W2G`; `D-6` is RETIRED as a wave label and survives only as a historical
alias in the design doc's own frontmatter). The engine being built is named
GOCHARA-2.0; the wave that builds it is W2G.

WHAT THIS PACKAGE IS. Design §6 lists six validations the 2.0 work must bind
against before it computes anything. This package is those six as running
code — each a pure function of a `QueryFn` seam, each returning a
`ValidationResult` whose status is produced by a detector that measures the
specific claim the status asserts (CLAUDE.md §N.8).

WHAT THIS PACKAGE IS NOT. It is not the 2.0 writer, and it writes nothing.
Every statement it issues is a SELECT. `kala_gochara_windows` data is an
untouchable (brief §7 / ADJUDICATION-6) and this package reads it only.

RULINGS BOUND INTO THE CODE (not merely cited in comments):
  * ADJUDICATION-3 — wave id `W2G` in every identifier and report field.
  * ADJUDICATION-4 — Tier 1 is the two canonical charts TOGETHER; V5 fails
    if either is incomplete.
  * ADJUDICATION-5 — V2 verifies 1900–2084 (not 1984–2084) and computes
    `calendar_epoch_start` as the max-over-bodies first-covered date,
    surfacing it as data; the runner then sizes V4 over the MEASURED epoch.
  * ADJUDICATION-6 — V5 detects whether a per-row generation discriminator
    exists at all, because "2.0 writes generation-stamped rows beside v1" is
    not expressible without one.
"""
from ._db import QueryFn, query_fn_from_conn
from .runner import DEFAULT_PILOT_YEAR, TIER1_CHART_IDS, TIER2_CHART_IDS, bind_gate, run_all
from .types import FAIL, INDETERMINATE, PASS, WAVE_ID, ValidationResult
from .v1_profile_split import validate_v1_profile_split
from .v2_ephemeris_coverage import validate_v2_ephemeris_coverage
from .v3_spline_accuracy import validate_v3_spline_accuracy
from .v4_transition_sizing import validate_v4_transition_sizing
from .v5_corpus_readiness import validate_v5_corpus_readiness
from .v6_divergence_pilot import (
    classify_divergence,
    run_divergence_report,
    validate_v6_divergence_pilot,
)

__all__ = [
    "WAVE_ID",
    "PASS",
    "FAIL",
    "INDETERMINATE",
    "ValidationResult",
    "QueryFn",
    "query_fn_from_conn",
    "run_all",
    "bind_gate",
    "TIER1_CHART_IDS",
    "TIER2_CHART_IDS",
    "DEFAULT_PILOT_YEAR",
    "validate_v1_profile_split",
    "validate_v2_ephemeris_coverage",
    "validate_v3_spline_accuracy",
    "validate_v4_transition_sizing",
    "validate_v5_corpus_readiness",
    "validate_v6_divergence_pilot",
    "classify_divergence",
    "run_divergence_report",
]
