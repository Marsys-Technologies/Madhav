"""
test_ga_medical_sun_golden.py -- SS follow-up 2026-10-02 (band/X2 lane): an asset's integrity clause and
its writer must hold for ANY chart, so the Sun assertion is gone from both.

REMOVED: (1) the registry clause conjunct of migration 740, part (c): for chart 482012f1-..., ayanamsha
lahiri_chitrapaksha, graha 'Sun', `indication_strength <> 'strong'` must not exist; (2) the writer's
"non-fatal Sun advisory" (`sun_forensic_guard_warning`, logging only) and the canonical-chart
FORENSIC log. Both asserted a label about ONE chart's value (Sun in Capricorn, condition_score < 0.4
-> 'strong'); the seven FORENSIC anchors are positional, and this was not one of them.

What they were protecting is pinned here as a golden TEST on fixtures READ (SELECT-only, as the
read-only reader, 2026-10-02) for the canonical chart 482012f1-710e-4a25-994a-93821f5871aa and the
five ayanamshas. No database is touched by the test.

  chart_facts  graha_position / sign (fact_subject SUN)   -> Capricorn on all five ayanamshas
  ga_condition_composite  dignity_d1, condition_score    -> enemy_sign and the scores below
  ga_medical.indication_strength (stored)                 -> 'strong' on all five
  ga_vastu_planet_direction_map.direction_impact (stored) -> 'weakened' on all five

RESULT (reported, not edited to fit): the OLD claim (condition_score < 0.4 -> 'strong') HOLDS on every
one of the five ayanamshas under the ruled 0.4 / 0.7 table: Sun scores 0.286622 to 0.317568, all in the
LOW band, medical 'strong' (unchanged from the stored value), vastu 'weakened' (unchanged). Sun in
Capricorn is the classical enemy_sign, NOT debilitation (Sun debilitates in Libra); dignity_d1 stored is
'enemy_sign', which the fixtures pin.
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

# ayanamsha -> (sign from chart_facts, dignity_d1, condition_score, stored medical label,
#               stored vastu label), as read 2026-10-02.
SUN_CANONICAL = {
    "lahiri_chitrapaksha":       ("Capricorn", "enemy_sign", 0.303784, "strong", "weakened"),
    "krishnamurti":              ("Capricorn", "enemy_sign", 0.302703, "strong", "weakened"),
    "raman":                     ("Capricorn", "enemy_sign", 0.317568, "strong", "weakened"),
    "surya_siddhanta_classical": ("Capricorn", "enemy_sign", 0.286622, "strong", "weakened"),
    "true_chitra":               ("Capricorn", "enemy_sign", 0.303784, "strong", "weakened"),
}


def test_the_writer_and_registry_clause_text_carry_no_sun_assertion():
    assert not hasattr(med, "sun_forensic_guard_warning")
    src = pathlib.Path(med.__file__).read_text(encoding="utf-8")
    assert "FORENSIC ADVISORY" not in src
    assert "logger.warning" not in src.split("def build_ga_medical_substep")[1].split("# Step 3")[0]
    clause = (
        pathlib.Path(__file__).resolve().parents[3]
        / "00_ARCHITECTURE/briefs/suvarna/exec/band_x2/registry_clause_texts/ga_medical_integrity_NOT_APPLIED.sql"
    ).read_text(encoding="utf-8")
    body = "\n".join(line for line in clause.splitlines() if not line.lstrip().startswith("--"))
    assert CANONICAL_CHART_ID not in body and "'Sun'" not in body and "'Saturn'" not in body
    assert "lahiri_chitrapaksha" not in body  # the clause is chart- and ayanamsha-independent


@pytest.mark.parametrize("ayanamsha", sorted(SUN_CANONICAL))
def test_canonical_sun_is_capricorn_enemy_sign_not_debilitated(ayanamsha):
    sign, dignity, _, _, _ = SUN_CANONICAL[ayanamsha]
    assert sign == "Capricorn"
    assert dignity == "enemy_sign" and dignity != "debilitated"   # Sun debilitates in Libra


@pytest.mark.parametrize("ayanamsha", sorted(SUN_CANONICAL))
def test_canonical_sun_score_band_and_labels_under_the_ruled_table(ayanamsha):
    _, _, score, stored_medical, stored_vastu = SUN_CANONICAL[ayanamsha]
    assert 0.286622 <= score <= 0.317568
    assert bands.score_band(score) == bands.BAND_LOW
    assert med.indication_strength_from_score(score) == "strong" == stored_medical   # unchanged by the lane
    assert vas.compute_direction_impact(score) == "weakened" == stored_vastu          # unchanged by the lane


def test_the_old_forensic_claim_holds_on_all_five_ayanamshas_and_the_headroom_is_pinned():
    """The old assertion: condition_score < 0.4 -> 'strong'. It holds on every canonical ayanamsha.
    The closest score to the 0.4 edge is raman at 0.317568 (0.082432 below); a move of the edge, the
    scores or the band logic fails here, in CI."""
    scores = [v[2] for v in SUN_CANONICAL.values()]
    assert all(s < bands.CUT_LOW_MID for s in scores)
    assert round(bands.CUT_LOW_MID - max(scores), 6) == round(0.4 - 0.317568, 6)
