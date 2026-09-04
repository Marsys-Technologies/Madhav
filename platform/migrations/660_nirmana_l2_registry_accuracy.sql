-- 660_nirmana_l2_registry_accuracy.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (L2_W2_DECIDE_v1_0.md: M-09, M-11, N-20, N-21).
-- Pure asset_registry corrections for the Bodha layer. No schema change, no
-- data movement, no writer change. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Deliberately NOT in this migration: target_floor. CLAUDE.md §N.4 sets floors
-- to the ACHIEVED count *after* a build, and 20 of the layer's 22 assets are
-- currently state='stale' with a W4 rebuild pending. Writing today's counts as
-- floors now would pin pre-rebuild numbers and re-create exactly the staleness
-- §N.4 exists to prevent. Floors are set in L2-W5, from the rebuilt counts.

-- ── M-11 / N-20: two assets carry NULL target_table, and it has teeth ────────
--
-- bodha_cdlm_chart_summary and bodha_chart_gestalt both exist and are populated
-- (5 rows each, one per ayanamsha). Their count_sql already names them correctly
-- and returns the right figures, so this is not a reporting defect. But NULL
-- target_table has two live consequences:
--
--   1. CHECK asset_registry_natural_key_partition_needs_table forbids setting
--      natural_key_partition while target_table IS NULL, so the C12 conform work
--      for these two assets is blocked at the constraint level, not by choice.
--   2. Both are un-clearable from the cockpit: clear/route.ts:186 treats an asset
--      as clearable only if it has a delete_sql or a target_table, and neither
--      has a clear_tables entry or an assetClearSpec.ts entry either. All three
--      fallbacks are absent.
--
-- Origin: migration 358 registered them ("thin writer; no verdicts stored") with
-- neither target_table nor catalog_status.
UPDATE asset_registry SET target_table = 'bodha_cdlm_chart_summary'
 WHERE asset_id = 'bo_cdlm_summary' AND target_table IS NULL;
UPDATE asset_registry SET target_table = 'bodha_chart_gestalt'
 WHERE asset_id = 'bo_chart_gestalt' AND target_table IS NULL;

-- ── N-20: the DRAFT sweep — one mechanical defect, not nine judgments ────────
--
-- All nine DRAFT assets are UNPROMOTED, not incomplete. asset_registry.
-- catalog_status defaults to 'DRAFT', and eight registry migrations omitted the
-- column entirely: 358 (bo_chart_gestalt, bo_cdlm_summary, bo_cgm_motifs,
-- bo_cgm_paths), 438, 445, 446, 450, 451, 452, 453.
--
-- This is the IDENTICAL defect that migration 294_catalog_status_current.sql
-- already diagnosed and swept: "Fix catalog_status for built assets that
-- defaulted to 'DRAFT'. Root cause: several registry migrations omitted
-- catalog_status from their INSERT ... are invisible in the Nirmāṇa cockpit
-- (which filters on catalog_status)." Migration 358 and 438-453 landed AFTER
-- that sweep and reintroduced it. (Note 358's own bo_cgm_motifs/bo_cgm_paths
-- were picked up by a later sweep while its other two were not — which is how a
-- mechanical omission comes to look like a per-asset judgment.)
--
-- Evidence per asset, gathered in L2-W1 lane E: each has a real @register
-- writer, a non-zero live row count, and at least one serving-plane consumer.
-- Eight of the nine contain zero TODO/FIXME/NotImplemented/stub markers; the
-- ninth (bo_chart_gestalt) has one comment marking a documented optional CDLM
-- §C3 pivot field, not a stub. Details in L2_W1_ANALYSIS_v1_0.md §5 (E5).
UPDATE asset_registry
   SET catalog_status = 'CURRENT'
 WHERE layer = 'bodha'
   AND catalog_status = 'DRAFT'
   AND has_writer IS TRUE
   AND asset_id IN (
     'bo_arudha', 'bo_cdlm_summary', 'bo_chart_gestalt', 'bo_laksana_rerank',
     'bo_nakshatra_semantic', 'bo_special_lagna', 'bo_sudarshana',
     'bo_vargottama_dhana', 'bo_yantra_mechanism'
   );

-- ── N-21: two sort_order collisions ─────────────────────────────────────────
--
-- bo_yantra_mechanism and bo_nakshatra_semantic both sit at 20; bo_arudha and
-- bo_laksana_rerank both at 21. Ordering contiguity is one of the invariant
-- classes charter §C12 names, and a tie makes build order planner-dependent.
-- Migration 360 was the topological fix; the six assets registered by 438-453
-- landed after it and were never re-sequenced. Slots 15-17 are free (freed by
-- 447_bo_anveshana_retire.sql).
--
-- bo_yantra_mechanism -> 15: its dependencies are bo_cgm_motifs (4),
-- bo_cgm_paths (5) and bo_karanajala (3), all well below 15.
UPDATE asset_registry SET sort_order = 15 WHERE asset_id = 'bo_yantra_mechanism';
-- bo_laksana_rerank -> 24, i.e. last in the layer. It only UPDATEs
-- bodha_msr_signals rows, so it must run after every writer that INSERTs into
-- that table — which includes the five satellite emitters at 19-23, not just its
-- declared dependency bo_karanajala (3). The declared DAG edge alone would allow
-- it to run at 4 and update a table the satellites have not filled yet.
UPDATE asset_registry SET sort_order = 24 WHERE asset_id = 'bo_laksana_rerank';

-- ── M-09: expected_volume_formula — two wrong, nineteen absent ──────────────
--
-- Charter §C12 requires a volume expectation that is either DERIVED
-- (expected_volume_formula + expected_volume_inputs both populated) or a floor
-- (§N.4 achieved-count). It names a NULL formula as the defect. A WRONG formula
-- is worse than a NULL one, because it reads as done — so the two wrong ones are
-- addressed first, and the derivable absentees are filled.

-- bo_bimba claimed ACTUAL(bo_laksana): 385 graph nodes against 49,955 signals,
-- wrong by 130x. Graph nodes are not 1:1 with signals. Cleared rather than
-- guessed: per C12 "derive, never pick", the correct derivation is the writer's
-- own node-subject vocabulary x ayanamshas, which requires reading the vocabulary
-- off a current build. That lands in L2-W5 with the rebuild; until then this
-- asset's volume expectation is its §N.4 achieved-count floor.
UPDATE asset_registry
   SET expected_volume_formula = NULL,
       volume_explanation = 'L2-W3 (M-09): the previous formula ACTUAL(bo_laksana) was wrong by ~130x '
         || '(385 nodes vs 49,955 signals) — graph nodes are not 1:1 with signals. Cleared rather '
         || 'than replaced with a guess. The real derivation is the writer''s node-subject '
         || 'vocabulary x 5 ayanamshas and is authored in L2-W5 against the rebuilt node set. '
         || 'Until then the §N.4 achieved-count floor is this asset''s volume expectation.'
 WHERE asset_id = 'bo_bimba';

-- bo_karanajala claimed ACTUAL(bo_laksana) * EDGE_DENSITY, and EDGE_DENSITY is
-- an UNBOUND FREE SYMBOL — expected_volume_inputs is NULL on all 22 Bodha
-- assets, so there is nowhere it could have been bound. The formula was never
-- evaluable by anything, human or machine.
UPDATE asset_registry
   SET expected_volume_formula = NULL,
       volume_explanation = 'L2-W3 (M-09): the previous formula ACTUAL(bo_laksana) * EDGE_DENSITY '
         || 'carried an unbound free symbol — expected_volume_inputs was NULL, so EDGE_DENSITY had '
         || 'no binding anywhere and the expression was never evaluable. Cleared rather than '
         || 'assigned a density fitted to the observed 849 edges, which would make the formula '
         || 'true by construction and unable to fail. Real derivation authored in L2-W5 from the '
         || 'edge-type rule set; §N.4 achieved-count floor applies until then.'
 WHERE asset_id = 'bo_karanajala';

-- The six assets whose volume IS honestly derivable today. Each formula's every
-- symbol is bound in expected_volume_inputs — the specific failure EDGE_DENSITY
-- represents. All figures verified live against the canonical chart
-- 482012f1-710e-4a25-994a-93821f5871aa.

-- bo_samskara: 1:1 with bodha_msr_signals by the writer's own stated contract
-- (bo_samskara.py:4, "one bodha_signal_embeddings row per bodha_msr_signals row").
-- Live: 50,104 = 50,104 exactly. The previous ACTUAL(bo_laksana) was off by 149
-- because bo_laksana's count_sql filters to its 15 owned signal_type_classes,
-- while the table also holds the six satellite emitters' classes
-- (sudarshana_agreement 45 + nakshatra_semantic 45 + arudha 25 + special_lagna 20
-- + dhana_axis 10 + vargottama_amplification 4 = 149; 49,955 + 149 = 50,104).
-- Stating it as the table count rather than a sum of six ACTUALs makes it a real
-- cross-table invariant that cannot drift as emitters are added or removed.
UPDATE asset_registry
   SET expected_volume_formula = 'ROWS(bodha_msr_signals WHERE chart_id)',
       expected_volume_inputs = jsonb_build_object(
         'contract', '1:1 per signal',
         'contract_ref', 'platform/python-sidecar/pipeline/orchestrator/writers/bo_samskara.py:4',
         'measured_signals', 50104,
         'measured_embeddings', 50104,
         'measured_on_chart', '482012f1-710e-4a25-994a-93821f5871aa'),
       volume_explanation = 'One embedding row per MSR signal row, by the writer''s own contract. '
         || 'Expressed as the live table count rather than a sum of per-emitter ACTUALs so that '
         || 'adding or retiring a satellite emitter cannot silently invalidate it. Any divergence '
         || 'from equality is a FULL OUTER JOIN failure, not a volume shortfall.'
 WHERE asset_id = 'bo_samskara';

-- bo_drishti: one lens per (question_type x ayanamsha), UNIQUE-enforced on
-- (chart_id, ayanamsha_id, question_type). Live: 12 x 5 = 60.
UPDATE asset_registry
   SET expected_volume_formula = 'QUESTION_TYPES * AYANAMSHAS',
       expected_volume_inputs = jsonb_build_object(
         'QUESTION_TYPES', 12, 'AYANAMSHAS', 5,
         'uniqueness', '(chart_id, ayanamsha_id, question_type)',
         'measured', 60, 'measured_on_chart', '482012f1-710e-4a25-994a-93821f5871aa'),
       volume_explanation = '12 question types x 5 ayanamshas = 60 lenses per chart. The table''s '
         || 'own UNIQUE constraint on (chart_id, ayanamsha_id, question_type) makes this a tiling '
         || 'expectation, not an estimate: fewer means a gap, more is impossible.'
 WHERE asset_id = 'bo_drishti';

-- Three per-(chart x ayanamsha) rollups. Same derivation, verified separately.
UPDATE asset_registry
   SET expected_volume_formula = 'AYANAMSHAS',
       expected_volume_inputs = jsonb_build_object(
         'AYANAMSHAS', 5, 'grain', 'one row per (chart_id, ayanamsha_id)',
         'measured', 5, 'measured_on_chart', '482012f1-710e-4a25-994a-93821f5871aa'),
       volume_explanation = 'One rollup row per ayanamsha. A count other than 5 means a '
         || 'partially-completed per-ayanamsha build, which a chart-level total cannot detect.'
 WHERE asset_id IN ('bo_cdlm_summary', 'bo_chart_gestalt', 'bo_samvada');

-- bo_pramana_mapa: exactly one scorecard row per chart.
UPDATE asset_registry
   SET expected_volume_formula = 'ONE_PER_CHART',
       expected_volume_inputs = jsonb_build_object(
         'rows_per_chart', 1, 'measured', 1,
         'measured_on_chart', '482012f1-710e-4a25-994a-93821f5871aa'),
       volume_explanation = 'One synthesis_quality_scorecard row per chart, spanning all '
         || 'ayanamshas. Two rows means a stale generation survived a rebuild.'
 WHERE asset_id = 'bo_pramana_mapa';
