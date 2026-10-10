"""
brahmagyan.l0_gochara_citation_resolution - seed + writer logic for bg_gochara_citation_resolution
(MR-25 PARISKARA; R9 asset; 14 rows; static).

TI-L0-20 (SS Q7): the asset had NO writer - it was seeded by migration 565 and repaired by 630 and
631, so the orchestrator could not dispatch it, Build was unmeasurable and ELEVATED unreachable.
This module re-seeds the SAME 14 rows from git by delete-then-insert. ROWS is the net result of
migrations 565 + 630 + 631; its content is pinned by the integrity digest migration 631 sealed
(sha256 f87cfce8...b961be over the ordered rows), which the tests recompute inside PostgreSQL
from the real migration text - the rows are not retyped from memory.

Honest-gap discipline (B.10) is carried over unchanged: 13 of the 14 rows are `unresolved`
corpus gaps (`chunk_id` = `CORPUS_GAP:<slug>`); no chunk is invented. Dispatch is reserved to Suvarṇa
in its certification window (the asset feeds the gochara serving join).
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

ROWS: list[dict[str, Any]] = [
    {
        "citation_string": "BPHS Ch.22 — Graha Gati (planetary motion parameters)",
        "chunk_id": "CORPUS_GAP:bphs_ch22",
        "text_id": "bphs",
        "verse_ref": "CH22",
        "status": "unresolved",
        "source_citation": "BPHS Ch.22 Graha Gati — chapter not confirmed in l0_texts.py SEED_CHUNKS.",
        "constant_name": "GRAHA_GATI_BPHS_22",
        "note": "BPHS Ch.22 not confirmed in corpus seed. Honest gap per B.10.",
    },
    {
        "citation_string": "BPHS Ch.26 — Ashtakavarga (sarvashtakavarga bindu system; 337-bindu Parashara constant)",
        "chunk_id": "CORPUS_GAP:bphs_ch26_ashtakavarga",
        "text_id": "bphs",
        "verse_ref": "CH26:ashtakavarga",
        "status": "unresolved",
        "source_citation": "BPHS Ch.26 Ashtakavarga — the sarvashtakavarga bindu doctrine is not in the bphs_ch26_v001 chunk (which covers graha drishti). Corpus gap per B.10.",
        "constant_name": "ASHTAKAVARGA_BPHS_26",
        "note": "Although bphs_ch26_v001 exists in the corpus, its content covers planetary aspects, not the sarvashtakavarga bindu system (different verses in Ch.26). A more specific chunk is needed. Honest gap per B.10.",
    },
    {
        "citation_string": "BPHS Ch.26 — Graha Drishti (planetary aspects: full/3-quarter/half/quarter by house distance)",
        "chunk_id": "CORPUS_GAP:bphs_ch26_graha_drishti",
        "text_id": "bphs",
        "verse_ref": "CH26 exact graha-drishti passage not ingested",
        "status": "unresolved",
        "source_citation": "BPHS Ch.26 Graha Drishti citation; the exact passage is absent from the current immutable classical_text_chunks corpus.",
        "constant_name": "GRAHA_DRISHTI_BPHS_26",
        "note": "The prior bphs_ch26_v001 mapping is absent from the immutable corpus; this citation remains an explicit corpus gap until canonical ingestion restores the exact passage.",
    },
    {
        "citation_string": "BPHS Ch.26 — Graha Drishti, rasi drishti rendering (whole-sign special aspect: planet aspects specific SIGNS counted from its own occupied sign, not a degree point -- the base doctrine's natural application to a bhava/span target)",
        "chunk_id": "CORPUS_GAP:bphs_ch26_graha_drishti_rasi",
        "text_id": "bphs",
        "verse_ref": "CH26 exact graha-drishti passage not ingested",
        "status": "unresolved",
        "source_citation": "BPHS Ch.26 Graha Drishti rasi-rendering citation; the exact passage is absent from the current immutable classical_text_chunks corpus.",
        "constant_name": "GRAHA_DRISHTI_RASI_BPHS_26",
        "note": "The prior bphs_ch26_v001 mapping is absent from the immutable corpus; this rasi-rendering citation remains an explicit corpus gap until canonical ingestion restores the exact passage.",
    },
    {
        "citation_string": "BPHS Ch.27 — Vakra (retrogression; cheshta bala)",
        "chunk_id": "CORPUS_GAP:bphs_ch27_vakra",
        "text_id": "bphs",
        "verse_ref": "CH27 exact vakra passage not ingested",
        "status": "unresolved",
        "source_citation": "BPHS Ch.27 vakra/cheshta-bala citation; the exact passage is absent from the current classical_text_chunks corpus.",
        "constant_name": "VAKRA_RETROGRADE_BPHS_27",
        "note": "The prior bphs_ch27_v001 mapping was same-chapter proximity only; that chunk contains karaka doctrine and cannot ground this claim.",
    },
    {
        "citation_string": "BPHS Ch.29 — Gochara Phala (transit results)",
        "chunk_id": "CORPUS_GAP:bphs_ch29",
        "text_id": "bphs",
        "verse_ref": "CH29",
        "status": "unresolved",
        "source_citation": "BPHS Ch.29 Gochara Phala — chapter absent from classical_text_chunks seed corpus (l0_texts.py has no Ch.29 seed tuple). Honest gap per B.10.",
        "constant_name": "GOCHARA_PHALA_BPHS_29",
        "note": "BPHS Ch.29 is not in the l0_texts.py SEED_CHUNKS. verse_ref and chunk_id are placeholder stubs; Wave 5 seeding will populate once Ch.29 is ingested.",
    },
    {
        "citation_string": "BPHS Ch.66 — Kakṣyā (Ashtakavarga 1/8-sign sub-division; fine transit strength)",
        "chunk_id": "CORPUS_GAP:bphs_ch66",
        "text_id": "bphs",
        "verse_ref": "CH66",
        "status": "unresolved",
        "source_citation": "BPHS Ch.66 Kakshya/Ashtakavarga — chapter absent from corpus.",
        "constant_name": "KAKSHYA_BPHS_66",
        "note": "BPHS Ch.66 is not in the l0_texts.py SEED_CHUNKS. Honest gap per B.10.",
    },
    {
        "citation_string": "BPHS Ch.66–68 (Ashtakavarga) — bg_transit_av_gates; Phaladeepika Ch.26",
        "chunk_id": "CORPUS_GAP:bphs_ch66_68",
        "text_id": "bphs",
        "verse_ref": "CH66-CH68",
        "status": "unresolved",
        "source_citation": "BPHS Ch.66-68 Ashtakavarga + Phaladeepika Ch.26 composite — chapters absent from corpus.",
        "constant_name": "ASHTAKAVARGA_AV_GATES",
        "note": "Composite citation spanning BPHS Ch.66-68 and Phaladeepika Ch.26. Neither source chapter is in the current corpus seed. Honest gap per B.10.",
    },
    {
        "citation_string": "BPHS Ch.71 — Sade Sati (Saturn's 3-sign transit around natal Moon; phase-position rule)",
        "chunk_id": "CORPUS_GAP:bphs_ch71",
        "text_id": "bphs",
        "verse_ref": "CH71",
        "status": "unresolved",
        "source_citation": "BPHS Ch.71 Sade Sati — chapter absent from corpus.",
        "constant_name": "SADE_SATI_BPHS_71",
        "note": "BPHS Ch.71 is not in the l0_texts.py SEED_CHUNKS. Honest gap per B.10.",
    },
    {
        "citation_string": "Muhurta Chintamani §Tara Bala; Brihat Parashara Hora Shastra §Tara; Jataka Parijata §Tara Bala computation",
        "chunk_id": "CORPUS_GAP:muhurta_chintamani_tara_bala",
        "text_id": "muhurta_chintamani",
        "verse_ref": "Tara Bala chapter",
        "status": "unresolved",
        "source_citation": "Muhurta Chintamani Tara Bala — corpus has muhurta_chintamani but chunks are Hindi OCR (migration 190: 274 untagged chunks; English classifier yields 0). Specific Tara Bala chunk not confirmed. Honest gap per B.10.",
        "constant_name": "TARA_BALA_MUHURTA_CHINTAMANI",
        "note": "muhurta_chintamani is in the corpus (13 texts) but its chunks are Devanagari-only (migration 190 note). Specific Tara Bala passage not confirmed by read-only query.",
    },
    {
        "citation_string": "Muhurta Chintamani, Jyotish Sara Sangraha (Sarvatobhadra Chakra, 28-nakshatra 9×9 grid; l1_sarvatobhadra_positions/l1_sarvatobhadra_vedha table comments, platform/migrations/_archive/140_sarvatobhadra_chakra.sql)",
        "chunk_id": "CORPUS_GAP:muhurta_chintamani_sarvatobhadra",
        "text_id": "muhurta_chintamani",
        "verse_ref": "Sarvatobhadra chapter",
        "status": "unresolved",
        "source_citation": "Sarvatobhadra Chakra passage — muhurta_chintamani corpus has Devanagari-only chunks. Specific passage not confirmed. Honest gap per B.10.",
        "constant_name": "SARVATOBHADRA_MUHURTA_CHINTAMANI",
        "note": "Same muhurta_chintamani corpus gap as TARA_BALA. Not confirmed by read-only query.",
    },
    {
        "citation_string": "Phaladeepika Ch.26 §double-gochara (Jupiter+Saturn simultaneous transit); BPHS Ch.29",
        "chunk_id": "CORPUS_GAP:phaladeepika_ch26_double_gochara",
        "text_id": "phaladeepika",
        "verse_ref": "Adh.XXVI §double-gochara",
        "status": "unresolved",
        "source_citation": "Phaladeepika Ch.26 double-gochara passage — specific double-transit passage not among the chunks verified in migration 528 (which verified pg0338/pg0339/pg0353). Honest gap per B.10.",
        "constant_name": "DOUBLE_GOCHARA_PHALADEEPIKA_26",
        "note": "The phaladeepika_pg* chunks confirmed in mig-528 cover Adh.XXVI Sloka 42-44 and PG353. The double-gochara passage is not among them. Corpus gap.",
    },
    {
        "citation_string": "Phaladeepika Ch.26 — Gochara Vedha",
        "chunk_id": "phaladeepika_pg0353_c01",
        "text_id": "phaladeepika",
        "verse_ref": "Adh.XXVI PG353",
        "status": "resolved",
        "source_citation": "[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 (archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG353. Vedha doctrine: malefic-count effect scale (fear/failure/killing/death/ignominy).",
        "constant_name": "PHALADEEPIKA_VEDHA_26",
        "note": "citations.py constant PHALADEEPIKA_VEDHA_26. Chunk phaladeepika_pg0353_c01 verified READ-ONLY in migration 528 (ADJUDICATION-11 Part 4, 'Both chunks were read READ-ONLY via the postgres MCP ... BEFORE any row below was written').",
    },
    {
        "citation_string": "Prasna Marga (Sarvatobhadra Chakra vedha geometry: rekha/kona/vithi vedha); cf. ga_sensitive_degree_writer.py sarvatobhadra_vedha evidence row",
        "chunk_id": "CORPUS_GAP:prasna_marga_sarvatobhadra",
        "text_id": "prasna_marga",
        "verse_ref": "Sarvatobhadra vedha",
        "status": "unresolved",
        "source_citation": "Prasna Marga Sarvatobhadra vedha — Prasna Marga not confirmed as a text_id in the current corpus (l0_texts.py TEXTS list does not include prasna_marga). Honest gap per B.10.",
        "constant_name": "SARVATOBHADRA_VEDHA_PRASNA_MARGA",
        "note": "Prasna Marga is not in l0_texts.py TEXTS (text_id list). Corpus gap.",
    },
]

_COLUMNS = ("citation_string", "chunk_id", "text_id", "verse_ref", "status",
            "source_citation", "constant_name", "note")


def seed_gochara_citation_resolution(conn, *, dry_run: bool = False) -> dict[str, int]:
    """Delete-then-insert the 14 rows. Never commits; the caller owns the transaction.

    The whole table is writer-owned (a static, chart-agnostic reference table with no
    foreign key and no other producer), so the replace is unscoped by design; replace-not-
    accrete means a row removed from ROWS disappears on the next build."""
    if dry_run:
        return {"bg_gochara_citation_resolution": len(ROWS), "deleted": 0}
    with conn.cursor() as cur:
        cur.execute("DELETE FROM bg_gochara_citation_resolution")
        deleted = cur.rowcount
        for row in ROWS:
            cur.execute(
                "INSERT INTO bg_gochara_citation_resolution "
                "(citation_string, chunk_id, text_id, verse_ref, status, source_citation, constant_name, note) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                tuple(row[c] for c in _COLUMNS),
            )
    logger.info("[L0/gochara_citation_resolution] replaced %d rows with %d", deleted, len(ROWS))
    return {"bg_gochara_citation_resolution": len(ROWS), "deleted": deleted}
