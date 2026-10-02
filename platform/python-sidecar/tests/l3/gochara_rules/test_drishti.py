"""graduated_drishti evaluator (WINDOW_SWEEP_ANSWER_v1_0 item 4).

Every assertion runs the production code (services.gochara_rules.drishti / valence / records /
gochara_kernel.convention); no table or rule is re-implemented here."""
import pytest

from services.gochara_kernel.convention import SPECIAL_DRISHTI_DEG
from services.gochara_rules import drishti
from services.gochara_rules.drishti import graduated_drishti
from services.gochara_rules.registry import FACTORS


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



# ── version binding + canonical input adaptation (Codex R4/R5) ─────────────────────────────────
def test_the_result_carries_the_factor_ref_of_the_caller_version(monkeypatch):
    import copy
    assert graduated_drishti("Mars", 4)["factor"] == drishti.FACTOR_REF               # default 1.0.0
    # a second registered version (as #2897 adds): stand-in copy so the binding is exercised on main too
    monkeypatch.setitem(FACTORS, ("graduated_drishti", "1.1.0"), {**copy.deepcopy(FACTORS[drishti.FACTOR_REF]), "rule_version": "1.1.0"})
    for ref in [k for k in FACTORS if k[0] == "graduated_drishti"]:                   # every registered version
        r = graduated_drishti("Mars", 4, factor_ref=ref)
        assert r["factor"] == ref and r["value"] == 1.0
        assert graduated_drishti("Pluto", 4, factor_ref=ref)["factor"] == ref          # the null result is labelled too
    with pytest.raises(ValueError):
        graduated_drishti("Mars", 4, factor_ref=("activity_kernel", "1.0.0"))
    with pytest.raises(ValueError):
        graduated_drishti("Mars", 4, factor_ref=("graduated_drishti", "9.9.9"))


def test_persisted_lowercase_tokens_go_through_a_closed_adapter():
    for token, name in (("sun", "Sun"), ("moon", "Moon"), ("mars", "Mars"), ("mercury", "Mercury"), ("jupiter", "Jupiter"),
                        ("venus", "Venus"), ("saturn", "Saturn")):
        assert drishti.normalize_agent(token) == name and drishti.normalize_agent(name) == name
        assert graduated_drishti(token, 7)["value"] == 1.0
    assert graduated_drishti("mars", 4)["value"] == 1.0 and graduated_drishti("rahu", 7)["reason"] == "node_casts_no_drishti"
    for bad in ("MARS", "mArs", " mars", "pluto", "", None, 3, "sat"):
        assert drishti.normalize_agent(bad) is None or bad in drishti._CASTERS, bad
        if bad not in drishti._CASTERS:
            assert graduated_drishti(bad, 7)["reason"] == "agent_unrecognised"


# ── golden grid: every graha x every offset, literal expectations (steward ruling 2026-10-02) ──
_Q, _H, _T, _F = 0.25, 0.5, 0.75, 1.0
# offsets 1..12; None = no aspect at that offset
_GOLDEN = {
    "Sun":     [None, None, _Q, _T, _H, None, _F, _T, _H, _Q, None, None],
    "Moon":    [None, None, _Q, _T, _H, None, _F, _T, _H, _Q, None, None],
    "Mercury": [None, None, _Q, _T, _H, None, _F, _T, _H, _Q, None, None],
    "Venus":   [None, None, _Q, _T, _H, None, _F, _T, _H, _Q, None, None],
    "Mars":    [None, None, _Q, _F, _H, None, _F, _F, _H, _Q, None, None],      # 4th, 8th special full
    "Jupiter": [None, None, _Q, _T, _F, None, _F, _T, _F, _Q, None, None],      # 5th, 9th special full
    "Saturn":  [None, None, _F, _T, _H, None, _F, _T, _H, _F, None, None],      # 3rd, 10th special full
    "Rahu":    [None] * 12,                                                    # N-14: nodes cast none
    "Ketu":    [None] * 12,
}


@pytest.mark.parametrize("agent", sorted(_GOLDEN))
def test_golden_grid_every_offset(agent):
    got = [graduated_drishti(agent, o)["value"] for o in range(1, 13)]
    assert got == _GOLDEN[agent], agent
