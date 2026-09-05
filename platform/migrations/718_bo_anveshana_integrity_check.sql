-- 718_bo_anveshana_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Adds a real
-- integrity_check_sql for bo_anveshana. Transaction ownership belongs to
-- platform/scripts/migrate.ts. Ninth migration of L2's 710-729 range.
--
-- bo_anveshana mines the other 7 Bodha assets (including bodha_cgm_nodes,
-- known live-orphaned per #1888/D-CND-29's not-yet-resynced state) via
-- broker detection, but its OWN structural guarantees -- the vocabulary
-- and bounds of what it writes -- do not depend on whether those upstream
-- node references still resolve. This check is deliberately scoped to
-- exactly that: never asserts constituent_refs_jsonb / cross_subsystem_
-- refs_jsonb resolve to live CGM nodes (that inherits #1888's open state),
-- only what the writer's own construction logic guarantees regardless.
--
-- Eleven invariants across bodha_discoveries and bodha_anomalies, all
-- independently verified live against all three production charts before
-- landing (C12):
--   1. discovery_class is one of the 5 values the writer's own emit sites
--      can produce (latent_insight, embedding_outlier,
--      distributional_anomaly, cross_subsystem_root, structural_hole) --
--      derived from source, not just the 3 observed live.
--   2. anomaly_type is one of the 3 values the writer's own emit sites
--      can produce (low_salience_high_consequence, embedding_outlier,
--      distributional_anomaly).
--   3. meaningfulness_gate_result is one of the 2 values
--      _passes_meaningfulness_gate's boolean result can be mapped to
--      (promoted, candidate_only).
--   4. non_obviousness_score is bounded [0, 1].
--   5. consequence_score is bounded [0, 1].
--   6. composite_discovery_rank is never negative.
--   7. constituent_refs_jsonb is never NULL (every discovery references
--      at least one substrate id -- ANTI-DRIFT ABSOLUTE: "every discovery
--      REFERENCES substrate ids, never invents a pattern not in the data").
--   8. reasoning_chain_jsonb is never NULL.
--   9. why_an_acharya_misses_it is never NULL or empty.
--   10. meaningfulness_basis is never NULL or empty.
--   11. sigma_from_baseline is never NULL on any anomaly row.
--   Plus table-wide distinctness (no duplicate discovery_id/anomaly_id)
--   and epistemic_jsonb/provenance/discovery_subsystem never NULL.

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  NOT EXISTS (
    SELECT 1 FROM bodha_discoveries
    WHERE discovery_class NOT IN (
      'latent_insight', 'embedding_outlier', 'distributional_anomaly',
      'cross_subsystem_root', 'structural_hole'
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_anomalies
    WHERE anomaly_type NOT IN (
      'low_salience_high_consequence', 'embedding_outlier', 'distributional_anomaly'
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_anomalies
    WHERE meaningfulness_gate_result NOT IN ('promoted', 'candidate_only')
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_discoveries
    WHERE non_obviousness_score < 0 OR non_obviousness_score > 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_discoveries
    WHERE consequence_score < 0 OR consequence_score > 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_discoveries WHERE composite_discovery_rank < 0
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_discoveries WHERE constituent_refs_jsonb IS NULL
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_discoveries WHERE reasoning_chain_jsonb IS NULL
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_discoveries
    WHERE why_an_acharya_misses_it IS NULL OR why_an_acharya_misses_it = ''
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_discoveries
    WHERE meaningfulness_basis IS NULL OR meaningfulness_basis = ''
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_anomalies WHERE sigma_from_baseline IS NULL
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_discoveries
    WHERE epistemic_jsonb IS NULL OR provenance IS NULL OR discovery_subsystem IS NULL
  )
  AND NOT EXISTS (
    SELECT discovery_id FROM bodha_discoveries GROUP BY discovery_id HAVING count(*) > 1
  )
  AND NOT EXISTS (
    SELECT anomaly_id FROM bodha_anomalies GROUP BY anomaly_id HAVING count(*) > 1
  )
$ic$
 WHERE asset_id = 'bo_anveshana';
