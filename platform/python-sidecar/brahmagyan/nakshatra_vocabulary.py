"""
nakshatra_vocabulary.py -- the single Python source of the 27 nakshatra NAMES and the ONE normaliser
that turns any registered spelling into the canonical one.

CANONICAL FAMILY AND AUTHORITY. The canonical spelling is the L0 lexicon's: `name_en` of the
`bg_nakshatra` seed (`brahmagyan.l0_nakshatra.NAKSHATRAS_ENRICHED`, written to
`reference_nakshatra.name_en` by `l0_nakshatra.seed_nakshatra()`), which is also the
`canonical_name_en` of the L0 ontology (`brahmagyan.l0_ontology.NAK_DATA`). Three of the 27 are
spelled differently from the way the L1 name table (`pyjhora_adapter._names`) writes them:

    no.  5  canonical "Mrigasira"   (the L1 adapter writes "Mrigashira")
    no. 19  canonical "Moola"       (the L1 adapter writes "Mula")
    no. 23  canonical "Dhanishtha"  (the L1 adapter writes "Dhanishta")

SS N-548 (narrow shape): the canonical spelling is applied at the vocabulary / emitter boundary. The
ga_* writers that EMIT a nakshatra name pass the adapter's string through `normalize_nakshatra()`
before it reaches chart_facts; `pyjhora_adapter._names`, `pipeline.transit_search` and
`services.ka_graha_sancara.engine` are left byte-identical (unifying them at source waits for the
next naturally full rebuild). Every L1/L2/L3 table that names a nakshatra derives from
`CANONICAL_NAKSHATRA_NAMES` (CLAUDE.md §N.5 / §N.7 item 3: no wrapper-local constant shadows a
canonical value), and every lookup BY NAME goes through the normaliser: no raw `.index(name)`, no
`.get(name, 0)`.

THE NORMALISER. `normalize_nakshatra(name)` maps a registered spelling -- the canonical name, the
lexicon's `alt_names` and IAST name, the ontology's `canonical_name_sa` and synonyms, or one of the
three legacy L1 spellings -- onto the canonical name, ignoring case, whitespace, underscores, hyphens
and combining diacritics. It RAISES `UnknownNakshatraError` (a ValueError) for anything else: never a
silent default, never index 0 / Ashwini (CLAUDE.md §N.7 item 6, B.10). `nakshatra_index()` is the same
lookup returning the 1-based number. `canonical_nakshatra()` / `nakshatra_number()` are the Optional
forms (None instead of raising) for the few readers that must FLAG an unresolved name rather than
abort (e.g. kala_permission's `tara_unresolved`); they are thin wrappers on the normaliser, not a
second table.

This module imports only pure-data L0 seed modules (no database, no writer).
"""
from __future__ import annotations

import unicodedata
from types import MappingProxyType
from typing import Mapping

from brahmagyan.l0_nakshatra import NAKSHATRAS_ENRICHED
from brahmagyan.l0_ontology import NAK_DATA

#: The 27 canonical names, index 0 = Ashwini (nakshatra no. 1) ... index 26 = Revati (no. 27).
#: Abhijit (the 28th row of the seed) is not one of the 27.
CANONICAL_NAKSHATRA_NAMES: tuple[str, ...] = tuple(
    row["name_en"]
    for row in sorted(NAKSHATRAS_ENRICHED, key=lambda r: r["nakshatra_id"])
    if 1 <= row["nakshatra_id"] <= 27
)
if len(CANONICAL_NAKSHATRA_NAMES) != 27 or len(set(CANONICAL_NAKSHATRA_NAMES)) != 27:  # pragma: no cover
    raise RuntimeError("bg_nakshatra seed must carry 27 distinct nakshatra names")

#: The spellings the L1 name table (`pyjhora_adapter._names.NAKSHATRA_NAMES`) writes for nakshatras
#: 5 / 19 / 23, mapped to the canonical spelling: the emit-side fold in the ga_* writers, the read-side
#: tolerance for facts stored before those writers canonicalised, and the three extra names migration
#: 1364 lets bo_nakshatra_semantic's integrity check accept. Each is ALSO a registered alias of the
#: lexicon / ontology (asserted at import below); this dict only names the three explicitly.
LEGACY_L1_SPELLINGS: dict[str, str] = {
    "Mrigashira": "Mrigasira",
    "Mula": "Moola",
    "Dhanishta": "Dhanishtha",
}


class UnknownNakshatraError(ValueError):
    """The name is not a registered spelling of any of the 27 nakshatras."""


def _fold(name: str) -> str:
    """NFKD-decompose, drop combining marks, case-fold, keep alphanumerics only -- so 'Purva Phalguni',
    'PurvaPhalguni', 'purva_phalguni' and 'Pūrva Phalgunī' share one key."""
    decomposed = unicodedata.normalize("NFKD", str(name))
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return "".join(c for c in stripped.casefold() if c.isalnum())


def _build_synonyms() -> dict[str, str]:
    """folded spelling -> canonical name, from the lexicon and the ontology; fails loudly on ambiguity."""
    table: dict[str, str] = {}
    sources: dict[str, str] = {}

    def add(spelling: object, canonical: str, source: str) -> None:
        if not isinstance(spelling, str):
            return
        key = _fold(spelling)
        if not key:
            return
        if key in table and table[key] != canonical:
            raise RuntimeError(
                f"nakshatra spelling {spelling!r} ({source}) would resolve to both {table[key]!r} "
                f"({sources[key]}) and {canonical!r}: the alias map must be unambiguous")
        table.setdefault(key, canonical)
        sources.setdefault(key, source)

    by_id = {row["nakshatra_id"]: row for row in NAKSHATRAS_ENRICHED if 1 <= row["nakshatra_id"] <= 27}
    for _nid, row in sorted(by_id.items()):
        canon = row["name_en"]
        add(canon, canon, "lexicon name_en")
        add(row.get("name_sa_iast"), canon, "lexicon name_sa_iast")
        for alt in row.get("alt_names") or ():
            add(alt, canon, "lexicon alt_names")
    for nid, name_en, name_sa, synonyms in NAK_DATA:
        canon = by_id[nid]["name_en"]
        if name_en != canon:  # pragma: no cover
            raise RuntimeError(f"l0_ontology.NAK_DATA names nakshatra {nid} {name_en!r}; the lexicon says {canon!r}")
        add(name_sa, canon, "ontology canonical_name_sa")
        for syn in synonyms:
            add(syn, canon, "ontology synonym")
    for legacy, canon in LEGACY_L1_SPELLINGS.items():
        if table.get(_fold(legacy)) != canon:  # pragma: no cover
            raise RuntimeError(f"legacy L1 spelling {legacy!r} is not a registered alias of {canon!r} in the lexicon / ontology")
    return table


_SYNONYMS: dict[str, str] = _build_synonyms()

#: Read-only view of the alias map (folded spelling -> canonical name), for tests and reports.
NAKSHATRA_SYNONYMS: Mapping[str, str] = MappingProxyType(_SYNONYMS)

_INDEX_BY_CANONICAL: dict[str, int] = {n: i + 1 for i, n in enumerate(CANONICAL_NAKSHATRA_NAMES)}


def normalize_nakshatra(name: object) -> str:
    """THE normaliser: the canonical spelling of a registered nakshatra spelling.

    Raises TypeError for a non-string and UnknownNakshatraError (a ValueError) for a string that is
    not a registered spelling of one of the 27 -- never a default."""
    if not isinstance(name, str):
        raise TypeError(f"nakshatra name must be a string, got {type(name).__name__}")
    canon = _SYNONYMS.get(_fold(name))
    if canon is None:
        raise UnknownNakshatraError(f"unknown nakshatra name {name!r}: not a registered spelling of any of the 27")
    return canon


def nakshatra_index(name: object) -> int:
    """The 1-based nakshatra number (1..27) of a registered spelling; raises like `normalize_nakshatra`."""
    return _INDEX_BY_CANONICAL[normalize_nakshatra(name)]


def canonical_nakshatra(name: object) -> str | None:
    """Optional form of `normalize_nakshatra`: None (never a guess) for a non-string or an unknown name."""
    try:
        return normalize_nakshatra(name)
    except (TypeError, UnknownNakshatraError):
        return None


def nakshatra_number(name: object) -> int | None:
    """Optional form of `nakshatra_index`: None for a non-string or an unknown name."""
    canon = canonical_nakshatra(name)
    return None if canon is None else _INDEX_BY_CANONICAL[canon]
