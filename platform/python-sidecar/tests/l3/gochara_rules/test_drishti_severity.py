"""graduated_drishti evaluator + severity-is-a-named-null (WINDOW_SWEEP_ANSWER_v1_0 items 4/5).

Every assertion runs the production code (services.gochara_rules.drishti / valence / records /
gochara_kernel.convention); no table or rule is re-implemented here."""
import pytest

from services.gochara_kernel.convention import SPECIAL_DRISHTI_DEG
from services.gochara_rules import drishti
from services.gochara_rules.drishti import graduated_drishti
from services.gochara_rules.records import RelationshipRecord
from services.gochara_rules.registry import FACTORS
from services.gochara_rules.valence import compute_valence


def val(agent, offset):
    return graduated_drishti(agent, offset)["value"]


def test_ordinary_aspects_are_graduated_for_every_graha():
    # Brihat Jataka ii.13 (brihat_jataka:PG65:C1): 3/10 quarter, 5/9 half, 4/8 three-quarters, 7 full
    for agent in ("Sun", "Moon", "Mercury", "Venus"):
        assert [val(agent, o) for o in (3, 10)] == [0.25, 0.25]
        assert [val(agent, o) for o in (5, 9)] == [0.5, 0.5]
        assert [val(agent, o) for o in (4, 8)] == [0.75, 0.75]
        assert val(agent, 7) == 1.0


def test_specials_are_full_and_only_for_their_owner():
    assert [val("Mars", o) for o in (4, 8)] == [1.0, 1.0]
    assert [val("Jupiter", o) for o in (5, 9)] == [1.0, 1.0]
    assert [val("Saturn", o) for o in (3, 10)] == [1.0, 1.0]
    assert val("Mars", 5) == 0.5 and val("Jupiter", 4) == 0.75 and val("Saturn", 5) == 0.5   # others stay graduated
    assert graduated_drishti("Mars", 4)["basis"] == "special_full"
    assert graduated_drishti("Venus", 4)["basis"] == "ordinary_graduated"
    # mutation guard: a fractional special, or a graduated 7th, fails
    assert val("Mars", 4) != 0.75 and val("Saturn", 7) == 1.0


def test_special_offsets_equal_the_kernels_special_angles():
    # the kernel owns the angles, this module the strengths — they must agree (one source each)
    for agent, offsets in drishti.SPECIAL_FULL.items():
        kernel_offsets = {int(a // 30) + 1 for a in SPECIAL_DRISHTI_DEG[agent]} - {7}
        assert set(offsets) == kernel_offsets, agent
    for agent in ("Sun", "Moon", "Mercury", "Venus"):
        assert {int(a // 30) + 1 for a in SPECIAL_DRISHTI_DEG[agent]} == {7}


def test_nodes_cast_no_drishti_and_non_aspect_offsets_are_a_named_null():
    for node in ("Rahu", "Ketu"):
        r = graduated_drishti(node, 7)           # not even the 7th (N-14)
        assert r["value"] is None and r["reason"] == "node_casts_no_drishti"
    for offset in (1, 2, 6, 11, 12):
        r = graduated_drishti("Saturn", offset)
        assert r["value"] is None and r["reason"] == "no_aspect_at_this_offset"
    # never an invented 0 or 1 for an unclassifiable operand
    for agent, offset in (("Pluto", 7), ("Mars", 0), ("Mars", 13), ("Mars", True), ("Mars", 7.0), (None, 7)):
        r = graduated_drishti(agent, offset)
        assert r["value"] is None, (agent, offset)
        assert r["null_state"] == FACTORS[drishti.FACTOR_REF]["null_state"] == "unqualified"
    for bad in (0, 13, -1):                       # out of the inclusive 1..12 house count: a different reason than 'no aspect'
        assert graduated_drishti("Mars", bad)["reason"] == "offset_not_an_inclusive_house_count_1_12"


def test_every_value_is_in_the_factor_codomain():
    lo, hi = FACTORS[drishti.FACTOR_REF]["range"]
    for agent in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        for offset in range(1, 13):
            v = val(agent, offset)
            assert v is None or lo <= v <= hi


def test_registry_effect_text_states_the_same_fractions():
    # the registry row's declared effect must not drift from the evaluator's table
    effect = FACTORS[drishti.FACTOR_REF]["effect"]
    assert "¼/½/¾/1 at 3-10/5-9/4-8/7" in effect and "specials full" in effect


# ── severity is a named NULL, never an invented 0.0 ─────────────────────────────
def test_valence_severity_is_null_computed_and_unqualified():
    assert compute_valence("bereavement", evidence_for=0.5, evidence_against=0.0).severity is None
    assert compute_valence("marriage", evidence_for=0.7, evidence_against=0.3).severity is None
    unresolved = compute_valence("career_entry", 0.4, 0.0, unresolved_operand="P5c donor matrix")
    assert unresolved.severity is None and unresolved.outcome_valence_for_native == "unqualified"


def test_relationship_record_severity_defaults_to_null():
    import dataclasses
    f = {x.name: x for x in dataclasses.fields(RelationshipRecord)}["severity"]
    assert f.default is None
