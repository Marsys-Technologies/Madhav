-- Migration 132: ayanamsha_registry table
-- BUILD-ORCH-A-01 | G20 multi-ayanamsha support
-- Created: 2026-05-29

CREATE TABLE IF NOT EXISTS ayanamsha_registry (
  ayanamsha_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  formula_type TEXT NOT NULL,
  epoch_pin_jd FLOAT,
  value_at_epoch_deg FLOAT,
  derivative_per_tropical_year FLOAT NOT NULL,
  current_value_deg FLOAT,
  is_canonical BOOLEAN DEFAULT true,
  capability_only BOOLEAN DEFAULT false,
  classical_citation TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO ayanamsha_registry (ayanamsha_id, name, formula_type, derivative_per_tropical_year, is_canonical, classical_citation, notes) VALUES
  ('lahiri', 'Lahiri (Chitrapaksha)', 'svp_minus_180', 50.2738, true, 'Government of India Calendar Reform Committee 1955', 'Default Indian national almanac ayanamsha'),
  ('true_chitra', 'True Chitra (Revati)', 'star_fixed', 50.2738, true, 'BPHS tradition; Chitra at 180 degrees tropical', 'Fixes Spica/Chitra at exactly 0 Libra tropical'),
  ('kp', 'Krishnamurti Paddhati (KP)', 'kp_lahiri_variant', 50.2738, true, 'K.S. Krishnamurti, Padhdhati Vol 1', 'Lahiri - 0.883333 degrees offset'),
  ('raman', 'B.V. Raman', 'raman_formula', 50.2738, true, 'B.V. Raman, Hindu Predictive Astrology', 'Calcutta Ephemeris tradition'),
  ('surya_siddhanta', 'Surya Siddhanta', 'classical_formula', 54.9, true, 'Surya Siddhanta classical text', 'Ancient classical formula from Surya Siddhanta')
ON CONFLICT (ayanamsha_id) DO NOTHING;
