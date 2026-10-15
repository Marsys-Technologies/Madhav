"""Shared canonical Title-case graha name for graha-VALUED chart_facts text (SS N-305).

The L0 reference tables store a nakshatra / pada lord as a lowercase id ('jupiter', 'ketu', legacy
'rahu_mean'); every other graha-valued column of chart_facts uses the released Title name ('Jupiter').
One helper for every emitter so the rule cannot drift between writers. It FAILS CLOSED: a token that is
not a recognised graha is returned UNCHANGED (never silently title-cased into a plausible-looking name).
"""
from __future__ import annotations

from brahmagyan.graha_vocabulary import graha_subject_code, to_title

_LEGACY_SUFFIX = "_mean"


def canonical_graha_title(value: object) -> str:
    """Released Title-case graha name for a recognised graha id/name; the original text otherwise."""
    text = str(value)
    base = text[: -len(_LEGACY_SUFFIX)] if text.lower().endswith(_LEGACY_SUFFIX) else text
    try:
        graha_subject_code(base)
    except ValueError:
        return text
    return to_title(base) or text
