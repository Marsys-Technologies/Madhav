-- 854_nirmana_l3_w3_gochara_expected_volume.sql
--
-- NIRMĀṆA L3 Kāla — W3. Closes F-L3-4 for `ka_gochara`: `expected_volume_formula`,
-- `expected_volume_inputs` and `volume_explanation` were all NULL, leaving the already-correct
-- `target_floor` (83, an achieved-count floor per §N.4, unchanged by this migration) an
-- undocumented constant rather than a derived, auditable figure (C12: "derive, never pick").
--
-- No self-transaction wrapper (transaction ownership belongs to platform/scripts/migrate.ts,
-- matching migration 670/850/852/853's convention for this range).
--
-- `ka_gochara` (the GOCHARA-2.0/W2G materialization, `services/w2g/materialize.py`) is NOT a
-- flat-count asset. Derived here from the writer itself, not guessed:
--
--   Candidate discovery pulls from the chart-INDEPENDENT contact stream (`bg_gochara_arcs`, built
--   once globally), restricted to Tier A (eager) bodies and to event classes whose
--   `temporal_shape == 'point'` only (`materialize.py` module docstring, §"HONEST SCOPE OF THIS
--   FIRST LANE"). Each candidate is scored against THIS chart's natal targets (from
--   `ka_gochara_resonance`) and active dasha periods via v1's own, unmodified
--   `gochara_intensity.compute_lambda_e`, over a progressive +/-3-year horizon
--   (`PROGRESSIVE_HORIZON_YEARS = 3`, `progressive_horizon()`). A candidate below
--   `compute_lambda_e`'s own active-runs threshold is honest inactivity, not a served row
--   (materialize.py:264, "honest inactivity, not a served row -- matches v1's _active_runs
--   threshold") -- it produces NO row, not a zero-valued one.
--
-- The row count is therefore a function of (a) how many Tier-A/point-class candidates the global
-- contact stream offers inside the +/-3yr window, (b) how many of THIS chart's own natal targets
-- and active dasha periods those candidates actually engage, and (c) how many clear
-- `compute_lambda_e`'s threshold -- three chart- and time-dependent gates stacked, not one
-- constant.
--
-- Live-measured for the canonical chart (482012f1-710e-4a25-994a-93821f5871aa), re-verified this
-- cycle via `count(*) FROM kala_gochara_windows_v2 WHERE chart_id=... AND generation='2.0'
-- GROUP BY event_class` (matches the asset's own count_sql, which additionally filters
-- generation='2.0' -- this writer's own table also holds a distinct v1-corpus generation this
-- migration does not touch):
--   illness_acute               15
--   career_entry                11
--   bereavement                 10
--   surgery                      8
--   property_acquisition         8
--   achievement_recognition      7
--   travel_event                 4
--   birth_anchor                 4
--   career_advancement           4
--   marriage                     3
--   romantic_start               3
--   exam_outcome                 3
--   childbirth                   3
--   --------------------------------
--   TOTAL                       83   (matches target_floor and count_sql exactly)
--
-- Per migration 690/852/853's own recorded practice: this formula is intentionally
-- prose+structured-inputs, not a `COUNT()`/`ACTUAL()`/arithmetic literal the seed's
-- `validateFormulas` parser accepts, because the real computation is chart- and time-dependent
-- across three stacked gates and cannot be reduced to a single closed-form arithmetic identity.
-- This migration does not touch the seed; the row is DB-authoritative and seed-divergent in the
-- same documented, already-flagged way migration 690's six rows (and migrations 852/853's one row
-- each) are.

UPDATE asset_registry
   SET expected_volume_formula = 'SUM_OVER_EVENT_CLASSES(lambda_e_scored_candidates_above_threshold), not a flat count',
       expected_volume_inputs = jsonb_build_object(
         'kind', 'chart_scored_candidate_count',
         'chart_scoped', true,
         'horizon_years', 3,
         'horizon_kind', 'progressive, anchored at build time (PROGRESSIVE_HORIZON_YEARS)',
         'candidate_source', 'bg_gochara_arcs (chart-independent contact stream, built once globally)',
         'scope_restriction', 'Tier A (eager) bodies only, temporal_shape=''point'' event classes only',
         'scoring', 'gochara_intensity.compute_lambda_e against this chart''s ka_gochara_resonance targets and active dasha periods',
         'gate', 'a candidate below compute_lambda_e''s own active-runs threshold produces no row (honest inactivity, never a zero-valued row)',
         'per_row', 'one row per (event_class, scored window) that clears the active-runs threshold, inside the horizon',
         'derivation', 'derived from services/w2g/materialize.py directly, not guessed, and not reducible to one closed-form arithmetic expression because it depends on the chart''s own natal targets, active dasha periods, and the global contact stream''s candidate density inside the horizon',
         'observed_2026_09_07', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', jsonb_build_object(
             'illness_acute', 15, 'career_entry', 11, 'bereavement', 10, 'surgery', 8,
             'property_acquisition', 8, 'achievement_recognition', 7, 'travel_event', 4,
             'birth_anchor', 4, 'career_advancement', 4, 'marriage', 3, 'romantic_start', 3,
             'exam_outcome', 3, 'childbirth', 3, 'total', 83
           )
         ),
         'supersedes', 'NULL (F-L3-4)'
       ),
       volume_explanation = 'Not a flat count: one row per (event_class, scored window) that clears compute_lambda_e''s active-runs threshold, drawn from Tier-A/point-class candidates in the global contact stream, scored against this chart''s own natal targets and dasha periods, inside a progressive +/-3-year horizon. A sub-threshold candidate is honest inactivity and produces no row at all. 83 is the live-measured count for the canonical chart, matching target_floor and count_sql exactly, not an invented figure.'
 WHERE asset_id = 'ka_gochara'
   AND expected_volume_formula IS NULL;
