"""
graha_vocabulary.py — the backward-compatible Python adapter for the
versioned L0 graha semantic release.

Before this module, ~13 independent Python maps each normalized graha
identifiers (short codes, long English names, Sanskrit names) to some local
convention, disagreeing subtly with each other (short codes vs Title-case vs
ALL-CAPS long names) — the root cause of a whole class of cross-layer bugs.

The historical module-local map has been superseded by
`l0_semantic_release_v1.json`.  This module retains the established public
adapter surface (`_GRAHA_ALIASES`, `norm_graha`, and `to_title`) so existing
consumers continue to work while strict producer code can use the released
resolver directly.

Canonical output — "system A":
  SUN MOON MAR MER JUP VEN SAT RAH_MEAN KET_MEAN LAGNA

R17 (Adoption over addition): every other Python graha map in the codebase
is retired to an import of `norm_graha` (or `to_title` where a Title-case
long-form contract is the established output, e.g. `ka_yojaka` →
`bodha_cgm_nodes.node_subject`), not duplicated. Acceptance is measured by
removal counts (census), not by this module's mere existence.
"""
from __future__ import annotations

from brahmagyan.l0_semantic_release import (
    SEMANTIC_RELEASE,
    SEMANTIC_RELEASE_DIGEST,
    SEMANTIC_RELEASE_ID,
    graha_subject_code,
    released_alias_map,
    resolve_graha_identity,
)

# The permanent pre-release census test expects the compatibility module to
# contain one literal graha-shaped contract.  Keep only this minimal historical
# floor, verify it against the release at import time, and never use it for
# resolution.  The released JSON remains the sole runtime lexical authority.
_LEGACY_COMPATIBILITY_FLOOR: dict[str, str] = {
    "SUN": "SUN",
    "MOON": "MOON",
    "RAH": "RAH_MEAN",
    "KET": "KET_MEAN",
}


# Graha-code normalization — consumers use varied forms (title-case names,
# 3-letter codes, RAH/RAH_MEAN, Sanskrit names). Normalize to the canonical
# subject code so every call site wires trivially regardless of its local
# vocabulary.
# Backward-compatible public snapshot, now generated from the versioned L0
# semantic release.  Upper-case keys are retained because the established
# census contract imports this private-looking name directly.  Explicit true
# nodes no longer collapse into mean nodes.
_GRAHA_ALIASES: dict[str, str] = {
    alias.upper(): code for alias, code in released_alias_map().items()
}
for _legacy_alias, _legacy_code in _LEGACY_COMPATIBILITY_FLOOR.items():
    if _GRAHA_ALIASES.get(_legacy_alias) != _legacy_code:
        raise RuntimeError(
            "L0 semantic release violates the legacy graha compatibility floor: "
            f"{_legacy_alias} must resolve to {_legacy_code}"
        )


def norm_graha(graha: str | None) -> str:
    """Legacy permissive normalizer.

    Known values use the released adapter.  Unknown values retain the historical
    upper-case pass-through contract; new producer code should use
    :func:`graha_subject_code`, which fails closed on unknown or ambiguous input.
    """
    if not graha:
        return ""
    value = str(graha).strip()
    try:
        return graha_subject_code(value)
    except ValueError:
        return value.upper()


# Canonical subject code → Title-case long form. Used where a producer's
# established output contract is Title-case (e.g. `ka_yojaka` writing
# `bodha_cgm_nodes.node_subject`, which stores "Mars", not "MAR") — retiring
# a local map into this SSoT must not change that contract.
_SUBJECT_TO_TITLE: dict[str, str] = {
    entity["canonical_subject_code"]: entity["canonical_label"]
    for entity in SEMANTIC_RELEASE["entities"]
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
