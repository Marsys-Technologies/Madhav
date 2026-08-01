"""
brahmagyan.l0_phaladeepika_vedha — bg_vedha_malefic_scale + bg_phaladeepika_latta
L0 global seed (ADJUDICATION-11 Part 4, mandatory for R-19 closure).

SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md, ADJUDICATION-11 (ANTARYĀMIN,
2026-08-01, supplemental ruling issued after PR #1009's disclosure): "item 5
also seeds + serves at least the two cited vedha rows the corpus holds
today, transcribed exactly: Phaladeepika PG353 (vedha scale) and PG339
(Lattā, `vedha_kind='latta'`, `uncited_extension=false`), as versioned cited
L0 rows." Both chunks were read READ-ONLY via the postgres MCP (SELECT only)
against `classical_text_chunks` (text_id='phaladeepika') this session,
BEFORE this module was authored.

── VERBATIM SOURCE TEXT (transcribed from the OCR'd content_en column, line
breaks cleaned, wording UNCHANGED) ───────────────────────────────────────────

PG353 (chunk phaladeepika_pg0353_c01, Adh. XXVI):
    "When at the time of a battle, there is a (Vedha) caused by one, two,
    three, four or five malefics, the corresponding effects will be fear,
    failure, killing (blood-shed), death and ignominy respectively."

PG338-339 (chunks phaladeepika_pg0338_c01 + phaladeepika_pg0339_c01, joined
across the OCR page break, Adh. XXVI, Sloka 42-44):
    "The 12th asterism counted from that occupied by the Sun at the time,
    the 3rd from that of Mars, the 6th from that of Jupiter, and the 8th
    from that of Saturn are termed ... forward Lattas. The 5th star
    reckoned from that of Venus, the 7th from that of Mercury; the 9th from
    that of Rahu and the 22nd from that of the Moon are called ... rear
    Latta. If, when thus counting, the Janma-nakshatra (natal star) happens
    to come as the Latta star, there will be sickness and anguish."
Per-graha effects, same passage:
    "During the Sun's Latta there will be ruin of every business. Misery
    will result during the Latta of Rahu and Ketu. In the Latta of Jupiter,
    death, ruin of relations and a sort of general fear or insecurity may
    occur. There will be quarrel in the Latta of Venus. In Mercury's Latta
    will occur loss of position or similar untoward event. A great loss
    will mark the Moon's Latta."

── HONEST GAPS (disclosed, not silently filled) ──────────────────────────────
- Mars and Saturn have a counting rule but NO distinct per-graha effect text
  was found in the retrieved passage — `effect_description=None` for both;
  the shared `AFFLICTION_CONDITION` still applies to them.
- Ketu is named in the EFFECTS text ("Misery will result during the Latta of
  Rahu and Ketu") but its own counting rule was NOT found in the retrieved
  passage. NOT seeded (B.10 — never guessed). Filed as a follow-on
  extraction item (ADJUDICATION-11 Part 6, alongside the other 13
  unretrieved Phaladeepika vedha hits).
- Sloka 47 (multi-Latta synchronisation multiplies severity 2x-3x) and
  Sloka 48 (a general SBC-vedha auspicious/evil note) are present in the
  source material but NOT implemented as computed logic — a documented
  follow-on refinement, not attempted under time pressure.
- PG353's verse context is explicitly "at the time of a battle" — a
  muhurta/nimitta scenario, not generalized in the text itself to ordinary
  transit vedha. This module stores the scale verbatim and cited;
  `services/ka_vedha_gochara/writer.py` discloses its own
  `uncited_extension=True` on the specific field where it APPLIES this
  scale to a non-battle context (the table's own rows are not themselves an
  extension — see that module's docstring).

── VERSIONING (§N.3 / §B.8) ───────────────────────────────────────────────────
`TABLE_VERSION` zero-padded (`phaladeepika_vedha_v01`) per the ne_vNN /
kota_chakra_rings_vNN precedent. A revision (e.g. adding Ketu once sourced)
is a new `_v02` row set landed by INSERT, never an in-place edit.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

TABLE_VERSION = "phaladeepika_vedha_v01"

_CITATION_PG353 = (
    "[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 "
    "(archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG353"
)
_VERSE_REF_PG353 = "Adh.XXVI PG353"

_CITATION_PG339 = (
    "[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 "
    "(archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG339"
)
_VERSE_REF_LATTA = "Adh.XXVI PG338-339 Sloka 42-44"

AFFLICTION_CONDITION = (
    "If, when thus counting, the Janma-nakshatra (natal star) happens to "
    "come as the Latta star, there will be sickness and anguish."
)

# (malefic_count, effect_grade, effect_description) — verbatim from PG353.
MALEFIC_SCALE_ROWS: list[tuple[int, str, str]] = [
    (1, "fear",     "Vedha caused by one malefic: fear."),
    (2, "failure",  "Vedha caused by two malefics: failure."),
    (3, "killing",  "Vedha caused by three malefics: killing (blood-shed)."),
    (4, "death",    "Vedha caused by four malefics: death."),
    (5, "ignominy", "Vedha caused by five malefics: ignominy."),
]

# (graha, count_from_graha, direction, effect_description) — verbatim from
# PG338-339 Sloka 42-44. Ketu deliberately ABSENT (see module docstring).
LATTA_ROWS: list[tuple[str, int, str, str | None]] = [
    ("Sun",     12, "forward",  "Ruin of every business."),
    ("Mars",     3, "forward",  None),
    ("Jupiter",  6, "forward",  "Death, ruin of relations and a sort of general fear or insecurity may occur."),
    ("Saturn",   8, "forward",  None),
    ("Venus",    5, "backward", "Quarrel."),
    ("Mercury",  7, "backward", "Loss of position or similar untoward event."),
    ("Rahu",     9, "backward", "Misery."),
    ("Moon",    22, "backward", "A great loss."),
]

assert len(MALEFIC_SCALE_ROWS) == 5, "malefic scale must carry exactly 5 rows (counts 1..5)"
assert {r[0] for r in MALEFIC_SCALE_ROWS} == {1, 2, 3, 4, 5}
assert len(LATTA_ROWS) == 8, "latta rule must carry exactly 8 graha rows (Ketu deliberately absent)"
assert {r[0] for r in LATTA_ROWS} == {"Sun", "Mars", "Jupiter", "Saturn", "Venus", "Mercury", "Rahu", "Moon"}


def seed_vedha_malefic_scale(conn: Any, dry_run: bool = False, autocommit: bool = True) -> dict[str, int]:
    """Upsert the 5-row PG353 malefic-count -> effect-grade scale."""
    if dry_run:
        logger.info("[L0/vedha_malefic_scale] dry_run — would upsert %d rows", len(MALEFIC_SCALE_ROWS))
        return {"bg_vedha_malefic_scale": len(MALEFIC_SCALE_ROWS)}

    upserted = 0
    with conn.cursor() as cur:
        for malefic_count, effect_grade, effect_description in MALEFIC_SCALE_ROWS:
            cur.execute(
                """
                INSERT INTO bg_vedha_malefic_scale
                  (table_version, malefic_count, effect_grade, effect_description, source_citation, verse_ref)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (table_version, malefic_count)
                DO UPDATE SET effect_grade       = EXCLUDED.effect_grade,
                              effect_description = EXCLUDED.effect_description,
                              source_citation    = EXCLUDED.source_citation,
                              verse_ref          = EXCLUDED.verse_ref
                """,
                (TABLE_VERSION, malefic_count, effect_grade, effect_description, _CITATION_PG353, _VERSE_REF_PG353),
            )
            upserted += 1

    if autocommit:
        conn.commit()

    logger.info("[L0/vedha_malefic_scale] upserted %d rows (table_version=%s)", upserted, TABLE_VERSION)
    return {"bg_vedha_malefic_scale": upserted}


def seed_phaladeepika_latta(conn: Any, dry_run: bool = False, autocommit: bool = True) -> dict[str, int]:
    """Upsert the 8-row PG338-339 Lattā rule (Ketu deliberately absent)."""
    if dry_run:
        logger.info("[L0/phaladeepika_latta] dry_run — would upsert %d rows", len(LATTA_ROWS))
        return {"bg_phaladeepika_latta": len(LATTA_ROWS)}

    upserted = 0
    with conn.cursor() as cur:
        for graha, count_from_graha, direction, effect_description in LATTA_ROWS:
            cur.execute(
                """
                INSERT INTO bg_phaladeepika_latta
                  (table_version, graha, count_from_graha, direction, effect_description,
                   affliction_condition, source_citation, verse_ref)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (table_version, graha)
                DO UPDATE SET count_from_graha      = EXCLUDED.count_from_graha,
                              direction             = EXCLUDED.direction,
                              effect_description    = EXCLUDED.effect_description,
                              affliction_condition  = EXCLUDED.affliction_condition,
                              source_citation       = EXCLUDED.source_citation,
                              verse_ref             = EXCLUDED.verse_ref
                """,
                (TABLE_VERSION, graha, count_from_graha, direction, effect_description,
                 AFFLICTION_CONDITION, _CITATION_PG339, _VERSE_REF_LATTA),
            )
            upserted += 1

    if autocommit:
        conn.commit()

    logger.info("[L0/phaladeepika_latta] upserted %d rows (table_version=%s)", upserted, TABLE_VERSION)
    return {"bg_phaladeepika_latta": upserted}
