"""graduated_drishti v1.0 evaluator (GOCHARA_DESIGN_SPECS_v1_4 §2.1 factor
catalogue + O-CF-DRISHTI; WINDOW_SWEEP_ANSWER_v1_0 item 4).

A pure function of ONE operand: the inclusive whole-sign HOUSE OFFSET of the
target from the aspecting graha's sign (1 = the same sign, 7 = opposite). It
never computes a position and never reads the database.

Strength table — served corpus, read verbatim 2026-10-02:
  * Brihat Jataka ch. II sloka 13 (corpus locator brihat_jataka:PG65:C1): "All
    the planets cast a quarter glance at the 3rd and 10th houses; half a
    glance at the 5th and 9th; three quarters of a glance at the 4th and 8th;
    and a full eye at the 7th. Saturn is exceedingly powerful when he casts
    his glance at the 3rd and 10th. Jupiter is auspicious in his glances at
    the 5th and 9th. Mars is potent with his glance at the 4th and 8th."
  * Uttara Kalamrita (uttara_kalamrita:PG40:C2): Mars has a full aspect on the
    fourth and eighth houses from himself; the others a three-fourths aspect
    there; the other planets only a half aspect on the fifth and ninth.
    (The served chunk is truncated mid-sentence; used only as corroboration.)
  * Jataka Parijata sloka 30 (jataka_parijata:PG99:C1): the same graduation
    (quarter 3/10, half 5/9, three-quarters 4/8, full 7th); its special-aspect
    sentences are OCR-garbled in the served chunk — corroboration only.
  * The spec/oracles also cite BPHS1:16496-16502 (O-CF-DRISHTI). That passage
    is NOT retrievable from the served corpus by verse search (two attempts,
    2026-10-02), so it is not cited here; a human re-read is still owed.
Specials are FULL (1.0): Mars 4/8, Jupiter 5/9, Saturn 3/10 — the same
angles services/gochara_kernel/convention.SPECIAL_DRISHTI_DEG carries
(a test cross-checks them; the kernel owns the ANGLES, this module owns the
STRENGTHS). Rāhu/Ketu cast no dṛṣṭi at all (N-14).

Applies to ASPECT records only. Residence and conjunction have no offset: the
factor is NOT APPLICABLE there, which is a declared state of the registry
(AM-13 candidate), not a missing operand and never a silent 1.

Output = the factor result the score algebra consumes (`{"value",
"null_state"}`): value in [0, 1], or None (+ the registry row's null_state,
`unqualified`) for an operand that cannot be classified — never an invented
0 or 1 (CLAUDE.md §N.7 item 6).
"""
from __future__ import annotations

from .registry import FACTORS, RULE_VERSION, composite_ref

FACTOR_REF = composite_ref("graduated_drishti", RULE_VERSION)

# offset -> fraction (ordinary aspects; Brihat Jataka ii.13)
ORDINARY: dict[int, float] = {3: 0.25, 10: 0.25, 5: 0.5, 9: 0.5, 4: 0.75, 8: 0.75, 7: 1.0}
# graha -> offsets at which it casts a FULL special aspect
SPECIAL_FULL: dict[str, tuple[int, ...]] = {"Mars": (4, 8), "Jupiter": (5, 9), "Saturn": (3, 10)}
_CASTERS = frozenset({"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"})
_NODES = frozenset({"Rahu", "Ketu"})


def _unqualified(reason: str, agent, offset) -> dict:
    return {"value": None, "null_state": FACTORS[FACTOR_REF]["null_state"],
            "reason": reason, "factor": FACTOR_REF,
            "evidence": {"scored": False, "kind": "typed_operand_evidence",
                         "agent": agent, "house_offset": offset}}


def graduated_drishti(agent: str, offset: int) -> dict:
    """Aspect strength of `agent` onto a target `offset` houses from its sign."""
    if not isinstance(agent, str) or agent not in _CASTERS | _NODES:
        return _unqualified("agent_unrecognised", agent, offset)
    if agent in _NODES:
        return _unqualified("node_casts_no_drishti", agent, offset)          # N-14
    if isinstance(offset, bool) or not isinstance(offset, int) or not 1 <= offset <= 12:
        return _unqualified("offset_not_an_inclusive_house_count_1_12", agent, offset)
    if offset in SPECIAL_FULL.get(agent, ()):
        value, basis = 1.0, "special_full"
    elif offset in ORDINARY:
        value, basis = ORDINARY[offset], "ordinary_graduated"
    else:
        return _unqualified("no_aspect_at_this_offset", agent, offset)
    return {"value": value, "null_state": FACTORS[FACTOR_REF]["null_state"],
            "reason": None, "basis": basis, "factor": FACTOR_REF,
            "evidence": {"scored": False, "kind": "typed_operand_evidence",
                         "agent": agent, "house_offset": offset}}
