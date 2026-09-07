-- l4_w5_mechanical_checks.sql
--
-- L4 (Phala) W5 VERIFY — cross-asset mechanical checks, READ-ONLY.
--
-- Plan §4 W5 requires, per asset: "scripted mechanical checks (integrity SQL, digests,
-- counts, consumer reachability) + fresh-context judgment verification". This file is the
-- CROSS-asset scripted half, following the L5 precedent (l5_scripts/
-- l5_w5_mechanical_checks.sql). It deliberately does NOT duplicate:
--   * the 9 per-asset integrity_check_sql contracts on asset_registry (migration 681,
--     C12/D-CND-03) — the W5 runbook's batch DO block runs those;
--   * checks a per-asset contract already expresses (e.g. ph_pratikara's obstruction
--     tiling, ph_suddha_sodhana's anchor tiling, ph_muhurta's same-chart anchor link,
--     ph_sodhana's same-chart anchor link, ph_nimitta's 8-column anchor RESOLUTION sweep).
-- What lives here is only what NO single asset's contract can express: same-chart
-- enforcement on references whose resolution-but-not-chart is checked elsewhere, reference
-- columns nothing checks at all, and the four W1-derived invariants deliberately withheld
-- from migration 681 because they fail on current (pre-W4-rebuild) data.
--
-- Every check returns one row: check_id, passed (boolean), detail. A check that cannot
-- fail on real corruption does not belong here (C12 rewrite-floor test). Where a check
-- passes vacuously on empty data, its detail SAYS SO rather than reporting a bare green.
--
-- READ-ONLY. Nothing here writes. Run before any capsule is proposed; the capsule cites
-- the output, and a fresh-context verifier re-runs it independently (implementer !=
-- certifier, charter C8 / prompt §7.4).
--
-- RUN STATUS AS OF 2026-09-07 (recorded so a reader knows these are RUN, not merely
-- authored — C12: a check that has never been green OR red is a PROPOSAL, not a gate):
--   7 of 10 PASS (3 of those 7 vacuously, and each SAYS SO: X5, X6, W1 guard columns/
--   statuses with zero rows in pre-rebuild data). 3 FAIL, and EVERY failure is on a defect
--   already found, root-caused, and code-fixed — red persists only because no W4 rebuild
--   has run yet:
--     W2 rect load_bearing discriminates FAIL — F3/#1834: load_bearing=true at win_margin=0
--     W3 rect confidence band valid      FAIL — confidence_low=-0.2000 persisted, both charts
--     W4 sankrama no-gap tiling          FAIL — #1788: exactly 250 missing pairs measured,
--                                        matching the writer's own recorded defect figure —
--                                        the check independently reproduces the known count
--   Those three failures are the C12 rewrite-floor test PASSING: these checks CAN fail on
--   real corruption, and they do, on the corruption that actually exists. Expect all three
--   to stay red until the E-gate opens and W4 rebuilds the data — that is the point.
--   Populations behind the non-vacuous greens: X1 1,277 links, X4 60 refs.

\echo '=== L4 W5 MECHANICAL CHECKS (read-only) ==='

-- ---------------------------------------------------------------------------
-- X1. phala_mitigation.linked_anchor_id must be SAME-CHART
-- ---------------------------------------------------------------------------
-- ph_nimitta's detector (clause a6) proves the link RESOLVES; nothing proves it resolves
-- into the same chart's anchors. anchor_id carries no chart component (D-CND-04 is a
-- content hash), so a cross-chart link is representable and nothing else would see it.
SELECT
  'X1_mitigation_anchor_same_chart' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM phala_mitigation m
      JOIN phala_anchors a ON a.anchor_id = m.linked_anchor_id
     WHERE m.linked_anchor_id IS NOT NULL AND a.chart_id <> m.chart_id
  ) AS passed,
  CASE WHEN NOT EXISTS (SELECT 1 FROM phala_mitigation WHERE linked_anchor_id IS NOT NULL)
       THEN 'VACUOUS: zero non-NULL linked_anchor_id rows exist — green proves nothing'
       ELSE format('a mitigation may not cite another chart''s anchor (%s non-NULL links checked)',
                   (SELECT count(*) FROM phala_mitigation WHERE linked_anchor_id IS NOT NULL))
  END AS detail;

-- ---------------------------------------------------------------------------
-- X2. phala_sankrama.source_anchor_id must be SAME-CHART
-- ---------------------------------------------------------------------------
SELECT
  'X2_sankrama_anchor_same_chart' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM phala_sankrama s
      JOIN phala_anchors a ON a.anchor_id = s.source_anchor_id
     WHERE a.chart_id <> s.chart_id
  ) AS passed,
  'a spillover may not originate from another chart''s anchor (resolution is checked by ph_nimitta clause a4; chart identity only here)' AS detail;

-- ---------------------------------------------------------------------------
-- X3. phala_phaladesa.top_anchor_id must be SAME-CHART
-- ---------------------------------------------------------------------------
-- ph_phaladesa's own detector (clause 4) proves the verdict anchor EXISTS; its
-- anchor_count clause counts the chart's own anchors — but the headline anchor row
-- itself could still belong to a different chart and both clauses stay green.
SELECT
  'X3_phaladesa_top_anchor_same_chart' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM phala_phaladesa pd
      JOIN phala_anchors a ON a.anchor_id = pd.top_anchor_id
     WHERE pd.top_anchor_id IS NOT NULL AND a.chart_id <> pd.chart_id
  ) AS passed,
  'a domain verdict may not headline another chart''s anchor' AS detail;

-- ---------------------------------------------------------------------------
-- X4. phala_muhurta.overlapping_obstruction_id resolves, SAME-CHART
-- ---------------------------------------------------------------------------
-- No detector anywhere touches this column: ph_muhurta's contract checks linked_anchor_id,
-- windows, and fingerprints; ph_pratikara's checks obstruction TILING, not muhurta's
-- back-reference into kala_obstruction.
SELECT
  'X4_muhurta_obstruction_resolves_same_chart' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM phala_muhurta m
      LEFT JOIN kala_obstruction o ON o.id = m.overlapping_obstruction_id
     WHERE m.overlapping_obstruction_id IS NOT NULL
       AND (o.id IS NULL OR o.chart_id <> m.chart_id)
  ) AS passed,
  CASE WHEN NOT EXISTS (SELECT 1 FROM phala_muhurta WHERE overlapping_obstruction_id IS NOT NULL)
       THEN 'VACUOUS: zero non-NULL overlapping_obstruction_id rows exist — green proves nothing'
       ELSE format('an adversity-window flag must cite a real obstruction of the same chart (%s non-NULL refs checked)',
                   (SELECT count(*) FROM phala_muhurta WHERE overlapping_obstruction_id IS NOT NULL))
  END AS detail;

-- ---------------------------------------------------------------------------
-- X5. phala_pramana.linked_sodhana_id resolves, SAME-CHART
-- ---------------------------------------------------------------------------
-- No detector anywhere touches this column.
SELECT
  'X5_pramana_sodhana_link_resolves_same_chart' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM phala_pramana p
      LEFT JOIN phala_sodhana s ON s.sodhana_id = p.linked_sodhana_id
     WHERE p.linked_sodhana_id IS NOT NULL
       AND (s.sodhana_id IS NULL OR s.chart_id <> p.chart_id)
  ) AS passed,
  CASE WHEN NOT EXISTS (SELECT 1 FROM phala_pramana WHERE linked_sodhana_id IS NOT NULL)
       THEN 'VACUOUS: zero non-NULL linked_sodhana_id rows exist — green proves nothing'
       ELSE format('a pramana''s anomaly link must resolve within its own chart (%s non-NULL links checked)',
                   (SELECT count(*) FROM phala_pramana WHERE linked_sodhana_id IS NOT NULL))
  END AS detail;

-- ---------------------------------------------------------------------------
-- X6. phala_sankrama.mitigation_ref resolves, SAME-CHART
-- ---------------------------------------------------------------------------
-- No detector anywhere touches this column.
SELECT
  'X6_sankrama_mitigation_ref_resolves_same_chart' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM phala_sankrama k
      LEFT JOIN phala_mitigation m ON m.mitigation_id::text = k.mitigation_ref::text
     WHERE k.mitigation_ref IS NOT NULL
       AND (m.mitigation_id IS NULL OR m.chart_id <> k.chart_id)
  ) AS passed,
  CASE WHEN NOT EXISTS (SELECT 1 FROM phala_sankrama WHERE mitigation_ref IS NOT NULL)
       THEN 'VACUOUS: zero non-NULL mitigation_ref rows exist — green proves nothing'
       ELSE format('a spillover''s mitigation pointer must resolve within its own chart (%s non-NULL refs checked)',
                   (SELECT count(*) FROM phala_sankrama WHERE mitigation_ref IS NOT NULL))
  END AS detail;

-- ===========================================================================
-- W-series: the four invariants W1 derived as real but migration 681 deliberately
-- WITHHELD because they fail on current data (runbook §"Known gaps"). Pre-written
-- here so the cycle that runs W5 executes them instead of re-deriving them. Each is
-- EXPECTED RED until its asset's W4 rebuild lands the already-merged code fix into
-- data; a red here on post-rebuild data is a REAL failure, not an expected one.
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- W1. ph_pramana: a life_event_miss must cite a resolvable LEL comparison
-- ---------------------------------------------------------------------------
-- W1-era data failed this 12/12. Since then migration 684 added the
-- 'detector_unavailable' disposition and PR #1842 fixed the domain-vocabulary mismatch
-- that made life_event_match unreachable — current pre-rebuild data holds ZERO
-- life_event_miss rows, so today this passes VACUOUSLY. The check earns its green only
-- on post-W4 data where miss rows exist again.
SELECT
  'W1_pramana_miss_cites_lel' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM phala_pramana p
     WHERE p.window_status = 'life_event_miss'
       AND (p.lel_entry_id IS NULL
            OR NOT EXISTS (SELECT 1 FROM life_events le WHERE le.id::text = p.lel_entry_id::text))
  ) AS passed,
  CASE WHEN NOT EXISTS (SELECT 1 FROM phala_pramana WHERE window_status = 'life_event_miss')
       THEN 'VACUOUS: zero life_event_miss rows in current data — green proves nothing until a W4 rebuild produces miss rows'
       ELSE format('every life_event_miss must cite a resolvable life_events row (%s miss rows checked)',
                   (SELECT count(*) FROM phala_pramana WHERE window_status = 'life_event_miss'))
  END AS detail;

-- ---------------------------------------------------------------------------
-- W2. ph_rectification: load_bearing may not be true on a non-discriminating fit
-- ---------------------------------------------------------------------------
-- The F3 defect (fix merged, #1834): a best-candidate row claiming load_bearing while
-- win_margin = 0 asserts a discrimination the scoring never made. load_bearing lives in
-- judgment_flags (jsonb), not a column.
SELECT
  'W2_rect_load_bearing_discriminates' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM phala_rectification_best
     WHERE (judgment_flags->>'load_bearing')::boolean IS TRUE
       AND coalesce(win_margin, 0) <= 0
  ) AS passed,
  'EXPECTED RED until W4 rebuild: pre-rebuild data persists load_bearing=true at win_margin=0 (code fix #1834 merged; only a rebuild fixes the data)' AS detail;

-- ---------------------------------------------------------------------------
-- W3. ph_rectification: confidence band must be a valid probability band
-- ---------------------------------------------------------------------------
-- Pre-rebuild data persists confidence_low = -0.2000. A confidence bound outside [0,1]
-- is not a probability; a band with low > high is not a band.
SELECT
  'W3_rect_confidence_band_valid' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM phala_rectification_best
     WHERE confidence_low < 0 OR confidence_high > 1 OR confidence_low > confidence_high
  ) AS passed,
  'EXPECTED RED until W4 rebuild: pre-rebuild data persists confidence_low=-0.2000 on every chart' AS detail;

-- ---------------------------------------------------------------------------
-- W4. ph_sankrama: full no-gap tiling against material CDLM cells
-- ---------------------------------------------------------------------------
-- ph_sankrama's own detector proves value-fidelity on rows that EXIST (§N.5 drift) and
-- natural-key distinctness — it cannot see a MISSING row. The writer's contract
-- (ph_sankrama.py): for every anchor, every cell of the same chart with
-- domain_row = lower(anchor.domain) (identity map — the vocabularies converged; the old
-- 'transition'→'general' map entry was the defect) and net_linkage_strength >= 0.25
-- must yield exactly one row keyed (source_anchor_id, cdlm_cell_id). 'wealth' anchors
-- legitimately tile nothing (no such domain_row — B.10-disclosed in the writer).
SELECT
  'W4_sankrama_no_gap_tiling' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM phala_anchors a
      JOIN bodha_cdlm_cells c
        ON c.chart_id = a.chart_id
       AND lower(c.domain_row) = lower(a.domain)
       AND c.net_linkage_strength >= 0.25
     WHERE NOT EXISTS (
        SELECT 1 FROM phala_sankrama s
         WHERE s.chart_id = a.chart_id
           AND s.source_anchor_id = a.anchor_id
           AND s.cdlm_cell_id = c.cell_id
     )
  ) AS passed,
  format('EXPECTED RED until W4 rebuild: pre-rebuild data misses the ''transition'' spillovers the old domain map destroyed (fix #1788 merged; %s missing pairs measured now)',
         (SELECT count(*) FROM phala_anchors a
            JOIN bodha_cdlm_cells c
              ON c.chart_id = a.chart_id
             AND lower(c.domain_row) = lower(a.domain)
             AND c.net_linkage_strength >= 0.25
           WHERE NOT EXISTS (
              SELECT 1 FROM phala_sankrama s
               WHERE s.chart_id = a.chart_id
                 AND s.source_anchor_id = a.anchor_id
                 AND s.cdlm_cell_id = c.cell_id))) AS detail;

\echo '=== END L4 W5 MECHANICAL CHECKS ==='
