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

import unicodedata

from brahmagyan.nakshatra_vocabulary import nakshatra_number

from .ashtakavarga import NAKSHATRAS

TARA_CLASSES = {
    1: "janma", 2: "sampat", 3: "vipat", 4: "kshema", 5: "pratyari",
    6: "sadhaka", 7: "vadha", 8: "mitra", 9: "ati_mitra",
}
# Names per the standard nine-fold tārā table; class NUMBER is the pinned
# assertion surface (O-P6-TARA asserts the class, tolerance exact).

CHANDRASHTAMA_GENERIC_RULE = None  # absent as a generic rule (predicate count 0)


def _normalise_name(text: str) -> str:
    """NFKD-decompose, drop combining marks, case-fold, keep alphanumerics only
    (IDENTITY_CANONICAL_BYTES_CONTRACT_v1_0 §5)."""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return "".join(c for c in stripped.casefold() if c.isalnum())


# Exact-match table: the normalised form of each of the 27 CANONICAL names in
# ashtakavarga.NAKSHATRAS (Ashwini = 1 … Revati = 27). The ONLY aliases are the three
# legacy-L1 spellings (Mrigashira/Mula/Dhanishta), resolved by the vocabulary helper below.
_NAKSHATRA_BY_KEY: dict[str, int] = {
    _normalise_name(name): index for index, name in enumerate(NAKSHATRAS, start=1)}
assert len(_NAKSHATRA_BY_KEY) == 27, "canonical nakshatra names must normalise to 27 distinct keys"


def nakshatra_index(name: str) -> int:
    """The 1-based nakṣatra number (1..27) of a canonical nakṣatra name, matched
    EXACTLY after normalisation (case, whitespace/punctuation and combining
    diacritics are ignored). A name that does not match a canonical name raises
    ValueError — a null key must never reach `tara()` (defect #5, the case-mismatch
    null); a non-string raises TypeError."""
    if not isinstance(name, str):
        raise TypeError(f"nakṣatra name must be a string, got {type(name).__name__}")
    key = _normalise_name(name)
    if key in _NAKSHATRA_BY_KEY:
        return _NAKSHATRA_BY_KEY[key]
    if (number := nakshatra_number(name)) is not None:  # legacy-L1 spelling -> canonical number
        return number
    raise ValueError(f"unknown nakṣatra name {name!r} (normalised {key!r}): "
                     "no canonical name matches")


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
