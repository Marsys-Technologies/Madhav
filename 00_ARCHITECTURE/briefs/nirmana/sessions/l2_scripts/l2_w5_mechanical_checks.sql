-- l2_w5_mechanical_checks.sql
--
-- L2 (Bodha) W5 VERIFY — cross-asset mechanical checks, READ-ONLY.
--
-- Plan §4 W5 requires, per asset: "scripted mechanical checks (integrity SQL, digests,
-- counts, consumer reachability) + fresh-context judgment verification". This file is the
-- CROSS-asset scripted half, following the L4/L5 precedent (l4_scripts/
-- l4_w5_mechanical_checks.sql, l5_scripts/l5_w5_mechanical_checks.sql). It deliberately
-- does NOT duplicate:
--   * the 20 per-asset integrity_check_sql contracts on asset_registry (M-14 wave;
--     D-CND-01-conformant) — the W5 runbook's batch DO block runs those;
--   * bo_laksana / bo_laksana_rerank per-asset contracts — those two are the only L2
--     assets with integrity_check_sql still NULL, deliberately: their contracts land with
--     the held rebuild (campaign hold #1770 + L1 freeze E-gate), and a contract authored
--     against pre-rebuild data would pin the wrong shape.
-- What lives here is only what NO single asset's contract can express: cross-table
-- same-universe enforcement, cross-LAYER reference resolution (§N.5), and vocabulary/
-- tiling invariants that span co-writers of one table.
--
-- Every check returns one row: check_id, passed (boolean), detail. A check that cannot
-- fail on real corruption does not belong here (C12 rewrite-floor test; standing ruling
-- D-CND-01: a bare count(*) = N is forbidden — every count here is a conjunct of a
-- distinctness/tiling/resolution invariant that can fail on corruption the count alone
-- cannot see). Where a check passes vacuously on empty data, its detail SAYS SO rather
-- than reporting a bare green.
--
-- READ-ONLY. Nothing here writes. Run before any capsule is proposed; the capsule cites
-- the output, and a fresh-context verifier re-runs it independently (implementer !=
-- certifier, charter C8 / prompt W5).
--
-- RUN STATUS AS OF 2026-09-07 (recorded so a reader knows these are RUN, not merely
-- authored — C12: a check that has never been green OR red is a PROPOSAL, not a gate):
--   5 of 8 PASS (X7 vacuously — bodha_grounding_matches has 0 rows until bo_grounding's
--   registration/dispatch clears its #2258 manifest ruling — and its detail says so).
--   3 FAIL, and EVERY failure is on a defect already found and documented — red persists
--   because no W4 rebuild has run yet (all L2 rebuilds are E-gate/hold blocked):
--     X2 §N.5 constituent_facts_array resolution  FAIL — 11,355 of 210,697 distinct cited
--        fact_ids do not resolve into chart_facts. Consistent with the fact_id hash-scheme
--        change (#1747 / PR #1898) that already made ga_yoga_firings.constituent_fact_ids
--        systemically stale (state file, cycle 810 finding 2); the held bo_laksana rebuild
--        re-derives the arrays under the current scheme.
--     X3 triangulation signal_ids resolution      FAIL — 159 of 148,462 distinct cited
--        signal_ids dangle (no bodha_msr_signals row). First measured figure for the
--        "bodha_triangulation.signal_ids[] disposition" open item (state file, loop 6).
--     X8 constituent_signals_array self-resolution FAIL — 20 distinct cited constituent
--        signal_ids dangle across the 156 citing rows; same defect class as X3, intra-table.
--   Those failures are the C12 rewrite-floor test PASSING: these checks CAN fail on real
--   corruption, and they do, on corruption that actually exists. Expect them to stay red
--   until the E-gate opens and the held rebuilds re-derive the citing arrays.
--   Populations behind the non-vacuous greens: X1 10,515 anomaly rows; X4 135 resonance
--   rows (9 grahas x 5 ayanamshas x 3 charts); X5 4 populated tables; X6 50,104+ signals.

\echo '=== L2 W5 MECHANICAL CHECKS (read-only) ==='

-- ---------------------------------------------------------------------------
-- X1. bodha_anomalies must live inside bodha_msr_signals' (chart, ayanamsha) universe
-- ---------------------------------------------------------------------------
-- bo_anveshana's own contract checks its rows; nothing checks that an anomaly was
-- discovered over a chart+ayanamsha combination the signal substrate actually covers.
-- An anomaly on a universe with no signals is either an orphan of a deleted build or a
-- writer scoping bug — representable, and invisible to both assets' own contracts.
SELECT
  'X1_anomalies_within_signal_universe' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM (SELECT DISTINCT chart_id, ayanamsha_id FROM bodha_anomalies) a
    WHERE NOT EXISTS (
      SELECT 1 FROM bodha_msr_signals s
      WHERE s.chart_id = a.chart_id AND s.ayanamsha_id = a.ayanamsha_id
    )
  ) AS passed,
  CASE WHEN NOT EXISTS (SELECT 1 FROM bodha_anomalies)
       THEN 'VACUOUS: zero anomaly rows exist — green proves nothing'
       ELSE format('every anomaly (chart, ayanamsha) universe has signal coverage (%s anomaly rows checked)',
                   (SELECT count(*) FROM bodha_anomalies))
  END AS detail;

-- ---------------------------------------------------------------------------
-- X2. §N.5 — bodha_msr_signals.constituent_facts_array MUST resolve into chart_facts
-- ---------------------------------------------------------------------------
-- CLAUDE.md §N.5 verbatim: "The constituent_facts_array in MSR signals resolves back to
-- chart_facts.fact_id — these MUST resolve." This is the L1-authority invariant no
-- single-asset contract expresses (it crosses the L1/L2 boundary). Same-chart is part of
-- the claim: a signal may not cite another chart's fact.
SELECT
  'X2_n5_constituent_facts_resolve' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals s, unnest(s.constituent_facts_array) AS cited(fact_id)
    WHERE NOT EXISTS (
      SELECT 1 FROM chart_facts cf
      WHERE cf.fact_id = cited.fact_id AND cf.chart_id = s.chart_id
    )
  ) AS passed,
  CASE WHEN NOT EXISTS (SELECT 1 FROM bodha_msr_signals WHERE array_length(constituent_facts_array,1) > 0)
       THEN 'VACUOUS: no signal cites any fact — green proves nothing'
       ELSE format('%s of %s distinct cited fact_ids fail same-chart resolution into chart_facts (0 required by §N.5)',
                   (SELECT count(DISTINCT cited.fact_id)
                      FROM bodha_msr_signals s, unnest(s.constituent_facts_array) AS cited(fact_id)
                     WHERE NOT EXISTS (SELECT 1 FROM chart_facts cf
                                        WHERE cf.fact_id = cited.fact_id AND cf.chart_id = s.chart_id)),
                   (SELECT count(DISTINCT f) FROM (SELECT unnest(constituent_facts_array) FROM bodha_msr_signals) u(f)))
  END AS detail;

-- ---------------------------------------------------------------------------
-- X3. bodha_triangulation.signal_ids[] must resolve into bodha_msr_signals, same chart
-- ---------------------------------------------------------------------------
-- The open "signal_ids[] disposition" item (state file, loop 6). Triangulation verdicts
-- cite the signals they aggregate; a dangling citation means the verdict rests on a
-- signal a later REPLACE removed — the exact accretion-vs-replace seam between the two
-- co-writers, which neither asset's own contract can see.
SELECT
  'X3_triangulation_signal_ids_resolve' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM bodha_triangulation t, unnest(t.signal_ids) AS cited(signal_id)
    WHERE NOT EXISTS (
      SELECT 1 FROM bodha_msr_signals s
      WHERE s.signal_id = cited.signal_id AND s.chart_id = t.chart_id
    )
  ) AS passed,
  CASE WHEN NOT EXISTS (SELECT 1 FROM bodha_triangulation WHERE array_length(signal_ids,1) > 0)
       THEN 'VACUOUS: no triangulation cites any signal — green proves nothing'
       ELSE format('%s of %s distinct cited signal_ids dangle (no same-chart bodha_msr_signals row)',
                   (SELECT count(DISTINCT cited.signal_id)
                      FROM bodha_triangulation t, unnest(t.signal_ids) AS cited(signal_id)
                     WHERE NOT EXISTS (SELECT 1 FROM bodha_msr_signals s
                                        WHERE s.signal_id = cited.signal_id AND s.chart_id = t.chart_id)),
                   (SELECT count(DISTINCT x) FROM (SELECT unnest(signal_ids) FROM bodha_triangulation) u(x)))
  END AS detail;

-- ---------------------------------------------------------------------------
-- X4. bodha_rm_resonances graha tiling: exactly the 9 grahas per (chart, ayanamsha, snapshot)
-- ---------------------------------------------------------------------------
-- Tiling + distinctness (D-CND-01 named invariant): every populated scope carries each of
-- the nine grahas exactly once. A count(*)=135 alone cannot see a scope with Mars twice
-- and no Ketu.
SELECT
  'X4_rm_resonance_graha_tiling' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM bodha_rm_resonances
    GROUP BY chart_id, ayanamsha_id, snapshot_type
    HAVING count(*) <> 9
        OR count(DISTINCT graha) <> 9
        OR count(*) FILTER (WHERE graha NOT IN
             ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu')) > 0
  ) AS passed,
  CASE WHEN NOT EXISTS (SELECT 1 FROM bodha_rm_resonances)
       THEN 'VACUOUS: zero resonance rows exist — green proves nothing'
       ELSE format('every (chart, ayanamsha, snapshot) scope tiles the 9 canonical grahas exactly once (%s scopes)',
                   (SELECT count(*) FROM (SELECT DISTINCT chart_id, ayanamsha_id, snapshot_type
                                            FROM bodha_rm_resonances) sc))
  END AS detail;

-- ---------------------------------------------------------------------------
-- X5. Canonical ayanamsha vocabulary guard across every populated bodha_* table
-- ---------------------------------------------------------------------------
-- The five canonical ayanamshas are a cross-writer contract; one writer inventing a
-- sixth spelling (or a casing variant) silently partitions every downstream join. No
-- per-asset contract owns the shared vocabulary.
WITH bad AS (
  SELECT ayanamsha_id FROM bodha_msr_signals
  UNION ALL SELECT ayanamsha_id FROM bodha_anomalies
  UNION ALL SELECT ayanamsha_id FROM bodha_rm_resonances
  UNION ALL SELECT ayanamsha_id FROM bodha_triangulation
  UNION ALL SELECT ayanamsha_id FROM bodha_grounding_matches
)
SELECT
  'X5_canonical_ayanamsha_vocab' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM bad WHERE ayanamsha_id NOT IN
      ('lahiri_chitrapaksha','raman','krishnamurti','surya_siddhanta_classical','true_chitra')
  ) AS passed,
  format('all ayanamsha_id values across 5 bodha_* tables are canonical (%s total rows swept)',
         (SELECT count(*) FROM bad)) AS detail;

-- ---------------------------------------------------------------------------
-- X6. Salience percentile + confidence range guards on bodha_msr_signals
-- ---------------------------------------------------------------------------
-- Range guards (D-CND-01 named invariant). salience_pctl_in_class is a percentile in
-- [0,1] by the tail-lane contract (PR #1755); cross_ayanamsha_consistency_score likewise.
-- NULL is honest and allowed (§N.7 item 6) — only a PRESENT value may not leave range.
SELECT
  'X6_salience_range_guards' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE (salience_pctl_in_class IS NOT NULL
           AND (salience_pctl_in_class < 0 OR salience_pctl_in_class > 1))
       OR (cross_ayanamsha_consistency_score IS NOT NULL
           AND (cross_ayanamsha_consistency_score < 0 OR cross_ayanamsha_consistency_score > 1))
  ) AS passed,
  CASE WHEN NOT EXISTS (SELECT 1 FROM bodha_msr_signals
                        WHERE salience_pctl_in_class IS NOT NULL
                           OR cross_ayanamsha_consistency_score IS NOT NULL)
       THEN 'VACUOUS: both guarded columns are all-NULL — green proves nothing'
       ELSE format('all present percentile/consistency values in [0,1] (%s signal rows swept)',
                   (SELECT count(*) FROM bodha_msr_signals))
  END AS detail;

-- ---------------------------------------------------------------------------
-- X7. bodha_grounding_matches: tier vocabulary + sruti evidence + target resolution
-- ---------------------------------------------------------------------------
-- D-NATIVE-09: tier in (sruti, yukti, pratyaksa); a sruti claim without its matched rule
-- is a fabricated citation (D-GROUNDING floor violation); targets must resolve into the
-- table their target_kind names, same chart. VACUOUS until bo_grounding dispatches
-- (#2258 manifest ruling) — recorded green-with-caveat, not silently green.
SELECT
  'X7_grounding_tier_and_targets' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM bodha_grounding_matches g
    WHERE g.grounding_tier NOT IN ('sruti','yukti','pratyaksa')
       OR (g.grounding_tier = 'sruti' AND g.matched_rule_id IS NULL)
       OR (g.target_kind = 'msr_signal' AND NOT EXISTS (
             SELECT 1 FROM bodha_msr_signals s
             WHERE s.signal_id::text = g.target_id AND s.chart_id = g.chart_id))
       OR (g.target_kind = 'yoga_dosha_firing' AND NOT EXISTS (
             SELECT 1 FROM ga_yoga_firings f
             WHERE f.id::text = g.target_id AND f.chart_id = g.chart_id))
  ) AS passed,
  CASE WHEN NOT EXISTS (SELECT 1 FROM bodha_grounding_matches)
       THEN 'VACUOUS: zero grounding rows exist (bo_grounding undispatched, #2258) — green proves nothing'
       ELSE format('tier vocab + sruti evidence + same-chart target resolution hold (%s rows)',
                   (SELECT count(*) FROM bodha_grounding_matches))
  END AS detail;

-- ---------------------------------------------------------------------------
-- X8. bodha_msr_signals.constituent_signals_array self-resolution, same chart
-- ---------------------------------------------------------------------------
-- Same defect class as X3, intra-table: an aggregate signal citing member signals a
-- later REPLACE removed rests on evidence that no longer exists. The writer's own
-- idempotency (delete-then-insert per chart x natural key) makes this representable
-- whenever citing and cited rows belong to different build generations.
SELECT
  'X8_constituent_signals_self_resolve' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals s, unnest(s.constituent_signals_array) AS cited(sid)
    WHERE NOT EXISTS (
      SELECT 1 FROM bodha_msr_signals m
      WHERE m.signal_id::text = cited.sid::text AND m.chart_id = s.chart_id
    )
  ) AS passed,
  CASE WHEN NOT EXISTS (SELECT 1 FROM bodha_msr_signals WHERE array_length(constituent_signals_array,1) > 0)
       THEN 'VACUOUS: no signal cites another signal — green proves nothing'
       ELSE format('%s distinct cited constituent signal_ids dangle (0 required)',
                   (SELECT count(DISTINCT cited.sid)
                      FROM bodha_msr_signals s, unnest(s.constituent_signals_array) AS cited(sid)
                     WHERE NOT EXISTS (SELECT 1 FROM bodha_msr_signals m
                                        WHERE m.signal_id::text = cited.sid::text AND m.chart_id = s.chart_id)))
  END AS detail;
