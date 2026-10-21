"""P1 period-lord valence: the effective dignity rung and the (natural nature, rung) -> (side, value) mapping.

Doctrine: OWNER-DOCTRINE-CONFIRMED-20261021 / P1-MAPPING-DECISION (Form B), ANSWERS.md v2.1 §B.2-B.5. This module holds the
STRUCTURE — the rung precedence, the closed vocabulary, the mapping's shape and its validation, the node disclosures. It holds NO
cell value: the 16 (nature, rung) cells are DATA a registry row declares under `category_mapping` (the D2 binding) and are read
through `mapping_from_row`; nothing here can drift from the row it was bound to (CLAUDE.md §N.7 item 3).

Effective rung of the period lord at t, in this order (ANSWERS §B.2 — the order matters; debility is tested before the sign-lord's
friendship or it is never reached):

    COMB  the L1 combustion state is "combust" (SR-Q6-L1: the state and its orbs are L1 facts, inherited, never re-derived here)
    EX    the lord is in its exaltation SIGN (L0 `bg_dignity_reference`)
    MT    within its mūlatrikoṇa degrees in that sign (L0)
    OWN   in an own sign (L0)
    DEB   in its debilitation sign (L0)
    FR/NEU/INI  otherwise, by the lord's OWN natural friendship (`bg_graha_naisargika_friendship WHERE graha = lord`) toward the
                lord of the sign it occupies — never the sign lord's table (BJ II.16-17 translator's note, brihat_jataka:PG69:C1)

EX is tested before MT: inside one sign the order is EX > MT > OWN (the Moon's Taurus and Mercury's Virgo read as exaltation
throughout). L1's natal classifier `dignity_d1_from_sign` tests MT before EX; the two conventions differ in exactly those two
placements (Moon in Taurus from 4 degrees, Mercury in Virgo 16-20) and nowhere else — the owner's order governs transit scoring,
the difference is pinned by a differential test, not hidden.

Nodes (ANSWERS §B.5, ruling): Rāhu/Ketu are never combust (declared). Their exaltation/debilitation come from L0 as seeded; the
mūlatrikoṇa and own signs the served verse names (BPHS 47.34-39, bphs:PG573:C2-PG574:C1) are NOT in L0, so a node in one of
those signs has NO rung (`node_dignity_unclassified`, an honest null — not a guess) until L0 carries them. An own sign L0 later
adds to a node's row is classified by that row and leaves the reserved set by itself; a node MŪLATRIKOṆA cannot, because the
strict reader `p1_inputs.validated_dignity_row` deliberately drops a node's mūlatrikoṇa (it has no degree range) — carrying it
needs that reader changed, not this module. The disputed node-friendship pairs and the variant own signs are DISCLOSED on the
result, not silently resolved.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Mapping

from .p1_inputs import (GRAHAS, SIGNS, StrictInputError, _l1, dignity_boundaries, validated_dignity_row,
                        validated_naisargika)

NATURES = ("benefic", "malefic")
SIDES = ("favourable", "adverse")
#: every rung the effective-rung rule can return (closed vocabulary; a mapping must declare exactly these per nature)
RUNGS = ("COMB", "EX", "MT", "OWN", "DEB", "FR", "NEU", "INI")
NODES = ("Rahu", "Ketu")
_FRIENDSHIP_RUNG = {"friend": "FR", "neutral": "NEU", "enemy": "INI"}

#: the signs BPHS 47.34-39 reserves for the nodes' mūlatrikoṇa / own (bphs:PG573:C2-PG574:C1 [V]): Rāhu Gemini (MT) and Aquarius
#: (own), Ketu Sagittarius (MT) and Scorpio (own; Ketu's Scorpio is exaltation in L0 and wins by precedence). Not in L0 today.
NODE_RESERVED_SIGNS = {"Rahu": frozenset({"Gemini", "Aquarius"}), "Ketu": frozenset({"Sagittarius"})}
#: the variant own signs "some learned" hold (Rāhu Virgo, Ketu Pisces): a L0 decision, classified by friendship meanwhile
NODE_VARIANT_OWN_SIGNS = {"Rahu": "Virgo", "Ketu": "Pisces"}
#: the five node pairs on which L0 and the translator's note under BPHS 3.55 (bphs:PG40:C1 [C]) disagree
NODE_FRIENDSHIP_DISPUTED = frozenset({("Rahu", "Mercury"), ("Rahu", "Mars"), ("Rahu", "Jupiter"),
                                      ("Ketu", "Sun"), ("Ketu", "Moon")})
REASON_NODE_UNCLASSIFIED = "node_dignity_unclassified"
DISCLOSE_FRIENDSHIP = "node_friendship_source_disputed"
DISCLOSE_VARIANT_OWN = "node_own_sign_variant_unresolved"


#: SR-B1-Q3C-JOB: the SIDE rule is code, not only table data. Q3(c) (ANSWERS.md v2.1 §B.4): the natural nature sets the DEFAULT side; dignity
#: and combustion override it at the extremes the texts name and ONLY there — a benefic lord goes ADVERSE when combust, debilitated or in an
#: inimical sign; a malefic lord goes FAVOURABLE when exalted, in mūlatrikoṇa or in its own sign. Every other rung (a benefic's EX/MT/OWN/FR/NEU,
#: a malefic's COMB/DEB/INI/FR/NEU) keeps the nature's side. It is defined for rule version 1.3.0 only; the 1.0.0 rows declare no table.
SIDE_RULE_VERSION = "1.3.0"
DEFAULT_SIDE = {"benefic": "favourable", "malefic": "adverse"}
BENEFIC_TURNS_ADVERSE = frozenset({"COMB", "DEB", "INI"})
MALEFIC_TURNS_FAVOURABLE = frozenset({"EX", "MT", "OWN"})


def q3c_side(nature: str, rung: str) -> str:
    """The side of a period lord of natural `nature` at effective `rung` under Q3(c) / Form B (ANSWERS.md v2.1 §B.4). The rung is already the
    effective rung (combustion > EX > MT > OWN > DEB > FR/NEU/INI), so each override is tested on it alone."""
    if nature not in NATURES:
        raise StrictInputError("nature_unknown", repr(nature))
    if rung not in RUNGS:
        raise StrictInputError("rung_unknown", repr(rung))
    if nature == "benefic" and rung in BENEFIC_TURNS_ADVERSE:
        return "adverse"
    if nature == "malefic" and rung in MALEFIC_TURNS_FAVOURABLE:
        return "favourable"
    return DEFAULT_SIDE[nature]


@dataclass(frozen=True)
class RungResult:
    """The effective rung at one instant: `rung` (None = unclassified, with `reason`) and the disclosures that qualify it."""
    rung: str | None
    reason: str | None = None
    disclosures: tuple = ()
    basis: str | None = None           # the check that decided it (the precedence step), for the audit trail


@dataclass(frozen=True)
class SideValueMapping:
    """The (natural nature, rung) -> (side, value) table, validated. Built only through `mapping_from_row` / `validate_mapping`."""
    cells: Mapping = field(compare=True)
    ref: str | None = None             # the registry row / ledger reference the cells were read from

    def side_and_value(self, nature: str, rung: str) -> tuple[str, float]:
        try:
            return self.cells[(nature, rung)]
        except KeyError:
            raise StrictInputError("mapping_cell_missing", f"{nature}/{rung}") from None


def validate_mapping(raw: Mapping, *, ref: str | None = None) -> SideValueMapping:
    """`raw` = {nature: {rung: {"side": s, "value": v}}} (extra keys such as an evidence tag are allowed). Refuses anything but
    EXACTLY the closed 2 x 8 cells, a side outside SIDES, or a value that is not a real number in (0, 1] — spec §2.3 inv 3: a
    modifier never removes a window, so no cell is 0, and a value above 1 would exceed the unit range the product assumes."""
    if not isinstance(raw, Mapping) or set(raw) != set(NATURES):
        raise StrictInputError("mapping_natures_invalid", f"expected exactly {NATURES}, got {sorted(raw) if isinstance(raw, Mapping) else raw!r}")
    cells: dict[tuple[str, str], tuple[str, float]] = {}
    for nature in NATURES:
        col = raw[nature]
        if not isinstance(col, Mapping) or set(col) != set(RUNGS):
            raise StrictInputError("mapping_rungs_invalid", f"{nature}: expected exactly {RUNGS}")
        for rung in RUNGS:
            cell = col[rung]
            side, value = cell.get("side"), cell.get("value")
            if side not in SIDES:
                raise StrictInputError("mapping_side_invalid", f"{nature}/{rung}: {side!r}")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0.0 < value <= 1.0:
                raise StrictInputError("mapping_value_invalid", f"{nature}/{rung}: {value!r} (need a real in (0, 1])")
            if side != q3c_side(nature, rung):
                # the table may not contradict the side rule it is read under: a Q3(a) table (nature alone) is refused by name
                raise StrictInputError("mapping_side_contradicts_q3c", f"{nature}/{rung}: table says {side!r}, Q3(c) says {q3c_side(nature, rung)!r}")
            cells[(nature, rung)] = (side, float(value))
    return SideValueMapping(cells=cells, ref=ref)


def mapping_from_row(row: Mapping) -> SideValueMapping:
    """The mapping a factor row declares under `category_mapping` (the precedent key, plan I-6). A row without one is a named
    missing input, never a default."""
    raw = row.get("category_mapping")
    if not raw:
        raise StrictInputError("category_mapping_undeclared", str(row.get("factor_id")))
    return validate_mapping(raw, ref=f"{row.get('factor_id')}@{row.get('rule_version')}")


#: the three soft factors that together declare the Form B table (D2): the dignity row's 14 (nature, rung) cells, the combustion row's
#: `combust` cell and the agent_nature row's default side per nature (magnitude 1 by declaration)
FORM_B_FACTORS = ("dignity_of_transit_sign", "combustion", "agent_nature")
_DIGNITY_RUNGS = tuple(r for r in RUNGS if r != "COMB")


def _unit_cell(cell, name: str) -> float:
    v = cell.get("value") if isinstance(cell, Mapping) else None
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v != 1.0:
        raise StrictInputError("form_b_neutral_element_not_one", f"{name}: {cell!r} (a declared magnitude-1 / neutral cell must be 1.0, or the "
                               "builder's product would differ from the table)")
    return 1.0


def has_form_b(factor_rows: Iterable) -> bool:
    """True iff some Form B factor row declares a `category_mapping` (the 1.0.0 rows declare none: nothing changes for them)."""
    return any(r.get("factor_id") in FORM_B_FACTORS and r.get("category_mapping") for r in factor_rows)


def mapping_from_rows(factor_rows: Iterable) -> SideValueMapping:
    """The 2 x 8 (nature, rung) -> (side, value) table the path's three Form B rows declare TOGETHER (ANSWERS.md v2.1 §B.2: "one mapping").
    `dignity_of_transit_sign` carries the seven dignity rungs per nature, `combustion` the `combust` cell (= the COMB rung, both natures) and
    the neutral element `not_combust` = 1.0, `agent_nature` the default side per nature at magnitude 1.0. The builder multiplies
    nature x dignity x combustion (the sources do), so the two neutral declarations are checked to be 1.0 here — a row that declared
    another would make this table differ from what the sweep computes."""
    by_id = {r["factor_id"]: r for r in factor_rows if r.get("factor_id") in FORM_B_FACTORS}
    for fid in FORM_B_FACTORS:
        if fid not in by_id or not by_id[fid].get("category_mapping"):
            raise StrictInputError("category_mapping_undeclared", fid)
        if by_id[fid].get("rule_version") != SIDE_RULE_VERSION:      # the side rule is Q3(c) under 1.3.0 only; no other version defines one
            raise StrictInputError("side_rule_undefined_for_version", f"{fid}@{by_id[fid].get('rule_version')!r}")
    dig, comb, nat = (by_id[f]["category_mapping"] for f in FORM_B_FACTORS)
    if not isinstance(dig, Mapping) or set(dig) != {f"{n}/{r}" for n in NATURES for r in _DIGNITY_RUNGS}:
        raise StrictInputError("mapping_rungs_invalid", "dignity_of_transit_sign: expected exactly the 14 nature/rung cells")
    if not isinstance(comb, Mapping) or set(comb) != {"combust", "not_combust"}:
        raise StrictInputError("mapping_rungs_invalid", "combustion: expected exactly combust / not_combust")
    if not isinstance(nat, Mapping) or set(nat) != set(NATURES):
        raise StrictInputError("mapping_natures_invalid", "agent_nature: expected exactly benefic / malefic")
    _unit_cell(comb["not_combust"], "combustion/not_combust")
    for n in NATURES:
        _unit_cell(nat[n], f"agent_nature/{n}")
        if nat[n].get("side") != DEFAULT_SIDE[n]:      # the agent_nature row declares the DEFAULT side: Q3(c) starts from the nature's
            raise StrictInputError("mapping_side_contradicts_q3c", f"agent_nature/{n}: table says {nat[n].get('side')!r}, the default is {DEFAULT_SIDE[n]!r}")
    raw = {n: {**{r: dict(dig[f"{n}/{r}"]) for r in _DIGNITY_RUNGS}, "COMB": dict(comb["combust"])} for n in NATURES}
    return validate_mapping(raw, ref="+".join(f"{f}@{by_id[f].get('rule_version')}" for f in FORM_B_FACTORS))


def _sign_lord(sign: str) -> str:
    # L1's table through `p1_inputs._l1()`: imported BY NAME, never by an `import` statement, so the gochara writer's executable closure (and
    # its no-commit / no-connect conformance scan) does not absorb the whole L1 condition writer — the dependency is listed in the input
    # vector's `evaluation` implementation modules instead (see `p1_inputs._l1`)
    return _l1().SIGN_LORDS[sign]


class LordRungRules:
    """The effective-rung rule for ONE period lord over validated, complete L0 rows. Constructed once per lord (validation is not
    repeated per instant); `rung` is then a pure function of (sign, degree, combust)."""

    def __init__(self, graha: str, dignity_rows: Iterable, naisargika_rows: Iterable):
        if graha not in GRAHAS:
            raise StrictInputError("graha_unknown", repr(graha))
        self.graha = graha
        dignity_rows = list(dignity_rows)
        self.ref = validated_dignity_row(dignity_rows, graha)
        if graha not in NODES:
            dignity_boundaries(graha, dignity_rows)         # L0 and L1 must agree on the mūlatrikoṇa range (refused otherwise)
        nais = validated_naisargika(naisargika_rows)
        self.friendship = {other: rel for (g, other), rel in nais.items() if g == graha}
        # an own sign L0 now DOES carry for the node is classified by L0 and is not reserved any more (see the module docstring
        # for why a node mūlatrikoṇa cannot close this way)
        self.reserved_signs = frozenset(set(NODE_RESERVED_SIGNS.get(graha, ())) - set(self.ref["own_signs"]))

    def rung(self, sign: str, degree_in_sign: float, combust: bool | None) -> RungResult:
        if sign not in SIGNS:
            raise StrictInputError("sign_unknown", repr(sign))
        if isinstance(degree_in_sign, bool) or not isinstance(degree_in_sign, (int, float)) or not 0.0 <= degree_in_sign < 30.0:
            raise StrictInputError("degree_in_sign_invalid", repr(degree_in_sign))
        ref = self.ref
        if self.graha in NODES:
            if combust:
                raise StrictInputError("node_cannot_be_combust", self.graha)   # L1 M-19: a declared non-applicability upstream
        elif not isinstance(combust, bool):
            raise StrictInputError("combust_missing_or_not_boolean", repr(combust))   # an unevaluated state is not "not combust"
        if combust:
            return RungResult("COMB", basis="combust")
        if sign == ref["exaltation_sign"]:
            return RungResult("EX", basis="exaltation_sign")
        if ref.get("moolatrikona_sign") == sign and ref["moolatrikona_from"] <= degree_in_sign < ref["moolatrikona_to"]:
            return RungResult("MT", basis="moolatrikona_range")
        if sign in ref["own_signs"]:
            return RungResult("OWN", basis="own_sign")
        if sign == ref["debilitation_sign"]:
            return RungResult("DEB", basis="debilitation_sign")
        if sign in self.reserved_signs:
            return RungResult(None, reason=REASON_NODE_UNCLASSIFIED, basis="node_reserved_sign")
        lord = _sign_lord(sign)
        rel = self.friendship.get(lord)
        if rel is None:
            raise StrictInputError("friendship_pair_missing", f"{self.graha}->{lord}")     # validated complete; unreachable unless lord == graha
        disclosures = []
        if (self.graha, lord) in NODE_FRIENDSHIP_DISPUTED:
            disclosures.append(DISCLOSE_FRIENDSHIP)
        if NODE_VARIANT_OWN_SIGNS.get(self.graha) == sign:
            disclosures.append(DISCLOSE_VARIANT_OWN)
        return RungResult(_FRIENDSHIP_RUNG[rel], disclosures=tuple(disclosures), basis=f"naisargika:{self.graha}->{lord}")


__all__ = ["BENEFIC_TURNS_ADVERSE", "DEFAULT_SIDE", "DISCLOSE_FRIENDSHIP", "FORM_B_FACTORS", "MALEFIC_TURNS_FAVOURABLE", "SIDE_RULE_VERSION", "q3c_side", "DISCLOSE_VARIANT_OWN", "LordRungRules", "NATURES", "NODES", "NODE_FRIENDSHIP_DISPUTED",
           "NODE_RESERVED_SIGNS", "NODE_VARIANT_OWN_SIGNS", "REASON_NODE_UNCLASSIFIED", "RUNGS", "RungResult", "SIDES",
           "SideValueMapping", "has_form_b", "mapping_from_row", "mapping_from_rows", "validate_mapping"]
