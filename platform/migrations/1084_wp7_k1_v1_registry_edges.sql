-- 1084_wp7_k1_v1_registry_edges.sql
-- WP7 packets K-1 / V-1 (Kṣetra + Saṅgam read-site dependencies).
--
-- K-1: ka_kshetra's stage-4 `load_legacy_crosscheck` reads
--      `kala_gochara_windows` (asset ka_gochara) and the new authority table
--      (asset ka_vedha_gochara, owner of kala_gochara_authority). Both reads
--      were undeclared in the DAG; this declares them.
-- V-1: ka_sangam reads `kala_gochara_authority` (ka_vedha_gochara) for the
--      authoritative generation seam; declared here.
--
-- EDGE ROLES: `asset_registry.depends_on` is text[] with no role column, so
-- roles cannot be stored. Semantics per packet:
--   ka_kshetra -> ka_gochara        : counterevidence (cross-check corpus)
--   ka_kshetra -> ka_vedha_gochara  : service (authority seam)
--   ka_sangam  -> ka_vedha_gochara  : service (authority seam)
-- The absence of a role column means V-1's "re-type as service" is recorded
-- only here; flagged in REVIEW_REQUEST_K1.md.
--
-- DOWN (undo path for ops reference — not executed by migrate.ts):
--   UPDATE asset_registry
--   SET depends_on = array_remove(array_remove(depends_on, 'ka_gochara'), 'ka_vedha_gochara')
--   WHERE asset_id = 'ka_kshetra';
--   UPDATE asset_registry
--   SET depends_on = array_remove(depends_on, 'ka_vedha_gochara')
--   WHERE asset_id = 'ka_sangam';
--
-- Idempotent: safe to run multiple times (no-op if edges already present).

BEGIN;

UPDATE asset_registry
SET depends_on = array_append(depends_on, 'ka_gochara')
WHERE asset_id = 'ka_kshetra'
  AND NOT (depends_on @> ARRAY['ka_gochara']);

UPDATE asset_registry
SET depends_on = array_append(depends_on, 'ka_vedha_gochara')
WHERE asset_id = 'ka_kshetra'
  AND NOT (depends_on @> ARRAY['ka_vedha_gochara']);

UPDATE asset_registry
SET depends_on = array_append(depends_on, 'ka_vedha_gochara')
WHERE asset_id = 'ka_sangam'
  AND NOT (depends_on @> ARRAY['ka_vedha_gochara']);

COMMIT;
