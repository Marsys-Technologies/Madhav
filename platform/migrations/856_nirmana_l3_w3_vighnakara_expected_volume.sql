-- 856_nirmana_l3_w3_vighnakara_expected_volume.sql
--
-- NIRMĀṆA L3 Kāla — W3. Closes F-L3-4 for `ka_vighnakara`: `expected_volume_formula`,
-- `expected_volume_inputs` and `volume_explanation` were all NULL, leaving the already-correct
-- `target_floor` (536, an achieved-count floor per §N.4, unchanged by this migration) an
-- undocumented constant rather than a derived, auditable figure (C12: "derive, never pick").
--
-- No self-transaction wrapper (transaction ownership belongs to platform/scripts/migrate.ts,
-- matching migration 670/850/852/853/854/855's convention for this range).
--
-- `ka_vighnakara` (the obstruction/counter-indicator detector,
-- pipeline/orchestrator/writers/ka_vighnakara.py) is NOT a flat-count asset and is more layered
-- than migrations 852/853/855's single-source horizon scans. Derived here from the writer's own
-- `run()` method directly, not guessed:
--
--   ANCHOR DATES scanned come from TWO sources, deduplicated:
--     (a) `kala_convergence` rows for this chart with `peak_date IS NOT NULL`, ordered by
--         `convergence_score DESC`, capped at the TOP 500 (writer.py:170-178, `LIMIT 500`) --
--         NOT every convergence window, only the top-500-scored ones. This chart has 14,868 such
--         rows total (matches `ka_sangam`'s own target_floor), so the writer scans well under 4%
--         of them by design.
--     (b) up to `_MAX_DASHA_ANCHORS = 200` additional dasha-timeline (MD/AD midpoint) dates, a
--         separate coverage source layered on top of (a).
--
--   Each anchor is run through `_detect_all()` (writer.py:475-508), which tries 4 CURRENTLY
--   IMPLEMENTED detectors independently per anchor -- `malefic_transit`, `panchanga_obstruction`,
--   `gandanta`, `combustion` -- each producing AT MOST ONE row per (anchor, detector) pair, only
--   when that detector's own live-computed condition is actually met (an anchor with no hit
--   produces nothing for that detector, not a null-valued row). A 5th detector,
--   `papakartari`, is implemented but found zero matches for this native across every scanned
--   anchor -- an honest zero, not a missing branch. Two further `obstruction_type` values
--   (`dasha_lord_afflicted`, `rashi_dristi_conflict`) are declared in the table's own CHECK
--   constraint but are explicitly RESERVED FOR FUTURE DETECTORS (writer.py:89) -- not yet
--   implemented at all, so they can never appear in a row count today.
--
-- The row count is therefore bounded above by min(500, |convergence windows|) + 200, times up to
-- 4 detector types, but the REAL count is far lower because each detector's condition is only
-- sometimes true -- a chart- and time-dependent quantity, not a closed-form arithmetic identity.
--
-- Live-measured for the canonical chart (482012f1-710e-4a25-994a-93821f5871aa), re-verified this
-- cycle via `count(*) FROM kala_obstruction WHERE chart_id=... GROUP BY obstruction_type`:
--   malefic_transit          358
--   combustion               123
--   gandanta                  38
--   panchanga_obstruction     17
--   -----------------------------
--   TOTAL                    536   (matches target_floor and count_sql exactly)
--
-- Per migration 690/852/853/854/855's own recorded practice: this formula is intentionally
-- prose+structured-inputs, not a `COUNT()`/`ACTUAL()`/arithmetic literal the seed's
-- `validateFormulas` parser accepts, because the real computation depends on which of up to ~700
-- scanned anchors actually trip each of 4 independently-gated, chart- and time-dependent
-- detectors. This migration does not touch the seed; the row is DB-authoritative and
-- seed-divergent in the same documented, already-flagged way migration 690's six rows (and
-- migrations 852/853/854/855's one row each) are.

UPDATE asset_registry
   SET expected_volume_formula = 'SUM_OVER_ANCHORS_AND_DETECTORS(obstruction_hits), not a flat count',
       expected_volume_inputs = jsonb_build_object(
         'kind', 'anchor_and_detector_gated_count',
         'chart_scoped', true,
         'anchor_sources', jsonb_build_object(
           'convergence_windows', jsonb_build_object(
             'source', 'kala_convergence WHERE chart_id=$chart AND peak_date IS NOT NULL, ORDER BY convergence_score DESC',
             'cap', 500,
             'live_total_available_2026_09_07', 14868,
             'note', 'top-500-scored only, not every convergence window'
           ),
           'dasha_timeline', jsonb_build_object(
             'source', 'dasha MD/AD midpoint anchors',
             'cap', 200,
             'note', 'a separate coverage source layered on top of the convergence anchors, deduplicated'
           )
         ),
         'detectors', jsonb_build_object(
           'implemented_and_active_for_this_chart', jsonb_build_array('malefic_transit', 'panchanga_obstruction', 'gandanta', 'combustion'),
           'implemented_but_zero_hits_this_chart', jsonb_build_array('papakartari'),
           'reserved_not_yet_implemented', jsonb_build_array('dasha_lord_afflicted', 'rashi_dristi_conflict')
         ),
         'per_row', 'one row per (anchor_date, detector_type) where that detector''s own live-computed condition is met, at most 1 row per detector per anchor, never a null-valued placeholder',
         'derivation', 'derived from pipeline/orchestrator/writers/ka_vighnakara.py directly, not guessed, and not reducible to one closed-form arithmetic expression because it depends on which of up to ~700 scanned anchors trip each of 4 independently-gated, chart- and time-dependent detectors',
         'observed_2026_09_07', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', jsonb_build_object(
             'malefic_transit', 358, 'combustion', 123, 'gandanta', 38, 'panchanga_obstruction', 17, 'total', 536
           )
         ),
         'supersedes', 'NULL (F-L3-4)'
       ),
       volume_explanation = 'Not a flat count: one row per (anchor_date, detector_type), where anchors are the top-500-scored kala_convergence windows plus up to 200 dasha-timeline anchors, and each of 4 currently-active detectors (malefic_transit, panchanga_obstruction, gandanta, combustion) independently checks its own live-computed condition at that anchor. A fifth detector (papakartari) is implemented but found zero matches for this native, and two further obstruction_type values are reserved for detectors not yet built. 536 is the live-measured count for the canonical chart, matching target_floor and count_sql exactly, not an invented figure.'
 WHERE asset_id = 'ka_vighnakara'
   AND expected_volume_formula IS NULL;
