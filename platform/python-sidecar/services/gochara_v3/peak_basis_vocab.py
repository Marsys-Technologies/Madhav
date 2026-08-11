"""
gochara_v3.peak_basis_vocab — named `peak_basis` vocabulary (PK-R-8 R8.8).

BACKGROUND (the defect this closes): every row this engine ever served
carried the SAME bare literal `"gochara_lambda_v3"` in its `peak_basis`
column, regardless of whether the peak behind that row was:
  (a) a day-refined true local-maximum argmax (genuinely a specific-date
      timing claim — see resolution_hierarchy.refine_peak_to_day), or
  (b) a 50-sample dense-scan argmax over the WHOLE era window (coarse —
      _find_peak in interval_solver.py samples 50 points across up to a
      multi-year span; a "peak" at that resolution is a rough locator, not
      a day-precision claim), or
  (c) (pre-PK-R-8) a fixed-step MIDPOINT that was never a peak at all.

A caller reading `peak_basis == 'gochara_lambda_v3'` on any of these three
rows could not distinguish "trust this date" from "this date is a coarse
locator" from "this was never a peak" — exactly the §N.7/§N.6 "flattening
confirmed and unverified into one undifferentiated label" defect, one layer
down in the vocabulary itself.

THE THREE BASES (R8.8, binding)
--------------------------------
  LAMBDA_V3_ARGMAX          The ONLY basis permitted on a served TIMING
                             window (month/day-tier rows) — the day-refined
                             (1-day-resolution, ±7-day window) true argmax
                             from resolution_hierarchy.refine_peak_to_day.
  LAMBDA_V3_COARSE_ARGMAX   Era-tier rows take THIS basis — the era peak is
                             a 50-sample dense scan over the FULL era span
                             (interval_solver._find_peak, `_PEAK_SAMPLE_
                             COUNT = 50`), which for a multi-year era window
                             can be a 74-day-or-coarser effective grid. It
                             must stop wearing the plain `'gochara_lambda_
                             v3'` label as if it were day-precision.
  LAMBDA_V3_MIDPOINT        Defined for completeness/documentation and for
                             any future audit of pre-PK-R-8 rows — but
                             PROHIBITED on any row this codebase writes from
                             here forward (R8.1 deleted the midpoint-tiling
                             code path entirely; there is no live call site
                             that could legitimately stamp this constant).

RETIREMENT: the bare legacy string `'gochara_lambda_v3'` is retired for ALL
NEW writes (every writer call site must import and use one of the three
named constants above, never a literal). Existing already-written rows
carrying the bare legacy string are NEVER rewritten by this change — they
are a historical fact about how they were computed, not something a later
migration silently reinterprets.

Writers MUST use these named constants, never a bare string literal — a
source guard (test_peak_basis_vocab_used_not_literal in the writer's own
test suite) bans `"peak_basis": "gochara_lambda` (and the v1 'gochara_
lambda_e_v1' literal is exempt — that is the untouched v1 engine's own
citation, not this module's vocabulary) as a literal inside
ka_gochara_v3_century_materialize.py.
"""
from __future__ import annotations

# R8.8: the ONLY basis permitted on a served TIMING window (resolution IN
# ('month','day')). Day-refined (1-day resolution, ±7-day window) true
# local-maximum argmax — see resolution_hierarchy.refine_peak_to_day.
LAMBDA_V3_ARGMAX: str = "gochara_lambda_v3_argmax"

# Era-tier rows' peak — a coarse (50-sample) dense-scan argmax over the
# FULL era span (interval_solver._find_peak). Never claims day precision.
LAMBDA_V3_COARSE_ARGMAX: str = "gochara_lambda_v3_coarse_argmax"

# Defined for documentation/audit purposes only. PROHIBITED on any row this
# codebase writes going forward — R8.1 deleted the fixed-step midpoint
# tiling code path (build_month_windows/build_day_windows) that used to
# produce this shape of "peak".
LAMBDA_V3_MIDPOINT: str = "gochara_lambda_v3_midpoint"

# The complete set of bases this module knows about, for membership checks
# (e.g. "is this basis one of ours at all, vs. a v1-engine or unknown tag").
ALL_BASES: frozenset[str] = frozenset({
    LAMBDA_V3_ARGMAX,
    LAMBDA_V3_COARSE_ARGMAX,
    LAMBDA_V3_MIDPOINT,
})

# R8.9: the bases a served row's peak_basis must be IN for is_timing_window
# to be earned via the (resolution IN {'month','day'} AND genuine basis)
# clause. Deliberately a NAMED, extensible-only-by-recorded-evidence set —
# a future lane that wants to add a basis here must cite the evidence
# demonstrating that basis's peak derivation is genuinely day-precision
# (see the module docstring's R8.10 v1-row precedent for the shape that
# evidence-based extension takes).
GENUINE_PEAK_BASES: frozenset[str] = frozenset({LAMBDA_V3_ARGMAX})

__all__ = [
    "LAMBDA_V3_ARGMAX",
    "LAMBDA_V3_COARSE_ARGMAX",
    "LAMBDA_V3_MIDPOINT",
    "ALL_BASES",
    "GENUINE_PEAK_BASES",
]
