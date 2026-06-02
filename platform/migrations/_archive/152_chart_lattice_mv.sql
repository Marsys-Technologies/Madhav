-- Migration 152: l25_chart_lattice_snapshots — META-α Structural Timeline Lattice
-- META-α-S1 [BUILD-ORCH-STREAM-D-META-ALPHA-S1]
-- Single-read omniscient join for any moment in a native's life.
-- Per: META_ENHANCEMENTS_SPEC_v1_0.md §1
--
-- Design: regular table with UNIQUE(chart_id, ayanamsha_id, date_iso) rather than
-- a PostgreSQL MATERIALIZED VIEW because:
--   1. MV refresh is all-or-nothing — we need per-chart selective refresh.
--   2. Cloud Scheduler triggers a Python writer that upserts a rolling 3-year window per chart.
--   3. On-demand compute for historical/future dates outside the window is also supported.
--
-- All statements are idempotent (CREATE TABLE IF NOT EXISTS, CREATE INDEX IF NOT EXISTS).

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS l25_chart_lattice_snapshots (
  snapshot_id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id                      UUID        NOT NULL,
  ayanamsha_id                  TEXT        NOT NULL,
  build_id                      UUID,

  -- The calendar date this snapshot represents
  date_iso                      DATE        NOT NULL,

  -- A7: active dasha summary at date_iso
  -- {vimshottari: {maha, antar, pratyantar}, yogini: {...}, chara: {...}}
  active_dasha_jsonb            JSONB,

  -- A15: synchronicity window(s) active at date_iso
  -- [{window_id, intensity, type}]
  active_synchronicity_jsonb    JSONB,

  -- A16: predicted-event anchors whose window contains date_iso
  -- [{anchor_id, label, confidence}]
  active_anchors_jsonb          JSONB,

  -- A18: vedhas active at date_iso
  -- [{vedha_id, severity, type}]
  active_vedhas_jsonb           JSONB,

  -- A19: Bhrigu Bindu transits within ±30 days of date_iso
  -- [{hit_id, graha}]
  nearby_bhrigu_hits_jsonb      JSONB,

  -- A21: exact graha aspects within ±15 days of date_iso
  -- [{aspect_id, natal_graha, transit_graha, exact_date}]
  nearby_exact_aspects_jsonb    JSONB,

  -- Cross-asset aggregated metrics
  total_active_pattern_count    INT         NOT NULL DEFAULT 0,
  resonance_class_at_date       TEXT        CHECK (resonance_class_at_date IN ('high','medium','low','quiescent')),
  high_priority_attention_flag  BOOLEAN     NOT NULL DEFAULT false,

  -- Embedding for cross-chart moment similarity (populated by Vertex AI step)
  lattice_moment_embedding_vec  vector(768),

  computed_at                   TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE (chart_id, ayanamsha_id, date_iso)
);

-- Primary access pattern: single-date lookup
CREATE INDEX IF NOT EXISTS lattice_chart_date_idx
  ON l25_chart_lattice_snapshots (chart_id, ayanamsha_id, date_iso);

-- High-priority attention flag filter (partial index — small, fast)
CREATE INDEX IF NOT EXISTS lattice_attention_idx
  ON l25_chart_lattice_snapshots (chart_id, ayanamsha_id)
  WHERE high_priority_attention_flag = true;

-- Cross-chart moment-similarity search via HNSW (embedding must be present)
CREATE INDEX IF NOT EXISTS lattice_embedding_hnsw
  ON l25_chart_lattice_snapshots USING hnsw (lattice_moment_embedding_vec vector_cosine_ops)
  WHERE lattice_moment_embedding_vec IS NOT NULL;

-- Resonance class range queries
CREATE INDEX IF NOT EXISTS lattice_resonance_idx
  ON l25_chart_lattice_snapshots (chart_id, ayanamsha_id, resonance_class_at_date);

-- Range query: date window scans
CREATE INDEX IF NOT EXISTS lattice_date_range_idx
  ON l25_chart_lattice_snapshots (chart_id, ayanamsha_id, date_iso, total_active_pattern_count);
