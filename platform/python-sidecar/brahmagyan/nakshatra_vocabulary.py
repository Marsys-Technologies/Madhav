"""
nakshatra_vocabulary.py -- tolerant readers for the 27 nakshatra NAMES.

The canonical spelling is the L0 lexicon's: `name_en` of the `bg_nakshatra` seed
(`brahmagyan.l0_nakshatra.NAKSHATRAS_ENRICHED`). Three of the 27 are spelled differently by the
L1 name table (`pyjhora_adapter._names`) and by some writers' local 27-name tables:

    no.  5  canonical "Mrigasira"   (also written "Mrigashira")
    no. 19  canonical "Moola"       (also written "Mula")
    no. 23  canonical "Dhanishtha"  (L1 writes "Dhanishta"; some local tables "Dhanishtha")

`canonical_nakshatra()` / `nakshatra_number()` are READ-side tolerant: they fold those spellings
(and case / whitespace / underscore variants) onto the canonical name, so an exact-match lookup in a
local table no longer silently misses a Moon in nakshatra 5, 19 or 23. They never change a stored
spelling and return None, never a guess, for a name that is not one of the 27 (CLAUDE.md §N.7 item 6).

Imports only the pure-data L0 seed module (no database, no writer).
"""
from __future__ import annotations

from brahmagyan.l0_nakshatra import NAKSHATRAS_ENRICHED

#: The 27 canonical names, index 0 = Ashwini (no. 1) ... index 26 = Revati (no. 27). Abhijit (the
#: 28th seed row) is not one of the 27.
CANONICAL_NAKSHATRA_NAMES: tuple[str, ...] = tuple(
    row["name_en"]
    for row in sorted(NAKSHATRAS_ENRICHED, key=lambda r: r["nakshatra_id"])
    if 1 <= row["nakshatra_id"] <= 27
)
if len(CANONICAL_NAKSHATRA_NAMES) != 27 or len(set(CANONICAL_NAKSHATRA_NAMES)) != 27:  # pragma: no cover
    raise RuntimeError("bg_nakshatra seed must carry 27 distinct nakshatra names")

#: Alternate spellings in circulation (L1 `_names.py`, writers' local tables) -> canonical spelling.
ALTERNATE_SPELLINGS: dict[str, str] = {
    "Mrigashira": "Mrigasira",
    "Mula": "Moola",
    "Dhanishta": "Dhanishtha",
}


def _fold(name: str) -> str:
    return " ".join(str(name).replace("_", " ").split()).casefold()


_BY_FOLDED: dict[str, str] = {_fold(n): n for n in CANONICAL_NAKSHATRA_NAMES}
_BY_FOLDED.update({_fold(old): new for old, new in ALTERNATE_SPELLINGS.items()})


def canonical_nakshatra(name: object) -> str | None:
    """The canonical spelling of a nakshatra name (canonical or alternate spelling, any case, any
    whitespace / underscore variant), or None when the name is not one of the 27."""
    if not isinstance(name, str):
        return None
    return _BY_FOLDED.get(_fold(name))


def nakshatra_number(name: object) -> int | None:
    """The 1-based nakshatra number (1..27) of a name `canonical_nakshatra` resolves, else None."""
    canon = canonical_nakshatra(name)
    return None if canon is None else CANONICAL_NAKSHATRA_NAMES.index(canon) + 1
