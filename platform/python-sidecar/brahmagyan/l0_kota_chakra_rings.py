"""
brahmagyan.l0_kota_chakra_rings — bg_kota_chakra_rings L0 global seed.

ADJUDICATION-9 (00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md, ANTARYĀMIN, ruled 2026-08-01): the
Kota-Chakra (fort chakra) ring partition previously lived as an inline Python
dict inside services/ka_kota_chakra/logic.py. The DATA-HONESTY RAIL
(NIGHT_RUN §D) requires every value to enter as a "cited, versioned L0 row"
— three conjuncts (cited / versioned / L0 row). The inline dict was cited
(via its own docstring) but neither versioned nor an L0 row, so a silent edit
could change the served fort-chakra generation-to-generation with no drift
signal and no version bump — the exact B.8 silent-mutation defect. This
module (+ migration 523's `bg_kota_chakra_rings` table) is the single source
of truth the ruling requires.

**NO SERVED VALUE CHANGES.** The partition below is TRANSCRIBED EXACTLY from
the prior inline dict — "no served value changes whatsoever" (the ruling's
own words, ADJUDICATION-9). Only where the values live changes. See the
byte-identity fixture test: tests/l3/test_ka_kota_chakra.py
(TestByteIdenticalAfterL0Move) — it proves this module's partition is
identical, position-for-position, to the pre-move inline dict.

── COUNTING CONVENTION (unchanged) ───────────────────────────────────────────
`ring_position` is 1-indexed distance from the janma nakshatra, inclusive of
the janma nakshatra itself as position 1:

    Stambha (innermost/pillar):      4th, 11th, 18th, 25th
    Durgantara / Madhya (inner-mid): 3rd, 5th, 10th, 12th, 17th, 19th, 24th, 26th
    Prakara (boundary wall):         2nd, 6th, 9th, 13th, 16th, 20th, 23rd, 27th
    Bahya (exterior):                everything else — 1st, 7th, 8th, 14th,
                                      15th, 21st, 22nd (7 positions; the janma
                                      nakshatra ITSELF, position 1, is not
                                      named in any of the other three sets in
                                      the source description, so it falls to
                                      Bahya by the partition — disclosed here
                                      explicitly rather than silently assumed)

── ROW COUNT — 27, NOT 28 (disclosed) ────────────────────────────────────────
ADJUDICATION-9's own prose estimates "~28 rows"; the actual served partition
is exactly 27 (ring_position 1..27), matching the 27-nakshatra mod-27
arithmetic ka_kota_chakra's writer already uses (services/ka_graha_sancara/
engine.py's NAK_SIZE_DEG-based nakshatra_idx) — NOT the 28-nakshatra,
Abhijit-inclusive count the unrelated bg_nakshatra global reference asset
carries. Given the ruling's own overriding constraint ("no served value
changes whatsoever"), transcribing the currently-served 27-position
partition exactly is what discharges the ruling; a 28th row would be a NEW
value, not a residence change.

── CITATION TIER (unchanged) ─────────────────────────────────────────────────
Tier-(iii) secondary-source transcription per the W3K citation hierarchy
(SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K). `corpus_status='not_in_corpus'` on
every row. Corpus-ingestion gap filed (ADJUDICATION-9 item 5): the two live
candidate primary sources are `muhurta_chintamani` (already ingested but
untranslated OCR — see ADJUDICATION-8) and a Nārada-Saṃhitā-class text not
yet held. Do NOT attempt ingestion from this module — that is a separately
filed work item, not this migration's job.

── VERSIONING (§N.3 / §B.8) ──────────────────────────────────────────────────
`table_version` is zero-padded (`kota_chakra_rings_v01`) per the ne_vNN
precedent (ADJUDICATION-2) — an unpadded `v10` would string-sort below `v2`.
A revision is a new `_v02` row set landed by INSERT, never an in-place edit
of `_v01`'s rows.

Idempotency: L0 = ON CONFLICT DO UPDATE (global, not per-chart), per §N.3.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

TABLE_VERSION = "kota_chakra_rings_v01"

CITATION = (
    "Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, "
    "Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) "
    "secondary-source transcription per the W3K citation hierarchy "
    "(SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical "
    "text. Corpus-ingestion gap filed; see ADJUDICATION-9 "
    "(SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md)."
)

RATIFIED_BY = "ADJUDICATION-9_2026-08-01"

# ── Ring partition — TRANSCRIBED EXACTLY from the prior services/ka_kota_chakra/
# logic.py inline dict (see module docstring; ADJUDICATION-9 item 2). Bahya is
# defined as the COMPLEMENT of the other three within {1..27} — this both
# matches the source description ("bahya = everything else, the exterior")
# and gives a partition invariant asserted below, rather than a 4th
# hand-listed set that could silently drift out of sync. ─────────────────────
STAMBHA_COUNTS: frozenset[int] = frozenset({4, 11, 18, 25})
DURGANTARA_COUNTS: frozenset[int] = frozenset({3, 5, 10, 12, 17, 19, 24, 26})
PRAKARA_COUNTS: frozenset[int] = frozenset({2, 6, 9, 13, 16, 20, 23, 27})
BAHYA_COUNTS: frozenset[int] = frozenset(
    c for c in range(1, 28) if c not in (STAMBHA_COUNTS | DURGANTARA_COUNTS | PRAKARA_COUNTS)
)

# ring_name -> (ring_index [1=innermost .. 4=outermost], member ring_positions)
_RING_ORDER: list[tuple[str, int, frozenset[int]]] = [
    ("stambha", 1, STAMBHA_COUNTS),
    ("durgantara", 2, DURGANTARA_COUNTS),
    ("prakara", 3, PRAKARA_COUNTS),
    ("bahya", 4, BAHYA_COUNTS),
]

# (ring_position, ring_name, ring_index, dvara_assignment) — literal, reviewable,
# GENERATED from the sets above so the 1..27 partition invariant can never
# silently drift out of sync with what is actually served. dvara_assignment is
# always None: reserved for a future dvāra (gate/direction) reading, NOT used
# by the current ka_kota_chakra writer (disclosed, not an oversight).
ROWS: list[tuple[int, str, int, None]] = sorted(
    (position, ring_name, ring_index, None)
    for ring_name, ring_index, members in _RING_ORDER
    for position in members
)

assert len(ROWS) == 27, f"expected 27 ring_position rows (1..27 partition), got {len(ROWS)}"
assert {r[0] for r in ROWS} == set(range(1, 28)), "ring_position rows must partition 1..27 exactly"


def ring_sets_by_name() -> dict[str, frozenset[int]]:
    """In-memory {ring_name: frozenset(ring_position)} partition — the same
    shape ka_kota_chakra's writer previously hardcoded as a module-level
    dict, now derived from this module's single source of truth. Used both
    to build ROWS above and by callers (writer.py at DB-read time; tests
    proving byte-identity) that want the partition without a DB round-trip."""
    return {name: members for name, _idx, members in _RING_ORDER}


def seed_kota_chakra_rings(
    conn: Any,
    build_id: str | None = None,
    dry_run: bool = False,
    autocommit: bool = True,
) -> dict[str, int]:
    """
    Upsert all 27 rows into bg_kota_chakra_rings.

    Returns {"bg_kota_chakra_rings": <total_upserted>}.

    autocommit: if False, caller owns the transaction (pass False from the
    orchestrator's asset_runner — §N.2 frozen contract: the writer never
    commits ctx.db_conn).
    """
    if dry_run:
        logger.info("[L0/kota_chakra_rings] dry_run — would upsert %d rows", len(ROWS))
        return {"bg_kota_chakra_rings": len(ROWS)}

    upserted = 0
    with conn.cursor() as cur:
        for (ring_position, ring_name, ring_index, dvara_assignment) in ROWS:
            cur.execute(
                """
                INSERT INTO bg_kota_chakra_rings
                  (table_version, ring_position, ring_name, ring_index, dvara_assignment,
                   citation, corpus_status, ratified_by)
                VALUES (%s, %s, %s, %s, %s, %s, 'not_in_corpus', %s)
                ON CONFLICT (table_version, ring_position)
                DO UPDATE SET ring_name        = EXCLUDED.ring_name,
                              ring_index       = EXCLUDED.ring_index,
                              dvara_assignment = EXCLUDED.dvara_assignment,
                              citation         = EXCLUDED.citation,
                              corpus_status    = EXCLUDED.corpus_status,
                              ratified_by      = EXCLUDED.ratified_by
                """,
                (TABLE_VERSION, ring_position, ring_name, ring_index, dvara_assignment, CITATION, RATIFIED_BY),
            )
            upserted += 1

    if autocommit:
        conn.commit()

    logger.info("[L0/kota_chakra_rings] upserted %d rows (table_version=%s)", upserted, TABLE_VERSION)
    return {"bg_kota_chakra_rings": upserted}
