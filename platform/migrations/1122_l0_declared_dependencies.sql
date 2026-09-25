-- Migration 1122: L0 declared dependencies — sync live asset_registry.depends_on
-- to the W-L0-2 seed values for 16 consumer assets.
-- Created: 2026-09-25
--
-- W-L0-2 (MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md §4.2, "Declared
-- dependencies and declared use"): 21 of 40 L0 assets had no cross-layer
-- consumer declared while all 40 are read by code. The writer-side census
-- (python-sidecar/brahmagyan/l0_declared_use_register_v1.json) recorded every
-- code read of a bg_* table; each writer-side read is now a registered
-- depends_on edge on the consumer's seed row. This migration carries those
-- seed values into the live registry.
--
-- Companion code change (same worktree, prerequisite): the 16 depends_on
-- arrays in scripts/seed/asset_registry_seed.ts carry the new edges (each
-- marked with a `// W-L0-2 (2026-09-25)` comment), and
-- scripts/__tests__/l0_declared_dependencies.test.ts is the standing detector
-- that refuses any undeclared writer-side read. The 28-row pin in
-- scripts/__tests__/asset_registry_seed_dag_parity.test.ts was updated in
-- place (denominator unchanged).
--
-- Reconciliation note (census-verified 2026-09-25): ka_gochara and ka_kshetra
-- live rows already carried edges the seed lacked (migration-governed live
-- without seed backfill — e.g. ka_gochara's bg_ephemeris/bg_transit_rules/
-- ka_vedha_gochara/ka_moorti_nirnaya/ga_* set, ka_kshetra's ka_vedha_gochara).
-- The canonical arrays below are the live+seed UNION; no live edge is dropped.
--
-- Guard discipline (migration 1075/1120/1121 pattern): this migration refuses
-- to run if (a) any of the 16 assets is absent, (b) any canonical edge names
-- an asset_id absent from the registry (no phantom declarations), or (c) any
-- of the 16 live rows carries a depends_on element outside its canonical
-- array — that would be an edge added after the census, which must not be
-- silently dropped. Converging a row whose live array is a subset of the
-- canonical array is the intended no-op-safe path (safe re-run).
--
-- HELD: authored 2026-09-25 against the unreconciled _migrations_applied
-- ledger (1080–1095 effects live, ledger empty). Apply only after the
-- consolidation session (madhav-65) reconciles the ledger and the strategy
-- session confirms the number. Number 1122 chosen by scanning every origin/*
-- head across BOTH platform/migrations/ (head 1091) and
-- platform/supabase/migrations/ (head 1090): no 1092–1199 exists on any ref;
-- 1120 and 1121 are this session's W-L0-1 and W-L0-9 migrations.
--
-- Transaction ownership belongs to migrate.ts.

BEGIN;

DO $$
DECLARE
  missing_id text;
BEGIN
  -- Pre-flight (a): all 16 assets must exist.
  FOR missing_id IN
    SELECT v.id FROM (VALUES
      ('ga_sensitive_degree'),
      ('ga_structural'),
      ('ga_condition'),
      ('ga_yoga'),
      ('ga_medical'),
      ('bo_laksana'),
      ('bo_pratijna'),
      ('bo_upaya'),
      ('bo_grounding'),
      ('ka_gochara'),
      ('ka_gochara_resonance'),
      ('ka_gochara_v3_century_materialize'),
      ('ka_kshetra'),
      ('ph_nimitta'),
      ('ph_rectification'),
      ('mi_darshana')
    ) AS v(id)
    WHERE NOT EXISTS (SELECT 1 FROM asset_registry a WHERE a.asset_id = v.id)
  LOOP
    RAISE EXCEPTION 'migration 1122 refuses: asset % absent from asset_registry', missing_id;
  END LOOP;

  -- Pre-flight (b): every canonical edge must name a registered asset (no
  -- phantom declarations).
  FOR missing_id IN
    SELECT DISTINCT edge FROM (
      SELECT unnest(canonical) AS edge FROM (VALUES
        ('ga_sensitive_degree'::text, ARRAY['ga_positions','bg_nakshatra']::text[]),
        ('ga_structural', ARRAY['ga_dashas','ga_nakshatra','ga_panchanga','ga_positions','ga_sensitive','ga_strength','ga_vargas','bg_yogas','bg_doshas']),
        ('ga_condition', ARRAY['ga_positions','ga_vargas','ga_dashas','bg_dignity_reference']),
        ('ga_yoga', ARRAY['ga_structural','ga_dashas','bg_yogas']),
        ('ga_medical', ARRAY['ga_condition','ga_positions','bg_medical_mappings','bg_nakshatra_medical']),
        ('bo_laksana', ARRAY['bg_rules','ga_positions','ga_strength','ga_sensitive','ga_panchanga','ga_sade_sati','ga_structural','ga_nakshatra','ga_condition','ga_vargas','ga_vichara','bg_texts','bg_yogas','bg_doshas','bg_class_priors']),
        ('bo_pratijna', ARRAY['bo_laksana','bo_sangati','bg_reference']),
        ('bo_upaya', ARRAY['bo_laksana','bo_sangati','ga_structural','ga_dashas','bo_cgm_motifs','bg_remedies']),
        ('bo_grounding', ARRAY['ga_yoga','bo_laksana','bo_sudarshana','bo_nakshatra_semantic','bo_arudha','bo_special_lagna','bo_vargottama_dhana','bg_rules']),
        ('ka_gochara', ARRAY['bg_gochara_arcs','ka_gochara_resonance','bg_ephemeris','bg_transit_rules','ka_vedha_gochara','ka_moorti_nirnaya','ga_positions','ga_dashas','ga_yoga']),
        ('ka_gochara_resonance', ARRAY['bg_transit_rules','bg_ghatana']),
        ('ka_gochara_v3_century_materialize', ARRAY['ka_gochara_resonance','ka_vedha_gochara','ka_moorti_nirnaya','ka_kota_chakra','ka_tithi_pravesha','bg_sky_calendar','bg_ghatana','bg_vedha_malefic_scale','bg_transit_rules']),
        ('ka_kshetra', ARRAY['ka_dasha_kala','ka_gochara_resonance','ga_panchanga','bo_pratijna','bo_sangati','bo_upaya','bg_cohort','bg_class_lifetime_counts','ka_vedha_gochara','bg_ghatana','bg_ephemeris','bg_kp_sublord_division','bg_transit_rules']),
        ('ph_nimitta', ARRAY['ka_sangam','ka_bhavishya_lekha','bo_bimba','bo_samskara','bo_karanajala','bo_sangati','bo_anveshana','bo_cgm_paths','bo_laksana','bg_ghatana']),
        ('ph_rectification', ARRAY['ph_nimitta','bg_formula_constants']),
        ('mi_darshana', ARRAY['mi_pramana','mi_adhilepa','mi_sambandha','mi_pariksha','mi_gunanaka','mi_kula','mi_jivanaghatana','bo_pratijna','bg_ghatana'])
      ) AS c(id, canonical)
    ) edges
    WHERE NOT EXISTS (SELECT 1 FROM asset_registry a WHERE a.asset_id = edges.edge)
  LOOP
    RAISE EXCEPTION 'migration 1122 refuses: canonical edge names unregistered asset %', missing_id;
  END LOOP;

  -- Pre-flight (c): refuse if any live row carries an edge outside its
  -- canonical array — a post-census addition by another session that must not
  -- be silently dropped.
  IF EXISTS (
    SELECT 1 FROM (
      SELECT a.asset_id, d AS live_edge
      FROM asset_registry a
      JOIN (VALUES
        ('ga_sensitive_degree'::text, ARRAY['ga_positions','bg_nakshatra']::text[]),
        ('ga_structural', ARRAY['ga_dashas','ga_nakshatra','ga_panchanga','ga_positions','ga_sensitive','ga_strength','ga_vargas','bg_yogas','bg_doshas']),
        ('ga_condition', ARRAY['ga_positions','ga_vargas','ga_dashas','bg_dignity_reference']),
        ('ga_yoga', ARRAY['ga_structural','ga_dashas','bg_yogas']),
        ('ga_medical', ARRAY['ga_condition','ga_positions','bg_medical_mappings','bg_nakshatra_medical']),
        ('bo_laksana', ARRAY['bg_rules','ga_positions','ga_strength','ga_sensitive','ga_panchanga','ga_sade_sati','ga_structural','ga_nakshatra','ga_condition','ga_vargas','ga_vichara','bg_texts','bg_yogas','bg_doshas','bg_class_priors']),
        ('bo_pratijna', ARRAY['bo_laksana','bo_sangati','bg_reference']),
        ('bo_upaya', ARRAY['bo_laksana','bo_sangati','ga_structural','ga_dashas','bo_cgm_motifs','bg_remedies']),
        ('bo_grounding', ARRAY['ga_yoga','bo_laksana','bo_sudarshana','bo_nakshatra_semantic','bo_arudha','bo_special_lagna','bo_vargottama_dhana','bg_rules']),
        ('ka_gochara', ARRAY['bg_gochara_arcs','ka_gochara_resonance','bg_ephemeris','bg_transit_rules','ka_vedha_gochara','ka_moorti_nirnaya','ga_positions','ga_dashas','ga_yoga']),
        ('ka_gochara_resonance', ARRAY['bg_transit_rules','bg_ghatana']),
        ('ka_gochara_v3_century_materialize', ARRAY['ka_gochara_resonance','ka_vedha_gochara','ka_moorti_nirnaya','ka_kota_chakra','ka_tithi_pravesha','bg_sky_calendar','bg_ghatana','bg_vedha_malefic_scale','bg_transit_rules']),
        ('ka_kshetra', ARRAY['ka_dasha_kala','ka_gochara_resonance','ga_panchanga','bo_pratijna','bo_sangati','bo_upaya','bg_cohort','bg_class_lifetime_counts','ka_vedha_gochara','bg_ghatana','bg_ephemeris','bg_kp_sublord_division','bg_transit_rules']),
        ('ph_nimitta', ARRAY['ka_sangam','ka_bhavishya_lekha','bo_bimba','bo_samskara','bo_karanajala','bo_sangati','bo_anveshana','bo_cgm_paths','bo_laksana','bg_ghatana']),
        ('ph_rectification', ARRAY['ph_nimitta','bg_formula_constants']),
        ('mi_darshana', ARRAY['mi_pramana','mi_adhilepa','mi_sambandha','mi_pariksha','mi_gunanaka','mi_kula','mi_jivanaghatana','bo_pratijna','bg_ghatana'])
      ) AS c(id, canonical) ON a.asset_id = c.id
      CROSS JOIN LATERAL unnest(a.depends_on) AS d
      WHERE d <> ALL (c.canonical)
    ) unexpected
  ) THEN
    RAISE EXCEPTION 'migration 1122 refuses: a live depends_on edge outside the canonical set exists — another session moved on after the census';
  END IF;

  -- Converge: set each row to its canonical array. Rows already canonical are
  -- no-ops; rows whose live array is a strict subset gain the missing edges.
  UPDATE asset_registry SET depends_on = ARRAY['ga_positions','bg_nakshatra']
    WHERE asset_id = 'ga_sensitive_degree';
  UPDATE asset_registry SET depends_on = ARRAY['ga_dashas','ga_nakshatra','ga_panchanga','ga_positions','ga_sensitive','ga_strength','ga_vargas','bg_yogas','bg_doshas']
    WHERE asset_id = 'ga_structural';
  UPDATE asset_registry SET depends_on = ARRAY['ga_positions','ga_vargas','ga_dashas','bg_dignity_reference']
    WHERE asset_id = 'ga_condition';
  UPDATE asset_registry SET depends_on = ARRAY['ga_structural','ga_dashas','bg_yogas']
    WHERE asset_id = 'ga_yoga';
  UPDATE asset_registry SET depends_on = ARRAY['ga_condition','ga_positions','bg_medical_mappings','bg_nakshatra_medical']
    WHERE asset_id = 'ga_medical';
  UPDATE asset_registry SET depends_on = ARRAY['bg_rules','ga_positions','ga_strength','ga_sensitive','ga_panchanga','ga_sade_sati','ga_structural','ga_nakshatra','ga_condition','ga_vargas','ga_vichara','bg_texts','bg_yogas','bg_doshas','bg_class_priors']
    WHERE asset_id = 'bo_laksana';
  UPDATE asset_registry SET depends_on = ARRAY['bo_laksana','bo_sangati','bg_reference']
    WHERE asset_id = 'bo_pratijna';
  UPDATE asset_registry SET depends_on = ARRAY['bo_laksana','bo_sangati','ga_structural','ga_dashas','bo_cgm_motifs','bg_remedies']
    WHERE asset_id = 'bo_upaya';
  UPDATE asset_registry SET depends_on = ARRAY['ga_yoga','bo_laksana','bo_sudarshana','bo_nakshatra_semantic','bo_arudha','bo_special_lagna','bo_vargottama_dhana','bg_rules']
    WHERE asset_id = 'bo_grounding';
  UPDATE asset_registry SET depends_on = ARRAY['bg_gochara_arcs','ka_gochara_resonance','bg_ephemeris','bg_transit_rules','ka_vedha_gochara','ka_moorti_nirnaya','ga_positions','ga_dashas','ga_yoga']
    WHERE asset_id = 'ka_gochara';
  UPDATE asset_registry SET depends_on = ARRAY['bg_transit_rules','bg_ghatana']
    WHERE asset_id = 'ka_gochara_resonance';
  UPDATE asset_registry SET depends_on = ARRAY['ka_gochara_resonance','ka_vedha_gochara','ka_moorti_nirnaya','ka_kota_chakra','ka_tithi_pravesha','bg_sky_calendar','bg_ghatana','bg_vedha_malefic_scale','bg_transit_rules']
    WHERE asset_id = 'ka_gochara_v3_century_materialize';
  UPDATE asset_registry SET depends_on = ARRAY['ka_dasha_kala','ka_gochara_resonance','ga_panchanga','bo_pratijna','bo_sangati','bo_upaya','bg_cohort','bg_class_lifetime_counts','ka_vedha_gochara','bg_ghatana','bg_ephemeris','bg_kp_sublord_division','bg_transit_rules']
    WHERE asset_id = 'ka_kshetra';
  UPDATE asset_registry SET depends_on = ARRAY['ka_sangam','ka_bhavishya_lekha','bo_bimba','bo_samskara','bo_karanajala','bo_sangati','bo_anveshana','bo_cgm_paths','bo_laksana','bg_ghatana']
    WHERE asset_id = 'ph_nimitta';
  UPDATE asset_registry SET depends_on = ARRAY['ph_nimitta','bg_formula_constants']
    WHERE asset_id = 'ph_rectification';
  UPDATE asset_registry SET depends_on = ARRAY['mi_pramana','mi_adhilepa','mi_sambandha','mi_pariksha','mi_gunanaka','mi_kula','mi_jivanaghatana','bo_pratijna','bg_ghatana']
    WHERE asset_id = 'mi_darshana';

  -- Postflight: every row must now equal its canonical array exactly.
  IF EXISTS (
    SELECT 1 FROM asset_registry a
    JOIN (VALUES
      ('ga_sensitive_degree'::text, ARRAY['ga_positions','bg_nakshatra']::text[]),
      ('ga_structural', ARRAY['ga_dashas','ga_nakshatra','ga_panchanga','ga_positions','ga_sensitive','ga_strength','ga_vargas','bg_yogas','bg_doshas']),
      ('ga_condition', ARRAY['ga_positions','ga_vargas','ga_dashas','bg_dignity_reference']),
      ('ga_yoga', ARRAY['ga_structural','ga_dashas','bg_yogas']),
      ('ga_medical', ARRAY['ga_condition','ga_positions','bg_medical_mappings','bg_nakshatra_medical']),
      ('bo_laksana', ARRAY['bg_rules','ga_positions','ga_strength','ga_sensitive','ga_panchanga','ga_sade_sati','ga_structural','ga_nakshatra','ga_condition','ga_vargas','ga_vichara','bg_texts','bg_yogas','bg_doshas','bg_class_priors']),
      ('bo_pratijna', ARRAY['bo_laksana','bo_sangati','bg_reference']),
      ('bo_upaya', ARRAY['bo_laksana','bo_sangati','ga_structural','ga_dashas','bo_cgm_motifs','bg_remedies']),
      ('bo_grounding', ARRAY['ga_yoga','bo_laksana','bo_sudarshana','bo_nakshatra_semantic','bo_arudha','bo_special_lagna','bo_vargottama_dhana','bg_rules']),
      ('ka_gochara', ARRAY['bg_gochara_arcs','ka_gochara_resonance','bg_ephemeris','bg_transit_rules','ka_vedha_gochara','ka_moorti_nirnaya','ga_positions','ga_dashas','ga_yoga']),
      ('ka_gochara_resonance', ARRAY['bg_transit_rules','bg_ghatana']),
      ('ka_gochara_v3_century_materialize', ARRAY['ka_gochara_resonance','ka_vedha_gochara','ka_moorti_nirnaya','ka_kota_chakra','ka_tithi_pravesha','bg_sky_calendar','bg_ghatana','bg_vedha_malefic_scale','bg_transit_rules']),
      ('ka_kshetra', ARRAY['ka_dasha_kala','ka_gochara_resonance','ga_panchanga','bo_pratijna','bo_sangati','bo_upaya','bg_cohort','bg_class_lifetime_counts','ka_vedha_gochara','bg_ghatana','bg_ephemeris','bg_kp_sublord_division','bg_transit_rules']),
      ('ph_nimitta', ARRAY['ka_sangam','ka_bhavishya_lekha','bo_bimba','bo_samskara','bo_karanajala','bo_sangati','bo_anveshana','bo_cgm_paths','bo_laksana','bg_ghatana']),
      ('ph_rectification', ARRAY['ph_nimitta','bg_formula_constants']),
      ('mi_darshana', ARRAY['mi_pramana','mi_adhilepa','mi_sambandha','mi_pariksha','mi_gunanaka','mi_kula','mi_jivanaghatana','bo_pratijna','bg_ghatana'])
    ) AS c(id, canonical) ON a.asset_id = c.id
    WHERE a.depends_on IS DISTINCT FROM c.canonical
  ) THEN
    RAISE EXCEPTION 'migration 1122 postflight registry mismatch';
  END IF;
END $$;

COMMIT;

-- =============================================================================
-- VERIFY (falsifier — run after apply):
--   SELECT asset_id, depends_on FROM asset_registry
--   WHERE asset_id IN ('ga_sensitive_degree','ga_structural','ga_condition',
--     'ga_yoga','ga_medical','bo_laksana','bo_pratijna','bo_upaya','bo_grounding',
--     'ka_gochara','ka_gochara_resonance','ka_gochara_v3_century_materialize',
--     'ka_kshetra','ph_nimitta','ph_rectification','mi_darshana')
--   ORDER BY asset_id;
--   -- expect: each depends_on equal to the canonical array above.
--
-- DOWN (manual rollback — restores exactly the pre-W-L0-2 state; the
-- ka_gochara and ka_kshetra entries are the live-verified pre-sets, which
-- include the migration-governed live edges the seed lacked):
--   BEGIN;
--   UPDATE asset_registry SET depends_on = ARRAY['ga_positions'] WHERE asset_id = 'ga_sensitive_degree';
--   UPDATE asset_registry SET depends_on = ARRAY['ga_dashas','ga_nakshatra','ga_panchanga','ga_positions','ga_sensitive','ga_strength','ga_vargas'] WHERE asset_id = 'ga_structural';
--   UPDATE asset_registry SET depends_on = ARRAY['ga_positions','ga_vargas','ga_dashas'] WHERE asset_id = 'ga_condition';
--   UPDATE asset_registry SET depends_on = ARRAY['ga_structural','ga_dashas'] WHERE asset_id = 'ga_yoga';
--   UPDATE asset_registry SET depends_on = ARRAY['ga_condition','ga_positions'] WHERE asset_id = 'ga_medical';
--   UPDATE asset_registry SET depends_on = ARRAY['bg_rules','ga_positions','ga_strength','ga_sensitive','ga_panchanga','ga_sade_sati','ga_structural','ga_nakshatra','ga_condition','ga_vargas','ga_vichara'] WHERE asset_id = 'bo_laksana';
--   UPDATE asset_registry SET depends_on = ARRAY['bo_laksana','bo_sangati'] WHERE asset_id = 'bo_pratijna';
--   UPDATE asset_registry SET depends_on = ARRAY['bo_laksana','bo_sangati','ga_structural','ga_dashas','bo_cgm_motifs'] WHERE asset_id = 'bo_upaya';
--   UPDATE asset_registry SET depends_on = ARRAY['ga_yoga','bo_laksana','bo_sudarshana','bo_nakshatra_semantic','bo_arudha','bo_special_lagna','bo_vargottama_dhana'] WHERE asset_id = 'bo_grounding';
--   UPDATE asset_registry SET depends_on = ARRAY['ka_gochara_resonance','bg_ephemeris','bg_transit_rules','ka_vedha_gochara','ka_moorti_nirnaya','ga_positions','ga_dashas','ga_yoga'] WHERE asset_id = 'ka_gochara';
--   UPDATE asset_registry SET depends_on = ARRAY['bg_transit_rules'] WHERE asset_id = 'ka_gochara_resonance';
--   UPDATE asset_registry SET depends_on = ARRAY['ka_gochara_resonance','ka_vedha_gochara','ka_moorti_nirnaya','ka_kota_chakra','ka_tithi_pravesha','bg_sky_calendar'] WHERE asset_id = 'ka_gochara_v3_century_materialize';
--   UPDATE asset_registry SET depends_on = ARRAY['ka_dasha_kala','ka_gochara_resonance','ga_panchanga','bo_pratijna','bo_sangati','bo_upaya','bg_cohort','bg_class_lifetime_counts','ka_vedha_gochara'] WHERE asset_id = 'ka_kshetra';
--   UPDATE asset_registry SET depends_on = ARRAY['ka_sangam','ka_bhavishya_lekha','bo_bimba','bo_samskara','bo_karanajala','bo_sangati','bo_anveshana','bo_cgm_paths','bo_laksana'] WHERE asset_id = 'ph_nimitta';
--   UPDATE asset_registry SET depends_on = ARRAY['ph_nimitta'] WHERE asset_id = 'ph_rectification';
--   UPDATE asset_registry SET depends_on = ARRAY['mi_pramana','mi_adhilepa','mi_sambandha','mi_pariksha','mi_gunanaka','mi_kula','mi_jivanaghatana','bo_pratijna'] WHERE asset_id = 'mi_darshana';
--   COMMIT;
-- =============================================================================
