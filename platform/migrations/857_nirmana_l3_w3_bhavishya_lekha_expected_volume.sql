-- 857_nirmana_l3_w3_bhavishya_lekha_expected_volume.sql
--
-- NIRMĀṆA L3 Kāla — W3. Closes F-L3-4 for `ka_bhavishya_lekha`: `expected_volume_formula`,
-- `expected_volume_inputs` and `volume_explanation` were all NULL, leaving the already-correct
-- `target_floor` (100, an achieved-count floor per §N.4, unchanged by this migration) an
-- undocumented constant rather than a derived, auditable figure (C12: "derive, never pick").
--
-- No self-transaction wrapper (transaction ownership belongs to platform/scripts/migrate.ts,
-- matching migration 670/850/852-856's convention for this range).
--
-- `ka_bhavishya_lekha` (probabilistic forward projection artifact,
-- pipeline/orchestrator/writers/ka_bhavishya_lekha.py) is a top-N-of-qualifying asset -- the same
-- shape as L5's `mi_adhilepa` (migration 690, `LEAST(5, COUNT(...))`), not a flat count, but far
-- simpler than migrations 852/853/855/856 in this batch (no per-graha/per-detector fan-out, just
-- a single ranked, capped SELECT):
--
--   SELECT ... FROM kala_darshana kd JOIN kala_convergence kc ON kd.convergence_id = kc.convergence_id
--   WHERE kd.chart_id = $chart AND kd.peak_date BETWEEN today AND today+5y
--     AND kd.net_label NOT IN ('obstructed_severe')
--   ORDER BY kd.effective_score DESC NULLS LAST, kd.peak_date, kd.convergence_id
--   LIMIT 100
--
-- (writer.py:80-107) -- row count is `LEAST(100, |eligible windows|)`, where "eligible" means a
-- `kala_darshana` row for this chart with `peak_date` inside the rolling next-5-years window and
-- a `net_label` that is not the worst-case `obstructed_severe` bucket. `today` is a rolling
-- build-time anchor, not calendar-fixed, so the eligible pool -- and therefore whether the count
-- is genuinely 100 (cap binding) or fewer (cap not binding) -- can shift build-to-build as windows
-- enter/exit the 5-year horizon.
--
-- Live-measured for the canonical chart (482012f1-710e-4a25-994a-93821f5871aa), re-verified this
-- cycle: 110 eligible windows exist today (re-run the WHERE clause above directly against
-- `kala_darshana`/`kala_convergence`), so the cap IS currently binding: LEAST(100, 110) = 100,
-- matching `target_floor` and `count_sql` exactly. (F-BHAV-3, already fixed in this writer per its
-- own comment: the ORDER BY previously had no tiebreak, so which 100 of the eligible windows
-- survived the cap varied build-to-build whenever `effective_score` ties -- measured "100/100
-- rows tied at 0.700" at the time of that fix. `peak_date, convergence_id` now give a real total
-- order, so which 100 survive is deterministic; this migration only documents the COUNT, not that
-- ordering fix, which already shipped.)
--
-- Per migration 690/852-856's own recorded practice: `LEAST(100, COUNT(...))` (unlike migration
-- 690's own `LEAST(5, COUNT(...))` literal) is still not encoded as the seed's own
-- `validateFormulas`/`ACTUAL()`/arithmetic grammar accepts, because the eligible-pool COUNT itself
-- is a multi-condition, rolling-horizon join this migration states in prose + structured inputs
-- rather than attempt to force through that narrower grammar. This migration does not touch the
-- seed; the row is DB-authoritative and seed-divergent in the same documented, already-flagged way
-- migration 690's six rows (and migrations 852-856's one row each) are.

UPDATE asset_registry
   SET expected_volume_formula = 'LEAST(100, COUNT(eligible kala_darshana windows in rolling next-5y horizon))',
       expected_volume_inputs = jsonb_build_object(
         'kind', 'top_n_of_qualifying',
         'chart_scoped', true,
         'cap', 100,
         'eligibility', jsonb_build_object(
           'source', 'kala_darshana kd JOIN kala_convergence kc ON kd.convergence_id = kc.convergence_id',
           'horizon', 'kd.peak_date BETWEEN today AND today + 5 years (rolling, build-time anchored)',
           'excluded_net_label', 'obstructed_severe'
         ),
         'ordering_for_cap', 'kd.effective_score DESC NULLS LAST, kd.peak_date, kd.convergence_id (a real total order, the F-BHAV-3 tiebreak fix already shipped in the writer, not this migration)',
         'derivation', 'derived from pipeline/orchestrator/writers/ka_bhavishya_lekha.py directly, not guessed, LEAST(100, |eligible|), not a flat count, because whether the cap binds depends on the rolling horizon''s eligible pool at build time',
         'observed_2026_09_07', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', jsonb_build_object(
             'eligible_windows', 110, 'cap', 100, 'served_rows', 100
           )
         ),
         'supersedes', 'NULL (F-L3-4)'
       ),
       volume_explanation = 'Top-N-of-qualifying, not a flat count: LEAST(100, count of kala_darshana windows for this chart with peak_date in the rolling next-5-years horizon and net_label not obstructed_severe), ranked by effective_score with a real tiebreak. 110 eligible windows exist for the canonical chart today, so the 100-row cap is currently binding (LEAST(100, 110) = 100), matching target_floor and count_sql exactly, not an invented figure. If the eligible pool ever drops below 100 as the horizon rolls forward, the served count would honestly drop below 100 too.'
 WHERE asset_id = 'ka_bhavishya_lekha'
   AND expected_volume_formula IS NULL;
