-- Migration 523: bg_kota_chakra_rings — Kota-Chakra ring table, versioned L0 (ADJUDICATION-9)
-- =============================================================================
-- ṢAḌ-DARŚANA campaign · ANTARYĀMIN Night-3 ADJUDICATION-9
-- (00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
--  SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md), ruled 2026-08-01, unblocking
-- the W3 gate-close-to-`main` PR (item 16, PR #999).
--
-- ── WHAT MOVED AND WHY ────────────────────────────────────────────────────────
-- `ka_kota_chakra`'s fort-chakra ring partition (Stambha/Durgantara/Prakara/
-- Bahya) previously lived as an inline Python dict in
-- services/ka_kota_chakra/logic.py. The DATA-HONESTY RAIL (NIGHT_RUN §D) reads:
-- "every value enters as a cited, versioned L0 row labeled structural_prior; a
-- number without a defensible source is a build error" — three conjuncts. The
-- inline dict was CITED (docstring) but NEITHER versioned NOR an L0 row, so a
-- silent edit could change the served fort-chakra generation-to-generation
-- with no drift signal and no version bump (the exact B.8 silent-mutation
-- defect). This migration seats the same values as a versioned L0 row instead.
--
-- **NO SERVED VALUE CHANGES.** The 27-row partition below is TRANSCRIBED
-- EXACTLY from the prior inline dict (services/ka_kota_chakra/logic.py,
-- pre-migration). Only where the values live changes. See the byte-identity
-- fixture test: platform/python-sidecar/tests/l3/test_ka_kota_chakra.py
-- (TestByteIdenticalAfterL0Move).
--
-- ── ROW COUNT (27, not 28) ────────────────────────────────────────────────────
-- ADJUDICATION-9's own text estimates "~28 rows"; the actual served partition
-- is exactly 27 (ring_position 1..27), matching the 27-nakshatra mod-27
-- arithmetic ka_kota_chakra's writer already uses (NOT the 28-nakshatra,
-- Abhijit-inclusive count the unrelated bg_nakshatra global reference asset
-- carries). Given the ruling's own overriding constraint — "no served value
-- changes whatsoever" — transcribing the currently-served 27-position
-- partition exactly is what discharges the ruling; a 28th row would be a NEW
-- value, not a residence change. Disclosed here, not silently reconciled.
--
-- ── CITATION TIER (unchanged) ─────────────────────────────────────────────────
-- Tier-(iii) secondary-source transcription per the W3K citation hierarchy
-- (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K). `corpus_status='not_in_corpus'` on
-- every row — the ingested corpus has ZERO hits for kota/kotachakra terms
-- (confirmed by ADJUDICATION-9's own corpus finding). Ingestion work item
-- filed for the primary source (muhurta_chintamani — ingested but
-- untranslated OCR, see ADJUDICATION-8 — and a Nārada-Saṃhitā-class text not
-- yet held); this migration does NOT attempt ingestion.
--
-- ── VERSIONING (§N.3 / §B.8) ──────────────────────────────────────────────────
-- `table_version` is zero-padded (`kota_chakra_rings_v01`) per the ne_vNN
-- precedent (ADJUDICATION-2): a bare `v10` would string-sort below `v2`. A
-- future revision is a new `_v02` row set landed by APPEND, never an in-place
-- edit of `_v01`'s rows.
--
-- ── IDEMPOTENCY ────────────────────────────────────────────────────────────────
-- L0 = ON CONFLICT DO UPDATE (global, not per-chart), per §N.3. PK is
-- (table_version, ring_position).
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS bg_kota_chakra_rings (
  table_version       TEXT        NOT NULL,
  ring_position        SMALLINT    NOT NULL CHECK (ring_position BETWEEN 1 AND 27),
  ring_name            TEXT        NOT NULL CHECK (ring_name IN ('stambha', 'durgantara', 'prakara', 'bahya')),
  ring_index           SMALLINT    NOT NULL CHECK (ring_index BETWEEN 1 AND 4),
  dvara_assignment     TEXT,
  citation             TEXT        NOT NULL,
  corpus_status        TEXT        NOT NULL DEFAULT 'not_in_corpus',
  ratified_by          TEXT,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT bg_kota_chakra_rings_pk PRIMARY KEY (table_version, ring_position)
);

COMMENT ON TABLE bg_kota_chakra_rings IS
  'ADJUDICATION-9: Kota-Chakra (fort chakra) ring partition, versioned L0 '
  'global reference. ring_position is the 1-indexed distance from the janma '
  'nakshatra (inclusive of the janma nakshatra itself as position 1); '
  'ring_name is one of stambha (innermost) / durgantara (a.k.a. madhya) / '
  'prakara / bahya (outermost); ring_index is the concentric ordinal '
  '(1=stambha .. 4=bahya). Consumed by ka_kota_chakra (L3 Kāla). Tier-(iii) '
  'secondary-source transcription — corpus_status=''not_in_corpus'' on every '
  'row; primary-source ingestion is a filed work item, not attempted here.';

COMMENT ON COLUMN bg_kota_chakra_rings.dvara_assignment IS
  'Reserved for a future dvāra (gate/direction) reading; NOT used by the '
  'current ka_kota_chakra writer (NULL on every row) — disclosed, not an '
  'oversight.';

COMMENT ON COLUMN bg_kota_chakra_rings.table_version IS
  'Zero-padded (vNN) per the ne_vNN precedent (ADJUDICATION-2) so string '
  'ordering (ORDER BY table_version DESC) sorts correctly across v01..v10+. '
  'A revision is a new vNN row set landed by INSERT, never an in-place edit '
  'of a prior version''s rows.';

-- ── 27-row seed (transcribed EXACTLY from the prior inline dict — see header) ─
-- Stambha:    4, 11, 18, 25
-- Durgantara: 3, 5, 10, 12, 17, 19, 24, 26
-- Prakara:    2, 6, 9, 13, 16, 20, 23, 27
-- Bahya:      1, 7, 8, 14, 15, 21, 22   (complement — 7 positions)

INSERT INTO bg_kota_chakra_rings
  (table_version, ring_position, ring_name, ring_index, dvara_assignment, citation, corpus_status, ratified_by)
VALUES
  ('kota_chakra_rings_v01', 1,  'bahya',      4, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 2,  'prakara',    3, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 3,  'durgantara', 2, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 4,  'stambha',    1, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 5,  'durgantara', 2, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 6,  'prakara',    3, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 7,  'bahya',      4, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 8,  'bahya',      4, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 9,  'prakara',    3, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 10, 'durgantara', 2, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 11, 'stambha',    1, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 12, 'durgantara', 2, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 13, 'prakara',    3, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 14, 'bahya',      4, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 15, 'bahya',      4, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 16, 'prakara',    3, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 17, 'durgantara', 2, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 18, 'stambha',    1, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 19, 'durgantara', 2, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 20, 'prakara',    3, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 21, 'bahya',      4, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 22, 'bahya',      4, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 23, 'prakara',    3, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 24, 'durgantara', 2, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 25, 'stambha',    1, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 26, 'durgantara', 2, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01'),
  ('kota_chakra_rings_v01', 27, 'prakara',    3, NULL, 'Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) secondary-source transcription per the W3K citation hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical text. Corpus-ingestion gap filed; see ADJUDICATION-9 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md).', 'not_in_corpus', 'ADJUDICATION-9_2026-08-01')
ON CONFLICT (table_version, ring_position) DO UPDATE SET
  ring_name        = EXCLUDED.ring_name,
  ring_index       = EXCLUDED.ring_index,
  dvara_assignment = EXCLUDED.dvara_assignment,
  citation         = EXCLUDED.citation,
  corpus_status    = EXCLUDED.corpus_status,
  ratified_by      = EXCLUDED.ratified_by;

-- ── asset_registry seed row for `bg_kota_chakra_rings` (Nirmāṇa contract
-- §2.5.1: seed row lands in the SAME PR as the writer) ───────────────────────

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer, has_substeps,
    writer_timeout_seconds,
    layer_name, layer_index, catalog_status, asset_kind,
    depends_on
) VALUES (
    'bg_kota_chakra_rings',
    'brahmagyan',
    72,
    'Koṭa-Cakra Valaya-Sāraṇī',
    'Kota-Chakra Ring Table',
    'ADJUDICATION-9: the Kota-Chakra fort-chakra ring partition '
    '(stambha/durgantara/prakara/bahya, 1-indexed distance from janma '
    'nakshatra), moved from an inline writer-code dict to a versioned L0 '
    'global reference table. Tier-(iii) secondary-source transcription; '
    'corpus_status=''not_in_corpus'' on every row; ingestion work item filed '
    'for the primary source, not attempted here. Consumed by ka_kota_chakra.',
    'postgres_table', 'bg_kota_chakra_rings',
    'SELECT COUNT(*) FROM bg_kota_chakra_rings',
    'SELECT pg_total_relation_size(''bg_kota_chakra_rings'')',
    27, 'global', true, true, false,
    60,
    'Brahmagyan', 'L0', 'CURRENT', 'data',
    ARRAY[]::text[]
) ON CONFLICT (asset_id) DO UPDATE SET
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

-- ── ka_kota_chakra gains the bg_kota_chakra_rings dependency edge (ADJUDICATION-9
-- item 3) — one-line registry edit, same PR ───────────────────────────────────

UPDATE asset_registry
   SET depends_on = ARRAY['ga_positions', 'bg_ephemeris', 'bg_kota_chakra_rings']::text[]
 WHERE asset_id = 'ka_kota_chakra';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   UPDATE asset_registry SET depends_on = ARRAY['ga_positions', 'bg_ephemeris']::text[]
--     WHERE asset_id = 'ka_kota_chakra';
--   DELETE FROM asset_registry WHERE asset_id = 'bg_kota_chakra_rings';
--   DROP TABLE IF EXISTS bg_kota_chakra_rings;
--   COMMIT;
-- =============================================================================
