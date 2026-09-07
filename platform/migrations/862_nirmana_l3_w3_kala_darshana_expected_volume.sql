-- 862_nirmana_l3_w3_kala_darshana_expected_volume.sql
--
-- NIRMĀṆA L3 Kāla — W3. Closes F-L3-4 for `ka_kala_darshana`: `expected_volume_formula`,
-- `expected_volume_inputs` and `volume_explanation` were all NULL, leaving the already-correct
-- `target_floor` (750, an achieved-count floor per §N.4, unchanged by this migration) an
-- undocumented constant rather than a derived, auditable figure (C12: "derive, never pick").
--
-- No self-transaction wrapper (transaction ownership belongs to platform/scripts/migrate.ts,
-- matching migration 670/850/852-861's convention for this range).
--
-- `ka_kala_darshana` (display-ready temporal view synthesizer,
-- pipeline/orchestrator/writers/ka_kala_darshana.py) is a top-N-of-qualifying asset -- the SAME
-- shape as `ka_bhavishya_lekha` (migration 857), simpler still: it has no additional
-- peak_date/net_label filter, just:
--
--   SELECT ... FROM kala_convergence kc WHERE kc.chart_id = $chart
--   ORDER BY kc.convergence_score DESC NULLS LAST
--   LIMIT 750
--
-- (writer.py:20-30) -- row count is `LEAST(750, |kala_convergence rows for this chart|)`. Every
-- selected row is served (obstruction data from `kala_obstruction` is joined in, but never used
-- to drop a row -- see writer.py's own §N.7 item 6 comment on the M9 fix, which corrected a
-- falsy-coalescing `conv_score or 0.5` default that silently mangled a real computed-zero score;
-- that fix already shipped and is unrelated to row COUNT, only to the served `effective_score`
-- value).
--
-- Live-measured for the canonical chart (482012f1-710e-4a25-994a-93821f5871aa), re-verified this
-- cycle: 14,868 `kala_convergence` rows exist for this chart (matches `ka_sangam`'s own
-- target_floor, and the same total `ka_vighnakara`'s migration 856 anchor-source count cited), so
-- the cap IS currently binding: LEAST(750, 14868) = 750, matching `target_floor` and `count_sql`
-- exactly.
--
-- Per migration 690/852-861's own recorded practice: `LEAST(750, COUNT(...))` is still not
-- encoded as the seed's own `validateFormulas`/`ACTUAL()`/arithmetic grammar accepts, so this
-- migration states it in prose + structured inputs instead. This migration does not touch the
-- seed; the row is DB-authoritative and seed-divergent in the same documented, already-flagged
-- way migration 690's six rows (and migrations 852-861's rows) are.

UPDATE asset_registry
   SET expected_volume_formula = 'LEAST(750, COUNT(kala_convergence rows for this chart))',
       expected_volume_inputs = jsonb_build_object(
         'kind', 'top_n_of_qualifying',
         'chart_scoped', true,
         'cap', 750,
         'eligibility', jsonb_build_object(
           'source', 'kala_convergence kc WHERE kc.chart_id = $chart',
           'note', 'no additional filter beyond chart_id, every convergence row for this chart is eligible'
         ),
         'ordering_for_cap', 'kc.convergence_score DESC NULLS LAST',
         'derivation', 'derived from pipeline/orchestrator/writers/ka_kala_darshana.py directly, not guessed, LEAST(750, |kala_convergence rows|), not a flat count, because whether the cap binds depends on how many convergence rows this chart has at build time',
         'observed_2026_09_07', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', jsonb_build_object(
             'eligible_convergence_rows', 14868, 'cap', 750, 'served_rows', 750
           )
         ),
         'supersedes', 'NULL (F-L3-4)'
       ),
       volume_explanation = 'Top-N-of-qualifying, not a flat count: LEAST(750, count of kala_convergence rows for this chart), ranked by convergence_score, no other filter. 14,868 convergence rows exist for the canonical chart today, so the 750-row cap is currently binding (LEAST(750, 14868) = 750), matching target_floor and count_sql exactly, not an invented figure.'
 WHERE asset_id = 'ka_kala_darshana'
   AND expected_volume_formula IS NULL;
