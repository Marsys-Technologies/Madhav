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

from .p1_inputs import (GRAHAS, SIGNS, StrictInputError, dignity_boundaries, validated_dignity_row,
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
            cells[(nature, rung)] = (side, float(value))
    return SideValueMapping(cells=cells, ref=ref)


def mapping_from_row(row: Mapping) -> SideValueMapping:
    """The mapping a factor row declares under `category_mapping` (the precedent key, plan I-6). A row without one is a named
    missing input, never a default."""
    raw = row.get("category_mapping")
    if not raw:
        raise StrictInputError("category_mapping_undeclared", str(row.get("factor_id")))
    return validate_mapping(raw, ref=f"{row.get('factor_id')}@{row.get('rule_version')}")


def _sign_lord(sign: str) -> str:
    import ga_writers.ga_condition_writer as l1     # lazy, as p1_inputs: it pulls psycopg and the engine adapter
    return l1.SIGN_LORDS[sign]


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


__all__ = ["DISCLOSE_FRIENDSHIP", "DISCLOSE_VARIANT_OWN", "LordRungRules", "NATURES", "NODES", "NODE_FRIENDSHIP_DISPUTED",
           "NODE_RESERVED_SIGNS", "NODE_VARIANT_OWN_SIGNS", "REASON_NODE_UNCLASSIFIED", "RUNGS", "RungResult", "SIDES",
           "SideValueMapping", "mapping_from_row", "validate_mapping"]
