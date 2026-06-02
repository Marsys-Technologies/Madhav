-- Phase 14C Stream A: life_events, life_events_staging, sade_sati_phases, sade_sati_phases_staging
-- life_events: 36 rows from LIFE_EVENT_LOG_v1_2.md with Swiss Ephemeris chart_state snapshots.
-- sade_sati_phases: 8-12 rows across 4 Saturn cycles (pre-birth + 3 lifetime).
BEGIN;

CREATE TABLE IF NOT EXISTS life_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id TEXT UNIQUE NOT NULL,       -- 'EVT.MARRIAGE_2014_05', 'EVT.JOB_CHANGE_2019_03'
  event_date DATE NOT NULL,
  category TEXT NOT NULL,              -- 'marriage'|'career'|'health'|'family'|'spiritual'|'travel'|'finance'
  description TEXT NOT NULL,
  significance TEXT,                   -- 'major'|'moderate'|'minor'
  chart_state JSONB NOT NULL,          -- pre-computed transit + dasha state at event time (Swiss Ephemeris from LEL v1.2)
  source_section TEXT NOT NULL,
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  provenance JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_life_events_date ON life_events(event_date);
CREATE INDEX IF NOT EXISTS idx_life_events_category ON life_events(category, event_date);

CREATE TABLE IF NOT EXISTS life_events_staging (LIKE life_events INCLUDING ALL);

CREATE TABLE IF NOT EXISTS sade_sati_phases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cycle_number SMALLINT NOT NULL,      -- 1, 2, 3 (lifetime cycles)
  phase TEXT NOT NULL CHECK (phase IN ('pre_birth', 'rising', 'peak', 'setting', 'gap')),
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  saturn_sign_at_start TEXT NOT NULL,
  notes TEXT,
  source_section TEXT NOT NULL,
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  UNIQUE(cycle_number, phase, start_date)
);

CREATE INDEX IF NOT EXISTS idx_sade_sati_dates ON sade_sati_phases(start_date, end_date);

CREATE TABLE IF NOT EXISTS sade_sati_phases_staging (LIKE sade_sati_phases INCLUDING ALL);

COMMIT;
