"""P5 aṣṭakavarga qualifiers P5a..P5e (GOCHARA_DESIGN_SPECS_v1_4 §2.2 / §8,
D-RQ1, S-05).

P5a: a KNOWN ZERO in the transiting graha's own BAV is adverse — the only
ruled numeric (BPHS ch.70 vv.24-27); any nonzero comparison is `unresolved`
with the operand named (no invented threshold, no sign mean). P5b: SAV bands
>30 favourable / 25-30 medium / <25 adverse (BPHS2:42332-42335) on the
MEASURED SAV, never config (#26). P5c: disabled with the rebuild-pending
reason when the donor matrix is absent (#19, PR #2731). P5d: piṇḍa × marks
mod 27, remainder 0 ⇒ 27th nakṣatra (Revatī). Each operand gates exactly its
own form; the whole AV build absent ⇒ all forms unqualified.

Chart constants below are data with source labels: the SARVA row and the
piṇḍas trace to the pinned G-10 extracts as printed in the oracles'
constants.av_extracts and spec §2.2 P5d (tier single_pass, verbatim).
"""
from __future__ import annotations

from ..gochara_kernel.convention import KAKSHYA_CELL_DEG, KAKSHYA_LORD_ORDER

# Real SARVA per sign — extract v1_0 (sha256 312de09e…88fe83), tier
# single_pass verbatim; printed in GOCHARA_TEST_ORACLES_v1_4
# constants.av_extracts. Aquarius SARVA = 23 is fact_id 36b81039eeb707a7.
SARVA_BY_SIGN: dict[str, int] = {
    "Aries": 29, "Taurus": 29, "Gemini": 27, "Cancer": 32, "Leo": 30,
    "Virgo": 26, "Libra": 34, "Scorpio": 32, "Sagittarius": 25,
    "Capricorn": 27, "Aquarius": 23, "Pisces": 23,
}
SARVA_SOURCE = ("design/L1_ASHTAKAVARGA_EXTRACT_v1_0.json SARVA row "
                "(tier single_pass verbatim)")

# Śodhya piṇḍas this chart — extract v1_1 (sha256 e9e5d4d3…3224), spec §2.2
# P5d; bhinna + raasi checked equal to śodhita per graha by the recompute;
# pinda_sarva per-subject split flagged not recompute-covered.
SHODHYA_PINDA: dict[str, int] = {
    "Sun": 204, "Moon": 162, "Mars": 222, "Mercury": 198,
    "Jupiter": 187, "Venus": 126, "Saturn": 102,
}
PINDA_SOURCE = "design/L1_ASHTAKAVARGA_EXTRACT_v1_1.json (tier single_pass verbatim)"

# The 27 names derive from the L0 lexicon (canonical_name_en, via brahmagyan.nakshatra_vocabulary)
# and are never retyped (Ashwini = 1 ... Revati = 27). Nakshatra 5/19/23 are Mrigasira / Moola /
# Dhanishtha (this list used to say Mrigashira / Mula / Dhanishta). p6.nakshatra_index() reads
# stored names through the TOLERANT vocabulary helper, so the legacy spellings still resolve.
# The import sits beside the list it replaces, so this module's line numbers stay put.
# (Abhijit, the seed's 28th row, is not among the 27.)
from brahmagyan.nakshatra_vocabulary import CANONICAL_NAKSHATRA_NAMES  # noqa: E402
NAKSHATRAS: tuple[str, ...] = CANONICAL_NAKSHATRA_NAMES

P5C_DISABLED_REASON = ("donor rows pending the native-authorised ga_strength "
                       "rebuild (#2731)")

UNQUALIFIED = "unqualified"
UNRESOLVED = "unresolved"
DISABLED = "disabled"


def _valid_count(x) -> bool:
    """A benefic-mark count, SAV total, piṇḍa or marks figure is a non-negative
    INTEGER. A bool, string, float, NaN or negative figure is not a bindu: it is
    an invalid operand → the form is `unqualified` with the operand named,
    never a TypeError, a coerced value, or a silent band (CLAUDE.md §N.7
    item 6: an honest null beats an invented judgment)."""
    return isinstance(x, int) and not isinstance(x, bool) and x >= 0


def p5a(transiting_graha: str, sign: str, bav_by_graha: dict | None) -> dict:
    """P5a — the operand is the TRANSITING graha's own BAV (#18, O-BP-1).
    Known zero ⇒ adverse; any nonzero comparison ⇒ unresolved with the
    operand named; missing BAV rows ⇒ P5a ALONE unqualified."""
    if bav_by_graha is None or transiting_graha not in bav_by_graha:
        return {"form": "P5a", "state": UNQUALIFIED,
                "operand": f"BAV({transiting_graha})"}
    count = bav_by_graha[transiting_graha].get(sign)
    if count is None:
        return {"form": "P5a", "state": UNQUALIFIED,
                "operand": f"BAV({transiting_graha})({sign})"}
    if not _valid_count(count):
        return {"form": "P5a", "state": UNQUALIFIED,
                "operand": f"BAV({transiting_graha})({sign})",
                "reason": "invalid_operand"}
    if count == 0:
        return {"form": "P5a", "state": "adverse", "count": 0,
                "rule": "known-zero doctrine, BPHS ch.70 vv.24-27 (D-RQ1)"}
    return {"form": "P5a", "state": UNRESOLVED,
            "operand": f"BAV({transiting_graha})({sign})={count}",
            "rule": "no cited numeric threshold for a nonzero comparison "
                    "(spec §2.2 P5a)"}


def p5b(sign: str, sav_by_sign: dict | None) -> dict:
    """P5b — SAV bands >30 favourable / 25-30 medium / <25 adverse
    (BPHS2:42332-42335) on the MEASURED SAV, never config (O-BP-5)."""
    if sav_by_sign is None or sign not in sav_by_sign:
        return {"form": "P5b", "state": UNQUALIFIED, "operand": f"SAV({sign})"}
    sav = sav_by_sign[sign]
    if not _valid_count(sav):
        return {"form": "P5b", "state": UNQUALIFIED, "operand": f"SAV({sign})",
                "reason": "invalid_operand"}
    band = "favourable" if sav > 30 else "medium" if sav >= 25 else "adverse"
    return {"form": "P5b", "state": band, "sav": sav,
            "rule": "BPHS2:42332-42335"}


def p5c(donor_matrix: dict | None) -> dict:
    """P5c — fruit delivered in the kakṣyā owned by the mark-donor (PG301).
    Missing donor matrix ⇒ P5c ALONE disabled, rebuild-pending (O-BP-2 case
    B); P5a/P5b stand untouched (S-05.2)."""
    if donor_matrix is None:
        return {"form": "P5c", "state": DISABLED, "reason": P5C_DISABLED_REASON}
    return {"form": "P5c", "state": "enabled"}


def kakshya_of(deg_in_sign: float) -> tuple[int, str]:
    """Kakṣyā division (PG301 śl.18-19; equal-eighths grid): 1-based cell
    index and its lord from the declared order Saturn, Jupiter, Mars, Sun,
    Venus, Mercury, Moon, Lagna."""
    idx = int(deg_in_sign // KAKSHYA_CELL_DEG)
    idx = min(idx, 7)
    return idx + 1, KAKSHYA_LORD_ORDER[idx]


def p5c_resolve_donor(deg_in_sign: float, donor_matrix: dict | None) -> dict:
    """Resolve the delivering kakṣyā through the declared donor key (O-BP-4):
    the donor's benefic mark in that division. A key-mismatched lookup fails;
    a sign-level fallback is a 'coarser P5a qualification', never donor
    evaluation (#19)."""
    if donor_matrix is None:
        return p5c(None)
    cell, lord = kakshya_of(deg_in_sign)
    if lord not in donor_matrix:
        return {"form": "P5c", "state": UNRESOLVED,
                "operand": f"donor mark of {lord} in kakṣyā {cell}"}
    return {"form": "P5c", "state": "resolved", "kakshya": cell,
            "kakshya_lord": lord, "donor_mark": donor_matrix[lord]}


def p5d(pinda: int | None, marks: int | None) -> dict:
    """P5d — śodhya-piṇḍa × marks mod 27 → nakṣatra (PG304/PG307); integer
    product, remainder 0 ⇒ the 27th nakṣatra (Revatī)."""
    if pinda is None or marks is None:
        return {"form": "P5d", "state": UNQUALIFIED,
                "operand": "pinda" if pinda is None else "marks"}
    if not _valid_count(pinda) or not _valid_count(marks):
        return {"form": "P5d", "state": UNQUALIFIED,
                "operand": "pinda" if not _valid_count(pinda) else "marks",
                "reason": "invalid_operand"}
    remainder = (int(pinda) * int(marks)) % 27
    index = 27 if remainder == 0 else remainder
    return {"form": "P5d", "state": "resolved", "remainder": remainder,
            "nakshatra_index": index, "nakshatra": NAKSHATRAS[index - 1]}


def p5e(ingress_substrate=None) -> dict:
    """P5e — Sun-month selection only where the rule says so (BPHS ch.70);
    no extension to other agents."""
    if ingress_substrate is None:
        return {"form": "P5e", "state": UNQUALIFIED,
                "operand": "solar ingress substrate"}
    return {"form": "P5e", "state": "resolved"}


def qualify_transit(transiting_graha: str, sign: str, *,
                    av_build_present: bool = True,
                    bav_by_graha: dict | None = None,
                    sav_by_sign: dict | None = None,
                    donor_matrix: dict | None = None,
                    pinda: int | None = None, marks: int | None = None,
                    ingress_substrate=None) -> dict:
    """All five forms for one transit, per the §2.2 missing-input matrix:
    each operand gates exactly its own form; the whole AV build absent ⇒ ALL
    forms unqualified (the only cross-form case, O-BP-2 case A)."""
    if not av_build_present:
        return {f: {"form": f, "state": UNQUALIFIED, "operand": "AV build"}
                for f in ("P5a", "P5b", "P5c", "P5d", "P5e")}
    return {
        "P5a": p5a(transiting_graha, sign, bav_by_graha),
        "P5b": p5b(sign, sav_by_sign),
        "P5c": p5c(donor_matrix),
        "P5d": p5d(pinda, marks),
        "P5e": p5e(ingress_substrate),
    }


# ── typed operand evidence + the AM-7 declaration read-back (O-BP-3) ─────────
BINDU_UNIT = "bindus"


class DeclarationReadBackRefused(ValueError):
    """AM-7: the writer's read-back of the consumed AV polarity declaration
    failed — the P5 record CANNOT be written. `reason` is one of:
    declarations_unavailable, declaration_absent, category_not_governed,
    operand_missing_from_extract, bindu_mismatch. Raised loudly; never a
    stored `false`/`unknown` (draft §AM-7, PREREQUISITE_EVALUATION_ANSWER)."""

    def __init__(self, reason: str, detail: dict):
        self.reason = reason
        self.detail = detail
        super().__init__(f"P5 declaration read-back refused: {reason} {detail}")


def typed_operands(transiting_graha: str, sign: str, *,
                   bav_by_graha: dict | None = None,
                   sav_by_sign: dict | None = None) -> list[dict]:
    """The bindu operands a P5 transit reads, with the SELECTION rule pinned:
    P5a reads the TRANSITING graha's OWN BAV in that sign (#18, O-BP-1 — never
    another graha's row, never the SAV); P5b reads the SAV of that sign (#26).
    Both are returned when both exist (competing BAV/SAV operands are both
    recorded, AM-7 (b)); a missing operand is simply absent — each form's
    missingness is independent (§2.2 matrix)."""
    ops: list[dict] = []
    own = (bav_by_graha or {}).get(transiting_graha)
    if own is not None and own.get(sign) is not None:
        ops.append({"kind": "BAV", "graha": transiting_graha, "sign": sign,
                    "value": own[sign], "unit": BINDU_UNIT, "form": "P5a"})
    if sav_by_sign is not None and sav_by_sign.get(sign) is not None:
        ops.append({"kind": "SAV", "graha": None, "sign": sign,
                    "value": sav_by_sign[sign], "unit": BINDU_UNIT, "form": "P5b"})
    return ops


def consume_declaration(declarations: dict | None, key: str, category: str,
                        operands: list[dict], extract: dict | None) -> dict:
    """The writer-side O-BP-3 / AM-7 read-back, as an evaluator path.

    Refuses (raises DeclarationReadBackRefused) when: the declaration set is
    unavailable; the named declaration key is ABSENT; the operands' fact
    category is NOT in the declaration's `applies_to_fact_categories`; an
    operand is missing from the L1 extract the declaration governs; or a
    recorded bindu figure DISAGREES with that extract. On success returns the
    accepted binding with typed evidence (value, unit 'bindus', provenance
    copied through) — evidence only, never a score.

    declarations = {key: {"applies_to_fact_categories": [...], ...}}
    extract      = {"BAV": {graha: {sign: int}}, "SAV": {sign: int}}
    """
    if declarations is None:
        raise DeclarationReadBackRefused("declarations_unavailable", {"key": key})
    row = declarations.get(key)
    if row is None:
        raise DeclarationReadBackRefused("declaration_absent", {"key": key})
    if category not in row.get("applies_to_fact_categories", []):
        raise DeclarationReadBackRefused(
            "category_not_governed",
            {"key": key, "category": category,
             "governed": list(row.get("applies_to_fact_categories", []))})
    evidence = []
    for op in operands:
        kind, sign = op["kind"], op["sign"]
        if kind == "BAV":
            stored = ((extract or {}).get("BAV", {}).get(op.get("graha"), {})
                      .get(sign))
        elif kind == "SAV":
            stored = (extract or {}).get("SAV", {}).get(sign)
        else:
            raise DeclarationReadBackRefused("operand_missing_from_extract",
                                             {"operand": op})
        if stored is None:
            raise DeclarationReadBackRefused("operand_missing_from_extract",
                                             {"operand": op})
        if op.get("value") != stored:
            raise DeclarationReadBackRefused(
                "bindu_mismatch",
                {"kind": kind, "graha": op.get("graha"), "sign": sign,
                 "recorded": op.get("value"), "extract": stored})
        evidence.append({"scored": False, "kind": "typed_operand_evidence",
                         "operand": kind, "graha": op.get("graha"),
                         "sign": sign, "value": stored, "unit": BINDU_UNIT,
                         **{k: op[k] for k in ("fact_id", "build_id", "form")
                            if k in op}})
    return {"state": "accepted", "declaration": key, "governs": category,
            "convention": row.get("convention", key), "evidence": evidence}
