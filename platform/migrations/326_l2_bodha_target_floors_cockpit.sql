-- 326_l2_bodha_target_floors_cockpit.sql
-- =============================================================================
-- L2 Bodha — cockpit reconcile: set target_floor = ACHIEVED count + correct
-- count_sql (summed across each asset's tables) for all 9 bo_* assets, and
-- register the 3 NEW assets (bo_drishti, bo_anveshana, bo_pramana_mapa) if the
-- seed didn't already add them. Floors are ASPIRATIONAL = achieved-after-build
-- ([[feedback-floors-are-aspirational-not-gates]]) — set to the SEALED counts
-- from L2_BODHA_CLOSE_v1_1.md §asset-manifest. Chart-scoped count_sql per the
-- native count_sql=SUM-across-tables rule.
--
-- Source of the achieved counts: L2_BODHA_CLOSE (build a712b250 / 482012f1):
--   bo_laksana=66,738 · bo_sangati=84 (70 cells+14 conv+0 contra) · bo_karanajala≥300
--   · bo_bimba=140 · bo_samvada=5 (gestalt) · bo_upaya=180 (45 res+135 presc)
--   · bo_samskara=66,738 · bo_drishti=60 · bo_anveshana=5,770 (1,411+4,359)
--   · bo_pramana_mapa=1.  Layer ~139,531 rows (excl. MVs).
--
-- NOTE (chart-scoped): the cockpit count is per-chart for the native; count_sql
-- filters chart_id. target_floor is the achieved per-chart count.
-- PREREQ: migrations through 325 applied. Number is 326 (> current max 325).
-- =============================================================================

BEGIN;

-- ── bo_laksana — bodha_msr_signals ──────────────────────────────────────────
UPDATE asset_registry SET
  target_floor = 66738,
  count_sql    = 'SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1'
WHERE asset_id = 'bo_laksana';

-- ── bo_sangati — CDLM (cells + convergence + contradictions) ─────────────────
UPDATE asset_registry SET
  target_floor = 84,
  count_sql    = 'SELECT (SELECT count(*) FROM bodha_cdlm_cells WHERE chart_id = $1)
                       + (SELECT count(*) FROM bodha_convergence WHERE chart_id = $1)
                       + (SELECT count(*) FROM bodha_contradictions WHERE chart_id = $1) AS count'
WHERE asset_id = 'bo_sangati';

-- ── bo_karanajala — CGM edges (+ sub_graphs/motifs/topology/paths) ───────────
UPDATE asset_registry SET
  target_floor = 300,
  count_sql    = 'SELECT (SELECT count(*) FROM bodha_cgm_edges WHERE chart_id = $1)
                       + (SELECT count(*) FROM bodha_cgm_paths WHERE chart_id = $1) AS count'
WHERE asset_id = 'bo_karanajala';

-- ── bo_bimba — CGM nodes ─────────────────────────────────────────────────────
UPDATE asset_registry SET
  target_floor = 140,
  count_sql    = 'SELECT count(*) FROM bodha_cgm_nodes WHERE chart_id = $1'
WHERE asset_id = 'bo_bimba';

-- ── bo_samskara — embeddings (1:1 with MSR) ──────────────────────────────────
UPDATE asset_registry SET
  target_floor = 66738,
  count_sql    = 'SELECT count(*) FROM bodha_signal_embeddings WHERE chart_id = $1'
WHERE asset_id = 'bo_samskara';

-- ── bo_samvada — UCD gestalt (thin writer; view is derived) ──────────────────
UPDATE asset_registry SET
  target_floor = 5,
  count_sql    = 'SELECT count(*) FROM bodha_chart_gestalt WHERE chart_id = $1'
WHERE asset_id = 'bo_samvada';

-- ── bo_upaya — RM (resonances + prescriptions; owns resonances per seed fix) ──
UPDATE asset_registry SET
  target_floor = 180,
  count_sql    = 'SELECT (SELECT count(*) FROM bodha_rm_resonances WHERE chart_id = $1)
                       + (SELECT count(*) FROM bodha_rm_remedy_prescriptions WHERE chart_id = $1) AS count'
WHERE asset_id = 'bo_upaya';

-- ── bo_drishti — question lenses (NEW asset; register if absent) ──────────────
-- INSERT supplies all NOT NULL cols (PG validates before ON CONFLICT check);
-- DO UPDATE SET is the live path since migration 325 already seeded this row.
INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name,
                            english_description, storage_type, scope,
                            target_table, count_sql, target_floor, depends_on, catalog_status)
VALUES ('bo_drishti', 'bodha', 9, 'Dṛṣṭi', 'Question Lenses',
        'Question-lens table: template + wildcard graph-sweep + ranks-never-caps, per question domain.',
        'postgres_table', 'per_chart',
        'bodha_question_lenses',
        'SELECT count(*) FROM bodha_question_lenses WHERE chart_id = $1',
        60, ARRAY['bo_laksana','bo_sangati','bo_karanajala'], 'CURRENT')
ON CONFLICT (asset_id) DO UPDATE SET
  target_floor = 60,
  count_sql    = 'SELECT count(*) FROM bodha_question_lenses WHERE chart_id = $1',
  catalog_status = 'CURRENT';

-- ── bo_anveshana — discovery (discoveries + anomalies; NEW asset) ─────────────
INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name,
                            english_description, storage_type, scope,
                            target_table, count_sql, target_floor, depends_on, catalog_status)
VALUES ('bo_anveshana', 'bodha', 10, 'Anveṣaṇa', 'Discovery Engine',
        'Discovery engine: non-obviousness + graph-mining + embedding outliers + bodha_discoveries + anomalies.',
        'postgres_table', 'per_chart',
        'bodha_discoveries',
        'SELECT (SELECT count(*) FROM bodha_discoveries WHERE chart_id = $1)
              + (SELECT count(*) FROM bodha_anomalies WHERE chart_id = $1) AS count',
        5770, ARRAY['bo_sangati','bo_karanajala','bo_samskara','bo_drishti'], 'CURRENT')
ON CONFLICT (asset_id) DO UPDATE SET
  target_floor = 5770,
  count_sql    = 'SELECT (SELECT count(*) FROM bodha_discoveries WHERE chart_id = $1)
                       + (SELECT count(*) FROM bodha_anomalies WHERE chart_id = $1) AS count',
  catalog_status = 'CURRENT';

-- ── bo_pramana_mapa — scorecard (global; NEW asset; per-chart row) ───────────
INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name,
                            english_description, storage_type, scope,
                            target_table, count_sql, target_floor, depends_on, catalog_status)
VALUES ('bo_pramana_mapa', 'bodha', 8, 'Pramāṇa-māpā', 'Synthesis Scorecard',
        'Per-build synthesis quality scorecard — citation density, whole-chart coverage, derivation compliance, layer separation score; keyed by (chart_id, build_id)',
        'postgres_table', 'per_chart',
        'synthesis_quality_scorecard',
        'SELECT count(*) FROM synthesis_quality_scorecard WHERE chart_id = $1',
        1, ARRAY['bo_upaya','bo_drishti','bo_anveshana'], 'CURRENT')
ON CONFLICT (asset_id) DO UPDATE SET
  target_floor = 1,
  count_sql    = 'SELECT count(*) FROM synthesis_quality_scorecard WHERE chart_id = $1',
  catalog_status = 'CURRENT';

COMMIT;

-- VERIFY (run after apply):
--   SELECT asset_id, target_floor, count_sql FROM asset_registry WHERE layer='bodha' ORDER BY asset_id;
--   -- all 9 bo_* present, target_floor = achieved, count_sql chart-scoped.
-- NOTE: column names (english_name/sanskrit_name/scope/depends_on/catalog_status) must match the
--   live asset_registry schema — if the live INSERT column set differs, adapt to the actual columns
--   (the UPDATEs are schema-safe; only the 3 INSERTs touch the full column set). Confirm vs the seed.
