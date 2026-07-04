-- 406_kala_mimamsa_dag_edge_completeness.sql
-- =============================================================================
-- BA_FULL_ASSET_AUDIT fix-forward pass — close 4 real depends_on gaps found by
-- direct code inspection (writer SQL reads vs. asset_registry.depends_on).
-- These are the 3 BLOCKERs recorded in BA_AUDIT_FIX_PLAN_v1_0.md §BLOCKERS
-- (ka_taranga/ka_sangam, ka_yojaka/bo_pratijna, mi_darshana/bo_pratijna) plus
-- the closely-related ka_avadhi correction found in the same audit pass
-- (BA_FULL_ASSET_AUDIT_REGISTER_v1_0.md, ka_avadhi/ka_taranga/ka_yojaka
-- L1-Registry findings). No writer behavior changes — registry-only.
--
-- 1) ka_yojaka — writer reads bodha_pratijna (JOIN brahma_event_ontology) for
--    P5A pratijna-linkage enrichment (ka_yojaka.py ~lines 67,81) but neither
--    bo_pratijna nor bg_ghatana was declared.
--
-- 2) ka_avadhi — writer never reads kala_activation_predicates (ka_yojaka's
--    target table) anywhere in ka_avadhi.py; 'ka_yojaka' in depends_on is a
--    phantom edge. It DOES read chart_dashas (ga_dashas owns it) and
--    brahma_event_ontology (bg_ghatana owns it), neither declared. Replace the
--    phantom edge with the real hard dependency (ga_dashas) and add bg_ghatana.
--    bo_pratijna (added by migration 395) is correctly retained.
--
-- 3) ka_taranga — writer reads kala_convergence directly (ka_sangam owns it),
--    chart_dashas (ga_dashas), and brahma_event_ontology (bg_ghatana), none
--    declared. ka_avadhi + bo_pratijna (migration 396) are correctly retained.
--
-- 4) mi_darshana — writer reads bodha_pratijna (JOIN brahma_event_ontology)
--    for status/grade + ranked evidence (mi_darshana.py ~lines 240,248,296),
--    bo_pratijna was not declared. bg_ghatana already implied via bo_pratijna
--    per the audit's "L0-bedrock guard-exempted" note; adding it explicitly
--    here too for derivation-ledger completeness (CLAUDE.md §I B.3).
--
-- Idempotent (UPDATE by asset_id; re-running sets the same array).
-- Applied surgically — never via deploy.yml. No rebuild triggered by this
-- migration; it only corrects scheduling/documentation metadata.
-- =============================================================================

BEGIN;

-- (1) ka_yojaka: add bo_pratijna, bg_ghatana
UPDATE asset_registry
   SET depends_on = ARRAY['bo_laksana','bg_transit_rules','ga_dashas','bo_bimba','bo_sangati','bo_pratijna','bg_ghatana']::text[]
 WHERE asset_id = 'ka_yojaka';

-- (2) ka_avadhi: drop phantom 'ka_yojaka', add real 'ga_dashas' + 'bg_ghatana'
UPDATE asset_registry
   SET depends_on = ARRAY['ga_dashas','bo_pratijna','bg_ghatana']::text[]
 WHERE asset_id = 'ka_avadhi';

-- (3) ka_taranga: add 'ka_sangam', 'ga_dashas', 'bg_ghatana'
UPDATE asset_registry
   SET depends_on = ARRAY['ka_avadhi','bo_pratijna','ka_sangam','ga_dashas','bg_ghatana']::text[]
 WHERE asset_id = 'ka_taranga';

-- (4) mi_darshana: add 'bo_pratijna'
UPDATE asset_registry
   SET depends_on = ARRAY['mi_pramana','mi_adhilepa','mi_sambandha','mi_pariksha','mi_gunanaka','mi_kula','mi_jivanaghatana','bo_pratijna']::text[]
 WHERE asset_id = 'mi_darshana';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--
-- BEGIN;
-- UPDATE asset_registry SET depends_on = ARRAY['bo_laksana','bg_transit_rules','ga_dashas','bo_bimba','bo_sangati']::text[] WHERE asset_id = 'ka_yojaka';
-- UPDATE asset_registry SET depends_on = ARRAY['ka_yojaka','bo_pratijna']::text[] WHERE asset_id = 'ka_avadhi';
-- UPDATE asset_registry SET depends_on = ARRAY['ka_avadhi','bo_pratijna']::text[] WHERE asset_id = 'ka_taranga';
-- UPDATE asset_registry SET depends_on = ARRAY['mi_pramana','mi_adhilepa','mi_sambandha','mi_pariksha','mi_gunanaka','mi_kula','mi_jivanaghatana']::text[] WHERE asset_id = 'mi_darshana';
-- COMMIT;
-- =============================================================================
