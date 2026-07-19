"""
gochara_intensity.valence — adverse/non-adverse event-class determination for
G-3's "adverse event-classes use IDENTICAL machinery with signed valence"
requirement (BRIEF_D5 §1 G-3 row; D-2's doctrine).

The task brief said to "check `brahma_event_ontology` or wherever valence
sign is already recorded for event classes; if you can't find an existing
valence field, treat classes like bereavement, major_loss, illness_acute,
career_setback, financial_deception, psychological_arc as adverse." A live
field WAS found: `brahma_event_ontology.evidence_requirements->>'valence'`
(migration `platform/supabase/migrations/456_brahma_event_ontology_dr13_shapes.sql`),
one of `gain|loss|neutral|mixed` per class (also surfaced in TypeScript as
`EvidenceValence` in `platform/src/lib/lel/event_ontology_shapes.ts`).

`VALENCE_MAP` below is the FULL 27-class table read directly from that
migration's INSERT/UPDATE VALUES at G-3 build time (2026-07-19) -- used as
the honest-degrade fallback when `brahma_event_ontology` is unreachable live
(same "read live, degrade to a documented fixture, never silently invent"
discipline as `gochara_grammar.resonance_map`/`dasha_data`). `fetch_valence`
always prefers a live read when `conn` is given.

Sign decision (documented, ENGINEERING JUDGMENT call, not itself a doctrine
ruling): `valence == 'loss'` -> adverse (negative signed lambda_e).
`valence == 'mixed'` is adverse ONLY for `psychological_arc`, matching the
task brief's own explicit enumeration of that class as adverse despite its
'mixed' (not 'loss') valence tag -- `psychological_arc`'s mixed tag reflects
that SOME instances are neutral/growth-oriented episodes, but the class as a
whole is the wave brief's named adverse specimen, so it is treated as
adverse here, with this call-out on the record. `parental_event` is also
'mixed' but is NOT in the brief's adverse enumeration and is left
non-adverse (magnitude-only, unsigned) -- a family member's health event
touches the native only indirectly and the brief did not name it, so no
sign is forced beyond what the live 'loss'-valence classes already cover.
`gain`/`neutral` valence classes are never adverse.
"""
from __future__ import annotations

import logging
from typing import Optional
from ._dbutil import safe_rollback

logger = logging.getLogger(__name__)

# Full 27-class valence table, transcribed verbatim from migration 456's
# VALUES blocks (evidence_requirements->>'valence') at G-3 build time.
VALENCE_MAP: dict[str, str] = {
    # ── 22 classes backfilled by the UPDATE ... FROM (VALUES ...) block ──
    "career_entry": "gain",
    "career_advancement": "gain",
    "career_change": "neutral",
    "career_setback": "loss",
    "business_launch": "gain",
    "education_milestone": "gain",
    "exam_outcome": "neutral",
    "marriage": "neutral",
    "romantic_start": "gain",
    "separation": "loss",
    "childbirth": "gain",
    "parental_event": "mixed",
    "bereavement": "loss",
    "major_gain": "gain",
    "major_loss": "loss",
    "property_acquisition": "gain",
    "relocation": "neutral",
    "foreign_settlement": "neutral",
    "illness_acute": "loss",
    "chronic_onset": "loss",
    "surgery": "neutral",
    "spiritual_turn": "gain",
    # ── 5 classes closing the live-data coverage gap (INSERT block) ──
    "achievement_recognition": "gain",
    "financial_deception": "loss",
    "psychological_arc": "mixed",
    "birth_anchor": "neutral",
    "travel_event": "neutral",
}

# Explicit adverse call-out beyond a bare valence=='loss' read -- see module
# docstring's "Sign decision" paragraph. Kept as its own named set (not
# folded silently into VALENCE_MAP) so the exception is visible in a diff
# and in any code review, not buried in data.
_ADVERSE_MIXED_OVERRIDE = frozenset({"psychological_arc"})


def fetch_valence(conn, event_class: str) -> str:
    """Live-read `brahma_event_ontology.evidence_requirements->>'valence'`
    for `event_class`; falls back to `VALENCE_MAP` (honest, documented
    fixture) on ANY DB-shape surprise -- table unreachable, row missing,
    connectivity error -- same defensive-read discipline as
    `gochara_grammar.resonance_map.fetch_resonance_targets`."""
    if conn is not None:
        try:
            cur = conn.execute(
                "SELECT evidence_requirements->>'valence' AS valence "
                "FROM brahma_event_ontology WHERE event_class_id = %s",
                [event_class],
            )
            row = cur.fetchone()
            if row is not None:
                v = row["valence"] if isinstance(row, dict) else row[0]
                if v:
                    return str(v)
        except Exception as exc:  # noqa: BLE001
            logger.info(
                "[gochara_intensity.valence] brahma_event_ontology live read failed for "
                "event_class=%s, falling back to VALENCE_MAP: %s", event_class, exc,
            )
            safe_rollback(conn)
    return VALENCE_MAP.get(event_class, "neutral")


def is_adverse(conn, event_class: str) -> tuple[bool, str]:
    """Returns (is_adverse, valence). See module docstring for the sign
    decision rule (valence=='loss', plus the documented psychological_arc
    override)."""
    valence = fetch_valence(conn, event_class)
    adverse = (valence == "loss") or (event_class in _ADVERSE_MIXED_OVERRIDE)
    return adverse, valence


__all__ = ["VALENCE_MAP", "fetch_valence", "is_adverse"]
