"""Offline Python reading of the census Ldgr citation-placeholder rule, for the citation-pass-2 tests (decision OS-2026-10-05-CITATIONS).

`scripts/governance/asset_census.py::_ldgr_lacking_text(x, citation=True)` is the SQL predicate "this citation value states no source". This module
re-implements the SAME rule in Python from the census's own constants (LDGR_PLACEHOLDERS, LDGR_CITATION_PLACEHOLDERS,
LDGR_CITATION_PLACEHOLDER_PREFIXES, _LDGR_INVISIBLE, _LDGR_SPACE), so a K1 / K2 citation column can be checked offline, with no database: after NFKC and
removal of invisible characters, junk is stripped at the ends, whitespace collapsed, case folded; the value lacks a source when it is empty, one of the
placeholders (also with spaces removed) or one of the citation-only labels (the bare 'classical_tradition', "classical tradition (Jyotish)", ...), or
starts with 'unsourced' followed by a separator, or is all-ASCII with no alphanumeric character. Kept byte-identical in the three citation-pass-2 PRs
(remedies, doshas, ontology).
"""
from __future__ import annotations

import re
import string
import sys
import unicodedata
from pathlib import Path

_GOV = Path(__file__).resolve().parents[2] / "scripts" / "governance"
if str(_GOV) not in sys.path:
    sys.path.insert(0, str(_GOV))
import asset_census as _census  # noqa: E402  (the one source of the vocabulary)

_JUNK_EXTRA = " ¡«·»¿।॥ −"


def _py_junk(ch: str) -> bool:
    o = ord(ch)
    return (ch.isspace() or ch in string.punctuation or unicodedata.category(ch).startswith("P") or ch in _JUNK_EXTRA
            or 0x2000 <= o <= 0x206f or 0x2e00 <= o <= 0x2e7f or 0x3000 <= o <= 0x303f or 0xfe00 <= o <= 0xfe6f or o == 0xfeff
            or 0xff01 <= o <= 0xff0f or 0xff1a <= o <= 0xff20)


def _normalise(x: str) -> tuple[str, str]:
    n0 = re.sub(_census._LDGR_INVISIBLE + "+", "", unicodedata.normalize("NFKC", x))
    lo, hi = 0, len(n0)
    while lo < hi and _py_junk(n0[lo]):
        lo += 1
    while hi > lo and _py_junk(n0[hi - 1]):
        hi -= 1
    norm = re.sub(r"[\s   -​    　﻿]+", " ", n0[lo:hi]).lower()
    return n0, norm


def citation_lacks_source(x) -> bool:
    """True when the citation text `x` states no source under the census rule (NULL included)."""
    if x is None:
        return True
    n0, norm = _normalise(str(x))
    words = tuple(_census.LDGR_PLACEHOLDERS) + tuple(_census.LDGR_CITATION_PLACEHOLDERS)
    if norm in words or norm.replace(" ", "") in {w.replace(" ", "") for w in words}:
        return True
    for pre in _census.LDGR_CITATION_PLACEHOLDER_PREFIXES:
        if norm.startswith(pre) and (len(norm) == len(pre) or _py_junk(norm[len(pre)])):
            return True
    return (not any(ch.isalnum() for ch in n0)) and all(ord(ch) < 0x80 for ch in n0)


def jsonb_citation_lacks_source(value) -> bool:
    """The census reading of a JSONB citation column: lacking when empty/NULL or when ANY array element has no string leaf that is a real source."""
    if value is None:
        return True
    if isinstance(value, list):
        return len(value) == 0 or any(jsonb_citation_lacks_source(v) for v in value)
    if isinstance(value, str):
        return citation_lacks_source(value)
    if isinstance(value, dict):
        leaves = list(_string_leaves(value))
        return not any(not citation_lacks_source(s) for s in leaves)
    return True


def _string_leaves(v):
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for x in v.values():
            yield from _string_leaves(x)
    elif isinstance(v, list):
        for x in v:
            yield from _string_leaves(x)
