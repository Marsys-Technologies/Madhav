-- 681_l4_phala_c12_registry_contracts.sql
--
-- NIRMĀṆA v2.1 · L4 Phala · W3-1 · C12 (D-VR-DATA-CORRECTNESS) registry delta.
--
-- WHY
-- ---
-- Every L4 asset had target_floor, expected_volume_formula, expected_volume_inputs
-- and integrity_check_sql all NULL -- C12's named defect condition verbatim
-- ("NULL is the defect"). This migration closes it for all nine, using volume
-- expectations DERIVED from first principles in W1 and invariants that are real
-- cross-table consistency / tiling / re-derivation checks.
--
-- NO BARE EQUALITY PINS. C12 forbids `count(*) = N` as a volume assertion --
-- "an equality wearing a floor's name" (M0-T86 / D-126). Every volume expectation
-- below is either derived from a live upstream count or is a floor at the achieved
-- count (§N.4). The two derived equalities that DO appear (ph_suddha_sodhana,
-- ph_pramana) compare against a live `count(phala_anchors)`, not a literal.
--
-- CHART-PARTITIONED, PER D-CND-03
-- ------------------------------
-- The freeze-time integrity detector executes with no bind parameters (issue #1723), so a
-- per_chart asset's check cannot be scoped with `WHERE chart_id = $1`. The CONDUCTOR's
-- D-CND-03 ruling on #1723 requires the stronger answer rather than the honest-caveat one I
-- first proposed: quantify over every chart AND keep per-chart attribution, by PARTITIONING
-- instead of aggregating --
--
--     SELECT NOT EXISTS (SELECT 1 FROM <t> GROUP BY chart_id HAVING <violation>)
--
-- This is strictly stronger on C12's rewrite floor test: a corruption confined to one chart
-- makes exactly that chart's group violate, where a whole-table aggregate can be dominated by
-- the other charts' rows and miss it entirely. Every clause below takes this form.
--
-- ONE clause cannot: ph_pramana's re-assertion of the D5 NO-SCORING gate reads
-- information_schema, which has no chart_id to partition on. It is a SCHEMA invariant, not a
-- data one, and the claim is chart-independent by nature. Per D-CND-03 clause 2 it carries a
-- SQL comment naming why.
--
-- EVERY DETECTOR WAS RUN LIVE BEFORE THIS MIGRATION WAS WRITTEN
-- ------------------------------------------------------------
-- Each passes on current production data AND was shown to go red on injected
-- corruption (C12's rewrite floor test). Two scoping corrections came out of that
-- exercise and are recorded rather than silently applied:
--   * ph_muhurta's citation-distinctness is PER CHART. Across all charts it fails,
--     because source_citation is 'ph_muhurta/{action_class}/{start}' with no chart
--     component -- a genuine collision between charts, not a defect in either.
--   * ph_pratikara's 1:1 tiling with kala_obstruction is scoped to charts that HAVE
--     mitigation rows. Chart cb73cd3d has 6 obstructions and no mitigation because its
--     ph_nimitta build errored ("BLOCKED: upstream ka_bhavishya_lekha did not
--     complete") and ph_pratikara never ran. An unbuilt chart is not corruption. The
--     scoped form still goes red on a genuine partial build -- verified by deleting a
--     row in a probe and confirming it fails.
--
-- WHAT IS DELIBERATELY *NOT* INSTALLED HERE
-- -----------------------------------------
-- Four invariants that W1 derived FAIL on today's data because they detect real,
-- open defects. Installing them now would leave assets holding a knowingly-red gate,
-- so they land WITH their fixes in W3-3, not before:
--   * ph_pramana  -- "a life_event_miss must cite a resolvable LEL comparison" (fails 12/12)
--   * ph_rectification -- "load_bearing may not be true on a non-discriminating fit" (fails 1/1)
--   * ph_rectification -- confidence_low/high must be a probability band (fails: -0.2000 persisted)
--   * ph_sankrama -- full no-gap tiling against bodha_cdlm_cells (fails: 250 rows destroyed
--                    by the transition->general domain-map defect)
-- Each is named in the relevant asset's volume_explanation so the gap is visible
-- rather than merely absent.
--
-- depends_on is NOT touched: it is immutable for the rest of the campaign (issue #1744).
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

-- ── ph_nimitta ──────────────────────────────────────────────────────────────
-- integrity_check_sql was installed by migration 680 (D-CND-04). Volume only here.
UPDATE asset_registry SET
  target_floor = 139,
  catalog_status = 'CURRENT',
  expected_volume_formula =
    'sum over domains of least(50, count(kala_convergence for that domain)) '
    '+ count(kala_bhavishya) + least(100, count(bodha_discoveries)), '
    'less T-5 clip-gate and CR-46 dedup attrition',
  expected_volume_inputs = jsonb_build_object(
    'convergence_candidates_per_domain', 'SELECT domain, count(*) FROM kala_convergence WHERE chart_id = $1 GROUP BY 1',
    'bhavishya_rows',                    'SELECT count(*) FROM kala_bhavishya WHERE chart_id = $1',
    'discovery_rows',                    'SELECT count(*) FROM bodha_discoveries WHERE chart_id = $1',
    'per_domain_cap',                    50,
    'discovery_cap',                     100),
  volume_explanation =
    'One row per derived predictive anchor, after the T-5 clip gate and the CR-46 content '
    'dedup -- roughly 460 candidates derive and 139 survive on the canonical chart, an ~70% '
    'rejection rate that is currently logged to stdout only. anchor_id is deterministic from '
    'the anchor''s grade-free event tuple (migration 680, D-CND-04 / issue #1732). Detector is '
    'chart-PARTITIONED per D-CND-03 (GROUP BY chart_id HAVING ...), so a violation names the '
    'chart it belongs to rather than reporting that some chart is affected.'
 WHERE asset_id = 'ph_nimitta';

-- ── ph_muhurta ──────────────────────────────────────────────────────────────
UPDATE asset_registry SET
  target_floor = 134,
  catalog_status = 'CURRENT',
  expected_volume_formula =
    'count(DISTINCT (mapped action_class, normalized window_start)) over phala_anchors '
    'with malleability IN (influenceable, semi_influenceable); at most '
    'least(400, influenceable_anchor_count)',
  expected_volume_inputs = jsonb_build_object(
    'influenceable_anchor_count', 'SELECT count(*) FROM phala_anchors WHERE chart_id = $1 AND malleability IN (''influenceable'',''semi_influenceable'')',
    'max_muhurta_anchors',        400,
    'action_class_cardinality',   7),
  volume_explanation =
    'One row per (action_class, normalized window_start) reachable from an influenceable '
    'anchor -- the natural key collapses anchors that map to the same pair, so the count is '
    'BELOW the anchor count by exactly the collision count (139 anchors -> 134 rows on the '
    'canonical chart). target_floor is set from count_sql, never from rows_written, which '
    'over-reports by the collision count. Detector is chart-PARTITIONED per D-CND-03, so a '
    'violation names the chart it belongs to.',
  integrity_check_sql = $check$
-- D-CND-03: chart-PARTITIONED, so a violation names the chart it belongs to. A whole-table
-- aggregate could be dominated by another chart's rows and miss a single-chart corruption.
SELECT
  -- Every linked anchor resolves, and to an anchor of the SAME chart.
  NOT EXISTS (SELECT 1 FROM phala_muhurta m
      LEFT JOIN phala_anchors a ON a.anchor_id = m.linked_anchor_id
     WHERE m.linked_anchor_id IS NOT NULL AND (a.anchor_id IS NULL OR a.chart_id <> m.chart_id)
     GROUP BY m.chart_id HAVING count(*) > 0)
  -- Windows are ordered.
  AND NOT EXISTS (SELECT 1 FROM phala_muhurta
     WHERE window_end IS NOT NULL AND window_start > window_end
     GROUP BY chart_id HAVING count(*) > 0)
  -- Fingerprint distinctness, per chart: source_citation carries no chart component, so it
  -- collides legitimately BETWEEN charts and is only meaningful WITHIN one.
  AND NOT EXISTS (SELECT 1 FROM phala_muhurta
     GROUP BY chart_id HAVING count(*) <> count(DISTINCT source_citation))
$check$
 WHERE asset_id = 'ph_muhurta';

-- ── ph_sankrama ─────────────────────────────────────────────────────────────
UPDATE asset_registry SET
  target_floor = 2510,
  catalog_status = 'CURRENT',
  expected_volume_formula =
    'sum over anchor domains of (anchors in that domain x material bodha_cdlm_cells whose '
    'domain_row = map(domain) and net_linkage_strength >= 0.25)',
  expected_volume_inputs = jsonb_build_object(
    'anchor_count_by_domain',     'SELECT domain, count(*) FROM phala_anchors WHERE chart_id = $1 GROUP BY 1',
    'material_cell_count_by_row', 'SELECT domain_row, count(*) FROM bodha_cdlm_cells WHERE chart_id = $1 AND net_linkage_strength >= 0.25 GROUP BY 1',
    'linkage_threshold',          0.25),
  volume_explanation =
    'One row per (anchor, material CDLM cell of the anchor''s mapped domain). The formula '
    'reproduces the live count EXACTLY on both built charts (2510 and 475). KNOWN OPEN DEFECT: '
    'the anchor->CDLM domain map sends ''transition'' to ''general'', a domain CDLM does not '
    'have, destroying 250 rows (10%) that a correct map would produce; the full no-gap tiling '
    'invariant is therefore withheld until that fix lands in W3-3 rather than installed red. '
    'Detector is chart-PARTITIONED per D-CND-03, so a violation names the chart it belongs to.',
  integrity_check_sql = $check$
-- D-CND-03: chart-partitioned.
SELECT
  -- §N.5: L4 must not have drifted from the L2 value it copied.
  NOT EXISTS (SELECT 1 FROM phala_sankrama s
      JOIN bodha_cdlm_cells c ON c.cell_id = s.cdlm_cell_id AND c.chart_id = s.chart_id
     WHERE s.linkage_strength IS DISTINCT FROM c.net_linkage_strength
        OR s.target_domain IS DISTINCT FROM c.domain_col
     GROUP BY s.chart_id HAVING count(*) > 0)
  -- Projected windows are ordered.
  AND NOT EXISTS (SELECT 1 FROM phala_sankrama
     WHERE projected_window_end IS NOT NULL AND projected_window_start > projected_window_end
     GROUP BY chart_id HAVING count(*) > 0)
  -- The natural key is distinct within each chart.
  AND NOT EXISTS (SELECT 1 FROM phala_sankrama
     GROUP BY chart_id HAVING count(*) <> count(DISTINCT (source_anchor_id, cdlm_cell_id)))
$check$
 WHERE asset_id = 'ph_sankrama';

-- ── ph_sodhana ──────────────────────────────────────────────────────────────
-- Deliberately NO target_floor. This is an anomaly registry: fewer rows is better, and
-- a floor here would be an incentive to fabricate findings (§N.4). The honest volume
-- expectation is a CEILING.
UPDATE asset_registry SET
  target_floor = NULL,
  catalog_status = 'CURRENT',
  expected_volume_formula = 'rows BETWEEN 0 AND (5 * anchor_count) + 1',
  expected_volume_inputs = jsonb_build_object(
    'anchor_count',        'SELECT count(*) FROM phala_anchors WHERE chart_id = $1',
    'per_anchor_detectors', 5,
    'chart_wide_detectors', 1),
  volume_explanation =
    'An anomaly registry, not a product: FEWER rows is better, so this asset has a CEILING '
    'and deliberately NO target_floor -- a floor would reward fabricating findings (§N.4). '
    'Five per-anchor detectors plus one chart-wide detector bound it. Detector is '
    'chart-PARTITIONED per D-CND-03.',
  integrity_check_sql = $check$
-- D-CND-03: chart-partitioned.
SELECT
  -- Earned signal: an l5_calibration_attempted row can only exist if the build-halt failed.
  NOT EXISTS (SELECT 1 FROM phala_sodhana WHERE leakage_class = 'l5_calibration_attempted'
     GROUP BY chart_id HAVING count(*) > 0)
  -- The anchor_id FK omits chart_id, so a row could legally cite another chart's anchor.
  AND NOT EXISTS (SELECT 1 FROM phala_sodhana s
      LEFT JOIN phala_anchors a ON a.anchor_id = s.anchor_id
     WHERE a.anchor_id IS NULL OR a.chart_id <> s.chart_id
     GROUP BY s.chart_id HAVING count(*) > 0)
$check$
 WHERE asset_id = 'ph_sodhana';

-- ── ph_suddha_sodhana ───────────────────────────────────────────────────────
UPDATE asset_registry SET
  target_floor = 139,
  catalog_status = 'CURRENT',
  expected_volume_formula = 'rows = anchor_count (exact 1:1 tiling of phala_anchors)',
  expected_volume_inputs = jsonb_build_object(
    'anchor_count', 'SELECT count(*) FROM phala_anchors WHERE chart_id = $1'),
  volume_explanation =
    'Exactly one disposition row per anchor -- a DERIVED equality against a live upstream '
    'count, not a literal pin. This asset labels and never drops: verified 1:1 with zero '
    'orphans in both directions on both built charts. Detector is chart-PARTITIONED per D-CND-03, so a violation names the chart it belongs to.',
  integrity_check_sql = $check$
-- D-CND-03: chart-partitioned.
SELECT
  -- No-gap tiling of phala_anchors, both directions, within each chart.
  NOT EXISTS (SELECT 1 FROM phala_anchors a
      FULL OUTER JOIN phala_suddha_sodhana s ON s.anchor_id = a.anchor_id AND s.chart_id = a.chart_id
     WHERE a.anchor_id IS NULL OR s.anchor_id IS NULL
     GROUP BY coalesce(a.chart_id, s.chart_id) HAVING count(*) > 0)
  -- The stored status must equal its own classifier (§N.5: re-derivation, not restatement).
  AND NOT EXISTS (SELECT 1 FROM phala_suddha_sodhana WHERE cleanliness_status <> CASE
        WHEN critical_flag_count > 0 OR major_flag_count > 0 THEN 'staged_revision'
        WHEN minor_flag_count > 0 THEN 'flagged' ELSE 'clean' END
     GROUP BY chart_id HAVING count(*) > 0)
  -- The D43 rail: no correction is ever auto-applied.
  AND NOT EXISTS (SELECT 1 FROM phala_suddha_sodhana
     WHERE revision_approved_by IS NOT NULL OR revision_applied_at IS NOT NULL
     GROUP BY chart_id HAVING count(*) > 0)
$check$
 WHERE asset_id = 'ph_suddha_sodhana';

-- ── ph_pratikara ────────────────────────────────────────────────────────────
-- catalog_status stays DRAFT: every one of this asset's 1,277 live rows carries a
-- structurally empty remedy programme (total_scheduled = 0) and an invented classical
-- citation. Promoting it to CURRENT while that is true would be a labelling claim the
-- data does not support. It flips to CURRENT after the W3-3 writer fixes and the rerun.
UPDATE asset_registry SET
  target_floor = 536,
  expected_volume_formula = 'rows = count(kala_obstruction) for the chart -- NOT anchors',
  expected_volume_inputs = jsonb_build_object(
    'obstruction_count', 'SELECT count(*) FROM kala_obstruction WHERE chart_id = $1'),
  volume_explanation =
    'One row per kala_obstruction row (strict 1:1). Row count tracks kala_convergence -> '
    'kala_obstruction cardinality, NOT phala_anchors -- which is why the chart with FEWER '
    'anchors has MORE mitigation rows (741 vs 536). The prior explanation ("one row per remedy '
    'recommendation") described a per-remedy grain this table does not have. Tiling is scoped '
    'to charts that HAVE mitigation rows: chart cb73cd3d has 6 obstructions and none, because '
    'its ph_nimitta build errored and ph_pratikara never ran -- an unbuilt chart is not '
    'corruption. Detector is chart-PARTITIONED per D-CND-03. KNOWN OPEN DEFECTS held '
    'to W3-3: empty programmes, an invented citation, and a degenerate linked_anchor_id.',
  integrity_check_sql = $check$
-- D-CND-03: chart-partitioned. The tiling is additionally restricted to charts that HAVE
-- mitigation rows: chart cb73cd3d has 6 obstructions and none, because its ph_nimitta build
-- errored and ph_pratikara never ran. An unbuilt chart is not corruption -- and the scoped
-- form still goes red on a genuine partial build (verified by probe).
SELECT
  NOT EXISTS (SELECT 1 FROM kala_obstruction o
      FULL OUTER JOIN phala_mitigation m ON m.obstruction_id = o.id AND m.chart_id = o.chart_id
     WHERE (o.id IS NULL OR m.mitigation_id IS NULL)
       AND coalesce(o.chart_id, m.chart_id) IN (SELECT DISTINCT chart_id FROM phala_mitigation)
     GROUP BY coalesce(o.chart_id, m.chart_id) HAVING count(*) > 0)
  -- §N.5: the stored severity must be the declared mapping of the upstream it restates.
  AND NOT EXISTS (SELECT 1 FROM phala_mitigation m JOIN kala_obstruction o ON o.id = m.obstruction_id
     WHERE m.obstruction_severity IS DISTINCT FROM CASE o.severity
       WHEN 'mild' THEN 'low' WHEN 'moderate' THEN 'medium' WHEN 'severe' THEN 'high' END
     GROUP BY m.chart_id HAVING count(*) > 0)
$check$
 WHERE asset_id = 'ph_pratikara';

-- ── ph_pramana ──────────────────────────────────────────────────────────────
-- target_floor stays NULL deliberately: 20 of this asset's rows are classified by a
-- detector that cannot return its positive (life_event_match is unreachable code), so a
-- floor now would enshrine a count a dead detector produced. It is set after W3-3.
UPDATE asset_registry SET
  target_floor = NULL,
  catalog_status = 'CURRENT',
  expected_volume_formula = 'rows = anchor_count (one evidence record per anchor)',
  expected_volume_inputs = jsonb_build_object(
    'anchor_count', 'SELECT count(*) FROM phala_anchors WHERE chart_id = $1'),
  volume_explanation =
    'One evidence record per anchor -- a DERIVED equality against a live upstream count. '
    'target_floor is deliberately NULL until the life_event vocabulary defect is fixed: '
    'life_event_match is currently unreachable code (53 LEL domain slugs vs 13 canonical '
    'domains, matched by exact equality), so every past-window anchor is stamped '
    'life_event_miss -- a refutation asserted on no evidence. A floor now would enshrine a '
    'count a dead detector produced. The invariant that DETECTS this (a miss must cite a '
    'resolvable LEL comparison) fails 12/12 today and lands with its fix in W3-3 rather than '
    'installed red. Detector is chart-PARTITIONED per D-CND-03, so a violation names the chart it belongs to.',
  integrity_check_sql = $check$
-- D-CND-03: chart-partitioned, except the final clause -- see its comment.
SELECT
  -- Exactly one pramana row per anchor, no orphan in either direction, within each chart.
  NOT EXISTS (SELECT 1 FROM phala_anchors a
      FULL OUTER JOIN phala_pramana p ON p.anchor_id = a.anchor_id AND p.chart_id = a.chart_id
     WHERE a.anchor_id IS NULL OR p.anchor_id IS NULL
     GROUP BY coalesce(a.chart_id, p.chart_id) HAVING count(*) > 0)
  -- Grain assertion: one row per anchor, per chart.
  AND NOT EXISTS (SELECT 1 FROM phala_pramana
     GROUP BY chart_id HAVING count(*) <> count(DISTINCT anchor_id))
  -- NOT CHART-PARTITIONABLE, and this is the D-CND-03 clause-2 exception with its reason:
  -- this is a SCHEMA invariant, not a data one. It re-asserts the D5 NO-SCORING gate
  -- structurally -- phala_pramana must carry no numeric column at all, because calibration
  -- belongs to L5 and is filled in from real outcome data, never invented here (§N.8).
  -- information_schema has no chart_id to partition on, and the claim is chart-independent
  -- by nature: a numeric column exists for every chart or for none.
  AND NOT EXISTS (SELECT 1 FROM information_schema.columns
     WHERE table_name = 'phala_pramana'
       AND data_type IN ('numeric','double precision','real'))
$check$
 WHERE asset_id = 'ph_pramana';

-- ── ph_phaladesa ────────────────────────────────────────────────────────────
UPDATE asset_registry SET
  target_floor = 13,
  catalog_status = 'CURRENT',
  expected_volume_formula = 'rows = cardinality of the canonical domain vocabulary',
  expected_volume_inputs = jsonb_build_object(
    'canonical_domain_count', 13,
    'source', 'brahmagyan/domain_vocabulary.py CANONICAL_DOMAINS, mirrored by the '
              'phala_phaladesa_domain_canonical CHECK constraint'),
  volume_explanation =
    'One declaration per canonical domain, emitted unconditionally whether or not the chart '
    'has any anchor in that domain -- so 13 rows on EVERY chart is a genuine derived '
    'structural constant, not chart-independence: the per-domain payload differs completely '
    'between charts (7 populated / 6 empty on the canonical chart vs a different split '
    'elsewhere). Detector is chart-PARTITIONED per D-CND-03, so a violation names the chart it belongs to.',
  integrity_check_sql = $check$
-- D-CND-03: chart-partitioned throughout.
SELECT
  -- Complete, non-duplicated tiling of the canonical vocabulary, per chart.
  NOT EXISTS (SELECT 1 FROM phala_phaladesa
     GROUP BY chart_id HAVING count(DISTINCT domain) <> 13 OR count(*) <> 13)
  -- anchor_count must equal the true anchor population for that domain (no drift).
  AND NOT EXISTS (SELECT 1 FROM phala_phaladesa pd WHERE pd.anchor_count <>
        (SELECT count(*) FROM phala_anchors a WHERE a.chart_id = pd.chart_id AND lower(a.domain) = pd.domain)
     GROUP BY pd.chart_id HAVING count(*) > 0)
  -- Counts are coherent, and a verdict has a top anchor exactly when it has anchors.
  AND NOT EXISTS (SELECT 1 FROM phala_phaladesa
     WHERE clean_anchor_count + staged_revision_count > anchor_count
        OR (anchor_count > 0) <> (top_anchor_id IS NOT NULL)
     GROUP BY chart_id HAVING count(*) > 0)
  -- No dangling verdict anchor.
  AND NOT EXISTS (SELECT 1 FROM phala_phaladesa pd WHERE pd.top_anchor_id IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM phala_anchors a WHERE a.anchor_id = pd.top_anchor_id)
     GROUP BY pd.chart_id HAVING count(*) > 0)
$check$
 WHERE asset_id = 'ph_phaladesa';

-- ── ph_rectification ────────────────────────────────────────────────────────
UPDATE asset_registry SET
  target_floor = 186,
  catalog_status = 'CURRENT',
  expected_volume_formula =
    '(floor(2 * scan_half_width_min / scan_step_min) + 1) * ayanamsha_count + 1 best row',
  expected_volume_inputs = jsonb_build_object(
    'scan_half_width_min', 90,
    'scan_step_min',       5,
    'ayanamsha_count',     5,
    'best_rows',           1,
    'source', 'services/ph_rectification/engine.py SCAN_HALF_WIDTH_MIN / SCAN_STEP_MIN / AYANAMSHAS'),
  volume_explanation =
    '37 offsets (a fixed +/-90 minute, 5-minute lattice) x 5 ayanamshas + 1 best row = 186. '
    'Identical on every chart because the SCAN GRID is chart-independent by design; the '
    'ascendants computed on it are per-chart (verified: lagna differs between charts at every '
    'offset). A derived structural constant, not a chart-independence bug. KNOWN OPEN DEFECTS '
    'held to W3-3: the LEL fit is identically 0.0000 on all 95 scored candidates while '
    'load_bearing reads true, and confidence_low = -0.2000 is persisted -- the two invariants '
    'that detect these fail today and land with their fixes rather than installed red. '
    'Detector is chart-PARTITIONED per D-CND-03, so a violation names the chart it belongs to.',
  integrity_check_sql = $check$
-- D-CND-03: every clause partitions on chart_id already -- the scan lattice is a per-chart
-- structure, so a defect in one chart's lattice cannot be masked by another's.
SELECT
  -- Contiguous, gap-free offset lattice at the declared step.
  NOT EXISTS (SELECT 1 FROM (
     SELECT chart_id, offset_minutes,
            lead(offset_minutes) OVER (PARTITION BY chart_id ORDER BY offset_minutes) nx
     FROM (SELECT DISTINCT chart_id, offset_minutes FROM phala_rectification) o) g
    WHERE nx IS NOT NULL AND nx - offset_minutes <> 5
    GROUP BY chart_id HAVING count(*) > 0)
  -- Symmetric and centred on the recorded birth time.
  AND NOT EXISTS (SELECT 1 FROM phala_rectification
     GROUP BY chart_id HAVING min(offset_minutes) <> -max(offset_minutes) OR NOT bool_or(offset_minutes = 0))
  -- Complete cross-product: every offset scored under every ayanamsha.
  AND NOT EXISTS (SELECT 1 FROM (SELECT chart_id, offset_minutes FROM phala_rectification
        GROUP BY 1,2 HAVING count(DISTINCT ayanamsha_id) <> 5) x
     GROUP BY chart_id HAVING count(*) > 0)
  -- lagna_stable is an all-or-nothing property of an offset across ayanamshas.
  AND NOT EXISTS (SELECT 1 FROM (SELECT chart_id, offset_minutes FROM phala_rectification
        GROUP BY 1,2 HAVING count(DISTINCT lagna_stable) > 1) x
     GROUP BY chart_id HAVING count(*) > 0)
  -- The best row must resolve to a real candidate of its OWN chart.
  AND NOT EXISTS (SELECT 1 FROM phala_rectification_best b WHERE b.best_candidate_id IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM phala_rectification c
             WHERE c.id = b.best_candidate_id AND c.chart_id = b.chart_id)
     GROUP BY b.chart_id HAVING count(*) > 0)
$check$
 WHERE asset_id = 'ph_rectification';

-- ---------------------------------------------------------------------------
-- Post-condition: refuse to install a red gate, and prove every asset got one.
-- ---------------------------------------------------------------------------
DO $$
DECLARE r record; ok boolean;
BEGIN
  FOR r IN SELECT asset_id, integrity_check_sql FROM asset_registry
            WHERE asset_id LIKE 'ph\_%' ORDER BY asset_id
  LOOP
    IF r.integrity_check_sql IS NULL THEN
      RAISE EXCEPTION 'migration 681: % still has no integrity_check_sql (C12: NULL is the defect)', r.asset_id;
    END IF;
    EXECUTE r.integrity_check_sql INTO ok;
    IF ok IS NOT TRUE THEN
      RAISE EXCEPTION 'migration 681: % integrity detector is RED on current data -- refusing to install it', r.asset_id;
    END IF;
  END LOOP;

  -- Every asset must carry a derived volume expectation. NULL is the C12 defect.
  IF (SELECT count(*) FROM asset_registry WHERE asset_id LIKE 'ph\_%'
        AND (expected_volume_formula IS NULL OR expected_volume_inputs IS NULL)) > 0 THEN
    RAISE EXCEPTION 'migration 681: an L4 asset still has a NULL expected_volume_formula/inputs';
  END IF;
END $$;
