-- 932_nirmana_l2_bo_laksana_rerank_integrity_check.sql
--
-- NIRMANA v2.5 -- L2 (Bodha). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- #2455 priority-2 pre-clearing (RESOLUTION v4 item 2): audit of the L2 chain
-- found exactly ONE remaining asset with integrity_check_sql IS NULL once
-- PR #2458 (migration 931, bo_laksana) lands: bo_laksana_rerank. The other
-- six audited assets (bo_bimba 711, bo_sangati 712, bo_samskara 713,
-- bo_cgm_motifs 761, bo_cgm_paths 762, bo_karanajala 763) all carry live,
-- chart-agnostic contracts verified green 2026-09-08 (each executed verbatim
-- against production: 6/6 -> t; no hardcoded chart_id, no fixed-total row
-- pins -- their numeric literals are structural universals: 9 grahas,
-- 12 bhavas, 768 embedding dims, strength bands). This migration closes the
-- last #2455-class gap in the L2 chain.
--
-- bo_laksana_rerank is an UPDATE-ONLY asset (bo_laksana.py:3886,
-- BoLaksanaRerankWriter, CR-84 + PARK-#4 + D-SYNTHESIS ruling #1720): it
-- never inserts or deletes bodha_msr_signals rows, only enriches columns on
-- rows other writers own. The detector shape therefore differs from the
-- ownership contracts (931 and siblings):
--   * NO cross-build accretion clause -- the asset inserts nothing, so there
--     is no accretion class to detect;
--   * NO row-count or coverage pin -- enrichment coverage varies by each
--     chart's own rebuild schedule and by whether a signal's
--     configuration_jsonb yields a primary graha at all (best-effort by
--     design); a coverage gate would false-block freezes on unrelated
--     charts' rebuild timing;
--   * NO fact_key clause -- it owns no rows.
-- What it CAN honestly gate is the SHAPE of every mark it leaves. All
-- clauses measured green live 2026-09-08 (10,968 non-NULL hook payloads
-- across 2 charts; rollup columns still 100% NULL fleet-wide -- those
-- clauses are ratcheting, same philosophy as 931 clause 1: they bind the
-- future population's shape and are vacuously green until the D-SYNTHESIS
-- pass first runs). Each clause has a reachable red path (SATYA-DIPA/N.8;
-- every one verified by overlay mutation -> f before this migration was
-- posted):
--
--   1. HOOK PAYLOAD KEY SET. Every non-NULL
--      graph_node_strength_contribution_jsonb carries the four load-bearing
--      keys the writer always emits (structural_role_score, primary_graha,
--      formula_version, computed_at). RED on a hand-edited or truncated
--      payload.
--
--   2. FORMULA VERSION CLOSED SET. Exactly 'structural_role_rerank_v1' --
--      the single value observed on all 10,968 live payloads. A new formula
--      version must update this contract deliberately (ratchet, not drift).
--      IS DISTINCT FROM also catches JSON-null. RED on any second version
--      appearing silently.
--
--   3. STRUCTURAL ROLE BAND. _structural_role_from_centrality maps a [0,1]
--      centrality composite onto the [0.8, 1.5] multiplier band (B.10 -- a
--      hub graha outweighs, never zeroes out, a peripheral one). Live range:
--      [0.936349, 0.967559]. The clause gates the DESIGN band, not the
--      observed slice (the observed range is chart-population-dependent; the
--      band is the writer's invariant). CASE guards evaluation order so a
--      non-number payload reads as a violation instead of a cast error.
--
--   4. PRIMARY GRAHA CLOSED SET. The 9-graha titles _SHORT_TO_LONG can
--      produce; NULL is a violation on a non-NULL payload (the writer only
--      writes when centrality resolved, which requires the graha).
--
--   5. D-SYNTHESIS NULL PAIRING (ruling #1720's three-way storage contract).
--      system_convergence_count and cross_system_consensus_count are written
--      by ONE combined UPDATE joined through resolvable-facts signals: both
--      set, or both left NULL ("nothing was checked, so nothing is
--      claimed"). A row with one set and the other NULL is a half-write or a
--      hand edit. RED exactly there.
--
--   6. ROLLUP VALUE FLOORS. convergence is a pair count (>= 0, measured
--      zero is real information); consensus is max(count(DISTINCT
--      tradition)) over a non-empty join (>= 1 wherever written). NULLs pass
--      (three-way contract); a written 0 consensus or negative convergence
--      is RED.
--
--   7. NULL-NOT-EMPTY on contradicts_signals_array. The storage contract
--      (ruling #1720) is NULL on non-participating rows, NEVER '{}' --
--      bo_upaya reads an empty array as a MEASURED "no contradictions
--      found" and would enable a term with no evidence behind it. An empty
--      array anywhere is RED.
--
--   8. PARK-#4 VALENCE INTEGRITY, chart-wide. Any row claiming
--      valence_source = 'ga_vichara_v1' must carry a non-NULL valence from
--      the closed set (benefic/malefic/neutral/mixed). Wider scope than
--      931's owned-class clause on purpose: the rerank pass is the writer
--      that flips satellite-class rows to ga_vichara_v1, so the claim must
--      hold on every class it can touch. Live: {benefic, malefic, mixed}
--      observed, 0 NULLs.
--
-- Deliberately NOT included: payload centrality values matching
-- bodha_cgm_nodes' CURRENT values -- a CGM rebuild after a rerank pass
-- legitimately drifts the snapshot until rerank re-runs; that is the same
-- rebuild-order coupling 931's header excludes for 661 PART 2 lineage (a
-- report, not a gate). Hook coverage / PARK-#4 reclaim-rate floors -- the
-- honest remainder is by design (B.10). fact_key anything -- not this
-- asset's rows.
--
-- Registry-contract consequence (same as 931, stated per the #2450/#2452
-- rulings): this UPDATE shifts bo_laksana_rerank's registry fingerprint, so
-- its W1/W2 acceptance chain must genuinely re-run -- the asset's OWN
-- contract changed; this is the non-relaxed case.
--
-- Post-apply verification (N.4 -- never trust a silent no-op): expect
-- UPDATE 1, then
--   SELECT integrity_check_sql IS NOT NULL FROM asset_registry
--    WHERE asset_id = 'bo_laksana_rerank'  -- expect t

UPDATE asset_registry
   SET integrity_check_sql = $INTEGRITY$
WITH hook AS (
  SELECT graph_node_strength_contribution_jsonb AS p
    FROM bodha_msr_signals
   WHERE graph_node_strength_contribution_jsonb IS NOT NULL
)
SELECT
  NOT EXISTS (
    SELECT 1 FROM hook
     WHERE NOT (p ?& ARRAY['structural_role_score','primary_graha','formula_version','computed_at'])
  )
  AND NOT EXISTS (
    SELECT 1 FROM hook
     WHERE p->>'formula_version' IS DISTINCT FROM 'structural_role_rerank_v1'
  )
  AND NOT EXISTS (
    SELECT 1 FROM hook
     WHERE CASE WHEN jsonb_typeof(p->'structural_role_score') = 'number'
                THEN (p->>'structural_role_score')::numeric NOT BETWEEN 0.8 AND 1.5
                ELSE true END
  )
  AND NOT EXISTS (
    SELECT 1 FROM hook
     WHERE p->>'primary_graha' IS NULL
        OR p->>'primary_graha' NOT IN
           ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu')
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
     WHERE (system_convergence_count IS NULL) <> (cross_system_consensus_count IS NULL)
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
     WHERE system_convergence_count < 0 OR cross_system_consensus_count < 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
     WHERE contradicts_signals_array IS NOT NULL
       AND array_length(contradicts_signals_array, 1) IS NULL
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
     WHERE valence_source = 'ga_vichara_v1'
       AND (valence IS NULL OR valence NOT IN ('benefic','malefic','neutral','mixed'))
  ) AS integrity_passed
$INTEGRITY$
 WHERE asset_id = 'bo_laksana_rerank'
   AND integrity_check_sql IS NULL;
