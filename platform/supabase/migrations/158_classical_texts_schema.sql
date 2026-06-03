-- 158_classical_texts_schema.sql
-- Promote archived migrations 053+054+055+056 into the active supabase baseline.
-- Required because 080+081 depend on these tables existing; fresh DB deployments were missing them.
-- 2026-06-03 brahmagyan.texts delta build

-- classical_texts (from archive 053 + 056)
CREATE TABLE IF NOT EXISTS classical_texts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  text_key TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  author TEXT,
  tradition TEXT NOT NULL,
  school TEXT NOT NULL,
  tier INTEGER NOT NULL CHECK (tier IN (1, 2, 3, 4)),
  language_original TEXT NOT NULL,
  translation_author TEXT,
  source_url TEXT,
  procurement_date DATE,
  chunk_count INTEGER DEFAULT 0,
  attribution_baseline_confidence NUMERIC(4, 3) DEFAULT 0.5,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE classical_texts IS 'M8/Brahmagyan: One row per classical Jyotish text. text_key is the canonical ingestion identifier (e.g. bphs, phaladeepika). tier: 1=mandatory, 2=high priority, 3=standard priority, 4=nadi/bnn.';

-- Add work column if not present (080 also adds this, but 080 runs after this)
ALTER TABLE classical_texts ADD COLUMN IF NOT EXISTS work TEXT GENERATED ALWAYS AS (upper(text_key)) STORED;
CREATE INDEX IF NOT EXISTS idx_classical_texts_work ON classical_texts (work);
COMMENT ON COLUMN classical_texts.work IS 'Uppercase canonical short-code generated from text_key. Added for MCP per-work queries.';

-- classical_chunks (from archive 054)
CREATE TABLE IF NOT EXISTS classical_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  text_id UUID NOT NULL REFERENCES classical_texts(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,
  chapter TEXT,
  verse_range TEXT,
  content TEXT NOT NULL,
  embedding VECTOR(768),
  language TEXT NOT NULL DEFAULT 'en',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (text_id, chunk_index)
);
CREATE INDEX IF NOT EXISTS classical_chunks_text_id_idx ON classical_chunks(text_id);
CREATE INDEX IF NOT EXISTS classical_chunks_embedding_idx ON classical_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
COMMENT ON TABLE classical_chunks IS 'M8/Brahmagyan: Chunked classical text passages. embedding is Vertex AI text-embedding-004 (768-dim). ivfflat for cosine similarity search.';

-- classical_attributions (from archive 055)
CREATE TABLE IF NOT EXISTS classical_attributions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  msr_signal_id TEXT NOT NULL,
  chunk_id UUID NOT NULL REFERENCES classical_chunks(id) ON DELETE CASCADE,
  attribution_type TEXT NOT NULL CHECK (
    attribution_type IN ('confirms', 'contradicts', 'partial', 'extends', 'silent')
  ),
  confidence NUMERIC(4, 3) NOT NULL,
  confidence_tier TEXT GENERATED ALWAYS AS (
    CASE
      WHEN confidence >= 0.75 THEN 'HIGH'
      WHEN confidence >= 0.50 THEN 'MEDIUM'
      ELSE 'LOW'
    END
  ) STORED,
  derivation_notes TEXT,
  translation_cross_checked BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS classical_attributions_signal_idx ON classical_attributions(msr_signal_id);
CREATE INDEX IF NOT EXISTS classical_attributions_chunk_idx ON classical_attributions(chunk_id);
CREATE INDEX IF NOT EXISTS classical_attributions_type_idx ON classical_attributions(attribution_type);
COMMENT ON TABLE classical_attributions IS 'M8/Brahmagyan: MSR signal x classical text chunk attribution. confidence_tier is generated.';
