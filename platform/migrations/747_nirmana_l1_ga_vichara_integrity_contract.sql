-- 747_nirmana_l1_ga_vichara_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_vichara: integrity_check_sql was
-- NULL, so the freeze-time detector fell back to count(*) > 0 (§N.8 -- an unearned signal).
--
-- Target table: chart_vichara. No distinctness conjunct: this table carries no natural-key
-- UNIQUE (only a surrogate PK on `id`), and legitimate row multiplicity exists per (actor,
-- target) pair across varga -- not asserted here (D-CND-03 rule 4 does not apply when no
-- natural key is well-defined).
--
-- Every conjunct below was EXECUTED against live production and MUTATION-PROVED before landing:
-- each was re-run against a corruption injected inside a CTE overlay and shown to return false.
-- Passes clean (integrity_passed = true) on live production today.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_vichara integrity contract (target table: chart_vichara)
SELECT
  -- (a) constituent_fact_ids must resolve with zero orphans against chart_facts.fact_id (§N.5,
  -- the writer's own stated rail). 24,736/24,736 rows clean live.
  NOT EXISTS (
    SELECT 1 FROM chart_vichara v, unnest(v.constituent_fact_ids) fid
    WHERE NOT EXISTS (SELECT 1 FROM chart_facts f WHERE f.fact_id = fid)
  )
  -- (b) constituent_facts_array must resolve with zero orphans against chart_facts.fact_id
  -- (§N.5) -- the schema note's OTHER consumer-facing column carrying the same rail.
  AND NOT EXISTS (
    SELECT 1 FROM chart_vichara v, unnest(v.constituent_facts_array) fid
    WHERE NOT EXISTS (SELECT 1 FROM chart_facts f WHERE f.fact_id = fid)
  )
  -- (c) varga / varga_id dual-column consistency (migration 435's schema-note reconciliation:
  -- this writer populates BOTH sides of each duplicated pair) -- 0/24,736 mismatches live,
  -- including NULL-NULL pairs where neither is populated.
  AND NOT EXISTS (
    SELECT 1 FROM chart_vichara WHERE varga IS DISTINCT FROM varga_id
  )
  -- (d) valence_pass family: actor must equal subject (the same schema-note duplication,
  -- scoped correctly -- the other four families legitimately leave actor blank and populate
  -- subject/domain instead, confirmed live: 100% actor<>subject on every OTHER family, 0/23,925
  -- mismatches within valence_pass itself).
  AND NOT EXISTS (
    SELECT 1 FROM chart_vichara
    WHERE vichara_family = 'valence_pass' AND actor IS DISTINCT FROM subject
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_vichara';
