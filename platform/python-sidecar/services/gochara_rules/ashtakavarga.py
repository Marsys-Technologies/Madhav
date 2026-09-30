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

NAKSHATRAS: tuple[str, ...] = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
)

P5C_DISABLED_REASON = ("donor rows pending the native-authorised ga_strength "
                       "rebuild (#2731)")

UNQUALIFIED = "unqualified"
UNRESOLVED = "unresolved"
DISABLED = "disabled"


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
