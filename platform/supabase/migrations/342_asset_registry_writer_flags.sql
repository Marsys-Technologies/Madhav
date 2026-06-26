-- Migration 342 — Asset registry writer flags + global-scope service type corrections
-- Pre-regen blockers sweep, 2026-06-26.
-- (a) Add has_writer boolean: plan resolver filter excludes placeholder assets from build plans.
-- (b) Mark all currently registered WriterBase writers (from discover_all() set).
-- (c) Correct asset_type='service' for ka_graha_sancara and ka_muhurta_seva (were 'data').
-- Idempotent: ADD COLUMN IF NOT EXISTS + UPDATE are safe to re-run.

-- (a) Add has_writer column
ALTER TABLE asset_registry
  ADD COLUMN IF NOT EXISTS has_writer boolean NOT NULL DEFAULT false;

-- (b) Mark registered writers (matches pipeline/orchestrator/writers/ shim set)
UPDATE asset_registry SET has_writer = true WHERE asset_id IN (
  -- L0 Brahmagyan
  'bg_compendium_index', 'bg_concordance', 'bg_dasha_systems', 'bg_dignity_reference',
  'bg_doshas', 'bg_ephemeris', 'bg_medical_mappings', 'bg_nakshatra', 'bg_ontology',
  'bg_prashna_rules', 'bg_reference', 'bg_remedies', 'bg_rules', 'bg_text_index',
  'bg_texts', 'bg_transit_rules', 'bg_vastu_directions', 'bg_yogas',
  -- L1 Gaṇita
  'ga_condition', 'ga_dashas', 'ga_medical', 'ga_nakshatra', 'ga_panchanga',
  'ga_positions', 'ga_prashna', 'ga_sade_sati', 'ga_sensitive', 'ga_strength',
  'ga_structural', 'ga_tajaka', 'ga_transit_anchors', 'ga_vargas', 'ga_vastu', 'ga_yoga',
  -- L2 Bodha
  'bo_anveshana', 'bo_bimba', 'bo_drishti', 'bo_karanajala', 'bo_laksana',
  'bo_pramana_mapa', 'bo_samskara', 'bo_samvada', 'bo_sangati', 'bo_upaya',
  -- L3 Kāla
  'ka_bhavishya_lekha', 'ka_dasha_kala', 'ka_gochara', 'ka_graha_sancara',
  'ka_jivana_parva', 'ka_kala_darshana', 'ka_kalasutra', 'ka_muhurta_seva',
  'ka_sangam', 'ka_vighnakara', 'ka_yojaka',
  -- L4 Phala
  'ph_muhurta', 'ph_nimitta', 'ph_phaladesa', 'ph_pramana', 'ph_pratikara',
  'ph_rectification', 'ph_sankrama', 'ph_sodhana', 'ph_suddha_sodhana'
);

-- (c) Correct asset_type for service writers that were mismarked as 'data'.
-- These are WriterBase self-test writers (scope='global'); asset_runner now routes
-- service assets with a registered writer through _run_data_writer (writer-aware path).
UPDATE asset_registry
  SET asset_type = 'service'
  WHERE asset_id IN ('ka_graha_sancara', 'ka_muhurta_seva')
    AND asset_type = 'data';
