-- Migration 132: ayanamsha_registry — formal DDL for multi-ayanamsha registry
-- Stream A-01 seeded data; this migration ensures schema is complete and constraints are formal.
-- MARSYS-JIS Multi-Ayanamsha Build Orchestrator [BUILD-ORCH-B-09]

-- Create table IF NOT EXISTS (idempotent — A-01 already created it in production)
CREATE TABLE IF NOT EXISTS ayanamsha_registry (
    ayanamsha_id              TEXT        PRIMARY KEY,
    name                      TEXT        NOT NULL,
    formula_type              TEXT        NOT NULL,
    epoch_pin_jd              FLOAT,
    value_at_epoch_deg        FLOAT,
    derivative_per_tropical_year FLOAT    NOT NULL DEFAULT 50.2738,
    current_value_deg         FLOAT,
    is_canonical              BOOLEAN     NOT NULL DEFAULT true,
    capability_only           BOOLEAN     NOT NULL DEFAULT false,
    classical_citation        TEXT,
    notes                     TEXT,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add any missing columns idempotently (no-ops if columns already exist)
ALTER TABLE ayanamsha_registry ADD COLUMN IF NOT EXISTS is_canonical   BOOLEAN     NOT NULL DEFAULT true;
ALTER TABLE ayanamsha_registry ADD COLUMN IF NOT EXISTS capability_only BOOLEAN    NOT NULL DEFAULT false;
ALTER TABLE ayanamsha_registry ADD COLUMN IF NOT EXISTS created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE ayanamsha_registry ADD COLUMN IF NOT EXISTS classical_citation TEXT;
ALTER TABLE ayanamsha_registry ADD COLUMN IF NOT EXISTS notes          TEXT;

-- Index on canonical flag for fast canonical-set lookups
CREATE INDEX IF NOT EXISTS ayan_reg_canonical_idx ON ayanamsha_registry(is_canonical) WHERE is_canonical = true;

-- Seed the 5 canonical ayanamshas; conflict = row already present, skip gracefully
INSERT INTO ayanamsha_registry
    (ayanamsha_id, name, formula_type, derivative_per_tropical_year,
     is_canonical, capability_only, classical_citation, notes)
VALUES
    ('lahiri',          'Lahiri (Chitrapaksha)',      'svp_minus_180',     50.2738,
     true, false,
     'Government of India Calendar Reform Committee 1955',
     'Default Indian national almanac ayanamsha'),
    ('true_chitra',     'True Chitra (Revati)',        'star_fixed',        50.2738,
     true, false,
     'BPHS tradition; Chitra at 180 degrees tropical',
     'Fixes Spica/Chitra at exactly 0 Libra tropical'),
    ('kp',              'Krishnamurti Paddhati (KP)', 'kp_lahiri_variant', 50.2738,
     true, false,
     'K.S. Krishnamurti, Padhdhati Vol 1',
     'Lahiri - 0.883333 degrees offset'),
    ('raman',           'B.V. Raman',                 'raman_formula',     50.2738,
     true, false,
     'B.V. Raman, Hindu Predictive Astrology',
     'Calcutta Ephemeris tradition'),
    ('surya_siddhanta', 'Surya Siddhanta',             'classical_formula', 54.9,
     true, false,
     'Surya Siddhanta classical text',
     'Ancient classical formula from Surya Siddhanta')
ON CONFLICT (ayanamsha_id) DO NOTHING;

COMMENT ON TABLE ayanamsha_registry IS
    '5 canonical ayanamshas + capability-only variants. Primary reference for ayanamsha_id values across all MARSYS tables. Seeded by A-01; schema formalized by migration 132.';
COMMENT ON COLUMN ayanamsha_registry.ayanamsha_id              IS 'Short machine key: lahiri | true_chitra | kp | raman | surya_siddhanta';
COMMENT ON COLUMN ayanamsha_registry.formula_type              IS 'Algorithm family used to compute the ayanamsha value';
COMMENT ON COLUMN ayanamsha_registry.derivative_per_tropical_year IS 'Precession rate in arc-seconds per tropical year';
COMMENT ON COLUMN ayanamsha_registry.is_canonical              IS 'true = included in standard MARSYS computations; false = experimental / capability-only';
COMMENT ON COLUMN ayanamsha_registry.capability_only           IS 'true = registered but not yet fully wired into the computation engine';
