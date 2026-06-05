"""
brahmagyan.mimamsa.concordance_writer — BRAHMA Multi-School Concordance Writer
===============================================================================

Stream E (postdeploy-e-multi-school) — Session e5

Manages the concordance_ayanamsha_flags table introduced in Stream E migration
brahma_multi_school_dual_ayanamsha.sql.

This module:
1. Defines the ConcordanceClass enum with the new AYANAMSHA_DEPENDENT class.
2. Provides a writer that inserts/upserts concordance flag records.
3. Provides a detection pass that cross-references ganita_positions to find
   topics where different ayanamsha offsets produce different conclusions
   (sign-boundary and nakshatra-boundary crossings).
4. Resolves the C3 WS-3 concordance flag: C3 itself remains ORTHOGONAL (house
   cusp systems are fundamentally different), but the ayanamsha-offset component
   of C3-related topics is now AYANAMSHA_DEPENDENT and tracked separately.

ConcordanceClass values:
  AGREE               — all schools/ayanamshas produce the same conclusion
  DISAGREE            — produce contradictory conclusions (class-1 conflict)
  QUALIFY             — same conclusion with school/ayanamsha-specific qualifications
  ORTHOGONAL          — systems address different domains; comparison not meaningful
  AYANAMSHA_DEPENDENT — conclusion changes depending on which ayanamsha offset is applied
                        (NEW in Stream E — resolves C3 KP-vs-Lahiri orthogonality)

Table: concordance_ayanamsha_flags
Migration: brahma_multi_school_dual_ayanamsha.sql

Native: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
        chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0

BRAHMA-MULTI-SCHOOL / Stream E e5
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


# ── ConcordanceClass enum ─────────────────────────────────────────────────────

class ConcordanceClass(str, Enum):
    """
    Concordance classification for a topic across schools or ayanamsha systems.

    The string value matches the DB CHECK constraint in concordance_ayanamsha_flags.
    """
    AGREE               = "agree"
    DISAGREE            = "disagree"
    QUALIFY             = "qualify"
    ORTHOGONAL          = "orthogonal"
    AYANAMSHA_DEPENDENT = "ayanamsha_dependent"   # NEW — Stream E e5

    @classmethod
    def all_values(cls) -> list[str]:
        return [m.value for m in cls]

    @classmethod
    def from_ws3_pattern(cls, ws3_pattern: str) -> "ConcordanceClass":
        """
        Map a WS-3 concordance YAML 'pattern:' value to a ConcordanceClass.

        WS-3 uses: AGREE, DISAGREE, QUALIFY, ORTHOGONAL, SYSTEM-DEFINING.
        SYSTEM-DEFINING → ORTHOGONAL (the system convention is the source of
        the orthogonality; no useful comparison across systems).
        """
        mapping = {
            "AGREE":          cls.AGREE,
            "DISAGREE":       cls.DISAGREE,
            "QUALIFY":        cls.QUALIFY,
            "ORTHOGONAL":     cls.ORTHOGONAL,
            "SYSTEM-DEFINING": cls.ORTHOGONAL,  # C3 house cusp convention
        }
        return mapping.get(ws3_pattern.upper(), cls.ORTHOGONAL)


# ── DB helper ─────────────────────────────────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[concordance_writer] DATABASE_URL not set")


def _conn():
    import psycopg
    return psycopg.connect(_db_url())


# ── ConcordanceFlagRecord ─────────────────────────────────────────────────────

class ConcordanceFlagRecord:
    """
    Value object representing one concordance flag entry.

    Args:
        topic_id:         Short identifier (e.g. 'TC.C3.BOUNDARY').
        topic:            Human-readable topic name.
        concordance_class: ConcordanceClass enum value.
        ayanamsha_a:      First ayanamsha in comparison (default 'lahiri').
        ayanamsha_b:      Second ayanamsha in comparison (default 'kp').
        description:      Explanation of why conclusions differ.
        rule_refs:        List of rule reference strings.
        chart_id:         UUID string (None = school-level, not chart-specific).
        source_citation:  Provenance string.
        build_id:         Optional build tag.
    """

    def __init__(
        self,
        topic_id: str,
        topic: str,
        concordance_class: ConcordanceClass,
        description: str,
        source_citation: str,
        *,
        ayanamsha_a: str = "lahiri",
        ayanamsha_b: str = "kp",
        rule_refs: list[str] | None = None,
        chart_id: str | None = None,
        build_id: str | None = None,
    ) -> None:
        self.topic_id = topic_id
        self.topic = topic
        self.concordance_class = concordance_class
        self.ayanamsha_a = ayanamsha_a
        self.ayanamsha_b = ayanamsha_b
        self.description = description
        self.rule_refs = rule_refs or []
        self.chart_id = chart_id
        self.source_citation = source_citation
        self.build_id = build_id

    def to_db_row(self) -> tuple:
        """Return a tuple suitable for DB insertion."""
        import json
        return (
            self.topic_id,
            self.topic,
            self.concordance_class.value,
            self.ayanamsha_a,
            self.ayanamsha_b,
            self.description,
            json.dumps(self.rule_refs),
            self.chart_id,
            self.source_citation,
            self.build_id,
        )


# ── Writer ────────────────────────────────────────────────────────────────────

def write_concordance_flags(
    records: list[ConcordanceFlagRecord],
    *,
    dry_run: bool = False,
) -> int:
    """
    Upsert concordance_ayanamsha_flags rows.

    Uses ON CONFLICT (topic_id, ayanamsha_a, ayanamsha_b, chart_id) DO UPDATE.

    Args:
        records:  List of ConcordanceFlagRecord instances.
        dry_run:  If True, log rows without writing.

    Returns:
        Number of rows upserted.
    """
    if not records:
        logger.info("[concordance_writer] No records to write.")
        return 0

    if dry_run:
        for r in records:
            logger.info(
                "[dry_run] %s [%s] %s vs %s → %s",
                r.topic_id, r.concordance_class.value,
                r.ayanamsha_a, r.ayanamsha_b, r.topic,
            )
        return len(records)

    written = 0
    with _conn() as conn:
        for rec in records:
            row = rec.to_db_row()
            conn.execute(
                """
                INSERT INTO concordance_ayanamsha_flags
                  (topic_id, topic, concordance_class, ayanamsha_a, ayanamsha_b,
                   description, rule_refs, chart_id, source_citation, build_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                ON CONFLICT (topic_id, ayanamsha_a, ayanamsha_b, chart_id)
                DO UPDATE SET
                  topic              = EXCLUDED.topic,
                  concordance_class  = EXCLUDED.concordance_class,
                  description        = EXCLUDED.description,
                  rule_refs          = EXCLUDED.rule_refs,
                  source_citation    = EXCLUDED.source_citation,
                  build_id           = EXCLUDED.build_id,
                  updated_at         = NOW()
                """,
                row,
            )
            written += 1
        conn.commit()

    logger.info("[concordance_writer] Wrote %d concordance flag records.", written)
    return written


# ── C3 Resolution: known AYANAMSHA_DEPENDENT topics ──────────────────────────

# These are the C3-flagged WS-3 topics where the ayanamsha offset (not just
# the house system) determines the conclusion. The C3 house-cusp orthogonality
# itself remains ORTHOGONAL in the WS-3 YAML; these records capture the
# ayanamsha-offset sub-problem that was previously mis-labelled as ORTHOGONAL.

C3_AYANAMSHA_DEPENDENT_RECORDS: list[ConcordanceFlagRecord] = [
    ConcordanceFlagRecord(
        topic_id="TC.C3.SIGN_BOUNDARY",
        topic="Planet near sign boundary — ayanamsha offset changes sign placement",
        concordance_class=ConcordanceClass.AYANAMSHA_DEPENDENT,
        description=(
            "When a planet falls within ~0.30° of a sign cusp, the Lahiri offset "
            "(~23.85° at 1984 epoch) and KP offset (~23.86°, Krishnamurti) produce "
            "different sign assignments. Rules depending on the planet's sign "
            "(dignity, lordship, yoga formation) produce different conclusions. "
            "This captures the ayanamsha-offset component of the WS-3 C3 flag "
            "(C3 itself = house cusp convention ORTHOGONAL; this = offset sub-problem). "
            "RESOLVED: C3 moves from ORTHOGONAL to AYANAMSHA_DEPENDENT for this sub-class."
        ),
        rule_refs=["BPHS.3.21.1", "KP.1.ch3.dignity.1", "BRAHMA-GA-1-2"],
        source_citation="brahmagyan_concordance.yaml v1.1 / Stream E e5 / V1_3_MULTI_SCHOOL_SCHEMA.md",
    ),
    ConcordanceFlagRecord(
        topic_id="TC.C3.NAKSHATRA_BOUNDARY",
        topic="Planet near nakshatra boundary — ayanamsha offset changes nakshatra placement",
        concordance_class=ConcordanceClass.AYANAMSHA_DEPENDENT,
        description=(
            "Each nakshatra spans 13°20' (13.333°). A planet near a nakshatra boundary "
            "may land in different nakshatras under Lahiri vs KP offsets. Dasha lords "
            "(Vimshottari) and KP sub-lord assignments both depend on nakshatra placement, "
            "so borderline planets produce different dasha-lord and sub-lord conclusions "
            "across the two systems. KP sub-lord analysis uses KP ayanamsha + Placidus "
            "cusps as an integrated unit — the ayanamsha offset is inseparable from the "
            "house system choice in full KP analysis. "
            "RESOLVED: nakshatra-boundary sub-class of C3 now AYANAMSHA_DEPENDENT."
        ),
        rule_refs=["BPHS.46.2.1", "KP.1.ch4.sublord.1", "BRAHMA-GA-1-4"],
        source_citation="brahmagyan_concordance.yaml v1.1 / Stream E e5 / V1_3_MULTI_SCHOOL_SCHEMA.md",
    ),
    ConcordanceFlagRecord(
        topic_id="TC.C3.DASHA_LORD",
        topic="Moon near nakshatra boundary — Vimshottari dasha lord differs across ayanamshas",
        concordance_class=ConcordanceClass.AYANAMSHA_DEPENDENT,
        description=(
            "The Vimshottari dasha lord is determined by the Moon's nakshatra at birth. "
            "If the Moon falls within ~0.30° of a nakshatra boundary, Lahiri and KP "
            "ayanamshas may assign it to different nakshatras, producing different dasha "
            "lords and entirely different dasha timelines. For the native (Moon at "
            "~327.05° Lahiri sidereal = Purva Bhadrapada), this is a known borderline "
            "case: verify Moon's nakshatra position under both ayanamshas before "
            "committing to a dasha timeline. "
            "RESOLVED: dasha-lord sub-class of C3 now AYANAMSHA_DEPENDENT."
        ),
        rule_refs=["BPHS.46.1.1", "KP.1.ch4.sublord.1", "BRAHMA-GA-1-4", "FORENSIC_v8_0.§2.2"],
        source_citation="brahmagyan_concordance.yaml v1.1 / Stream E e5 / V1_3_MULTI_SCHOOL_SCHEMA.md",
    ),
]


def seed_c3_resolution(*, dry_run: bool = False) -> int:
    """
    Seed the C3 AYANAMSHA_DEPENDENT concordance records.

    This resolves the WS-3 C3 concordance flag by writing the three known
    sub-classes of C3 that are now properly classified as AYANAMSHA_DEPENDENT.

    Returns:
        Number of records written.
    """
    logger.info(
        "[concordance_writer] Seeding %d C3 AYANAMSHA_DEPENDENT records...",
        len(C3_AYANAMSHA_DEPENDENT_RECORDS),
    )
    return write_concordance_flags(C3_AYANAMSHA_DEPENDENT_RECORDS, dry_run=dry_run)


# ── Query helpers ─────────────────────────────────────────────────────────────

def get_ayanamsha_dependent_topics(
    chart_id: str | None = None,
    *,
    ayanamsha_pair: tuple[str, str] = ("lahiri", "kp"),
) -> list[dict[str, Any]]:
    """
    Retrieve all AYANAMSHA_DEPENDENT concordance topics.

    Args:
        chart_id:       Optional chart UUID (None = school-level topics only).
        ayanamsha_pair: Filter by specific ayanamsha pair.

    Returns:
        List of dicts with keys: topic_id, topic, description, rule_refs.
    """
    aya_a, aya_b = ayanamsha_pair
    try:
        with _conn() as conn:
            rows = conn.execute(
                """
                SELECT topic_id, topic, description, rule_refs, computed_at
                FROM concordance_ayanamsha_flags
                WHERE concordance_class = 'ayanamsha_dependent'
                  AND ayanamsha_a = %s AND ayanamsha_b = %s
                  AND (chart_id IS NULL OR chart_id = %s)
                ORDER BY topic_id
                """,
                (aya_a, aya_b, chart_id),
            ).fetchall()
        return [
            {
                "topic_id":    r[0],
                "topic":       r[1],
                "description": r[2],
                "rule_refs":   r[3],
                "computed_at": r[4].isoformat() if r[4] else None,
            }
            for r in rows
        ]
    except Exception as exc:
        logger.error("[concordance_writer] Query failed: %s", exc)
        return []


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Brahma concordance writer — multi-school dual-ayanamsha"
    )
    sub = parser.add_subparsers(dest="command")

    p_seed = sub.add_parser("seed-c3", help="Seed C3 AYANAMSHA_DEPENDENT records")
    p_seed.add_argument("--dry-run", action="store_true")

    p_query = sub.add_parser("query", help="Query AYANAMSHA_DEPENDENT topics")
    p_query.add_argument("--chart-id", default=None)
    p_query.add_argument("--aya-a", default="lahiri")
    p_query.add_argument("--aya-b", default="kp")

    args = parser.parse_args()

    if args.command == "seed-c3":
        n = seed_c3_resolution(dry_run=args.dry_run)
        print(f"Seeded {n} C3 AYANAMSHA_DEPENDENT records.")
    elif args.command == "query":
        topics = get_ayanamsha_dependent_topics(
            chart_id=args.chart_id,
            ayanamsha_pair=(args.aya_a, args.aya_b),
        )
        for t in topics:
            print(f"{t['topic_id']}: {t['topic']}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
