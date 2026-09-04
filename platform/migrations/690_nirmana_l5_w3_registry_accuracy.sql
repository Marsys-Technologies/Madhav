-- 690_nirmana_l5_w3_registry_accuracy.sql
--
-- NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md L5-W3 IMPLEMENT, batch 1 of 2
-- (registry accuracy).  Source: L5_W2_DECIDE_v1_0.md §4.2 "W3-1 Registry
-- corrections", from the four L5_W1_ANALYSIS_BATCH_*.md files.
--
-- SCOPE OF THIS MIGRATION -- what it deliberately does NOT touch:
--
--   * `depends_on` is IMMUTABLE campaign-wide per adjudication #1744 /
--     D-CND-09 (the frozen definition can no longer be superseded; the
--     dispatcher compares exactly `layer` and `depends_on` against the frozen
--     manifest and takes every other contract field from the live row).  L5's
--     W1 found 32 DAG corrections -- 19 undeclared-but-read and 13
--     declared-but-unread -- and NONE of them are applied here.  They are
--     recorded instead in the Phase-Z DAG corrections register (issue #1734).
--   * No `integrity_check_sql`.  That is batch 2, authored under C12 /
--     D-CND-03 (chart-partitioned invariants, no bind placeholders) and
--     verified live before it ships.
--
-- SEQUENCING (adjudication #1744): a registry-contract change must land BEFORE
-- that asset's W2 acceptance event, or the accepted analysis needs
-- re-acceptance under charter C2 condition 3.  L5 has ZERO acceptance events
-- (the evidence-spine generalisation, #1715/PR #1736, is not yet merged), so
-- this lands in a clean window and races none of its own acceptances.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.


-- ---------------------------------------------------------------------------
-- 1. mi_sankalpa.target_floor: NULL -> 0
-- ---------------------------------------------------------------------------
-- L5-W1 batch D, finding D-F-D15.  `target_floor IS NULL` fails
-- asset_runner.py's `zero_rows_is_complete = (chart_id is None) or
-- (target_floor == 0)`, so a writer that CORRECTLY produces zero rows is left
-- in state='dormant', which plan.ts (`!t || t.state === 'dormant'`) then treats
-- as a build candidate on every single pass -- a correct writer re-queued
-- indefinitely.
--
-- Root cause is exact and dated: migration 364_mi_all_target_floor_zero.sql
-- swept `WHERE asset_id LIKE 'mi_%' AND target_floor IS NULL`, and its own
-- header names this hazard ("causes DEP-ASSERT cascade failures").
-- mi_sankalpa was created AFTERWARDS, by migration 532, with target_floor
-- NULL, and was never swept.
--
-- 0 is the honest floor, not a convenience: mimamsa_intervention_ledger is
-- populated at SERVE time when a native adopts an intervention (a live, tested
-- write path via kala_upaya_get -> intervention_ledger_record), so zero rows
-- from a build is the correct and expected result.  Per CLAUDE.md §N.4 floors
-- track achieved counts and are never fabricated upward.
-- Guard is IS DISTINCT FROM, not IS NULL (independent review, WARN 4): the
-- broken predicate is `target_floor == 0`, which fails for EVERY non-zero value,
-- not only NULL.  An `IS NULL` guard would silently decline to fix a row that had
-- drifted to some other number -- the exact defect, left in place, with the
-- migration reporting success.  IS DISTINCT FROM is NULL-safe and still no-ops on
-- a second run.
UPDATE asset_registry SET target_floor = 0
 WHERE asset_id = 'mi_sankalpa' AND target_floor IS DISTINCT FROM 0;


-- ---------------------------------------------------------------------------
-- 2. mi_bhara.target_floor: NULL -> 0, and target_table corrected
-- ---------------------------------------------------------------------------
-- L5-W1 batch C, findings C-F-21 and C-F-23.
--
-- target_table said `kala_field_weight_versions` -- a table this writer has
-- NEVER written and whose write path is unreachable: `insert_weights_version`
-- and `supersede_previous_active` (services/mi_bhara/db.py:223, :272) have
-- ZERO callers anywhere in the repo, not even in tests.  The live table holds
-- exactly one row, `v0_classical`, activated 2026-07-30, which is the
-- migration-491 seed and predates any mi_bhara run.
--
-- The writer actually writes `kala_field_skill` (7 live rows) and
-- `kala_field_gof` (6).  The registry already half-knew: count_sql counts
-- kala_field_skill, a DIFFERENT table from the declared target_table.
--
-- Why the write path is unreachable is CORRECT and is not a defect to fix
-- here: _fit_and_publish (mi_bhara.py:230-237) declines Phase 2 because the
-- theta-independent per-segment basis is Lane C's stage-4 emission and does
-- not exist yet -- "It does not fabricate a basis in order to look complete."
-- That refusal is §N.8 conduct and is recorded as deliberate.  Wiring it is
-- routed NEVER/LATER (plan §7.3 / SAD-DARSANA).
--
-- Ownership: `kala_field_weight_versions` and `kala_field_weights` are
-- L3-owned, L5-read-only for this campaign -- granted by the L3 session on
-- adjudication issue #1743, which also acked this exact registry correction.
--
-- target_floor 0 for the same reason as mi_sankalpa: a chart with no Life
-- Event Log correctly produces the structural-prior state
-- (skill_state = 'underpowered'), which the existing volume_explanation
-- already describes as "an honest zero, not an error".
UPDATE asset_registry
   SET target_table = 'kala_field_skill',
       target_floor = 0
 WHERE asset_id = 'mi_bhara';


-- ---------------------------------------------------------------------------
-- 3. mi_jivanaghatana.expected_volume_formula: corrected, not merely filled
-- ---------------------------------------------------------------------------
-- L5-W1 batch A, finding A-F-09.  The existing formula
-- `FILE_COUNT('01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md', 'EVT')` with
-- `file_count: 56` is wrong on three independent counts, established by full
-- derivation (see L5_W1_ANALYSIS_BATCH_A.md, the reconciliation table):
--
--   (a) 56 is not the EVT-block count.  The file carries 58 `^EVT.*:$`
--       headers, minus the §1.4 schema template = 57 real blocks.
--   (b) It names the WRONG SOURCE.  The writer has no markdown branch at all:
--       lel_source is hardcoded "db", lel_file_sha hardcoded None, and the
--       only read is `SELECT * FROM life_events WHERE chart_id = %s`.  A
--       FILE_COUNT over a markdown file cannot govern the volume of a table
--       the writer reads instead.
--   (c) It is not chart-scoped, so it would declare a HEALTHY build of chart
--       1c826d5a (which legitimately has no Life Event Log, hence 0 rows) a
--       56-row shortfall.
--
-- The live 64 rows reconcile EXACTLY and every row is attributed:
--   57 distinct lel_id blocks + 1 dual-role split (EVT.2019.05.XX.01 re-typed
--   foreign_settlement) + 5 native date-tightening corrections (D-4a Lane A-1,
--   ingested 2026-07-17/18) + 1 demo row = 64.
-- The row count is NOT a bug; the pin was.  Per charter C12 this is the "pin
-- stale/underived -> correct the check with the derivation in the PR" branch.
--
-- The demo row (event_id 5278d97c-e769-529a-b0c2-be1e965c2d6b,
-- source_section 'D-4a-A4-append-hook-demo') is recorded as finding A-F-03 and
-- is NOT silently absorbed into this derivation: the formula counts what the
-- writer reads, and disposition of that row is the native's call.
UPDATE asset_registry
   SET expected_volume_formula = 'COUNT(life_events WHERE chart_id = $chart)',
       expected_volume_inputs = jsonb_build_object(
         'source_table', 'life_events',
         'partition', 'chart_id',
         'chart_scoped', true,
         'derivation', 'one provenance row per life_events row for the chart; a chart with no Life Event Log correctly yields 0',
         'observed_2026_09_05', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', 64,
           '1c826d5a-41cb-4450-b4dc-59d440e5f75a', 0),
         'supersedes', 'FILE_COUNT(01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md, EVT) with file_count 56 -- wrong count, wrong source, not chart-scoped (finding A-F-09)'),
       volume_explanation = 'One row per life_events row for the chart. Derived from the table the writer actually reads (the writer has no markdown branch: lel_source is hardcoded "db"). A chart with no Life Event Log correctly produces 0 rows -- an honest zero, not a shortfall.'
 WHERE asset_id = 'mi_jivanaghatana';


-- ---------------------------------------------------------------------------
-- 4. mi_gunanaka.expected_volume_formula -- exactly derivable
-- ---------------------------------------------------------------------------
-- L5-W1 batch C, finding C-F-10.  Expected rows per chart = the count of
-- active non-control signal families.  Verified live: 9 such families, and
-- mimamsa_multipliers holds exactly 9 rows per built chart (9 x 2 charts = 18).
UPDATE asset_registry
   SET expected_volume_formula = 'COUNT(mimamsa_signal_families WHERE is_active AND default_state <> ''CONTROL_ONLY'')',
       expected_volume_inputs = jsonb_build_object(
         'source_table', 'mimamsa_signal_families',
         'partition', 'chart_id',
         'chart_scoped', true,
         'derivation', 'one multiplier row per active non-control signal family, per chart',
         'observed_2026_09_05', jsonb_build_object('families', 9, 'rows_per_chart', 9, 'charts_built', 2, 'total', 18))
 WHERE asset_id = 'mi_gunanaka';


-- ---------------------------------------------------------------------------
-- 5. mi_adhilepa.expected_volume_formula -- NOT a flat count
-- ---------------------------------------------------------------------------
-- L5-W1 batch C, finding C-F-15.  mimamsa_load_bearing's 9 rows are not a full
-- result: the writer takes [:5] of the families whose applied_multiplier >= 1.0,
-- so per chart the expectation is min(5, |qualifying families|) -- live, 4 for
-- the canonical chart and 5 for 1c826d5a.  A flat count pin would be exactly
-- the "equality wearing a floor's name" C12 forbids.
--
-- Recorded alongside it, because it is the reason the two charts differ:
-- fam_graha_natal -- the ONE family with real evidence on the canonical chart
-- -- is EXCLUDED from that chart's map because shrinkage moved it to 0.9924,
-- just under the hardcoded 1.0 cut, while fam_yoga (n_observations = 0) is
-- declared load_bearing.  That is finding C-F-13 (a MUST) and is fixed in the
-- writer, not here; this formula describes what the current writer produces.
UPDATE asset_registry
   SET expected_volume_formula = 'LEAST(5, COUNT(mimamsa_multipliers WHERE chart_id = $chart AND applied_multiplier >= 1.0))',
       expected_volume_inputs = jsonb_build_object(
         'source_table', 'mimamsa_multipliers',
         'partition', 'chart_id',
         'chart_scoped', true,
         'writer_cap', 5,
         'writer_threshold', 'applied_multiplier >= 1.0',
         'derivation', 'top-5 of the families at or above the multiplier threshold, per chart',
         'observed_2026_09_05', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', 4,
           '1c826d5a-41cb-4450-b4dc-59d440e5f75a', 5),
         'caveat', 'describes the CURRENT writer; the >= 1.0 threshold is itself finding C-F-13 (MUST) and this formula changes when that lands')
 WHERE asset_id = 'mi_adhilepa';


-- ---------------------------------------------------------------------------
-- 6. Event-driven ledgers: volume is EXOGENOUS, and saying so is the honest fill
-- ---------------------------------------------------------------------------
-- L5-W1 batch D, findings D-F-D03 and D-F-D21.  Charter C12 names a NULL
-- expected_volume_formula as the defect condition -- but for an append-only
-- ledger whose trigger is a real-world event, the honest fill is a formula
-- that states volume is exogenous with floor 0, NOT an invented number.  Both
-- tables' volume_explanation prose is already correct; only the
-- machine-readable field was empty.
UPDATE asset_registry
   SET expected_volume_formula = 'EXOGENOUS(append_only_event_log, floor 0)',
       expected_volume_inputs = jsonb_build_object(
         'kind', 'append_only_event_log',
         'trigger', 'an export delivery leaving the instrument',
         'floor', 0,
         'unbounded_above', true,
         'note', 'no build produces rows; the writer is specified to originate zero (spec 11_mi_vistara_SPEC_v1_0.md §7). Zero is measured-zero, not absent-data.')
 WHERE asset_id = 'mi_vistara';

UPDATE asset_registry
   SET expected_volume_formula = 'EXOGENOUS(append_only_event_log, floor 0)',
       expected_volume_inputs = jsonb_build_object(
         'kind', 'append_only_event_log',
         'trigger', 'a native adopting an elected intervention at serve time',
         'floor', 0,
         'unbounded_above', true,
         'write_path', 'kala_upaya_get -> recordInterventionLedgerEntry -> intervention_ledger_record (live and tested)',
         'note', 'this asset is the P7 SUBSTRATE, distinct from the remedy-efficacy LEDGER parked in plan §7.3, which is the analysis over it'),
       volume_explanation = 'Accumulates only when a native adopts an elected intervention at serve time. A build correctly produces zero rows; zero is measured-zero, not absent-data.'
 WHERE asset_id = 'mi_sankalpa';


-- ---------------------------------------------------------------------------
-- 7. estimated_seconds: measured, not guessed
-- ---------------------------------------------------------------------------
-- L5-W1 batch B finding B-F-11 and batch C finding C-F-17, re-measured
-- directly by the L5 session against build_run_assets before writing these
-- numbers (one W1 batch had claimed started_at was NULL for every L5 row --
-- that claim was FALSE and is corrected in L5_W1_ANALYSIS_BATCH_C.md note 7;
-- started_at is populated on 38-45 rows per asset).
--
-- Live measurement over completed runs (avg / max seconds):
--   mi_adhilepa  31.164 / 843.135   registry said 11   -- 77x low on the tail
--   mi_bhara     17.291 / 596.516   registry said  2   -- 298x low on the tail
--   mi_pariksha   4.176 /  32.910   registry said  2
--   mi_bhavisya   2.716 /  15.640   registry said  2
--   mi_jivanaghatana 1.990 / 22.790 registry said  1
--
-- estimated_seconds carries the MEAN (it is a scheduling estimate, not a
-- timeout).  The tails are the W4 hazard and are recorded in
-- L5_W2_DECIDE_v1_0.md rather than encoded here: mi_adhilepa and mi_bhara are
-- the two assets that would break a slot plan built on the old numbers.
-- Every other L5 asset's estimate is already within a second of measured and
-- is left alone rather than churned.
-- Guards are IS DISTINCT FROM, not equality against the expected pre-state
-- (independent review, WARN 3).  An `AND estimated_seconds = 11` guard is
-- NULL-unsafe (`NULL = 11` is NULL, not false -- and the seed defines several of
-- these as null) and silently no-ops if the value has drifted to a third number,
-- leaving the registry wrong while migrate.ts reports success.  The pre-state is
-- already documented in the comment block above; the guard does not need to
-- duplicate it, and duplicating it bought a way to fail quietly.
UPDATE asset_registry SET estimated_seconds = 31 WHERE asset_id = 'mi_adhilepa'      AND estimated_seconds IS DISTINCT FROM 31;
UPDATE asset_registry SET estimated_seconds = 17 WHERE asset_id = 'mi_bhara'         AND estimated_seconds IS DISTINCT FROM 17;
UPDATE asset_registry SET estimated_seconds = 4  WHERE asset_id = 'mi_pariksha'      AND estimated_seconds IS DISTINCT FROM 4;
UPDATE asset_registry SET estimated_seconds = 3  WHERE asset_id = 'mi_bhavisya'      AND estimated_seconds IS DISTINCT FROM 3;
UPDATE asset_registry SET estimated_seconds = 2  WHERE asset_id = 'mi_jivanaghatana' AND estimated_seconds IS DISTINCT FROM 2;


-- ---------------------------------------------------------------------------
-- KNOWN REVERT HAZARD -- recorded, not silently accepted
-- ---------------------------------------------------------------------------
-- Independent review (WARN 1) found that `asset_registry_seed.ts`'s
-- ON CONFLICT DO UPDATE SET includes target_table, target_floor,
-- expected_volume_formula, expected_volume_inputs and volume_explanation --
-- exactly the five columns statements 1-6 write -- while its TypeScript literals
-- still carry the pre-migration values.  So a `runSeed()` REVERTS statements 1-6.
-- (`estimated_seconds` is in the INSERT column list but NOT in the DO UPDATE SET,
-- so statement 7 survives.)  Verified directly, lines 3199-3205.
--
-- The seed is not wired into any deploy workflow or package.json script, so this
-- is not an automatic revert -- but it is a loaded gun, and sibling migration 643
-- carries identical exposure, so it is a campaign-wide pattern rather than
-- something this migration introduces.
--
-- The obvious fix -- mirror these six rows into the seed TS -- is BLOCKED by the
-- seed's own `validateFormulas`/`parseFormula` grammar, which arithmetic-evaluates
-- expected_volume_formula and throws on anything outside {ACTUAL(), FILE_COUNT(),
-- arithmetic}.  Every formula in this migration is outside that grammar, as is
-- every chart-partitioned formula charter C12 asks any layer to author.  Raised
-- to the Conductor as a cross-layer question rather than patched unilaterally in
-- a shared platform file.
--
-- Until that is ruled: these six rows are DB-AUTHORITATIVE and seed-divergent.
--
-- REVERSAL (per the 643 house convention) -- prior values, for a manual rollback:
--   mi_sankalpa       target_floor NULL; expected_volume_formula NULL; volume_explanation NULL
--   mi_bhara          target_floor NULL; target_table 'kala_field_weight_versions'
--   mi_jivanaghatana  expected_volume_formula "FILE_COUNT('01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md', 'EVT')";
--                     expected_volume_inputs {"file_count":56,"source_file":"01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md"};
--                     estimated_seconds 1
--   mi_gunanaka       expected_volume_formula NULL
--   mi_adhilepa       expected_volume_formula NULL; estimated_seconds 11
--   mi_vistara        expected_volume_formula NULL
--   mi_pariksha       estimated_seconds 2
--   mi_bhavisya       estimated_seconds 2
