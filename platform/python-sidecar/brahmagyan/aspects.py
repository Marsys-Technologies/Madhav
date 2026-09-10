"""Canonical Parāśari graha-dṛṣṭi authority.

``get_graha_aspects`` is deliberately dependency-free and returns immutable
house-offset/strength mappings.  Consumers must not retain their own
graha-to-aspect table: all grahas have the universal seventh aspect; Mars,
Jupiter, Saturn, Rahu, and Ketu add their classical special aspects.

Unknown, blank, and non-string graha values deliberately fall back to the
universal seventh aspect.  That preserves the historic consumers' safe
default without inventing special aspects for malformed input.
"""
from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType


def _immutable_aspects(offsets: dict[int, float]) -> Mapping[int, float]:
    """Freeze one public aspect profile without exposing a mutable dict."""
    return MappingProxyType(dict(offsets))


UNIVERSAL_PARASHARI_ASPECTS: Mapping[int, float] = _immutable_aspects({7: 1.0})
"""The universal, full-strength seventh-house aspect."""

# Rahu/Ketu cast the same special aspects as Jupiter per BPHS parāśari
# mainstream.  Kept as a compatibility export for existing callers; it is
# immutable and is also the canonical value used by ``get_graha_aspects``.
NODE_PARASHARI_ASPECTS: Mapping[int, float] = _immutable_aspects({5: 1.0, 7: 1.0, 9: 1.0})

_GRAHA_PARASHARI_ASPECTS: Mapping[str, Mapping[int, float]] = MappingProxyType({
    "mars": _immutable_aspects({4: 1.0, 7: 1.0, 8: 1.0}),
    "jupiter": _immutable_aspects({5: 1.0, 7: 1.0, 9: 1.0}),
    "saturn": _immutable_aspects({3: 1.0, 7: 1.0, 10: 1.0}),
    "rahu": NODE_PARASHARI_ASPECTS,
    "ketu": NODE_PARASHARI_ASPECTS,
})

# The PRATIJÑĀ v4 rubric deliberately scores nodal 5th/9th contacts through
# its general fractional tiers, rather than promoting them to its named
# Mars/Jupiter/Saturn full-contact tier.  Expose this identity classification
# here so that compatibility rule does not recreate aspect authority locally.
NODAL_GRAHAS = frozenset({"rahu", "ketu"})


def get_graha_aspects(graha: object) -> Mapping[int, float]:
    """Return this graha's immutable Parāśari whole-sign aspect profile.

    Names are stripped and case-normalized.  Any unrecognized input returns
    the immutable universal seventh-aspect profile, matching the legacy
    default path while keeping malformed names from gaining a special aspect.
    """
    if not isinstance(graha, str):
        return UNIVERSAL_PARASHARI_ASPECTS
    return _GRAHA_PARASHARI_ASPECTS.get(
        graha.strip().casefold(), UNIVERSAL_PARASHARI_ASPECTS
    )
