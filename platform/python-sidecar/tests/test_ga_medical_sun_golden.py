"""
test_ga_medical_sun_golden.py -- SS follow-up 2026-10-02 (band/X2 lane): an asset's integrity clause and
its writer must hold for ANY chart, so the Sun assertion is gone from both.

REMOVED: (1) the registry clause conjunct of migration 740, part (c): for chart 482012f1-..., ayanamsha
lahiri_chitrapaksha, graha 'Sun', `indication_strength <> 'strong'` must not exist; (2) the writer's
"non-fatal Sun advisory" (`sun_forensic_guard_warning`, logging only) and the canonical-chart
FORENSIC log. Both asserted a label about ONE chart's value (Sun in Capricorn, condition_score < 0.4
-> 'strong'); the seven FORENSIC anchors are positional, and this was not one of them.

What they were protecting is pinned here as a golden TEST that runs the REAL ga_condition compute path
(`dignity_d1_from_sign`, the dignity / deeptaadi / baladi score tables, `_compute_varga_composite`,
`compute_condition_score_v1`) on READ INPUTS for the canonical chart 482012f1-710e-4a25-994a-93821f5871aa
and the five ayanamshas (sign, degree, motion, the D1..D2700 dignity spread; see
`_ga_condition_canonical_inputs.py`, read SELECT-only 2026-10-02). The pinned scores are asserted against
the COMPUTED score, never fed in as literals. No database is touched by the test.

RESULT (reported, not edited to fit): the OLD claim (condition_score < 0.4 -> 'strong') HOLDS on every
one of the five ayanamshas under the ruled 0.4 / 0.7 table: Sun scores 0.286622 to 0.317568, all in the
LOW band, medical 'strong' (unchanged from the pre-lane stored value), vastu 'weakened' (unchanged). Sun
in Capricorn is the classical enemy_sign, NOT debilitation (Sun debilitates in Libra): the real dignity
rule returns 'enemy_sign' and the real deeptaadi ladder 'dina'.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import ga_condition_bands as bands  # noqa: E402
from ga_writers import ga_condition_writer as cw  # noqa: E402
from ga_writers import ga_medical_writer as med  # noqa: E402
from tests import _ga_condition_canonical_inputs as fx  # noqa: E402

CANONICAL_CHART_ID = fx.CANONICAL_CHART_ID
SUN = list(zip(fx.AYANAMSHAS, fx.SUN_PINNED_SCORES))


def _compute(ayanamsha):
    return fx.run_real_compute("Sun", fx.SUN_CANONICAL[ayanamsha])


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


@pytest.mark.parametrize("ayanamsha,pinned", SUN)
def test_real_compute_path_reproduces_the_pinned_sun_score(ayanamsha, pinned):
    r = _compute(ayanamsha)
    assert r["condition_score"] == pinned
    assert r["breakdown"]["varga_fallback_used"] is False   # the composite came from the D1..D2700 spread


@pytest.mark.parametrize("ayanamsha,pinned", SUN)
def test_sun_in_capricorn_is_enemy_sign_not_debilitated_by_the_real_dignity_rule(ayanamsha, pinned):
    assert fx.SUN_CANONICAL[ayanamsha]["sign"] == "Capricorn"   # the READ chart_facts sign (FORENSIC anchor)
    r = _compute(ayanamsha)
    assert r["dignity_d1"] == "enemy_sign"                       # computed, not pinned
    assert r["dignity_d1"] != "debilitated"
    assert cw._DEBILITATION["Sun"] == "Libra"                    # Sun debilitates in Libra, not Capricorn
    assert r["dignity_score"] == cw.DIGNITY_SCORES["enemy_sign"] == 0.3
    assert r["avastha_deeptaadi"] == "dina"
    assert r["is_combust"] is False and r["is_deeply_combust"] is False   # the Sun is never combust


@pytest.mark.parametrize("ayanamsha,pinned", SUN)
def test_every_intermediate_matches_what_the_writer_stored(ayanamsha, pinned):
    """The stored row is the second witness: each computed step equals the value the build wrote."""
    r, stored = _compute(ayanamsha), fx.SUN_CANONICAL[ayanamsha]["stored"]
    assert r["dignity_d1"] == stored["dignity_d1"]
    assert r["avastha_baladi"] == stored["avastha_baladi"]
    assert r["avastha_deeptaadi"] == stored["avastha_deeptaadi"]
    assert r["varga_dignity_composite"] == stored["varga_dignity_composite"]
    assert r["condition_score"] == stored["condition_score"]


@pytest.mark.parametrize("ayanamsha,pinned", SUN)
def test_canonical_sun_band_and_labels_under_the_ruled_table(ayanamsha, pinned):
    r = _compute(ayanamsha)
    assert r["band"] == bands.BAND_LOW
    assert r["medical_label"] == "strong"      # unchanged by the lane
    assert r["vastu_label"] == "weakened"      # unchanged by the lane


def test_the_old_forensic_claim_holds_on_all_five_ayanamshas_and_the_headroom_is_computed():
    """The old assertion: condition_score < 0.4 -> 'strong'. It holds on every canonical ayanamsha.
    The closest score to the 0.4 edge is raman (0.317568, 0.082432 below); a move of the edge, the
    inputs or the formula fails here, in CI."""
    scores = {ay: _compute(ay)["condition_score"] for ay in fx.AYANAMSHAS}
    assert all(s < bands.CUT_LOW_MID for s in scores.values())
    assert max(scores, key=scores.get) == "raman"
    assert round(bands.CUT_LOW_MID - scores["raman"], 6) == 0.082432


# ---- the goldens can fail: each mutation of a real input to the path moves a pinned value ------------

@pytest.mark.parametrize(
    "table,key,delta",
    [
        ("_DEEPTAADI_SCORES", "dina", +0.30),       # the Sun's deeptaadi label (enemy sign)
        ("DIGNITY_SCORES", "enemy_sign", +0.40),    # the Sun's D1 dignity
        ("_BALADI_SCORES", "vriddha", +0.50),       # the Sun's baladi on 4 of 5 ayanamshas
        ("DIGNITY_SCORES", "neutral_sign", +0.30),  # the varga composite's dominant label
    ],
)
def test_mutating_a_score_table_entry_breaks_the_sun_golden(monkeypatch, table, key, delta):
    tbl = getattr(cw, table)
    monkeypatch.setitem(tbl, key, tbl[key] + delta)
    moved = [ay for ay, pinned in SUN if _compute(ay)["condition_score"] != pinned]
    assert moved, f"mutating {table}[{key!r}] by {delta:+} did not move any pinned Sun score"


def test_mutating_the_dignity_rule_input_breaks_the_sun_golden(monkeypatch):
    """If the Sun's enemy-sign classification moved (e.g. Capricorn treated as debilitation) the
    dignity assertions fail, not only the score."""
    monkeypatch.setitem(cw._DEBILITATION, "Sun", "Capricorn")
    assert _compute("lahiri_chitrapaksha")["dignity_d1"] == "debilitated"
    assert _compute("lahiri_chitrapaksha")["condition_score"] != fx.SUN_PINNED_SCORES[0]


def test_moving_the_low_edge_breaks_the_band_assertion(monkeypatch):
    monkeypatch.setattr(bands, "SCORE_BANDS", tuple(
        bands.ScoreBand(b.name, 0.30 if b.name == bands.BAND_MID else b.lower,
                        0.30 if b.name == bands.BAND_LOW else b.upper)
        for b in bands.SCORE_BANDS
    ))
    # raman (0.317568) and lahiri (0.303784) now fall in the MID band
    assert _compute("raman")["band"] != bands.BAND_LOW
