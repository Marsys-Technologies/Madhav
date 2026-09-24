-- 1084_wp7_k1_v1_registry_edges.sql
-- WP7 packets K-1 / V-1 (Kṣetra + Saṅgam read-site dependencies).
--
-- K-1: ka_kshetra's stage-4 `load_legacy_crosscheck` reads `kala_gochara_windows`
--      at the generation `kala_gochara_authority` names, and that authority table
--      is owned by asset ka_vedha_gochara. THIS MIGRATION DECLARES ONLY THAT
--      SERVICE SEAM: ka_kshetra -> ka_vedha_gochara.
-- V-1: ka_sangam reads `kala_gochara_authority` (ka_vedha_gochara) for the
--      authoritative generation seam; declared here.
--
-- HELD, DELIBERATELY: the ka_kshetra -> ka_gochara edge this file first carried
-- (2026-09-24 amendment, at the Kṣetra stream's request; verified here):
--   * `depends_on` is a HARD build gate, not documentation. A dependency must be
--     `lit` for the chart before a build starts (asset_runner: state in
--     ('lit','service_ok')), and the dependencies feed the upstream hash. That edge
--     would make every Kṣetra build wait on the W2G `ka_gochara` writer.
--   * Its target is doubtful. The registry seed registers ka_gochara as owning
--     `kala_gochara_windows`, but its writer writes `kala_gochara_windows_v2`
--     ('2.0', unserved); the served '3.0' rows come from the century materializer
--     and 'v1' from the retired sweep. Kṣetra reads the authoritative generation,
--     not the W2G rows. Registry truth is WP10 step 5's job.
--   * Precedent: migration 569 had to REMOVE a retired-asset edge because its stale
--     throughput row deadlocked every ka_kshetra dispatch at preflight.
--   * The register has no role column, so "counterevidence read" cannot be typed.
-- The declaration is Kṣetra's own row. Its stage-3 executor applies or declines it,
-- stating the consequence. KNOWN, UNVERIFIED CONSEQUENCE of declining: the live-registry
-- test tests/test_dag_edge_guard.py::test_live_registry_has_no_hard_violations
-- (needs DATABASE_URL, no allowlist for this read) may report ka_kshetra reading a
-- table registered to ka_gochara. Whether the guard scans stage4_field.py at all was
-- not run — there is no registry database here.
--
-- EDGE ROLES (recorded here because the register cannot store them):
--   ka_kshetra -> ka_vedha_gochara  : service (authority seam)
--   ka_sangam  -> ka_vedha_gochara  : service (authority seam)
--
-- DOWN (undo path for ops reference — not executed by migrate.ts):
--   UPDATE asset_registry
--   SET depends_on = array_remove(depends_on, 'ka_vedha_gochara')
--   WHERE asset_id IN ('ka_kshetra', 'ka_sangam');
--
-- Idempotent: safe to run multiple times (no-op if edges already present).

BEGIN;

UPDATE asset_registry
SET depends_on = array_append(depends_on, 'ka_vedha_gochara')
WHERE asset_id = 'ka_kshetra'
  AND NOT (depends_on @> ARRAY['ka_vedha_gochara']);

UPDATE asset_registry
SET depends_on = array_append(depends_on, 'ka_vedha_gochara')
WHERE asset_id = 'ka_sangam'
  AND NOT (depends_on @> ARRAY['ka_vedha_gochara']);

COMMIT;
