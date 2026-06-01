-- Migration 009: MSR signals table
-- Creates the msr_signals table for storing Machine-readable Signal Registry
-- entries from MSR_v3_0.md and later versions. Supports per-native isolation,
-- domain/planet/dasha filtering, and forward-looking prediction tracking.
--
-- ROLLBACK:
-- DROP TABLE IF EXISTS msr_signals;

-- ─── Step 1: Create msr_signals table ────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.msr_signals (
  signal_id          VARCHAR(64)     PRIMARY KEY,
  native_id          VARCHAR(64)     NOT NULL DEFAULT 'abhisek',
  domain             VARCHAR(64)     NOT NULL,
  planet             VARCHAR(32),
  house              INTEGER,
  nakshatra          VARCHAR(64),
  dasha_lord         VARCHAR(32),
  confidence         DECIMAL(4,3)    NOT NULL,
  significance       DECIMAL(4,3)    NOT NULL,
  is_forward_looking BOOLEAN         NOT NULL DEFAULT false,
  claim_text         TEXT            NOT NULL,
  classical_basis    TEXT,
  falsifier          TEXT,
  source_file        VARCHAR(256)    NOT NULL,
  source_version     VARCHAR(32)     NOT NULL,
  ingested_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
  CONSTRAINT msr_signals_confidence_range CHECK (confidence BETWEEN 0 AND 1),
  CONSTRAINT msr_signals_significance_range CHECK (significance BETWEEN 0 AND 1)
);

-- ─── Step 2: Indices ──────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_msr_signals_native_domain
  ON public.msr_signals(native_id, domain, confidence DESC, significance DESC);

CREATE INDEX IF NOT EXISTS idx_msr_signals_planet
  ON public.msr_signals(planet) WHERE planet IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_msr_signals_dasha_lord
  ON public.msr_signals(dasha_lord) WHERE dasha_lord IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_msr_signals_forward_looking
  ON public.msr_signals(is_forward_looking) WHERE is_forward_looking = true;
