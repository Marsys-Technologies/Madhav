"""
ga_condition_bands.py -- the ONE band table for `ga_condition_composite.condition_score`.
=========================================================================================
I-28 / Q-L1-16(c) (SS ruling N-62, decision sheet L1 v1.2): the cut points that bucket a
`condition_score` into bands live in ONE declared table, owned by `ga_condition` (the
score's producer), read by both consumers (`ga_medical`, `ga_vastu`). The label
vocabularies of the consumers may differ (and have opposite polarity by design: a LOW
score is a "strong" medical indication but a "weakened" vastu direction); the CUT POINTS
may not.

Before this module there were two private copies over the same score, and they disagreed:

    ga_vastu    < 0.4 weakened | < 0.7 neutral | else strengthened | NULL -> 'neutral' (invented)
    ga_medical  < 0.4 strong   | <= 0.6 moderate | else mild       | NULL -> 'unknown'

(a planet scoring 0.6 to 0.7 was "mild" to medical and "neutral" to vastu.) The ruled cut
points are 0.4 / 0.7 (a friend-sign planet scoring 0.6 stays in the middle band for both).

Band semantics (lower bound inclusive, upper bound exclusive):

    score <  0.4           -> BAND_LOW
    0.4 <= score < 0.7     -> BAND_MID
    score >= 0.7           -> BAND_HIGH
    score is NULL / NaN    -> None  (NULL band; a consumer whose column is NOT NULL stores
                                     its own 'unknown' label, NEVER a middle-band label --
                                     CLAUDE.md N.7 item 6: an honest null beats an invented
                                     judgment)

PROVENANCE. The cut points are PROJECT CONVENTIONS, `unsourced` (no classical passage fixes
them; decision sheet Q-L1-16 citation: "the thresholds themselves are not classical"). They
are labelled as such here and are not claimed otherwise.

DIGEST HYGIENE. This is a NEW module imported ONLY by the three writers (`ga_condition_writer`,
`ga_medical_writer`, `ga_vastu_writer`); it imports nothing project-local, so it adds no
widely-imported L0 module to any writer's local-import closure and moves no digest outside
those three assets.

SEPARATE TABLE, SAME HOME: the dasha peak/weak cut points (`DASHA_PERIOD_CONDITION_CUTS`, 0.65 /
0.35) live in this module too (SS ruling 2026-10-02, decision b) but are a DIFFERENT concept from the
three-band label: they gate which mahadasha periods `ga_condition` stores as peak / weak, not a
label over the score. They do NOT merge into 0.4 / 0.7, their values are unchanged, and they are
labelled a project convention with provenance `unsourced`.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final, Optional

__all__ = [
    "BAND_LOW", "BAND_MID", "BAND_HIGH", "BAND_UNKNOWN",
    "CUT_LOW_MID", "CUT_MID_HIGH",
    "ScoreBand", "SCORE_BANDS", "BAND_NAMES",
    "score_band",
    "DashaPeriodConditionCuts", "DASHA_PERIOD_CONDITION_CUTS",
]

#: Band names. Writers map these to THEIR stored label vocabulary; the names themselves are
#: never stored by this module.
BAND_LOW: Final[str] = "low"
BAND_MID: Final[str] = "mid"
BAND_HIGH: Final[str] = "high"

#: The label a consumer whose column cannot hold NULL stores when the score is NULL. It is the
#: value `ga_medical.indication_strength` has always stored for NULL; `ga_vastu` now matches it
#: (it used to invent 'neutral'). Not a band: `score_band()` returns None for a NULL score.
BAND_UNKNOWN: Final[str] = "unknown"

#: The two cut points (project convention, unsourced). 0.4 is the low/mid edge, 0.7 the mid/high edge.
CUT_LOW_MID: Final[float] = 0.4
CUT_MID_HIGH: Final[float] = 0.7


@dataclass(frozen=True)
class ScoreBand:
    """One row of the band table: `lower <= score < upper` (`upper is None` = open above)."""

    name: str
    lower: Optional[float]   # inclusive; None = open below
    upper: Optional[float]   # exclusive; None = open above

    def contains(self, score: float) -> bool:
        if self.lower is not None and score < self.lower:
            return False
        if self.upper is not None and score >= self.upper:
            return False
        return True


#: THE band table: ordered low to high, contiguous, no gaps, no overlap (asserted below and in
#: tests/test_ga_condition_band_table.py).
SCORE_BANDS: Final[tuple[ScoreBand, ...]] = (
    ScoreBand(BAND_LOW, None, CUT_LOW_MID),
    ScoreBand(BAND_MID, CUT_LOW_MID, CUT_MID_HIGH),
    ScoreBand(BAND_HIGH, CUT_MID_HIGH, None),
)

BAND_NAMES: Final[tuple[str, ...]] = tuple(b.name for b in SCORE_BANDS)


def score_band(score: object) -> Optional[str]:
    """The band name for a `condition_score`, or None when the score is NULL / not a finite number.

    `score` may be a float, an int, a `decimal.Decimal` (psycopg returns `numeric` as Decimal) or
    a numeric string; it is converted with `float()` BEFORE comparing, because `Decimal('0.4') <
    0.4` is True in Python (the float 0.4 is slightly above 0.4) and a stored score of exactly 0.4
    would otherwise land in the LOW band for a Decimal-reading consumer.
    """
    if score is None:
        return None
    try:
        value = float(score)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if math.isnan(value):
        return None
    for band in SCORE_BANDS:
        if band.contains(value):
            return band.name
    # Unreachable for a finite float given the contiguous open-ended table; fail loud, never invent.
    raise AssertionError(f"SCORE_BANDS does not cover finite score {value!r}")  # pragma: no cover


@dataclass(frozen=True)
class DashaPeriodConditionCuts:
    """Cut points over `condition_score` that classify a graha's own mahadasha periods as PEAK or
    WEAK in `ga_condition_composite.peak_dasha_periods` / `.weak_dasha_periods`.

    NOT the three-band label table above (different concept, different values; they must never be
    merged into 0.4 / 0.7). `peak_at_or_above`: score >= this -> peak periods. `weak_at_or_below`:
    score <= this -> weak periods. Between them (exclusive) -> neither (both fields NULL, a real
    "no signal"). Values are UNCHANGED from the previous module constants in `ga_condition_writer`.
    """

    peak_at_or_above: float
    weak_at_or_below: float
    provenance: str  # the project's citation-state word for these numbers


#: Project convention; no classical passage fixes these numbers (`unsourced`).
DASHA_PERIOD_CONDITION_CUTS: Final[DashaPeriodConditionCuts] = DashaPeriodConditionCuts(
    peak_at_or_above=0.65,
    weak_at_or_below=0.35,
    provenance="unsourced",
)


def _assert_table_is_contiguous() -> None:
    """Import-time self-check: ordered, contiguous, open at both ends, names unique."""
    assert SCORE_BANDS[0].lower is None and SCORE_BANDS[-1].upper is None
    for left, right in zip(SCORE_BANDS, SCORE_BANDS[1:]):
        assert left.upper is not None and left.upper == right.lower, (left, right)
    assert len(set(BAND_NAMES)) == len(BAND_NAMES)


_assert_table_is_contiguous()
