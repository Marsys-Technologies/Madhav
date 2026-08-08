"""
graha_vocabulary.py — the SINGLE authoritative graha (planet) identifier
normalizer (ADHIṢṬHĀNA Campaign A, Lane A2; MASTER_PLAN_v1_0.md §3).

Before this module, ~13 independent Python maps each normalized graha
identifiers (short codes, long English names, Sanskrit names) to some local
convention, disagreeing subtly with each other (short codes vs Title-case vs
ALL-CAPS long names) — the root cause of a whole class of cross-layer bugs.

This module is the promoted (moved, not copied) `_GRAHA_ALIASES` +
`norm_graha()` that previously lived in `brahmagyan/valence_doctrine.py`
(the best existing resolver: accepts codes, long forms, and Sanskrit names).
`valence_doctrine.py` now imports `norm_graha` back from here so nothing
that already depends on `valence_doctrine.norm_graha` breaks (see its
re-export).

Canonical output — "system A":
  SUN MOON MAR MER JUP VEN SAT RAH_MEAN KET_MEAN LAGNA

R17 (Adoption over addition): every other Python graha map in the codebase
is retired to an import of `norm_graha` (or `to_title` where a Title-case
long-form contract is the established output, e.g. `ka_yojaka` →
`bodha_cgm_nodes.node_subject`), not duplicated. Acceptance is measured by
removal counts (census), not by this module's mere existence.
"""
from __future__ import annotations

# Graha-code normalization — consumers use varied forms (title-case names,
# 3-letter codes, RAH/RAH_MEAN, Sanskrit names). Normalize to the canonical
# subject code so every call site wires trivially regardless of its local
# vocabulary.
_GRAHA_ALIASES: dict[str, str] = {
    "SUN": "SUN", "SURYA": "SUN",
    "MOON": "MOON", "MON": "MOON", "CHANDRA": "MOON",
    "MARS": "MAR", "MAR": "MAR", "MANGALA": "MAR", "KUJA": "MAR",
    "MERCURY": "MER", "MER": "MER", "BUDHA": "MER",
    "JUPITER": "JUP", "JUP": "JUP", "GURU": "JUP",
    "VENUS": "VEN", "VEN": "VEN", "SHUKRA": "VEN",
    "SATURN": "SAT", "SAT": "SAT", "SHANI": "SAT",
    "RAHU": "RAH_MEAN", "RAH": "RAH_MEAN", "RAH_MEAN": "RAH_MEAN", "RAH_TRUE": "RAH_MEAN",
    "KETU": "KET_MEAN", "KET": "KET_MEAN", "KET_MEAN": "KET_MEAN", "KET_TRUE": "KET_MEAN",
}


def norm_graha(graha: str | None) -> str:
    """Normalize any recognized graha form → canonical subject code (or '' )."""
    if not graha:
        return ""
    return _GRAHA_ALIASES.get(str(graha).strip().upper(), str(graha).strip().upper())


# Canonical subject code → Title-case long form. Used where a producer's
# established output contract is Title-case (e.g. `ka_yojaka` writing
# `bodha_cgm_nodes.node_subject`, which stores "Mars", not "MAR") — retiring
# a local map into this SSoT must not change that contract.
_SUBJECT_TO_TITLE: dict[str, str] = {
    "SUN": "Sun",
    "MOON": "Moon",
    "MAR": "Mars",
    "MER": "Mercury",
    "JUP": "Jupiter",
    "VEN": "Venus",
    "SAT": "Saturn",
    "RAH_MEAN": "Rahu",
    "KET_MEAN": "Ketu",
    "LAGNA": "Lagna",
}


def to_title(graha: str | None) -> str:
    """Any recognized graha form → canonical Title-case long form
    (e.g. 'MAR' / 'Mars' / 'mangala' → 'Mars'). Falls back to a bare
    `.title()` of the normalized code for inputs outside the known 9
    grahas + Lagna (should not occur for well-formed graha input)."""
    code = norm_graha(graha)
    if not code:
        return ""
    return _SUBJECT_TO_TITLE.get(code, code.title())
