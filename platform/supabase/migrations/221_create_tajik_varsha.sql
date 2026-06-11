-- 221_create_tajik_varsha.sql
-- =============================================================================
-- Create `l1_tajik_varsha_year_lords` — the per-varsha Vārṣaphal annual-chart
-- store for the `ga_tajaka` L1 asset (the ONE deliberately-parked L1 asset,
-- activated per CLAUDECODE_BRIEF_GA_TAJAKA_VARSHAPHAL_WRITER_v1_0.md §3,
-- DDL from A17_A21_SUPPLEMENTARY_SPEC_v1_0.md §5).
--
-- One row per (chart_id, ayanamsha_id, varsha_year): the solar-return instant,
-- Muntha position, Vārṣeśa (year-lord) by both methods with candidate scores,
-- and the Tājik yogas firing in the annual chart.
--
-- ATOMIC-GRAIN NOTE (sanctioned JSONB): `candidate_lord_jsonb` and
-- `muntha_position_jsonb` are irreducible composites — the 5 candidate
-- office-bearers each carry a Pañcavargīya component breakdown whose cardinality
-- and component set are fixed-by-doctrine but not flatten-able into queryable
-- columns without losing the per-candidate score semantics; the Muntha position
-- bundles {sign, two house framings, lord, degree} as a single chart-point.
-- The queryable atoms — `year_lord`, `varsha_year`, `varsha_start_iso`,
-- `varsha_end_iso`, `year_lord_method` — are first-class columns. The
-- atomic-grain gate accepts this JSONB as sanctioned (documented here + in the
-- writer).
--
-- Idempotent (CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS).
-- Reversible DOWN block below. [verify-against: prod]
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS l1_tajik_varsha_year_lords (
  varsha_id UUID PRIMARY KEY,
  chart_id UUID NOT NULL,
  ayanamsha_id TEXT NOT NULL,
  build_id UUID NOT NULL,
  varsha_year INT NOT NULL,                   -- birth-year-relative (1..N); 1 = birth year
  varsha_start_iso TIMESTAMPTZ NOT NULL,      -- exact solar return (Sun → natal sidereal longitude)
  varsha_end_iso TIMESTAMPTZ NOT NULL,        -- next year's solar return
  year_lord_method TEXT NOT NULL,             -- 'tajik_classical' | 'panchavargiya'
  year_lord TEXT NOT NULL,                    -- Vārṣeśa for this varsha (atomic)
  candidate_lord_jsonb JSONB,                 -- 5 office-bearers + Pañcavargīya scores (sanctioned composite)
  muntha_position_jsonb JSONB,                -- {sign, house_from_natal_lagna, house_from_varsha_lagna, lord, degree} (sanctioned composite)
  applicable_tajik_yogas_array TEXT[],        -- Ithasala/Ishrafa/Nakta/Kambula/Dutthottha fired this year
  classical_source_citation TEXT NOT NULL,
  ephemeris_audit_jsonb JSONB,
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL,
  citation_human TEXT NOT NULL,
  computed_at TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, varsha_year)
);

CREATE INDEX IF NOT EXISTS tajik_varsha_chart_idx
  ON l1_tajik_varsha_year_lords (chart_id, ayanamsha_id);
CREATE INDEX IF NOT EXISTS tajik_varsha_year_idx
  ON l1_tajik_varsha_year_lords (chart_id, ayanamsha_id, varsha_year);

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DROP TABLE IF EXISTS l1_tajik_varsha_year_lords;
--   COMMIT;
-- =============================================================================
