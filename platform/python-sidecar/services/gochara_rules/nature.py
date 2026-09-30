"""Agent nature and naisargika maitrī (PROMISE_NATURE_YOGA_MAP_v1_1 §2–§3;
BPHS ch.3 śl.11 PG26:C1 and śl.55–58 PG39:C1–PG40:C2, all [D]).

Interpretive modifiers only — they assign channel/valence and rank, never
admit, exclude, or zero (spec §2.3 inv 3). Node maitrī is NOT included: the
PG40:C1 Rahu/Ketu lists are the translator's appended note, not a Parāśari
śloka — node relationship modifiers stay `unqualified` pending a
text-located rule (§3.3).
"""
from __future__ import annotations

# Natural benefic/malefic (BPHS ch.3 śl.11, PG26:C1 [D]): "the Sun, Saturn,
# Mars, decreasing Moon, Rahu and Ketu … are malefics while the rest are
# benefics. Mercury, however, is a malefic if he joins a malefic."
NATURAL_MALEFICS = frozenset({"Sun", "Saturn", "Mars", "Rahu", "Ketu"})
NATURAL_BENEFICS = frozenset({"Jupiter", "Venus"})
# Moon: malefic when waning, benefic when waxing (śl.11 + translator's
# Saravali note PG26:C2). Mercury: malefic only when joined to a malefic.

# Naisargika (natural) maitrī — śl.55 [D] PG39:C1. Derived from the śl.55
# rule applied to the mūlatrikoṇa/exaltation data (§4.2), cell by cell, and
# cross-checked against the readable fragments of the OCR-degraded printed
# table PG39:C2 (PROMISE_NATURE_YOGA_MAP_v1_1 §3.1 — derivation, not
# transcription, recorded honestly).
# MOON ROW EXCEPTION: the śl.55 mechanical derivation puts Mercury in both
# computations for the Moon (friend AND enemy ⇒ neutral), but the printed
# fragment and the translator's Parāśara citation (PG40:C1) record "the Moon
# does not consider anyone as her enemy … the Sun and Mercury are Moon's
# friends while others are her neutrals" — the Moon row follows the text's
# own exception ([D] PG39:C2 + PG40:C1 with this note).
NAISARGIKA_MAITRI: dict[str, dict[str, frozenset[str]]] = {
    "Sun": {"friends": frozenset({"Moon", "Mars", "Jupiter"}),
            "enemies": frozenset({"Venus", "Saturn"}),
            "neutral": frozenset({"Mercury"})},
    "Moon": {"friends": frozenset({"Sun", "Mercury"}),
             "enemies": frozenset(),  # the text's own exception (PG40:C1)
             "neutral": frozenset({"Mars", "Jupiter", "Venus", "Saturn"})},
    "Mars": {"friends": frozenset({"Sun", "Moon", "Jupiter"}),
             "enemies": frozenset({"Mercury"}),
             "neutral": frozenset({"Venus", "Saturn"})},
    "Mercury": {"friends": frozenset({"Sun", "Venus"}),
                "enemies": frozenset({"Moon"}),
                "neutral": frozenset({"Mars", "Jupiter", "Saturn"})},
    "Jupiter": {"friends": frozenset({"Sun", "Moon", "Mars"}),
                "enemies": frozenset({"Mercury", "Venus"}),
                "neutral": frozenset({"Saturn"})},
    "Venus": {"friends": frozenset({"Mercury", "Saturn"}),
              "enemies": frozenset({"Sun", "Moon"}),
              "neutral": frozenset({"Mars", "Jupiter"})},
    "Saturn": {"friends": frozenset({"Mercury", "Venus"}),
               "enemies": frozenset({"Sun", "Moon", "Mars"}),
               "neutral": frozenset({"Jupiter"})},
}
NAISARGIKA_MAITRI_SOURCE = ("derived from BPHS ch.3 śl.55 [D] PG39:C1, "
                            "cross-checked against OCR-degraded PG39:C2")


def naisargika_relation(graha: str, other: str) -> str | None:
    """graha's natural view of `other` ∈ {friend, enemy, neutral}.
    Nodes are NOT in the table (translator's note, not registry content) —
    None = unqualified."""
    row = NAISARGIKA_MAITRI.get(graha)
    if row is None or other not in NAISARGIKA_MAITRI:
        return None
    if other in row["friends"]:
        return "friend"
    if other in row["enemies"]:
        return "enemy"
    if other in row["neutral"]:
        return "neutral"
    return None


def moon_paksa(sun_lon: float, moon_lon: float) -> str:
    """Waxing (Śukla) / waning (Kṛṣṇa) from Sun–Moon elongation: waxing while
    the Moon is 0–180° ahead of the Sun."""
    return "waxing" if (moon_lon - sun_lon) % 360.0 < 180.0 else "waning"


def mercury_affiliation(joined_to_malefic: bool | None) -> str:
    """Condition predicate on Mercury (śl.11): joined to a malefic ⇒ malefic;
    else benefic. Unevaluated ⇒ unqualified, never assumed."""
    if joined_to_malefic is None:
        return "unqualified"
    return "malefic" if joined_to_malefic else "benefic"


def agent_nature(graha: str, *, sun_lon: float | None = None,
                 moon_lon: float | None = None,
                 joined_to_malefic: bool | None = None) -> str:
    """Natural benefic/malefic of an agent (śl.11). Moon needs the elongation
    operands; Mercury needs the affiliation operand; missing ⇒ unqualified."""
    if graha in NATURAL_MALEFICS:
        return "malefic"
    if graha in NATURAL_BENEFICS:
        return "benefic"
    if graha == "Moon":
        if sun_lon is None or moon_lon is None:
            return "unqualified"
        return "malefic" if moon_paksa(sun_lon, moon_lon) == "waning" else "benefic"
    if graha == "Mercury":
        return mercury_affiliation(joined_to_malefic)
    raise ValueError(f"unknown graha {graha!r}")
