-- 931_nirmana_l2_bo_laksana_integrity_check.sql
--
-- NIRMANA v2.5 -- L2 (Bodha). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Adjudication #2455: bo_laksana is the only frozen-track L2 signal writer
-- whose asset_registry row has integrity_check_sql IS NULL, so the freeze
-- pairing hard-fails at integrity_verified (collectIntegrityObservation
-- rejects the parameterised count_sql fallback by design). This migration
-- gives it a real chart-agnostic detector in the sibling style
-- (bo_arudha/bo_special_lagna/bo_sudarshana/bo_nakshatra_semantic: one
-- read-only SELECT, one boolean row, no bind placeholders, no semicolon).
--
-- WHAT THE CHECK ASSERTS (every clause measured green live 2026-09-08 across
-- all 150,280 owned rows / 3 charts, and each has a reachable red path --
-- SATYA-DIPA/N.8: no clause here is vacuous):
--
--   1. RATCHETING IDENTITY CONFORMANCE. Migration 661 PART 4 named full
--      identity conformance (stored signal_id = bodha_signal_identity()
--      recomputed from the row's own columns) as THE check bo_laksana would
--      adopt after its deterministic-id rebuild. Two facts prevent gating on
--      full conformance tonight: (a) only the canonical chart has been
--      rebuilt under the deterministic-id writer -- the other two charts
--      still carry legacy uuid4-era ids and rebuild on their own product
--      schedule, and (b) the writer's identity payload double-encoded
--      configuration_jsonb (pre-serialised string, not the parsed object),
--      so even freshly rebuilt rows were not re-derivable from stored
--      columns -- that writer defect is fixed in this same PR
--      (assign_deterministic_signal_ids now parses the string back to the
--      object per 661's key-order-invariance design). The clause below is
--      the honest intermediate: NO CHART MAY BE HALF-CONFORMANT. A chart
--      with zero conformant rows is legacy (allowed, until its own rebuild);
--      a chart with any conformant rows must be wholly conformant. Green
--      today (0 conformant anywhere); green after the canonical rebuild
--      (wholly conformant there, legacy elsewhere); RED on a partial
--      rebuild, a hand-edited row, or writer drift away from the identity
--      function on any rebuilt chart. As each remaining chart rebuilds, the
--      clause's coverage extends to it automatically -- when all charts are
--      conformant this clause IS 661 PART 4's full conformance check, with
--      no further migration needed.
--
--   2. B.3 DERIVATION-LEDGER MANDATE: no owned row may carry an empty/NULL
--      constituent_facts_array (same clause bo_arudha gates on; 0 offenders
--      live).
--
--   3. VALENCE CLOSED SET: benefic/malefic/neutral/mixed -- the writer-side
--      closed set (_infer_valence's 3 values + _VICHARA_TO_MSR_VALENCE's
--      range, which adds 'mixed' as first-class per DR-9); exactly these 4
--      observed live.
--
-- Deliberately NOT included: fact_key presence (rollup classes
-- bhavat_bhavam_amplifier / varga_pattern / varga_ratification_divergence
-- legitimately lack it -- 271 rows live, so the clause would false-fail);
-- the 661 PART 2 zero-dangling lineage check (an L1 rebuild legitimately
-- dangles refs until bo_laksana re-runs, so it would false-block freezes on
-- unrelated charts' L1 activity -- it stays a report, not a gate); any
-- fixed per-(chart, ayanamsha) row count (bo_laksana's output is a
-- heterogeneous projection, not a fixed-cardinality set like the siblings').
--
-- The class list matches BO_LAKSANA_OWNED_SIGNAL_TYPE_CLASSES
-- (pipeline/orchestrator/writers/bo_laksana.py:145-160) and migrations
-- 929/930's verified list.
--
-- Registry-contract consequence, stated on #2455 and accepted there: this
-- UPDATE shifts bo_laksana's live registry_fingerprint_sha256, so the
-- existing W1/W2 acceptance chain must genuinely re-run -- that is the
-- non-relaxed case of the #2450/#2452 rulings (the asset's OWN contract
-- changed), not the shared-pin drift case.

UPDATE asset_registry
   SET integrity_check_sql = $INTEGRITY$
WITH laksana AS (
  SELECT chart_id, ayanamsha_id, signal_type_id, varga_id, configuration_jsonb,
         signal_id, valence, constituent_facts_array
    FROM bodha_msr_signals
   WHERE signal_type_class IN (
     'yoga','dosha','sade_sati','panchanga','karaka_alignment','tradition_specific',
     'parivartana','configuration','varga_pattern','annual','medical','vastu',
     'composite_state','varga_ratification_divergence','bhavat_bhavam_amplifier')
), conformance AS (
  SELECT chart_id,
         count(*) FILTER (WHERE signal_id = bodha_signal_identity(
           chart_id, ayanamsha_id, signal_type_id, varga_id, configuration_jsonb)) AS conformant,
         count(*) AS total
    FROM laksana
   GROUP BY chart_id
)
SELECT
  NOT EXISTS (
    SELECT 1 FROM conformance WHERE conformant > 0 AND conformant != total
  )
  AND NOT EXISTS (
    SELECT 1 FROM laksana
     WHERE constituent_facts_array IS NULL
        OR array_length(constituent_facts_array, 1) IS NULL
        OR array_length(constituent_facts_array, 1) = 0
  )
  AND NOT EXISTS (
    SELECT 1 FROM laksana
     WHERE valence NOT IN ('benefic','malefic','neutral','mixed')
  ) AS integrity_passed
$INTEGRITY$
 WHERE asset_id = 'bo_laksana'
   AND integrity_check_sql IS NULL;
