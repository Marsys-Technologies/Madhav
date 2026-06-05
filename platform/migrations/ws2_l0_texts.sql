-- ws2_l0_texts.sql
-- BRAHMA WS-2 L0 Brahmagyan: Classical Texts corpus tables
--
-- Contract (L0_CONTRACT_REGISTRY_SEED §C 0.3):
--   brahmagyan.texts: primary-source corpus (original + translation, verse-addressable)
--   Each text has a canonical text_id; chunks have verse_ref; provenance on every unit
--
-- Volume floor: >= 50 verse chunks; each chunk has verse_ref; all rows have source_citation
-- Gate: text.read('BPHS', 'CH1:V1') resolves; chunk count >= 50; licensing cleared
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS classical_text_chunks CASCADE;
--   DROP TABLE IF EXISTS classical_texts CASCADE;
-- ─────────────────────────────────────────────────────────────────────────────

-- ── classical_texts ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS classical_texts (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  text_id         TEXT        NOT NULL UNIQUE,   -- stable slug, e.g. 'bphs','phaladeepika'
  title_en        TEXT        NOT NULL,
  title_sa        TEXT,
  author          TEXT,
  school          TEXT        NOT NULL,   -- 'parashari','jaimini','kp','tajaka'
  tradition       TEXT        NOT NULL,   -- 'vedic','kp','western'
  tier            SMALLINT    NOT NULL DEFAULT 1 CHECK (tier BETWEEN 1 AND 3),
  -- 1=primary canonical, 2=secondary classical, 3=modern/derivative
  license         TEXT        NOT NULL,  -- 'public_domain','open_access','proprietary_stub'
  license_cleared BOOLEAN     NOT NULL DEFAULT TRUE,
  total_chapters  SMALLINT,
  total_verses    INT,
  source_edition  TEXT,
  ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE classical_texts IS
  'BRAHMA L0 Brahmagyan: classical Jyotish text registry. '
  'Each text_id is stable and referenced by chunks and the retrieval tool. '
  'tier=1 primary sources; license_cleared=false means stubbed (not ingested). '
  'Gate: BG-0-3. WS-2 depth build.';

-- ── classical_text_chunks ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS classical_text_chunks (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  text_id         TEXT        NOT NULL REFERENCES classical_texts(text_id) ON DELETE CASCADE,
  chunk_id        TEXT        NOT NULL UNIQUE,   -- 'bphs_ch01_v001'
  verse_ref       TEXT        NOT NULL,          -- 'CH1:V1', 'CH2:V15-V18'
  chapter         SMALLINT    NOT NULL,
  verse_start     SMALLINT    NOT NULL,
  verse_end       SMALLINT    NOT NULL,
  content_sa      TEXT,                          -- Sanskrit original (may be null if unavailable)
  content_en      TEXT        NOT NULL,          -- English translation
  content_summary TEXT,                          -- one-line summary for retrieval
  topics          TEXT[]      NOT NULL DEFAULT '{}',  -- searchable topic tags
  source_citation TEXT        NOT NULL,
  ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_classical_chunks_text_id
  ON classical_text_chunks (text_id, chapter, verse_start);

CREATE INDEX IF NOT EXISTS idx_classical_chunks_verse_ref
  ON classical_text_chunks (verse_ref);

CREATE INDEX IF NOT EXISTS idx_classical_chunks_topics
  ON classical_text_chunks USING gin (topics);

COMMENT ON TABLE classical_text_chunks IS
  'BRAHMA L0 Brahmagyan: verse-addressable text chunks for classical texts. '
  'Each chunk has a stable chunk_id and verse_ref for citation. '
  'Topics array enables semantic + keyword retrieval. '
  'Gate: BG-0-3. WS-2 depth build.';
