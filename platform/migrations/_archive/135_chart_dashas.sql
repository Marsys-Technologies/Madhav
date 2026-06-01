-- Migration 135: chart_dashas — Prana-depth dasha periods, two-pass mandatory
-- A3-S2 | branch: feature/a3a4a5/a3-schema

CREATE TABLE IF NOT EXISTS chart_dashas (
  dasha_row_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id                  UUID NOT NULL,
  ayanamsha_id              TEXT NOT NULL,
  build_id                  UUID NOT NULL,
  system_id                 TEXT NOT NULL,
  level_n                   INT NOT NULL,
  parent_row_id             UUID REFERENCES chart_dashas(dasha_row_id),
  lord_graha                TEXT NOT NULL,
  lord_sign                 TEXT,
  start_date                DATE NOT NULL,
  end_date                  DATE NOT NULL,
  start_iso                 TIMESTAMPTZ NOT NULL,
  end_iso                   TIMESTAMPTZ NOT NULL,
  duration_days             NUMERIC NOT NULL,
  sandhi_flag               BOOLEAN NOT NULL DEFAULT false,
  karaka_role_at_period     TEXT,
  verification_pass_status  TEXT NOT NULL
    CHECK (verification_pass_status IN ('two_pass_verified','classical_match','divergent_flagged')),
  verification_method       TEXT NOT NULL DEFAULT '',
  citation_ref              TEXT NOT NULL DEFAULT '',
  citation_human            TEXT NOT NULL DEFAULT '',
  computed_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
  engine_version            TEXT NOT NULL DEFAULT ''
);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'chart_dashas'::regclass
      AND contype = 'u'
      AND conname = 'chart_dashas_chart_id_ayanamsha_id_system_id_level_n_start_is_key'
  ) THEN
    ALTER TABLE chart_dashas
      ADD CONSTRAINT chart_dashas_chart_id_ayanamsha_id_system_id_level_n_start_is_key
      UNIQUE (chart_id, ayanamsha_id, system_id, level_n, start_iso, build_id);
  END IF;
END
$$;

CREATE INDEX IF NOT EXISTS cd_temporal_lookup_idx ON chart_dashas
  (chart_id, ayanamsha_id, system_id, level_n, start_date, end_date);

CREATE INDEX IF NOT EXISTS cd_lord_lookup_idx ON chart_dashas
  (chart_id, ayanamsha_id, lord_graha, system_id);

CREATE INDEX IF NOT EXISTS cd_parent_idx ON chart_dashas (parent_row_id);
