"""graduated_drishti v1.0 evaluator (GOCHARA_DESIGN_SPECS_v1_4 §2.1 factor
catalogue + O-CF-DRISHTI; WINDOW_SWEEP_ANSWER_v1_0 item 4).

A pure function of ONE operand: the inclusive whole-sign HOUSE OFFSET of the
target from the aspecting graha's sign (1 = the same sign, 7 = opposite). It
never computes a position and never reads the database.

Strength table. AUTHORITY: the frozen oracle O-CF-DRISHTI (GOCHARA_TEST_ORACLES_v1_4, citing BPHS1:16496-16502):
ordinary aspects graduated ¼/½/¾/full at house offsets 3-10/5-9/4-8/7, specials FULL — Mars 4/8, Jupiter 5/9,
Saturn 3/10 — nodes cast none (N-14). Served-corpus CORROBORATION (read 2026-10-02; none of it numerically
establishes every entry — in particular not that Jupiter's and Saturn's specials are exactly 1.0):
  * Brihat Jataka ch. II sloka 13 (brihat_jataka:PG65:C1): the ordinary graduation (quarter 3rd/10th, half
    5th/9th, three-quarters 4th/8th, full 7th) and that Saturn is powerful at 3/10, Jupiter at 5/9, Mars at 4/8;
  * Jataka Parijata sloka 30 (jataka_parijata:PG99:C1): the same graduation; its special-aspect sentences are
    OCR-garbled in the served chunk;
  * Uttara Kalamrita (uttara_kalamrita:PG40:C2): Mars full on 4th/8th, others three-fourths; the chunk is truncated.
  The BPHS lines the oracle cites are not retrievable from the served corpus by verse search (two attempts):
  a human re-read is owed (decisions/NATIVE_OPEN_DECISIONS_v1_0.md).
The specials agree with services/gochara_kernel/convention.SPECIAL_DRISHTI_DEG (the kernel owns the ANGLES, this
module the STRENGTHS; a test cross-checks them).
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

FACTOR_REF = composite_ref("graduated_drishti", RULE_VERSION)      # the default (1.0.0) membership; callers pass their own

# offset -> fraction (ordinary aspects; Brihat Jataka ii.13)
ORDINARY: dict[int, float] = {3: 0.25, 10: 0.25, 5: 0.5, 9: 0.5, 4: 0.75, 8: 0.75, 7: 1.0}
# graha -> offsets at which it casts a FULL special aspect
SPECIAL_FULL: dict[str, tuple[int, ...]] = {"Mars": (4, 8), "Jupiter": (5, 9), "Saturn": (3, 10)}
_CASTERS = frozenset({"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"})
_NODES = frozenset({"Rahu", "Ketu"})
# Persisted records carry LOWERCASE graha tokens; the strength table speaks title case. A CLOSED adapter —
# anything outside it is not a graha this module knows (never `.title()`-guessed).
TOKEN_TO_AGENT = {n.lower(): n for n in sorted(_CASTERS | _NODES)}


def normalize_agent(token):
    """Persisted lowercase token (or an already title-case name) -> the helper's vocabulary, else None."""
    if not isinstance(token, str):
        return None
    if token in _CASTERS or token in _NODES:
        return token
    return TOKEN_TO_AGENT.get(token)


def _row(factor_ref):
    row = FACTORS.get(factor_ref)
    if row is None or row["factor_id"] != "graduated_drishti":
        raise ValueError(f"{factor_ref!r} is not a graduated_drishti factor row")
    return row


def _unqualified(reason: str, agent, offset, factor_ref) -> dict:
    return {"value": None, "null_state": _row(factor_ref)["null_state"],
            "reason": reason, "factor": factor_ref,
            "evidence": {"scored": False, "kind": "typed_operand_evidence",
                         "agent": agent, "house_offset": offset}}


def graduated_drishti(agent: str, offset: int, *, factor_ref: tuple[str, str] = FACTOR_REF) -> dict:
    """Aspect strength of `agent` onto a target `offset` houses from its sign. The result carries the factor
    ref of the membership that CALLED it (a 1.1.0 path gets a 1.1.0 result; a mismatched version is a caller
    defect, not silently re-labelled)."""
    _row(factor_ref)
    name = normalize_agent(agent)
    if name is None:
        return _unqualified("agent_unrecognised", agent, offset, factor_ref)
    if name in _NODES:
        return _unqualified("node_casts_no_drishti", agent, offset, factor_ref)          # N-14
    if isinstance(offset, bool) or not isinstance(offset, int) or not 1 <= offset <= 12:
        return _unqualified("offset_not_an_inclusive_house_count_1_12", agent, offset, factor_ref)
    if offset in SPECIAL_FULL.get(name, ()):
        value, basis = 1.0, "special_full"
    elif offset in ORDINARY:
        value, basis = ORDINARY[offset], "ordinary_graduated"
    else:
        return _unqualified("no_aspect_at_this_offset", agent, offset, factor_ref)
    return {"value": value, "null_state": _row(factor_ref)["null_state"],
            "reason": None, "basis": basis, "factor": factor_ref,
            "evidence": {"scored": False, "kind": "typed_operand_evidence",
                         "agent": agent, "house_offset": offset}}
