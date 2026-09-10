-- l3_w5_mechanical_checks.sql
--
-- L3 (Kāla) W5 VERIFY — mechanical checks, READ-ONLY.
--
-- Plan §4 W5 requires, per asset: "scripted mechanical checks (integrity SQL, digests,
-- counts, consumer reachability) + fresh-context judgment verification". This file is the
-- scripted half, authored as C8.5 prep AHEAD of W4 dispatch (most L3 assets are still
-- E-gate-blocked at authoring time). It is deliberately NOT the per-asset D-CND-03
-- integrity contracts — L3 already installed all 19 of those on asset_registry via
-- migration 670, each mutation-proved (see L3_STATE.md, PR #1792). These are the
-- CROSS-asset checks no single asset's contract can express: cascade seams between
-- layers, ranking-key integrity that serving depends on, orphan-family tripwires, and
-- the regression guards for W3's landed dispositions.
--
-- Every check returns one row: check_id, passed (boolean), detail. A check that cannot
-- fail on real corruption does not belong here (C12 rewrite-floor test). Where a check
-- passes vacuously on empty data, it SAYS SO in its detail column. Disclosure rows carry
-- passed = NULL — they are required context for any capsule, not gates.
--
-- READ-ONLY. Nothing here writes. Run before any capsule is proposed; the capsule cites
-- the output, and a fresh-context verifier re-runs it independently (implementer !=
-- certifier, charter C8 / D-CND-35).

\echo '=== L3 W5 MECHANICAL CHECKS (read-only) ==='
--
-- RUN STATUS AS OF 2026-09-07 (recorded so a reader knows these are RUN, not merely
-- authored — C12: a check that has never been green is a PROPOSAL, not a gate):
--   10 of 12 gates PASS. 2 FAIL, both on real corruption — the C12 rewrite-floor test
--   passing on the corruption that actually exists:
--     C1a predicates resolve   FAIL — TRUE POSITIVE FOUND BY THIS FILE'S FIRST RUN
--         (F-L3-16): 49,775 predicate rows already dangle against bodha_msr_signals.
--         49,730 on cb73cd3d (folds into #1793's known damage) — and 45 on the CANONICAL
--         chart 482012f1, all signature_class=CLASSIFY_RESIDUAL, all bound 2026-08-12:
--         a post-8/12 deletion of CLASSIFY_RESIDUAL signals cascaded away their
--         activations (kala_activation 672,551 -> 672,191 and kala_obstruction
--         1,283 -> 1,280 since F-L3-12's measurement) and dangled these predicates.
--         F-L3-12's "an L2 rebuild WOULD dangle them" is now "already has, twice".
--     C2  per-chart activation density   FAIL — #1793, chart cb73cd3d is cascade-damaged
--         (0.021 activations/predicate vs 6.699 / 6.694 on the two healthy charts).
--   Both stay red until the F-L3-12/#1793 disposition and a W4 rebuild — shipping either
--   green would be the gate-weakening the hard floor forbids.
--   Disclosures at run time: outcomes_recorded=0 of 200 (rebuild-safe today);
--   orb_strength 669,604/672,191 NULL on kala_activation (99.63%, known ka_sangam
--   coverage gap, F-KALA-1 context); staging=0; archive pins measured live and
--   hardcoded below the same day.

-- ---------------------------------------------------------------------------
-- C1. CASCADE-SEAM DANGLE TRIPWIRES  (F-L3-12; the #1748 shape at L3)
-- ---------------------------------------------------------------------------
-- All five FKs from L3 tables into bodha_msr_signals are ON DELETE CASCADE, so an
-- ordinary L2 bo_laksana rebuild silently destroys the FK-bearing rows — and DANGLES
-- kala_activation_predicates, which carries NO FK at all (150,150 rows at F-L3-12
-- measurement). C1a is the tripwire on that FK-less edge. C1b covers kala_activation:
-- green by FK today, but the FK is exactly what a future migration could drop or
-- soften, and this file must not depend on the constraint it is checking.
SELECT
  'C1a_predicates_resolve_to_signals' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM kala_activation_predicates p
    LEFT JOIN bodha_msr_signals s ON s.signal_id = p.signal_id
    WHERE s.signal_id IS NULL
  ) AS passed,
  'every kala_activation_predicates.signal_id resolves to bodha_msr_signals — the FK-less edge an L2 rebuild dangles silently (F-L3-12)' AS detail;

SELECT
  'C1b_activations_resolve_to_signals' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM kala_activation a
    LEFT JOIN bodha_msr_signals s ON s.signal_id = a.signal_id
    WHERE s.signal_id IS NULL
  ) AS passed,
  'every kala_activation.signal_id resolves — held by FK today; this check must outlive the constraint' AS detail;

-- ---------------------------------------------------------------------------
-- C2. PER-CHART ACTIVATION DENSITY  (the #1793 damage signature)
-- ---------------------------------------------------------------------------
-- The cascade damage F-L3-14 localised shows a precise signature: chart cb73cd3d has
-- 0.021 activations per predicate against 6.699 and 6.694 on the healthy charts, with
-- the FK-less predicate table intact. Any chart with a real predicate base (>= 1000
-- rows) but under 1 activation per predicate has lost its activation family. EXPECTED
-- TO FAIL while cb73cd3d awaits its formal disposition (#1793) — shipping this green
-- would be the gate-weakening the hard floor forbids.
SELECT
  'C2_no_activation_starved_chart' AS check_id,
  NOT EXISTS (
    SELECT 1
    FROM (SELECT chart_id, count(*) AS n_pred FROM kala_activation_predicates GROUP BY chart_id) p
    LEFT JOIN (SELECT chart_id, count(*) AS n_act FROM kala_activation GROUP BY chart_id) a
      USING (chart_id)
    WHERE p.n_pred >= 1000
      AND COALESCE(a.n_act, 0) < p.n_pred
  ) AS passed,
  'EXPECTED TO FAIL until #1793 rules chart cb73cd3d: a chart with a full predicate base but <1 activation/predicate has lost its activation family to the cascade seam' AS detail;

-- ---------------------------------------------------------------------------
-- C3. M12 DISPOSITION REGRESSION GUARD  (migration 672)
-- ---------------------------------------------------------------------------
-- Migration 672 deleted the 54 one-time debris rows (generation='3.0' with NULL
-- era_slice_key — foreign-engine output promoted into the century materializer's
-- surface, unreachable by the writer's own era-scoped DELETE). The writer by
-- construction cannot write such a row, so ANY reappearance is a new promotion-path
-- defect, not writer accretion.
SELECT
  'C3_no_null_era_slice_debris' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows
    WHERE generation = '3.0' AND era_slice_key IS NULL
  ) AS passed,
  'no generation-3.0 row may carry a NULL era_slice_key — the exact class migration 672 disposed of (M12/F-CENT-2)' AS detail;

-- ---------------------------------------------------------------------------
-- C4. P7 OUTCOME SEAM  (kala_bhavishya falsifiability data)
-- ---------------------------------------------------------------------------
-- outcome_recorded / outcome_notes is the layer's falsifiability seam: the first
-- outcome ever recorded is irreplaceable evidence, and the W3 preserve-on-rebuild work
-- exists to keep an ordinary rebuild from destroying it. C4a is the shape invariant;
-- C4b is the disclosure every W4 capsule MUST carry, because "how many outcomes would
-- a rebuild have to preserve" is the whole question.
SELECT
  'C4a_outcome_notes_imply_recorded' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM kala_bhavishya
    WHERE outcome_notes IS NOT NULL AND outcome_notes <> ''
      AND outcome_recorded IS NOT TRUE
  ) AS passed,
  'an outcome note may not exist on a row that claims no outcome was recorded' AS detail;

SELECT
  'C4b_outcome_seam_disclosure' AS check_id,
  NULL::boolean AS passed,
  'outcomes recorded (rebuild must preserve each one): '
  || (SELECT count(*) FROM kala_bhavishya WHERE outcome_recorded IS TRUE)
  || ' of ' || (SELECT count(*) FROM kala_bhavishya)
  || ' projections. 0 recorded = rebuild-safe today; any nonzero count makes preserve-on-rebuild LOAD-BEARING for the next W4.' AS detail;

-- ---------------------------------------------------------------------------
-- C5. KALA_FIELD FAMILY ORPHAN TRIPWIRE  (ka_kshetra; M8's real blocker context)
-- ---------------------------------------------------------------------------
-- The kala_field family has exactly ONE FK (weights -> weight_versions). Nothing binds
-- the 14 chart-bearing child tables to kala_field itself, so a per-chart parent rebuild
-- that dies before re-inserting — or a chart deletion — leaves the family orphaned
-- silently (the same F-L3-12 shape, ~2.3M rows at stake). A chart present in any child
-- but absent from the parent is debris no writer will ever reclaim.
SELECT
  'C5_field_family_charts_covered' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM (
      SELECT chart_id FROM kala_field_boundaries     UNION
      SELECT chart_id FROM kala_field_clocks         UNION
      SELECT chart_id FROM kala_field_gof            UNION
      SELECT chart_id FROM kala_field_kinematics     UNION
      SELECT chart_id FROM kala_field_null           UNION
      SELECT chart_id FROM kala_field_primitives     UNION
      SELECT chart_id FROM kala_field_promise_edges  UNION
      SELECT chart_id FROM kala_field_promise_nodes  UNION
      SELECT chart_id FROM kala_field_provenance     UNION
      SELECT chart_id FROM kala_field_routes         UNION
      SELECT chart_id FROM kala_field_salience       UNION
      SELECT chart_id FROM kala_field_skill          UNION
      SELECT chart_id FROM kala_field_snapshots      UNION
      SELECT chart_id FROM kala_field_windows
    ) child
    WHERE NOT EXISTS (SELECT 1 FROM kala_field f WHERE f.chart_id = child.chart_id)
  ) AS passed,
  'every chart appearing in any kala_field_* child table also has kala_field parent rows — the FK-less family a partial rebuild orphans (vacuous only if ALL family tables are empty, which the C10 counts would show)' AS detail;

-- ---------------------------------------------------------------------------
-- C6. RANKING-KEY INTEGRITY  (F-KALA-1's data-side precondition)
-- ---------------------------------------------------------------------------
-- Every serving-side ranking fix this campaign landed (judgment_query,
-- query_temporal_activation, ahead.ts x2) promotes dasha_activation_proximity_score to
-- the PRIMARY sort key precisely because it measured 0% NULL while orb_strength is
-- 99.6% NULL. If proximity scores ever go NULL, every one of those rankings silently
-- degrades back to the id-order defect. C6a pins the precondition; C6b disclosures the
-- orb coverage so a capsule cannot mistake it for a real signal.
SELECT
  'C6a_proximity_score_never_null' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM kala_activation
    WHERE dasha_activation_proximity_score IS NULL
  ) AS passed,
  'dasha_activation_proximity_score is the primary ranking key of four serving surfaces and was 0% NULL when they were built on it — a NULL here re-opens F-KALA-1 (vacuous only if kala_activation is empty; see C10)' AS detail;

SELECT
  'C6b_orb_strength_coverage_disclosure' AS check_id,
  NULL::boolean AS passed,
  'orb_strength NULL rate on kala_activation: '
  || (SELECT count(*) FROM kala_activation WHERE orb_strength IS NULL)
  || ' / ' || (SELECT count(*) FROM kala_activation)
  || ' (99.63% at authoring — ka_sangam covers only a fraction; any capsule citing orb-based ordering must disclose this)' AS detail;

-- ---------------------------------------------------------------------------
-- C7. PROJECTION SPINE REFERENTIAL CLOSURE  (kala_bhavishya's two parents)
-- ---------------------------------------------------------------------------
-- kala_bhavishya rows cite both a convergence and a signal. The convergence edge has
-- no FK; the signal edge cascades. Both must resolve for a served projection's
-- source_chain to be walkable at all.
SELECT
  'C7a_bhavishya_to_convergence' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM kala_bhavishya b
    LEFT JOIN kala_convergence c ON c.convergence_id = b.convergence_id
    WHERE b.convergence_id IS NOT NULL AND c.convergence_id IS NULL
  ) AS passed,
  'every projection''s convergence_id resolves (FK-less edge)' AS detail;

SELECT
  'C7b_bhavishya_to_signals' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM kala_bhavishya b
    LEFT JOIN bodha_msr_signals s ON s.signal_id = b.signal_id
    WHERE b.signal_id IS NOT NULL AND s.signal_id IS NULL
  ) AS passed,
  'every projection''s signal_id resolves' AS detail;

SELECT
  'C7c_convergence_to_signals' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM kala_convergence c
    LEFT JOIN bodha_msr_signals s ON s.signal_id = c.signal_id
    WHERE c.signal_id IS NOT NULL AND s.signal_id IS NULL
  ) AS passed,
  'every convergence''s signal_id resolves' AS detail;

-- ---------------------------------------------------------------------------
-- C8. ARCHIVE IMMUTABILITY PINS  (frozen corpora may never drift)
-- ---------------------------------------------------------------------------
-- Two snapshot tables are frozen by name and purpose. Unlike live tables, pinning an
-- exact count on an immutable artifact IS a content assertion (D-CND-01: the count is
-- a conjunct of the immutability contract, and any delta — up or down — is corruption).
-- The v1 sweep corpus itself is already guarded by its own D-CND-03 contract
-- (the in-database loss detector, migration 670); these two are the gaps it left.
-- Counts measured live 2026-09-07.
SELECT
  'C8a_archive_20260805_pinned' AS check_id,
  (SELECT count(*) FROM kala_gochara_windows_archive_20260805) = 35620 AS passed,
  'kala_gochara_windows_archive_20260805 must hold exactly 35,620 rows forever (measured at pin time); any delta is tampering with a frozen archive' AS detail;

SELECT
  'C8b_ssv_20260728c_pinned' AS check_id,
  (SELECT count(*) FROM kala_gochara_windows__ssv_20260728c) = 1267 AS passed,
  'kala_gochara_windows__ssv_20260728c must hold exactly 1,267 rows forever (measured at pin time)' AS detail;

-- ---------------------------------------------------------------------------
-- C9. STAGING AT REST  (interrupted-build indicator — disclosure, not a gate)
-- ---------------------------------------------------------------------------
-- kala_convergence_staging holds rows only mid-build. Rows AT REST suggest an
-- interrupted run (the SATYA-DĪPA no-op-completion shape: partial data present,
-- completion signal absent). Disclosed rather than gated because "empty at rest" is
-- the writer's observed behavior, not a contract this file is entitled to invent.
SELECT
  'C9_staging_at_rest_disclosure' AS check_id,
  NULL::boolean AS passed,
  'kala_convergence_staging rows at rest: '
  || (SELECT count(*) FROM kala_convergence_staging)
  || ' (0 = no interrupted build in flight; nonzero during an active W4 run is normal, nonzero at rest is not)' AS detail;

-- ---------------------------------------------------------------------------
-- C10. VACUITY DISCLOSURE — not a check, a required disclosure
-- ---------------------------------------------------------------------------
-- Charter C12: a check that passes vacuously on an empty table attests nothing. Any
-- capsule citing this file MUST carry these counts alongside the passes.
SELECT
  'C10_vacuity_disclosure' AS check_id,
  NULL::boolean AS passed,
  'row counts backing the checks above — a pass over 0 rows is vacuous: '
  || 'activation='   || (SELECT count(*) FROM kala_activation)
  || ' predicates='  || (SELECT count(*) FROM kala_activation_predicates)
  || ' convergence=' || (SELECT count(*) FROM kala_convergence)
  || ' bhavishya='   || (SELECT count(*) FROM kala_bhavishya)
  || ' darshana='    || (SELECT count(*) FROM kala_darshana)
  || ' obstruction=' || (SELECT count(*) FROM kala_obstruction)
  || ' gochara_windows=' || (SELECT count(*) FROM kala_gochara_windows)
  || ' field='       || (SELECT count(*) FROM kala_field)
  || ' field_windows=' || (SELECT count(*) FROM kala_field_windows)
  AS detail;
