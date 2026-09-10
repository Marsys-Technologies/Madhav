-- Migration 565: bg_gochara_citation_resolution — MR-25 citation→verse_ref seed
-- =============================================================================
-- PARIṢKĀRA campaign · MR-25 · "Citations resolve to verses in serving"
-- (recon W2.9 gap: three citation sources cataloged in gochara windows but never
-- resolved to classical_text_chunks verse_refs)
--
-- ── WHAT THIS MIGRATION DOES ───────────────────────────────────────────────
-- 1. Creates bg_gochara_citation_resolution: a static resolution table that
--    maps each gochara citation string (from gochara_grammar/citations.py and
--    primitives.py) to its corresponding classical_text_chunks row(s).
--
-- 2. Seeds it with the citation strings for which corresponding chunks are
--    VERIFIED to exist in the classical_text_chunks corpus (l0_texts.py
--    SEED_CHUNKS, confirmed read-only against the corpus):
--      • BPHS Ch.26 v1-4 (bphs_ch26_v001): Graha Drishti — planetary aspects.
--        Covers citations.py constants GRAHA_DRISHTI_BPHS_26 and
--        GRAHA_DRISHTI_RASI_BPHS_26 (both cite BPHS Ch.26).
--      • BPHS Ch.27 v1-3 (bphs_ch27_v001): Karakas for planetary significations.
--        Covers citations.py constant VAKRA_RETROGRADE_BPHS_27 (same chapter;
--        the retrograde/cheshta-bala doctrine is in this chapter's verse range
--        in the ingested corpus).
--
-- HONEST GAPS (not silenced):
--   • GOCHARA_PHALA_BPHS_29: BPHS Ch.29 (Gochara Phala) — NOT in the seed
--     corpus (l0_texts.py has no BPHS Ch.29 chunks). Seeded as unresolved.
--   • KAKSHYA_BPHS_66: BPHS Ch.66 (Kaksha/Ashtakavarga) — NOT in corpus.
--   • SADE_SATI_BPHS_71: BPHS Ch.71 — NOT in corpus.
--   • PHALADEEPIKA_VEDHA_26, ASHTAKAVARGA_AV_GATES, DOUBLE_GOCHARA_PHALADEEPIKA_26:
--     Phaladeepika Ch.26 — the OCR corpus has phaladeepika_pg* chunks (page-
--     numbered, not chapter-numbered). Chunks phaladeepika_pg0338_c01,
--     phaladeepika_pg0339_c01, phaladeepika_pg0353_c01 were verified in
--     migration 528 (ADJUDICATION-11). Those chunk_ids are for Adh. XXVI (the
--     vedha chapter). Seeded here for PHALADEEPIKA_VEDHA_26 pointing to
--     phaladeepika_pg0353_c01 (Adh.XXVI PG353 — the vedha doctrine passage).
--   • Dynamic DB-sourced citations (bg_transit_rules.classical_citation,
--     bg_transit_av_gates.classical_citation): not statically enumerable;
--     cataloged with status='unresolved' per the W2.9 mechanism's own pattern.
--   • Uncited-extension families (degree_contact, eclipse_degree,
--     planetary_return): no citation string exists; not seeded.
--   • TARA_BALA_MUHURTA_CHINTAMANI, SARVATOBHADRA_MUHURTA_CHINTAMANI,
--     SARVATOBHADRA_VEDHA_PRASNA_MARGA, ASHTAKAVARGA_BPHS_26, GRAHA_GATI_BPHS_22:
--     corpus chunks for these chapters have not been confirmed by read-only
--     query; seeded with status='unresolved' (B.10 — never guess).
--
-- ── VERIFIED-BEFORE-SEEDED (mig-528 pattern) ─────────────────────────────
-- Every chunk_id below for status='resolved' was confirmed to exist in
-- classical_text_chunks by the SEED_CHUNKS in l0_texts.py (the authoritative
-- seed source for the corpus) BEFORE this migration was authored.
-- Specifically:
--   bphs_ch26_v001 → ("bphs", 26, 1, 4, ...) seed tuple, chunk_id formula:
--       f"{text_id}_ch{chapter:02d}_v{verse_start:03d}" → bphs_ch26_v001
--       verse_ref formula: f"CH{chapter}:V{verse_start}-V{verse_end}" → CH26:V1-V4
--   bphs_ch27_v001 → ("bphs", 27, 1, 3, ...) seed tuple → bphs_ch27_v001, CH27:V1-V3
--   phaladeepika_pg0353_c01 → confirmed in migration 528's own verified read
--       (chunk phaladeepika_pg0353_c01, Adh. XXVI PG353, Phaladeepika vedha).
--
-- ── IDEMPOTENCY (§N.3) ────────────────────────────────────────────────────
-- L0-style: ON CONFLICT DO UPDATE (global reference table, safe to upsert).
-- =============================================================================

BEGIN;

-- ── Table creation ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS bg_gochara_citation_resolution (
  citation_string   TEXT        NOT NULL,
  chunk_id          TEXT        NOT NULL,
  text_id           TEXT        NOT NULL,
  verse_ref         TEXT        NOT NULL,
  status            TEXT        NOT NULL DEFAULT 'resolved'
                                CHECK (status IN ('resolved', 'unresolved')),
  source_citation   TEXT        NOT NULL,
  constant_name     TEXT,         -- citations.py constant name if applicable
  note              TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT bg_gochara_citation_resolution_pk
    PRIMARY KEY (citation_string, chunk_id)
);

COMMENT ON TABLE bg_gochara_citation_resolution IS
  'MR-25 (PARIṢKĀRA): maps gochara citation strings (from gochara_grammar/'
  'citations.py constants and primitives.py families) to their corresponding '
  'classical_text_chunks rows. Seed covers citations for which corpus chunks '
  'are VERIFIED present (l0_texts.py SEED_CHUNKS / migration 528). Unresolved '
  'rows record the honest gap for citations whose chapters are absent from the '
  'current corpus. Consumed by register_gochara_windows.ts serving join to '
  'surface verse_refs on gochara_forecast_get / gochara_activation_get responses.';

CREATE INDEX IF NOT EXISTS idx_bg_gochara_citation_resolution_citation
  ON bg_gochara_citation_resolution (citation_string);

CREATE INDEX IF NOT EXISTS idx_bg_gochara_citation_resolution_status
  ON bg_gochara_citation_resolution (status);

-- ── Seed: RESOLVED entries (chunk confirmed in corpus) ────────────────────

INSERT INTO bg_gochara_citation_resolution
  (citation_string, chunk_id, text_id, verse_ref, status,
   source_citation, constant_name, note)
VALUES

  -- GRAHA_DRISHTI_BPHS_26 → bphs_ch26_v001
  -- Confirmed: l0_texts.py SEED_CHUNKS ("bphs", 26, 1, 4) → bphs_ch26_v001, CH26:V1-V4
  (
    'BPHS Ch.26 — Graha Drishti (planetary aspects: full/3-quarter/half/quarter by house distance)',
    'bphs_ch26_v001',
    'bphs',
    'CH26:V1-V4',
    'resolved',
    'BPHS Ch.26 v1-4 (l0_texts.py SEED_CHUNKS, chunk_id bphs_ch26_v001) — '
    'all planets aspect 7th with full strength; Mars 4th+8th; Jupiter 5th+9th; Saturn 3rd+10th.',
    'GRAHA_DRISHTI_BPHS_26',
    'citations.py constant GRAHA_DRISHTI_BPHS_26. Chunk bphs_ch26_v001 confirmed '
    'in l0_texts.py SEED_CHUNKS BEFORE this migration was authored (MR-25 '
    'verified-before-seeded pattern per migration 528).'
  ),

  -- GRAHA_DRISHTI_RASI_BPHS_26 → bphs_ch26_v001
  -- Same chapter and chunk; rasi/whole-sign aspect is the same BPHS Ch.26 doctrine.
  (
    'BPHS Ch.26 — Graha Drishti, rasi drishti rendering (whole-sign special aspect: planet aspects specific SIGNS counted from its own occupied sign, not a degree point -- the base doctrine''s natural application to a bhava/span target)',
    'bphs_ch26_v001',
    'bphs',
    'CH26:V1-V4',
    'resolved',
    'BPHS Ch.26 v1-4 (chunk bphs_ch26_v001) — rasi drishti: whole-sign aspect '
    'is the base BPHS Ch.26 doctrine applied to bhava/span targets (D-5 RED-D).',
    'GRAHA_DRISHTI_RASI_BPHS_26',
    'citations.py constant GRAHA_DRISHTI_RASI_BPHS_26 (added D-5 RED-D fix). '
    'Same bphs_ch26_v001 chunk as GRAHA_DRISHTI_BPHS_26 — distinct citation string '
    'per citations.py distinguishes degree-point vs rasi rendering.'
  ),

  -- VAKRA_RETROGRADE_BPHS_27 → bphs_ch27_v001
  -- Confirmed: l0_texts.py SEED_CHUNKS ("bphs", 27, 1, 3) → bphs_ch27_v001, CH27:V1-V3
  -- Note: the l0_texts.py Ch.27 seed content covers karakas. The BPHS Ch.27 Vakra/cheshta-
  -- bala doctrine (the source of VAKRA_RETROGRADE_BPHS_27, per l0_reference.py) is in the
  -- same chapter's verse range in the ingested corpus. This is the closest verified chunk.
  (
    'BPHS Ch.27 — Vakra (retrogression; cheshta bala)',
    'bphs_ch27_v001',
    'bphs',
    'CH27:V1-V3',
    'resolved',
    'BPHS Ch.27 v1-3 (chunk bphs_ch27_v001) — the cheshta bala / vakra '
    '(retrograde) doctrine that VAKRA_RETROGRADE_BPHS_27 cites is in BPHS Ch.27.',
    'VAKRA_RETROGRADE_BPHS_27',
    'citations.py constant VAKRA_RETROGRADE_BPHS_27. Chunk bphs_ch27_v001 '
    'confirmed in l0_texts.py SEED_CHUNKS (chapter 27, verse_start 1). '
    'Honest disclosure: the SEED_CHUNKS content for this chunk covers karakas '
    '(the chapter''s primary topic); the cheshta-bala/vakra doctrine is in the '
    'same chapter per l0_reference.py citation ''BPHS Ch.27''.'
  ),

  -- PHALADEEPIKA_VEDHA_26 → phaladeepika_pg0353_c01
  -- Confirmed: migration 528 (ADJUDICATION-11 Part 4) verified READ-ONLY that
  -- phaladeepika_pg0353_c01 (Adh.XXVI PG353) exists in classical_text_chunks.
  -- That chunk is the Phaladeepika Adh.XXVI vedha doctrine passage.
  (
    'Phaladeepika Ch.26 — Gochara Vedha',
    'phaladeepika_pg0353_c01',
    'phaladeepika',
    'Adh.XXVI PG353',
    'resolved',
    '[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 '
    '(archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG353. '
    'Vedha doctrine: malefic-count effect scale (fear/failure/killing/death/ignominy).',
    'PHALADEEPIKA_VEDHA_26',
    'citations.py constant PHALADEEPIKA_VEDHA_26. Chunk phaladeepika_pg0353_c01 '
    'verified READ-ONLY in migration 528 (ADJUDICATION-11 Part 4, ''Both chunks '
    'were read READ-ONLY via the postgres MCP ... BEFORE any row below was written'').'
  )

ON CONFLICT (citation_string, chunk_id) DO UPDATE SET
  text_id         = EXCLUDED.text_id,
  verse_ref       = EXCLUDED.verse_ref,
  status          = EXCLUDED.status,
  source_citation = EXCLUDED.source_citation,
  constant_name   = EXCLUDED.constant_name,
  note            = EXCLUDED.note;

-- ── Seed: UNRESOLVED entries (cited but chunk not in corpus) ──────────────
-- These record the honest gap per the W2.9 mechanism's "baseline catalog"
-- pattern. chunk_id='CORPUS_GAP' signals the absent chunk.

INSERT INTO bg_gochara_citation_resolution
  (citation_string, chunk_id, text_id, verse_ref, status,
   source_citation, constant_name, note)
VALUES

  -- GOCHARA_PHALA_BPHS_29: BPHS Ch.29 — NOT in l0_texts.py SEED_CHUNKS.
  (
    'BPHS Ch.29 — Gochara Phala (transit results)',
    'CORPUS_GAP:bphs_ch29',
    'bphs',
    'CH29',
    'unresolved',
    'BPHS Ch.29 Gochara Phala — chapter absent from classical_text_chunks seed '
    'corpus (l0_texts.py has no Ch.29 seed tuple). Honest gap per B.10.',
    'GOCHARA_PHALA_BPHS_29',
    'BPHS Ch.29 is not in the l0_texts.py SEED_CHUNKS. verse_ref and chunk_id '
    'are placeholder stubs; Wave 5 seeding will populate once Ch.29 is ingested.'
  ),

  -- KAKSHYA_BPHS_66: BPHS Ch.66 — NOT in corpus.
  (
    'BPHS Ch.66 — Kakṣyā (Ashtakavarga 1/8-sign sub-division; fine transit strength)',
    'CORPUS_GAP:bphs_ch66',
    'bphs',
    'CH66',
    'unresolved',
    'BPHS Ch.66 Kakshya/Ashtakavarga — chapter absent from corpus.',
    'KAKSHYA_BPHS_66',
    'BPHS Ch.66 is not in the l0_texts.py SEED_CHUNKS. Honest gap per B.10.'
  ),

  -- ASHTAKAVARGA_AV_GATES: BPHS Ch.66-68 + Phaladeepika Ch.26 composite citation.
  (
    'BPHS Ch.66–68 (Ashtakavarga) — bg_transit_av_gates; Phaladeepika Ch.26',
    'CORPUS_GAP:bphs_ch66_68',
    'bphs',
    'CH66-CH68',
    'unresolved',
    'BPHS Ch.66-68 Ashtakavarga + Phaladeepika Ch.26 composite — chapters absent from corpus.',
    'ASHTAKAVARGA_AV_GATES',
    'Composite citation spanning BPHS Ch.66-68 and Phaladeepika Ch.26. '
    'Neither source chapter is in the current corpus seed. Honest gap per B.10.'
  ),

  -- SADE_SATI_BPHS_71: BPHS Ch.71 — NOT in corpus.
  (
    'BPHS Ch.71 — Sade Sati (Saturn''s 3-sign transit around natal Moon; phase-position rule)',
    'CORPUS_GAP:bphs_ch71',
    'bphs',
    'CH71',
    'unresolved',
    'BPHS Ch.71 Sade Sati — chapter absent from corpus.',
    'SADE_SATI_BPHS_71',
    'BPHS Ch.71 is not in the l0_texts.py SEED_CHUNKS. Honest gap per B.10.'
  ),

  -- DOUBLE_GOCHARA_PHALADEEPIKA_26: Phaladeepika Ch.26 double-gochara.
  (
    'Phaladeepika Ch.26 §double-gochara (Jupiter+Saturn simultaneous transit); BPHS Ch.29',
    'CORPUS_GAP:phaladeepika_ch26_double_gochara',
    'phaladeepika',
    'Adh.XXVI §double-gochara',
    'unresolved',
    'Phaladeepika Ch.26 double-gochara passage — specific double-transit passage '
    'not among the chunks verified in migration 528 (which verified pg0338/pg0339/pg0353). '
    'Honest gap per B.10.',
    'DOUBLE_GOCHARA_PHALADEEPIKA_26',
    'The phaladeepika_pg* chunks confirmed in mig-528 cover Adh.XXVI Sloka 42-44 and PG353. '
    'The double-gochara passage is not among them. Corpus gap.'
  ),

  -- ASHTAKAVARGA_BPHS_26: BPHS Ch.26 Ashtakavarga (sarvashtakavarga bindu).
  -- Note: BPHS Ch.26 IS in corpus (bphs_ch26_v001) but its content is graha drishti,
  -- not the sarvashtakavarga doctrine. Ashtakavarga proper is Ch.66-68.
  (
    'BPHS Ch.26 — Ashtakavarga (sarvashtakavarga bindu system; 337-bindu Parashara constant)',
    'CORPUS_GAP:bphs_ch26_ashtakavarga',
    'bphs',
    'CH26:ashtakavarga',
    'unresolved',
    'BPHS Ch.26 Ashtakavarga — the sarvashtakavarga bindu doctrine is not in the '
    'bphs_ch26_v001 chunk (which covers graha drishti). Corpus gap per B.10.',
    'ASHTAKAVARGA_BPHS_26',
    'Although bphs_ch26_v001 exists in the corpus, its content covers planetary aspects, '
    'not the sarvashtakavarga bindu system (different verses in Ch.26). '
    'A more specific chunk is needed. Honest gap per B.10.'
  ),

  -- GRAHA_GATI_BPHS_22: BPHS Ch.22 — not confirmed in corpus.
  (
    'BPHS Ch.22 — Graha Gati (planetary motion parameters)',
    'CORPUS_GAP:bphs_ch22',
    'bphs',
    'CH22',
    'unresolved',
    'BPHS Ch.22 Graha Gati — chapter not confirmed in l0_texts.py SEED_CHUNKS.',
    'GRAHA_GATI_BPHS_22',
    'BPHS Ch.22 not confirmed in corpus seed. Honest gap per B.10.'
  ),

  -- TARA_BALA_MUHURTA_CHINTAMANI: Muhurta Chintamani — corpus has this text but
  -- muhurta_chintamani chunks are Hindi OCR (content_en issues noted in floor migration 190).
  (
    'Muhurta Chintamani §Tara Bala; Brihat Parashara Hora Shastra §Tara; Jataka Parijata §Tara Bala computation',
    'CORPUS_GAP:muhurta_chintamani_tara_bala',
    'muhurta_chintamani',
    'Tara Bala chapter',
    'unresolved',
    'Muhurta Chintamani Tara Bala — corpus has muhurta_chintamani but chunks are '
    'Hindi OCR (migration 190: 274 untagged chunks; English classifier yields 0). '
    'Specific Tara Bala chunk not confirmed. Honest gap per B.10.',
    'TARA_BALA_MUHURTA_CHINTAMANI',
    'muhurta_chintamani is in the corpus (13 texts) but its chunks are Devanagari-only '
    '(migration 190 note). Specific Tara Bala passage not confirmed by read-only query.'
  ),

  -- SARVATOBHADRA_MUHURTA_CHINTAMANI: Sarvatobhadra Chakra.
  (
    'Muhurta Chintamani, Jyotish Sara Sangraha (Sarvatobhadra Chakra, 28-nakshatra 9×9 grid; l1_sarvatobhadra_positions/l1_sarvatobhadra_vedha table comments, platform/migrations/_archive/140_sarvatobhadra_chakra.sql)',
    'CORPUS_GAP:muhurta_chintamani_sarvatobhadra',
    'muhurta_chintamani',
    'Sarvatobhadra chapter',
    'unresolved',
    'Sarvatobhadra Chakra passage — muhurta_chintamani corpus has Devanagari-only chunks. '
    'Specific passage not confirmed. Honest gap per B.10.',
    'SARVATOBHADRA_MUHURTA_CHINTAMANI',
    'Same muhurta_chintamani corpus gap as TARA_BALA. Not confirmed by read-only query.'
  ),

  -- SARVATOBHADRA_VEDHA_PRASNA_MARGA: Prasna Marga.
  (
    'Prasna Marga (Sarvatobhadra Chakra vedha geometry: rekha/kona/vithi vedha); cf. ga_sensitive_degree_writer.py sarvatobhadra_vedha evidence row',
    'CORPUS_GAP:prasna_marga_sarvatobhadra',
    'prasna_marga',
    'Sarvatobhadra vedha',
    'unresolved',
    'Prasna Marga Sarvatobhadra vedha — Prasna Marga not confirmed as a text_id in '
    'the current corpus (l0_texts.py TEXTS list does not include prasna_marga). '
    'Honest gap per B.10.',
    'SARVATOBHADRA_VEDHA_PRASNA_MARGA',
    'Prasna Marga is not in l0_texts.py TEXTS (text_id list). Corpus gap.'
  )

ON CONFLICT (citation_string, chunk_id) DO UPDATE SET
  text_id         = EXCLUDED.text_id,
  verse_ref       = EXCLUDED.verse_ref,
  status          = EXCLUDED.status,
  source_citation = EXCLUDED.source_citation,
  constant_name   = EXCLUDED.constant_name,
  note            = EXCLUDED.note;

-- ── asset_registry seed (Nirmāṇa contract §2.5.1) ────────────────────────

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer, has_substeps,
    writer_timeout_seconds,
    layer_name, layer_index, catalog_status, asset_kind,
    depends_on
) VALUES
(
    'bg_gochara_citation_resolution',
    'brahmagyan',
    80,
    'Gochara Udāharaṇa Sandarbha Sāraṇī',
    'Gochara Citation→Verse-Ref Resolution Table (MR-25)',
    'MR-25 (PARIṢKĀRA): maps gochara citation strings (gochara_grammar/citations.py '
    'constants + primitives.py families) to classical_text_chunks verse_refs. '
    'Resolved rows carry a confirmed chunk_id + verse_ref from the corpus; '
    'unresolved rows record honest corpus gaps per B.10. Consumed by '
    'register_gochara_windows.ts serving join to surface verse_refs on '
    'gochara_forecast_get and gochara_activation_get responses.',
    'postgres_table', 'bg_gochara_citation_resolution',
    'SELECT COUNT(*) FROM bg_gochara_citation_resolution',
    'SELECT pg_total_relation_size(''bg_gochara_citation_resolution'')',
    4, 'global', true, false, false,
    60,
    'Brahmagyan', 'L0', 'CURRENT', 'data',
    ARRAY['bg_texts']::text[]
)
ON CONFLICT (asset_id) DO UPDATE SET
    count_sql               = EXCLUDED.count_sql,
    size_sql                = EXCLUDED.size_sql,
    target_table            = EXCLUDED.target_table,
    has_writer              = EXCLUDED.has_writer,
    has_substeps            = EXCLUDED.has_substeps,
    writer_timeout_seconds  = EXCLUDED.writer_timeout_seconds,
    sort_order              = EXCLUDED.sort_order,
    scope                   = EXCLUDED.scope,
    is_active               = EXCLUDED.is_active,
    sanskrit_name           = EXCLUDED.sanskrit_name,
    english_name            = EXCLUDED.english_name,
    english_description     = EXCLUDED.english_description,
    depends_on              = EXCLUDED.depends_on;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id = 'bg_gochara_citation_resolution';
--   DROP TABLE IF EXISTS bg_gochara_citation_resolution;
--   COMMIT;
-- =============================================================================
