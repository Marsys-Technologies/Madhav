"""Agent nature and naisargika maitrī (PROMISE_NATURE_YOGA_MAP_v1_1 §2–§3;
BPHS ch.3 śl.11 PG26:C1 and śl.55–58 PG39:C1–PG40:C2, all [D]).

Interpretive modifiers only — they assign channel/valence and rank, never
admit, exclude, or zero (spec §2.3 inv 3). Node maitrī is NOT included: the
PG40:C1 Rahu/Ketu lists are the translator's appended note, not a Parāśari
śloka — node relationship modifiers stay `unqualified` pending a
text-located rule (§3.3).
"""
from __future__ import annotations

from collections.abc import Mapping

# Natural benefic/malefic (BPHS ch.3 śl.11, PG26:C1 [D]): "the Sun, Saturn,
# Mars, decreasing Moon, Rahu and Ketu … are malefics while the rest are
# benefics. Mercury, however, is a malefic if he joins a malefic."
NATURAL_MALEFICS = frozenset({"Sun", "Saturn", "Mars", "Rahu", "Ketu"})
NATURAL_BENEFICS = frozenset({"Jupiter", "Venus"})
# Moon: malefic when waning, benefic when waxing (śl.11 + translator's
# Saravali note PG26:C2). Mercury: malefic only when joined to a malefic.

# Naisargika (natural) maitrī — śl.55 [D] PG39:C1. The table is L0 reference
# data: it lives in bg_graha_naisargika_friendship (migration 250) and is
# LOADED from those rows by naisargika_maitri_from_rows below — a module
# constant here could drift from its source (CLAUDE.md §N.7 item 3), so the
# only snapshot of the derivation lives in the test file as a fixture. The
# derivation itself: the śl.55 rule applied to the mūlatrikoṇa/exaltation
# data (§4.2), cell by cell, cross-checked against the readable fragments of
# the OCR-degraded printed table PG39:C2 (PROMISE_NATURE_YOGA_MAP_v1_1 §3.1 —
# derivation, not transcription, recorded honestly).
# MOON ROW EXCEPTION: the śl.55 mechanical derivation puts Mercury in both
# computations for the Moon (friend AND enemy ⇒ neutral), but the printed
# fragment and the translator's Parāśara citation (PG40:C1) record "the Moon
# does not consider anyone as her enemy … the Sun and Mercury are Moon's
# friends while others are her neutrals" — the Moon row follows the text's
# own exception ([D] PG39:C2 + PG40:C1 with this note).
NAISARGIKA_MAITRI_SOURCE = ("derived from BPHS ch.3 śl.55 [D] PG39:C1, "
                            "cross-checked against OCR-degraded PG39:C2")

# The seven non-node grahas the table covers (nodes are NOT Parāśari table
# content — the PG40:C1 Rahu/Ketu lists are the translator's appended note;
# §3.3). Every one of the 7×6 = 42 non-node pairs must be present in the
# source rows; a missing pair is a broken source, never a default.
NON_NODE_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

_RELATION_KEYS = {"friend": "friends", "enemy": "enemies", "neutral": "neutral"}


def naisargika_maitri_from_rows(rows) -> dict[str, dict[str, frozenset[str]]]:
    """Build the naisargika maitrī mapping from bg_graha_naisargika_friendship
    rows — the L0 source of truth (migration 250).

    `rows` is an already-fetched iterable (e.g. cursor.fetchall() of
    SELECT graha, other_graha, relation FROM bg_graha_naisargika_friendship);
    each row is a mapping with graha/other_graha/relation keys or a
    3-sequence in that order. Rows involving a node (Rahu/Ketu) are skipped
    — nodes are not Parāśari table content (module docstring §3.3).

    Raises ValueError on an unknown relation label or a missing non-node
    pair — refuse, never default (CLAUDE.md §N.7)."""
    table: dict[str, dict[str, set[str]]] = {
        g: {"friends": set(), "enemies": set(), "neutral": set()}
        for g in NON_NODE_GRAHAS
    }
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if isinstance(row, Mapping):
            graha, other, relation = row["graha"], row["other_graha"], row["relation"]
        else:
            graha, other, relation = row
        if relation not in ("friend", "enemy", "neutral"):
            raise ValueError(
                f"unknown relation label {relation!r} in bg_graha_naisargika_friendship "
                f"row ({graha!r}, {other!r}) — expected friend|enemy|neutral")
        if graha not in table or other in ("Rahu", "Ketu"):
            continue  # node row — not table content, see module docstring
        if other not in table:
            raise ValueError(
                f"unknown graha {other!r} in bg_graha_naisargika_friendship "
                f"row ({graha!r}, {other!r})")
        key = _RELATION_KEYS[relation]
        table[graha][key].add(other)
        seen.add((graha, other))
    missing = [(g, o) for g in NON_NODE_GRAHAS for o in NON_NODE_GRAHAS
               if g != o and (g, o) not in seen]
    if missing:
        raise ValueError(
            f"bg_graha_naisargika_friendship is missing {len(missing)} non-node "
            f"pair(s) (first: {missing[0]!r}) — the source is incomplete; "
            "refusing to default a pair")
    return {g: {"friends": frozenset(r["friends"]),
                "enemies": frozenset(r["enemies"]),
                "neutral": frozenset(r["neutral"])}
            for g, r in table.items()}


def naisargika_relation(graha: str, other: str,
                        table: dict[str, dict[str, frozenset[str]]]) -> str | None:
    """graha's natural view of `other` ∈ {friend, enemy, neutral}, looked up
    in `table` as loaded by naisargika_maitri_from_rows from the L0 rows.
    Nodes are NOT in the table (translator's note, not registry content) —
    None = unqualified."""
    row = table.get(graha)
    if row is None or other not in table:
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
