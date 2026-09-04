-- 650_nirmana_l1_w3_registry_truth.sql
--
-- NIRMĀṆA L1-W3 IMPLEMENT — registry truth for the Gaṇita layer.
-- Decisions: 00_ARCHITECTURE/briefs/nirmana/sessions/L1_W2_DECIDE_v1_0.md §3.
-- Evidence:  L1_W1_ANALYSIS_BATCH_A..E.md (findings cited per statement).
--
-- Every value below was MEASURED live across all three built charts
-- (1c826d5a, 482012f1, cb73cd3d) on 2026-09-05, not inferred. Nothing here
-- changes a writer, a schema, or a row of chart data; this migration only makes
-- the registry describe what the writers already do.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- SCOPE NOTE (§N.4, "floors are achieved counts, set AFTER the build"): a floor
-- is corrected here only where the routed change CANNOT REDUCE the count, so
-- that the value remains a valid lower bound after the W3 writer fixes land.
--   * The 11 `rebuild_only` assets qualify trivially -- their output does not change.
--   * ga_dashas is routed `changed`, and its floor IS corrected: both its fixes
--     (the two failing scope-cap sentinels, and the dignity-vocabulary
--     normalisation) can only ADD rows or leave the count unchanged, so
--     471,767 stays a true lower bound. Correcting it now matters because the
--     existing 536,471 actively invites someone to "close the gap" by restoring
--     exactly the fabricated Kalachakra repetition PR #527 removed.
--   * ga_vargas, ga_condition, ga_tajaka, ga_transit_anchors, ga_medical and
--     ga_vastu floors are deliberately LEFT ALONE: their fixes change what is
--     produced (ga_vargas' recovers ~15k suppressed rows), so their floors are
--     set from the achieved count AFTER their W4 build, per §N.4. Setting them
--     now would fabricate a number ahead of the measurement it records.
--
-- depends_on is NOT touched anywhere in this migration. It is immutable for the
-- remainder of the campaign (adjudication #1744: the frozen definition can no
-- longer be superseded, and the dispatcher rejects any live/frozen difference).
-- The DAG corrections L1-W1 found are recorded in the W2 decision document as
-- NEVER-LATER, not silently applied here.

-- ─────────────────────────────────────────────────────────────────────────────
-- PART 1 — count_sql completeness (F-A4, F-B2, F-B12)
--
-- Three assets' count_sql omit fact_categories that the writer WRITES and the
-- serving layer SERVES. The cockpit therefore under-reports the asset (§N.4
-- "cockpit truth": the stats route reads count_sql, so an omission here is
-- invisible everywhere else). Verified live that no other asset's count_sql
-- references any of these four categories, so none of this double-counts.
-- ─────────────────────────────────────────────────────────────────────────────

-- F-A4: ga_positions omits house_chalit (225) and sandhi_flag (90); the writer
-- emits both (ga_positions_writer.py:481,511). Counted 890 -> 1,205.
--
-- This is NOT overturning a prior decision -- it is closing a gap that decision
-- explicitly left open and named. asset_registry_seed.ts, on this very asset,
-- records: "DISCLOSED ADJACENT GAP, deliberately left open because it is
-- outside the Lane-1 scope statement: `house_chalit` and `sandhi_flag`, from
-- the same pass, are still uncounted." L1-W3 is the scope that owns them.
--
-- The same seed comment cautions "Floor NOT raised ... floors are aspirational
-- and are set from a measured build, never from an estimate (§N.4)". That
-- caution is honoured, not ignored: 1,205 is a MEASURED count, identical on all
-- three built charts, not an estimate of what the new categories might add.
UPDATE asset_registry
   SET count_sql = 'SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category IN (''graha_position'', ''graha_sign_attributes'', ''bhava_cusps'', ''house_chalit'', ''sandhi_flag'')'
 WHERE asset_id = 'ga_positions';

-- F-B2: ga_sensitive omits bhava_arudha (210 rows) -- written by the writer AND
-- served by get_karakas.ts, but counted by no asset at all.
UPDATE asset_registry
   SET count_sql = count_sql || ' OR fact_category = ''bhava_arudha'''
 WHERE asset_id = 'ga_sensitive'
   AND count_sql NOT LIKE '%bhava_arudha%';

-- F-B12: ga_sensitive_degree omits sensitive_point_yogi (60 rows) -- written by
-- the writer AND served by get_sensitive_degrees.
UPDATE asset_registry
   SET count_sql = 'SELECT COUNT(*) FROM chart_facts WHERE chart_id = $1 AND fact_category IN (''sensitive_degree_check'', ''sensitive_point_yogi'')'
 WHERE asset_id = 'ga_sensitive_degree';

-- ─────────────────────────────────────────────────────────────────────────────
-- PART 2 — floors set to the MINIMUM achieved count across all built charts
--
-- §N.4: floors are aspirational, not gates, and track achieved counts. A floor
-- must hold for every chart, so the minimum observed is the only honest choice
-- for a per-chart asset -- these counts are legitimately chart-dependent.
--
-- Measured (1c826d5a / 482012f1 / cb73cd3d):
--   ga_positions        890 /   890 /   890  -> 1,205 each with Part 1's count_sql
--   ga_nakshatra      2,858 / 2,847 / 1,813
--   ga_sensitive      8,565 / 8,565 / 8,565  (8,775 with Part 1's + arudha)
--   ga_sensitive_degree 275 /   275 /   275  (335 with Part 1's + yogi)
--   ga_strength      13,621 /13,621 /13,621
--   ga_structural    98,662 /98,542 /98,446
--   ga_yoga              69 /    63 /    80
--   ga_vichara        8,247 / 8,249 / 8,240
--   ga_sade_sati      6,280 / 6,287 / 6,120
--   ga_ayurdaya         130 /   130 /   130
--   ga_prashna            0 /     0 /     0  (dormant by design -- R-1)
-- ─────────────────────────────────────────────────────────────────────────────

-- F-A5: floor 50 was the retired `ganita_positions` figure, 24x stale.
-- 1,205 = 890 + 315, the Part 1 categories, identical on all three charts.
UPDATE asset_registry SET target_floor = 1205 WHERE asset_id = 'ga_positions';

-- F-B1: NOT a build deficit. Floor 8,610 is an achieved measurement from
-- migration 307 (2026-06-18) taken under a count_sql that no longer exists;
-- nothing re-measures a floor after a count_sql rewrite. With Part 1's
-- bhava_arudha restored the counted set is 8,775, matching rows_written.
UPDATE asset_registry SET target_floor = 8775 WHERE asset_id = 'ga_sensitive';

-- F-B13: floor was 0 -- unfalsifiable, a zero-row build passes. Derived:
-- (5 facets x 9 grahas + neecha_bhanga x 7 non-nodal + 3 chart-level + 12
-- sensitive_point_yogi) x 5 ayanamshas = 335, matching rows_written.
UPDATE asset_registry SET target_floor = 335 WHERE asset_id = 'ga_sensitive_degree';

UPDATE asset_registry SET target_floor = 1813  WHERE asset_id = 'ga_nakshatra';
UPDATE asset_registry SET target_floor = 13621 WHERE asset_id = 'ga_strength';
UPDATE asset_registry SET target_floor = 98446 WHERE asset_id = 'ga_structural';

-- F-D14: -43% ruled as a stale floor achieved by a since-proven-defective
-- writer, NOT a regression. 6,287 = 5 x (240 x 4 + 299) - 8 reconciles exactly;
-- N=4 Saturn cycles derived independently. PR #522's retrograde-shadow dedup
-- plus the pre-birth clip account for the difference. Minimum across charts.
UPDATE asset_registry SET target_floor = 6120 WHERE asset_id = 'ga_sade_sati';

-- F-A9: floor 536,471 encodes ~71k Kalachakra rows that register M-6 / PR #527
-- deliberately REMOVED as fabricated cycle repetition (ga_dashas_writer.py
-- :2769-2772: "not a bug to paper over with fabricated repetition"). The floor
-- is wrong because it records fabricated output. Minimum across the three
-- charts (471,767 / 483,859 / 505,348) -- legitimately chart-dependent, so a
-- single count can only ever be a floor, never an equality.
UPDATE asset_registry SET target_floor = 471767 WHERE asset_id = 'ga_dashas';

-- F-D10 / F-D4 / F-E1: floors unset (0) or long stale on assets with stable
-- achieved output.
UPDATE asset_registry SET target_floor = 8240 WHERE asset_id = 'ga_vichara';
UPDATE asset_registry SET target_floor = 63   WHERE asset_id = 'ga_yoga';
UPDATE asset_registry SET target_floor = 130  WHERE asset_id = 'ga_ayurdaya';

-- ─────────────────────────────────────────────────────────────────────────────
-- PART 3 — target_table where NULL (F-B4, F-D16)
-- Both assets demonstrably write chart_facts; the registry could not answer
-- "where does this asset land?" for either.
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE asset_registry SET target_table = 'chart_facts'
 WHERE asset_id IN ('ga_sensitive', 'ga_sade_sati') AND target_table IS NULL;

-- ─────────────────────────────────────────────────────────────────────────────
-- PART 4 — ga_vichara: DRAFT -> CURRENT (F-D9)
--
-- catalog_status = 'DRAFT' on an asset with 8,249 exactly-reconciling rows,
-- three L2 production consumers, nine live MSR signals citing it, and
-- bo_laksana.py:1031 describing it as "SHIPPED and live". The label was the
-- only thing provisional about it.
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE asset_registry SET catalog_status = 'CURRENT'
 WHERE asset_id = 'ga_vichara' AND catalog_status = 'DRAFT';

-- ─────────────────────────────────────────────────────────────────────────────
-- PART 5 — ga_prashna: record the R-1 dormant disposition (F-E21, F-E23)
--
-- Native ruling R-1: the horary facility stays DORMANT. Nothing here opens it,
-- populates it, or changes a writer. The defect being fixed is that R-1 was
-- nowhere machine-readable: data_disposition was NULL, so a 0-row outcome
-- rendered as 'lit' on two charts and 'stale' on the canonical one, and never
-- as a deliberate dormancy -- indistinguishable from a broken build.
--
-- RETAINED_AS_CAPITAL is the existing vocabulary member that fits: the corpus
-- and writer are kept, deliberately unbuilt, against a possible future go-live.
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE asset_registry
   SET data_disposition = 'RETAINED_AS_CAPITAL',
       volume_explanation =
         'DORMANT BY DESIGN (native ruling R-1, recorded 2026-09-05). ga_prashna and its '
         || 'upstream bg_prashna_rules are a horary (praśna) FACILITY that is deliberately not '
         || 'in service: 0 rows is the CORRECT outcome, not a build failure. The facility is '
         || 'real and reachable -- POST /api/compute/prashna/cast is mounted and has been used '
         || '(2 charts cast 2026-06-18) -- so dormancy is a product decision, not a property of '
         || 'the code. Go-live rehearsal is on the deferred register '
         || '(NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §7.3). Do not "fix" the zero count.'
 WHERE asset_id = 'ga_prashna';

-- ─────────────────────────────────────────────────────────────────────────────
-- PART 6 — provably false expected_volume_formula (F-B3, F-B31, F-E13)
--
-- C12/D-CND-01: a volume expectation must be DERIVED and correct, or absent.
-- A formula that evaluates to a number matching neither the floor nor reality
-- is worse than NULL -- it looks like a derivation while asserting nothing.
-- Each is replaced with the derivation that actually reproduces the live count.
-- ─────────────────────────────────────────────────────────────────────────────

-- F-B3: 'ACTUAL(bg_reference) * AYANAMSHAS' -- bg_reference is live 1,242, so
-- the formula yields 6,210, matching neither the floor (8,610) nor reality.
UPDATE asset_registry
   SET expected_volume_formula = 'ROWS_PER_AYANAMSHA * AYANAMSHAS',
       expected_volume_inputs  = '{"ROWS_PER_AYANAMSHA": 1755, "AYANAMSHAS": 5}'::jsonb,
       volume_explanation =
         '1,755 sensitive-point rows per ayanamsha x 5 ayanamshas = 8,775, matching '
         || 'asset_throughput.rows_written identically on all three built charts. Includes the '
         || '210 bhava_arudha rows restored to count_sql by migration 650 (L1-W1 F-B2).'
 WHERE asset_id = 'ga_sensitive';

-- F-B31: 'AYANAMSHAS' evaluates to 5, against 437 live rows -- provably false.
-- It is NOT replaced with another formula, deliberately. Measured across the
-- three built charts the count is 417 / 437 / 415, and the structure is
-- 67-per-ayanamsha x 5 + 102 INVARIANT only on the canonical chart: the
-- per-ayanamsha figure genuinely varies per chart (eclipse proximity, panchaka
-- and tara/chandra baselines are all chart-specific). A fixed-input formula
-- would therefore be an equality wearing a derivation's name -- the same defect
-- C12/D-126 names one level up. Per C12 the correct instrument for a
-- chart-varying count is a FLOOR, and ga_panchanga has one. The formula is
-- cleared to NULL and the reasoning recorded where the next reader will find it.
UPDATE asset_registry
   SET expected_volume_formula = NULL,
       expected_volume_inputs  = NULL,
       volume_explanation =
         'Chart-dependent by construction: measured 417 / 437 / 415 across the three built '
         || 'charts. On the canonical chart the shape is 67 per-ayanamsha x 5 ayanamshas + 102 '
         || 'INVARIANT = 437, but the per-ayanamsha figure varies with the chart (eclipse '
         || 'proximity, panchaka classification, and the tara/chandra natal baselines are all '
         || 'chart-specific). No fixed-input formula can be correct here, so per C12 the volume '
         || 'assertion is the target_floor, not a derivation. Prior formula ''AYANAMSHAS'' '
         || 'evaluated to 5 against 437 rows and asserted nothing (L1-W1 F-B31).'
 WHERE asset_id = 'ga_panchanga';

-- F-E13: 'GRAHAS * AYANAMSHAS' evaluates to 45; floor and reality are both 40.
-- The adjacent volume_explanation already had it right (8 directions x 5).
UPDATE asset_registry
   SET expected_volume_formula = 'DIRECTIONS * AYANAMSHAS',
       expected_volume_inputs  = '{"DIRECTIONS": 8, "AYANAMSHAS": 5}'::jsonb
 WHERE asset_id = 'ga_vastu';

-- F-B13: derived above; record the derivation as the formula.
UPDATE asset_registry
   SET expected_volume_formula = 'ROWS_PER_AYANAMSHA * AYANAMSHAS',
       expected_volume_inputs  = '{"ROWS_PER_AYANAMSHA": 67, "AYANAMSHAS": 5}'::jsonb
 WHERE asset_id = 'ga_sensitive_degree';
