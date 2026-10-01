"""
test_ga_medical_saturn_golden.py -- SS ruling 2026-10-02 (band/X2 lane, decision a).

The ga_medical Saturn "FORENSIC guard" (a build-halting assertion about one chart's label) was
REMOVED from the writer: it lived inside a writer that runs for every chart, was tied to an
unsourced cut point, and is not one of the seven FORENSIC anchors (those are positional: Sun sign,
Moon nakshatra, Lagna, tithi, vara, yoga, karana). What it was trying to protect is pinned here as a
golden TEST instead, so a future change to Saturn's stored score or band shows in CI, not as a
production halt.

Fixtures are values READ (SELECT-only, as the read-only reader, 2026-10-02) for the canonical chart
482012f1-710e-4a25-994a-93821f5871aa and the five ayanamshas; the test never touches a database:
  chart_facts  graha_position / sign (fact_subject SAT)      -> Libra on all five ayanamshas
  ga_condition_composite  dignity_d1, condition_score       -> exalted, the scores below
  ga_medical.indication_strength (stored BEFORE this lane)   -> 'mild' (old 0.6 cut)
  ga_vastu_planet_direction_map.direction_impact             -> 'neutral'

Under the ruled 0.4 / 0.7 band table every one of those scores is in the MID band, so the NEW
ga_medical label is 'moderate' (the old 'mild' came from the old 0.6 cut); vastu stays 'neutral'.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import ga_condition_bands as bands  # noqa: E402
from ga_writers import ga_medical_writer as med  # noqa: E402
from ga_writers import ga_vastu_writer as vas  # noqa: E402

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# ayanamsha -> (sign from chart_facts, dignity_d1, condition_score, STORED old medical label,
#               stored vastu label), as read 2026-10-02.
SATURN_CANONICAL = {
    "lahiri_chitrapaksha":       ("Libra", "exalted", 0.683108, "mild", "neutral"),
    "krishnamurti":              ("Libra", "exalted", 0.691486, "mild", "neutral"),
    "raman":                     ("Libra", "exalted", 0.697162, "mild", "neutral"),
    "surya_siddhanta_classical": ("Libra", "exalted", 0.680000, "mild", "neutral"),
    "true_chitra":               ("Libra", "exalted", 0.683108, "mild", "neutral"),
}


def test_the_writer_no_longer_has_a_saturn_guard():
    assert not hasattr(med, "saturn_forensic_guard_violation")
    src = pathlib.Path(med.__file__).read_text(encoding="utf-8")
    assert "FORENSIC VIOLATION" not in src
    assert "raise AssertionError" not in src


@pytest.mark.parametrize("ayanamsha", sorted(SATURN_CANONICAL))
def test_canonical_saturn_is_libra_exalted(ayanamsha):
    sign, dignity, _, _, _ = SATURN_CANONICAL[ayanamsha]
    assert (sign, dignity) == ("Libra", "exalted")


@pytest.mark.parametrize("ayanamsha", sorted(SATURN_CANONICAL))
def test_canonical_saturn_score_is_pinned_inside_the_measured_range(ayanamsha):
    _, _, score, _, _ = SATURN_CANONICAL[ayanamsha]
    assert 0.680 <= score <= 0.697162


@pytest.mark.parametrize("ayanamsha", sorted(SATURN_CANONICAL))
def test_canonical_saturn_band_and_labels_under_the_ruled_table(ayanamsha):
    _, _, score, old_medical, stored_vastu = SATURN_CANONICAL[ayanamsha]
    # the ruled 0.4 / 0.7 table puts every canonical Saturn score in the MID band
    assert bands.score_band(score) == bands.BAND_MID
    assert med.indication_strength_from_score(score) == "moderate"   # was 'mild' under the old 0.6 cut
    assert old_medical == "mild"                                     # the stored value this lane changes
    assert vas.compute_direction_impact(score) == stored_vastu == "neutral"   # unchanged


def test_all_five_canonical_saturn_scores_are_below_the_high_edge_so_a_cut_move_is_visible():
    """If the 0.7 edge, the scores, or the band logic moves, this fails in CI. The closest score to
    the edge is raman at 0.697162 (0.0028 below 0.7)."""
    scores = [v[2] for v in SATURN_CANONICAL.values()]
    assert max(scores) < bands.CUT_MID_HIGH
    assert min(scores) >= bands.CUT_LOW_MID
    assert round(bands.CUT_MID_HIGH - max(scores), 6) == round(0.7 - 0.697162, 6)
