-- Migration 148: Tajik Varsha Year Lords (A20 — Hadda fold)
-- Stream D — A20 [BUILD-ORCH-STREAM-D-A20]
-- Fully idempotent (CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS)
-- Source: TEMPORAL_SPINE_ENHANCEMENTS_v1_0.md §1.C + Tajika Neelakanthi

CREATE TABLE IF NOT EXISTS l1_tajik_varsha_year_lords (
  varsha_id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id                UUID        NOT NULL,
  ayanamsha_id            TEXT        NOT NULL,
  build_id                UUID        NOT NULL,
  varsha_year             INT         NOT NULL,         -- Tajik year number (1, 2, ..., 150)
  varsha_start_iso        TIMESTAMPTZ NOT NULL,
  varsha_end_iso          TIMESTAMPTZ NOT NULL,
  age_at_varsha           INT         NOT NULL,
  year_lord               TEXT        NOT NULL,          -- graha name: Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn
  year_lord_method        TEXT        NOT NULL,          -- 'muntha_lord' | 'hadda_lord' | 'abdadhipati'
  muntha_sign             TEXT,                          -- sign where Muntha falls this year
  muntha_house            INT,                           -- house of Muntha
  hadda_lord              TEXT,                          -- Hadda lord for the degree
  hadda_degree_start      NUMERIC,                       -- degree range start
  hadda_degree_end        NUMERIC,                       -- degree range end
  applicable_tajik_yogas_array TEXT[],                   -- active Tajik yogas for this year
  varsha_lagna            TEXT,                          -- rising sign at varsha start
  muntha_context_jsonb    JSONB,                         -- full Muntha analysis
  hadda_context_jsonb     JSONB,                         -- full Hadda context

  -- Verification
  verification_pass_status TEXT        NOT NULL DEFAULT 'unverified',
  citation_ref            TEXT        NOT NULL DEFAULT 'TEMPORAL_SPINE_ENHANCEMENTS_v1_0.md §1.C + FORENSIC §A20',
  citation_human          TEXT        NOT NULL DEFAULT 'Tajika Neelakanthi — Hadda lords + Muntha analysis',
  computed_at             TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE(chart_id, ayanamsha_id, build_id, varsha_year)
);

CREATE INDEX IF NOT EXISTS l1_tajik_varsha_year_lords_chart_idx
  ON l1_tajik_varsha_year_lords (chart_id, ayanamsha_id);

CREATE INDEX IF NOT EXISTS l1_tajik_varsha_year_lords_varsha_idx
  ON l1_tajik_varsha_year_lords (chart_id, ayanamsha_id, varsha_year);
