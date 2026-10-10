"""
nakshatra_vocabulary.py -- the single Python source of the 27 nakshatra NAMES.

The canonical spelling is the L0 lexicon's: `name_en` of the `bg_nakshatra` seed
(`brahmagyan.l0_nakshatra.NAKSHATRAS_ENRICHED`), which is also the
`canonical_name_en` of the L0 ontology (`brahmagyan.l0_ontology.NAK_DATA`). Three of the
27 are spelled differently from the way the L1 name table used to spell them:

    no.  5  canonical "Mrigasira"   (L1 used to write "Mrigashira")
    no. 19  canonical "Moola"       (L1 used to write "Mula")
    no. 23  canonical "Dhanishtha"  (L1 used to write "Dhanishta")

Every L1/L2 table that names a nakshatra derives from `CANONICAL_NAKSHATRA_NAMES`
(CLAUDE.md §N.5 / §N.7 item 3: no wrapper-local constant shadows a canonical value) instead of
keeping its own 27-string literal that can drift. `canonical_nakshatra()` /
`nakshatra_number()` are TOLERANT readers: they fold the legacy L1 spellings (and case /
whitespace variants) onto the canonical name, so a reader that meets a stored fact written before
the single rebuild that adopts the canonical spelling still resolves it. They return None, never a
guess, for a name that is not one of the 27 (§N.7 item 6).

This module imports only the pure-data L0 seed module (no database, no writer).
"""
from __future__ import annotations

from brahmagyan.l0_nakshatra import NAKSHATRAS_ENRICHED

#: The 27 canonical names, index 0 = Ashwini (nakshatra no. 1) ... index 26 = Revati (no. 27).
#: Abhijit (the 28th row of the seed) is not one of the 27.
CANONICAL_NAKSHATRA_NAMES: tuple[str, ...] = tuple(
    row["name_en"]
    for row in sorted(NAKSHATRAS_ENRICHED, key=lambda r: r["nakshatra_id"])
    if 1 <= row["nakshatra_id"] <= 27
)
if len(CANONICAL_NAKSHATRA_NAMES) != 27 or len(set(CANONICAL_NAKSHATRA_NAMES)) != 27:  # pragma: no cover
    raise RuntimeError("bg_nakshatra seed must carry 27 distinct nakshatra names")

#: Spellings the L1 name table (`pyjhora_adapter._names`) wrote before it adopted the lexicon, mapped
#: to the canonical spelling. Read-side tolerance only: no writer emits these any more.
LEGACY_L1_SPELLINGS: dict[str, str] = {
    "Mrigashira": "Mrigasira",
    "Mula": "Moola",
    "Dhanishta": "Dhanishtha",
}


def _fold(name: str) -> str:
    return " ".join(str(name).replace("_", " ").split()).casefold()


_BY_FOLDED: dict[str, str] = {_fold(n): n for n in CANONICAL_NAKSHATRA_NAMES}
_BY_FOLDED.update({_fold(old): new for old, new in LEGACY_L1_SPELLINGS.items()})


def canonical_nakshatra(name: object) -> str | None:
    """The canonical spelling of a nakshatra name (a canonical or legacy-L1 spelling, any case,
    any whitespace / underscore variant), or None when the name is not one of the 27."""
    if not isinstance(name, str):
        return None
    return _BY_FOLDED.get(_fold(name))


def nakshatra_number(name: object) -> int | None:
    """The 1-based nakshatra number (1..27) of a name `canonical_nakshatra` resolves, else None."""
    canon = canonical_nakshatra(name)
    return None if canon is None else CANONICAL_NAKSHATRA_NAMES.index(canon) + 1
