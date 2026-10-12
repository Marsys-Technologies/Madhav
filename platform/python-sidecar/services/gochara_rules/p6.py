"""P6 — Moon channel operators (GOCHARA_DESIGN_SPECS_v1_4 §2.2 P6).

Every P6 operator is `testimony` (D-PADMIT, S-04): annotate only, never
weight, gate, or admit, until the promotion gate (§2.2, B5.4 ablation
evidence) fires. Day rows come only from this path (M-3), on demand inside
admitted windows, with its own coverage record.

Tārā nine-fold (MC PG67/PG79 [D]): zero-based inclusive cyclic distance from
the janma-nakṣatra; nine-fold class = count mod 9 (0 ⇒ 9). Fixture: natal
star index 24, transit index 20 ⇒ count 24 ⇒ class 6 (O-P6-TARA).

Chandrāṣṭama is ABSENT as a generic rule (predicate count 0) — context-bound
8th-from-Moon rules only.
"""
from __future__ import annotations

from brahmagyan.nakshatra_vocabulary import UnknownNakshatraError, nakshatra_index as _nakshatra_index

from .ashtakavarga import NAKSHATRAS

TARA_CLASSES = {
    1: "janma", 2: "sampat", 3: "vipat", 4: "kshema", 5: "pratyari",
    6: "sadhaka", 7: "vadha", 8: "mitra", 9: "ati_mitra",
}
# Names per the standard nine-fold tārā table; class NUMBER is the pinned
# assertion surface (O-P6-TARA asserts the class, tolerance exact).

CHANDRASHTAMA_GENERIC_RULE = None  # absent as a generic rule (predicate count 0)


def nakshatra_index(name: str) -> int:
    """The 1-based nakṣatra number (1..27) of a nakṣatra name, resolved by the vocabulary's ONE
    normaliser (SS N-548): the canonical names, the legacy-L1 spellings and the lexicon / ontology
    aliases, ignoring case, whitespace / punctuation and combining diacritics. A name that is not a
    registered spelling raises ValueError — a null key must never reach `tara()` (defect #5, the
    case-mismatch null); a non-string raises TypeError."""
    if not isinstance(name, str):
        raise TypeError(f"nakṣatra name must be a string, got {type(name).__name__}")
    try:
        return _nakshatra_index(name)
    except UnknownNakshatraError as exc:
        raise ValueError(f"unknown nakṣatra name {name!r}: no registered spelling matches") from exc


def tara(natal_star_index: int, transit_star_index: int) -> dict:
    """Nine-fold tārā. Indices are 1-based nakṣatra numbers (1..27).
    count = zero-based inclusive cyclic distance from the natal star;
    class = count mod 9, with 0 ⇒ 9."""
    if not (1 <= natal_star_index <= 27 and 1 <= transit_star_index <= 27):
        raise ValueError("nakṣatra indices are 1..27")
    count = (transit_star_index - natal_star_index) % 27 + 1
    klass = count % 9 or 9
    return {"operator": "tara", "count": count, "class": klass,
            "class_name": TARA_CLASSES[klass],
            "operator_role": "testimony", "ruling_ref": "D-PADMIT",
            "weight": 0.0,  # testimony annotates; it never weights (S-04)
            "source": "MC PG67/PG79 [D]"}


def annotate(window: dict, term: dict) -> dict:
    """P6 testimony annotates an admitted day row; the annotation carries no
    weight and moves no score."""
    if term.get("operator_role") != "testimony":
        raise ValueError("P6 operators are testimony-only (D-PADMIT)")
    annotations = list(window.get("annotations", []))
    annotations.append(term)
    return {**window, "annotations": annotations}
