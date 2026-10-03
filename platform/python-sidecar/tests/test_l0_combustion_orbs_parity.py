"""TI-L0-22 (part a): the combustion orbs are held twice in L0 — keep them in step.

Asset briefs `bg_dignity_reference` FD-1 and `bg_formula_constants` FD-7 (PR #2829, SS Q15):
`bg_combustion_orbs` (seeded by `writers/bg_dignity_reference.py::_COMBUSTION_ORBS`) is the
single authority for the orbs; `brahma_formula_constants.combustion_orbs`
(`brahmagyan/l0_formula_constants.py::CONSTANTS`) duplicates them. The consolidation itself
(replace/remove the duplicate, fix `consumer_assets`) is a writer change plus a production
rebuild and is NOT part of this change. The brief says "until then keep the parity test";
no such test existed. This file is that test. It changes no seed and no writer.

What it pins, and the one thing it brings to light:

* `direct` of every graha equals `orb_degrees` of its `bg_combustion_orbs` row.
* the constant's `retrograde` value equals the row's `deep_orb_degrees` for every graha except
  the Moon (constant 12, row 10). For Mercury and Venus that is the classical retrograde
  exception (M-19, `ga_condition_writer._RETROGRADE_COMBUSTION_GRAHAS`: "Mercury 12 R, Venus
  8 R"). For the other grahas the code documents NO retrograde exception, so the constant's
  `retrograde` key there is the deep (atichara) orb under a different label, not an
  independent retrograde orb. The test states that relationship as a fact; it does not rule on
  which label is right (that is an acharya/SS reading before TI-L0-22b relies on the brief's
  "the same orbs" premise).

When TI-L0-22b removes the duplicate, delete this file in the same change.
"""
from __future__ import annotations

from brahmagyan.l0_formula_constants import CONSTANTS
from ga_writers.ga_condition_writer import _RETROGRADE_COMBUSTION_GRAHAS
from pipeline.orchestrator.writers.bg_dignity_reference import _COMBUSTION_ORBS


def _constant() -> dict:
    (row,) = [r for r in CONSTANTS if r["constant_id"] == "combustion_orbs"]
    return row["value_jsonb"]


def _table() -> dict[str, dict]:
    return {g: {"orb": orb, "deep": deep} for g, orb, deep, _note, _cite in _COMBUSTION_ORBS}


def test_both_copies_cover_the_same_eight_grahas_and_never_the_sun() -> None:
    assert set(_constant()) == set(_table())
    assert len(_table()) == 8
    assert "Sun" not in _table()


def test_direct_orb_of_the_constant_equals_orb_degrees_of_bg_combustion_orbs() -> None:
    const, table = _constant(), _table()
    for graha in table:
        assert const[graha]["direct"] == table[graha]["orb"], graha


def test_constant_retrograde_key_is_the_deep_orb_of_bg_combustion_orbs_except_the_moon() -> None:
    const, table = _constant(), _table()
    assert {g for g in table if const[g]["retrograde"] != table[g]["deep"]} == {"Moon"}
    assert (const["Moon"]["retrograde"], table["Moon"]["deep"]) == (12, 10)


def test_only_mercury_and_venus_are_a_documented_retrograde_exception() -> None:
    """The consumer (`check_combustion`) reads a retrograde orb for exactly two grahas; for
    them the constant's `retrograde` value is the classical M-19 pair (Mercury 12, Venus 8).
    For every other graha the constant's `retrograde` value is not read as a retrograde orb."""
    assert set(_RETROGRADE_COMBUSTION_GRAHAS) == {"Mercury", "Venus"}
    const = _constant()
    assert (const["Mercury"]["retrograde"], const["Venus"]["retrograde"]) == (12, 8)
    undocumented = {g for g in _table() if g not in _RETROGRADE_COMBUSTION_GRAHAS}
    assert undocumented == {"Moon", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"}
