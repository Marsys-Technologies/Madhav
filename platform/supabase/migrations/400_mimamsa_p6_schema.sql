-- Migration 400: Mīmāṃsā v2 schema extensions (BA-P6)
-- Adds: lel_file_sha/lel_source/event_class_id to mimamsa_event_provenance (PD-10 LEL intake)
--       base_rate/brier_vs_null to mimamsa_calibration (Brier vs climatology null)
--       mimamsa_calibration_snapshot table (versioned snapshots for two-key publication)
--       mi_pramana_scoring_weights in brahma_formula_constants (weight unification C6)
--       mi_pariksha_dim_weights in brahma_formula_constants (weight unification C6)

BEGIN;

-- ── 1. mimamsa_event_provenance EXT (PD-10 LEL markdown intake) ──────────────

ALTER TABLE mimamsa_event_provenance
    ADD COLUMN IF NOT EXISTS lel_file_sha   TEXT,
    ADD COLUMN IF NOT EXISTS lel_source     TEXT NOT NULL DEFAULT 'db',
    ADD COLUMN IF NOT EXISTS event_class_id TEXT;

COMMENT ON COLUMN mimamsa_event_provenance.lel_file_sha IS
  'BA-P6 PD-10: MD5 of LIFE_EVENT_LOG_v1_2.md at time of build. '
  'Provenance rows are "pinned" to this SHA — a changed file SHA triggers rebuild.';

COMMENT ON COLUMN mimamsa_event_provenance.lel_source IS
  'BA-P6 PD-10: "markdown" (from LEL .md file, canonical) | "db" (from life_events table, fallback). '
  'Markdown is the primary source per PD-10; DB is empty/chart-less.';

COMMENT ON COLUMN mimamsa_event_provenance.event_class_id IS
  'BA-P6 PD-10: event_class_id from brahma_event_ontology matching_rules. '
  'NULL if no ontology match for this event category+subcategory.';

-- ── 2. mimamsa_calibration EXT (Brier vs climatology null) ───────────────────

ALTER TABLE mimamsa_calibration
    ADD COLUMN IF NOT EXISTS base_rate       DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS brier_vs_null   DOUBLE PRECISION;

COMMENT ON COLUMN mimamsa_calibration.base_rate IS
  'BA-P6: climatology null base rate from brahma_event_ontology for this event_class. '
  'Sharpness of the model enters through the null (lower base_rate = harder test).';

COMMENT ON COLUMN mimamsa_calibration.brier_vs_null IS
  'BA-P6: Brier skill score vs climatology null. '
  'brier_vs_null = 1 - (model_brier / null_brier). Positive = beats null.';

-- ── 3. mimamsa_calibration_snapshot (two-key versioned snapshots) ─────────────

CREATE TABLE IF NOT EXISTS mimamsa_calibration_snapshot (
    snapshot_id             TEXT        NOT NULL,
    snapshot_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    chart_id                UUID        NOT NULL,
    proposing_executor      TEXT        NOT NULL,
    acharya_pratinidhi_key  TEXT,
    two_key_complete        BOOLEAN     NOT NULL DEFAULT false,
    cells_jsonb             JSONB,
    delta_from_prior_jsonb  JSONB,
    publication_status      TEXT        NOT NULL DEFAULT 'proposed',
    formula_version         TEXT        NOT NULL,
    CONSTRAINT mimamsa_calibration_snapshot_pk PRIMARY KEY (snapshot_id)
);

COMMENT ON TABLE mimamsa_calibration_snapshot IS
  'BA-P6 Step 4: Two-key versioned calibration snapshots. '
  'key-1 = proposing_executor (mi_gunanaka write), key-2 = Ācārya-Pratinidhi (native sign-off). '
  'Both keys required for publication_status=published. '
  'Snapshot flows to exactly three sinks: bg_class_priors overlay, anchor lift calibrations, '
  'triangulation tradition-weights.';

-- ── 4. Weight unification — scoring weights in brahma_formula_constants ───────

INSERT INTO brahma_formula_constants
  (constant_id, value_jsonb, class, consumer_assets, citation_or_ratification, calibratable, bounds, version)
VALUES
  ('mi_pramana_scoring_weights',
    '{"timing":0.30,"magnitude":0.20,"domain":0.25,"falsifier":0.15,"manifestation":0.10}',
    'native_judgment',
    ARRAY['mi_pramana','mi_pariksha'],
    'BA-P6 C6 weight unification: mi_pramana scoring dimension weights retired from inline code to registry. '
    'Sum must = 1.0. L5-calibratable within bounds.',
    true,
    '{"timing":[0.20,0.40],"magnitude":[0.10,0.30],"domain":[0.15,0.35],"falsifier":[0.05,0.25],"manifestation":[0.05,0.20]}',
    '1.0'),
  ('mi_pariksha_attribution_weights',
    '{"timing":0.30,"magnitude":0.20,"domain":0.25,"falsifier":0.15,"manifestation":0.10}',
    'native_judgment',
    ARRAY['mi_pariksha'],
    'BA-P6 C6: mi_pariksha._DIM_WEIGHTS retired from inline code to registry. '
    'Attribution dimension weights; must mirror mi_pramana_scoring_weights sum=1.0.',
    true,
    '{"timing":[0.20,0.40],"magnitude":[0.10,0.30],"domain":[0.15,0.35],"falsifier":[0.05,0.25],"manifestation":[0.05,0.20]}',
    '1.0'),
  ('mi_gunanaka_shrinkage_k',
    '{"k":5.0,"description":"Smoothing strength for hierarchical shrinkage. posterior = (n*likelihood + k*prior) / (n+k). At n=0, posterior=classical prior."}',
    'native_judgment',
    ARRAY['mi_gunanaka'],
    'BA-P6: shrinkage smoothing constant k=5 replaces n>=10 hard gate. Range [2,10].',
    true,
    '{"k":[2.0,10.0]}',
    '1.0')
ON CONFLICT (constant_id)
DO UPDATE SET
    value_jsonb              = EXCLUDED.value_jsonb,
    consumer_assets          = EXCLUDED.consumer_assets,
    citation_or_ratification = EXCLUDED.citation_or_ratification,
    bounds                   = EXCLUDED.bounds;

COMMIT;
