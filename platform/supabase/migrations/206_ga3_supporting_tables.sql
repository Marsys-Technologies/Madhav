-- Migration 206: GA3 supporting tables + index completion
-- Creates: chart_dashas, chart_facts_history, chart_facts_supersedence,
--          l25_msr_signals, l25_cdlm_cells, l25_cgm_nodes, l25_cgm_edges,
--          l25_rm_resonances, l25_ucn_digests (empty — L2 Bodha writes them).
-- Adds: remaining A3 §9 indexes on chart_facts missing from migration 204.
-- Adds: fact_category/fact_subject indexes on ganita_positions.
-- Per: GA3_CHART_FACTS_WRITER_BRIEF §4, A3_CHART_FACTS_SPEC §7–§9, §15.
-- All tables: idempotent (IF NOT EXISTS), reversible down-block below.

BEGIN;

-- ── 1. Complete chart_facts indexes (A3 §9) ─────────────────────────────────
-- Migration 204 added chart_id, category, subject, ayanamsha, build indexes.
-- Missing: combined retrieval index + verification partial index + GIN.

CREATE INDEX IF NOT EXISTS chart_facts_chart_aya_cat_idx
  ON chart_facts (chart_id, ayanamsha_id, fact_category);

CREATE INDEX IF NOT EXISTS chart_facts_chart_aya_sub_idx
  ON chart_facts (chart_id, ayanamsha_id, fact_subject);

CREATE INDEX IF NOT EXISTS chart_facts_chart_cat_sub_key_idx
  ON chart_facts (chart_id, fact_category, fact_subject, fact_key);

CREATE INDEX IF NOT EXISTS chart_facts_verification_idx
  ON chart_facts (verification_pass_status)
  WHERE verification_pass_status != 'single';

CREATE INDEX IF NOT EXISTS chart_facts_jsonb_gin
  ON chart_facts USING gin (fact_value_jsonb);

-- ── 2. chart_dashas (A3 §8) ──────────────────────────────────────────────────
-- Dasha hierarchy: Maha→Antar→Pratyantar→Sookshma (4-level per campaign §B,
-- schema supports 5 via level_n). Two-pass verification MANDATORY — CHECK disallows 'single'.

CREATE TABLE IF NOT EXISTS chart_dashas (
  dasha_row_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id                 UUID NOT NULL,
  ayanamsha_id             TEXT NOT NULL,
  build_id                 UUID NOT NULL,
  system_id                TEXT NOT NULL,
  level_n                  INT NOT NULL,
  parent_row_id            UUID,
  lord_graha               TEXT NOT NULL,
  lord_sign                TEXT,
  start_date               DATE NOT NULL,
  end_date                 DATE NOT NULL,
  start_iso                TIMESTAMPTZ NOT NULL,
  end_iso                  TIMESTAMPTZ NOT NULL,
  duration_days            NUMERIC NOT NULL,
  sandhi_flag              BOOLEAN NOT NULL DEFAULT FALSE,
  karaka_role_at_period    TEXT,
  verification_pass_status TEXT NOT NULL
    CHECK (verification_pass_status IN ('two_pass_verified','classical_match','divergent_flagged')),
  verification_method      TEXT NOT NULL,
  citation_ref             TEXT NOT NULL,
  citation_human           TEXT NOT NULL,
  computed_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  engine_version           TEXT NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, system_id, level_n, start_iso, build_id)
);

CREATE INDEX IF NOT EXISTS cd_temporal_lookup_idx
  ON chart_dashas (chart_id, ayanamsha_id, system_id, level_n, start_date, end_date);

CREATE INDEX IF NOT EXISTS cd_lord_lookup_idx
  ON chart_dashas (chart_id, ayanamsha_id, lord_graha, system_id);

CREATE INDEX IF NOT EXISTS cd_parent_idx
  ON chart_dashas (parent_row_id);

-- ── 3. chart_facts_history (A3 §15) ─────────────────────────────────────────
-- Append-only audit trail. Every chart_facts INSERT fires a copy here.
-- Retention: 30 days (nightly cron purge). No PK (append-only).

CREATE TABLE IF NOT EXISTS chart_facts_history (
  history_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fact_id       TEXT NOT NULL,
  chart_id      UUID NOT NULL,
  build_id      UUID NOT NULL,
  operation     TEXT NOT NULL DEFAULT 'INSERT',
  fact_category TEXT NOT NULL,
  fact_subject  TEXT NOT NULL,
  fact_key      TEXT NOT NULL,
  old_value_text TEXT,
  old_value_num  NUMERIC,
  new_value_text TEXT,
  new_value_num  NUMERIC,
  recorded_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS cfh_chart_idx ON chart_facts_history (chart_id, recorded_at);
CREATE INDEX IF NOT EXISTS cfh_fact_id_idx ON chart_facts_history (fact_id);

-- ── 4. chart_facts_supersedence (A3 §15) ─────────────────────────────────────
-- Records build transitions: old_build → new_build for same logical fact.

CREATE TABLE IF NOT EXISTS chart_facts_supersedence (
  sup_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id           UUID NOT NULL,
  ayanamsha_id       TEXT NOT NULL,
  fact_category      TEXT NOT NULL,
  fact_subject       TEXT NOT NULL,
  fact_key           TEXT NOT NULL,
  old_build_id       UUID NOT NULL,
  new_build_id       UUID NOT NULL,
  old_value_text     TEXT,
  old_value_num      NUMERIC,
  new_value_text     TEXT,
  new_value_num      NUMERIC,
  value_delta_pct    NUMERIC,
  recorded_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS cfs_chart_idx ON chart_facts_supersedence (chart_id, new_build_id);

-- ── 5. L2.5 tables (A3 §7) — DDL only, L2 Bodha writes them ─────────────────

CREATE TABLE IF NOT EXISTS l25_msr_signals (
  signal_id              TEXT PRIMARY KEY,
  chart_id               UUID NOT NULL,
  ayanamsha_id           TEXT NOT NULL,
  build_id               UUID NOT NULL,
  signal_code            TEXT NOT NULL,
  deterministic_strength NUMERIC,
  verification_certainty NUMERIC,
  computed_salience      NUMERIC,
  salience_formula_version TEXT,
  domains_affected       TEXT[],
  constituent_facts_array TEXT[],
  computed_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS l25_cdlm_cells (
  cell_id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id              UUID NOT NULL,
  ayanamsha_id          TEXT NOT NULL,
  build_id              UUID NOT NULL,
  row_domain            TEXT NOT NULL,
  col_domain            TEXT NOT NULL,
  shared_factor_count   INT,
  linkage_strength      NUMERIC,
  constituent_facts_array TEXT[],
  computed_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS l25_cgm_nodes (
  node_id               TEXT PRIMARY KEY,
  chart_id              UUID NOT NULL,
  ayanamsha_id          TEXT NOT NULL,
  build_id              UUID NOT NULL,
  node_type             TEXT NOT NULL,
  node_label            TEXT NOT NULL,
  node_weight           NUMERIC,
  constituent_facts_array TEXT[],
  computed_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS l25_cgm_edges (
  edge_id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id              UUID NOT NULL,
  ayanamsha_id          TEXT NOT NULL,
  build_id              UUID NOT NULL,
  from_node_id          TEXT NOT NULL,
  to_node_id            TEXT NOT NULL,
  edge_type             TEXT NOT NULL,
  edge_weight           NUMERIC,
  constituent_facts_array TEXT[],
  computed_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS l25_rm_resonances (
  resonance_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id              UUID NOT NULL,
  ayanamsha_id          TEXT NOT NULL,
  build_id              UUID NOT NULL,
  weak_graha            TEXT NOT NULL,
  remedy_candidate_id   TEXT,
  resonance_score       NUMERIC,
  constituent_facts_array TEXT[],
  computed_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS l25_ucn_digests (
  digest_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id              UUID NOT NULL,
  ayanamsha_id          TEXT NOT NULL,
  build_id              UUID NOT NULL,
  top_configurations    JSONB,
  dominant_grahas       TEXT[],
  dasha_context         TEXT,
  system_convergence_count INT,
  constituent_facts_array TEXT[],
  computed_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMIT;

-- DOWN (manual rollback):
-- DROP TABLE IF EXISTS l25_ucn_digests;
-- DROP TABLE IF EXISTS l25_rm_resonances;
-- DROP TABLE IF EXISTS l25_cgm_edges;
-- DROP TABLE IF EXISTS l25_cgm_nodes;
-- DROP TABLE IF EXISTS l25_cdlm_cells;
-- DROP TABLE IF EXISTS l25_msr_signals;
-- DROP TABLE IF EXISTS chart_facts_supersedence;
-- DROP TABLE IF EXISTS chart_facts_history;
-- DROP TABLE IF EXISTS chart_dashas;
-- DROP INDEX IF EXISTS chart_facts_jsonb_gin;
-- DROP INDEX IF EXISTS chart_facts_verification_idx;
-- DROP INDEX IF EXISTS chart_facts_chart_cat_sub_key_idx;
-- DROP INDEX IF EXISTS chart_facts_chart_aya_sub_idx;
-- DROP INDEX IF EXISTS chart_facts_chart_aya_cat_idx;
