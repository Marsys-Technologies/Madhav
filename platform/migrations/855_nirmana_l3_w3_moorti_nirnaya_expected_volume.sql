-- 855_nirmana_l3_w3_moorti_nirnaya_expected_volume.sql
--
-- NIRMĀṆA L3 Kāla — W3. Closes F-L3-4 for `ka_moorti_nirnaya`: `expected_volume_formula`,
-- `expected_volume_inputs` and `volume_explanation` were all NULL, leaving the already-correct
-- `target_floor` (72, an achieved-count floor per §N.4, unchanged by this migration) an
-- undocumented constant rather than a derived, auditable figure (C12: "derive, never pick").
--
-- No self-transaction wrapper (transaction ownership belongs to platform/scripts/migrate.ts,
-- matching migration 670/850/852/853/854's convention for this range).
--
-- `ka_moorti_nirnaya` is NOT a flat-count asset. Derived here from the writer itself
-- (services/ka_moorti_nirnaya/writer.py, logic.py), not guessed: same ungated sign-run-detection
-- shape as `ka_kota_chakra` (migration 853), but over SIGN index rather than nakshatra index, and
-- scoped to the 8 grahas OTHER than the Moon (`MOORTI_GRAHAS` -- Sun, Mars, Mercury, Jupiter,
-- Venus, Saturn, Rahu, Ketu; the Moon is disclosed out-of-scope in logic.py's own module
-- docstring, not an oversight: "the Moon's position at the Moon's own ingress" is not a construction
-- any codebase-attested classical source treats as a distinct technique). One row per (graha,
-- sign-run) over the same 460-day build-time-anchored horizon (HORIZON_BACK_DAYS=60,
-- HORIZON_FORWARD_DAYS=400) `ka_kota_chakra`/`ka_vedha_gochara` use. No rule-matching gate --
-- every sign-run for every in-scope graha is recorded, though `moorti_computed=false` (with the
-- moorti fields left NULL, not fabricated) on a run whose `start_truncated` flag means its true
-- ingress instant falls outside the scanned horizon (logic.py's own honesty discipline,
-- B.10/§N.7) -- that row still counts toward volume, since it is still emitted, just without a
-- moorti classification.
--
-- The row count per graha is proportional to that graha's own sign-transit rate over the horizon
-- (faster movers like Mercury/Venus/Sun ingress far more often than the slow outer bodies), the
-- same non-flat-count shape as migration 853.
--
-- Live-measured for the canonical chart (482012f1-710e-4a25-994a-93821f5871aa), re-verified this
-- cycle via `count(*) FROM kala_moorti_nirnaya WHERE chart_id=... GROUP BY graha`:
--   Mercury    20
--   Venus      17
--   Sun        16
--   Mars        9
--   Jupiter     4
--   Ketu        2
--   Rahu        2
--   Saturn      2
--   -----------------
--   TOTAL      72   (matches target_floor and count_sql exactly)
--
-- Per migration 690/852/853/854's own recorded practice: this formula is intentionally
-- prose+structured-inputs, not a `COUNT()`/`ACTUAL()`/arithmetic literal the seed's
-- `validateFormulas` parser accepts, because the real computation is transit-rate-dependent and
-- cannot be reduced to a single closed-form arithmetic identity across all 8 in-scope grahas. This
-- migration does not touch the seed; the row is DB-authoritative and seed-divergent in the same
-- documented, already-flagged way migration 690's six rows (and migrations 852/853/854's one row
-- each) are.

UPDATE asset_registry
   SET expected_volume_formula = 'SUM_OVER_8_GRAHAS(sign_transit_runs_in_horizon), not a flat count',
       expected_volume_inputs = jsonb_build_object(
         'kind', 'horizon_gated_transit_run_count',
         'chart_scoped', true,
         'horizon_back_days', 60,
         'horizon_forward_days', 400,
         'horizon_total_days', 460,
         'horizon_anchor', 'chart build time (today), not calendar-fixed',
         'gate', 'none, unconditional: all 8 in-scope grahas contribute every sign-run (moorti fields are NULL on a truncated run, but the row itself still counts)',
         'in_scope_grahas', 'Sun, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu (Moon deliberately excluded, disclosed in logic.py)',
         'per_row', 'one row per (graha, sign-run): a maximal contiguous run of days during which that graha occupies the same sign, inside the horizon',
         'derivation', 'derived from services/ka_moorti_nirnaya/writer.py and logic.py::detect_sign_runs directly, not guessed, and not reducible to one closed-form arithmetic expression because each graha''s row count is proportional to its own transit rate',
         'observed_2026_09_07', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', jsonb_build_object(
             'Mercury', 20, 'Venus', 17, 'Sun', 16, 'Mars', 9, 'Jupiter', 4,
             'Ketu', 2, 'Rahu', 2, 'Saturn', 2, 'total', 72
           )
         ),
         'supersedes', 'NULL (F-L3-4)'
       ),
       volume_explanation = 'Not a flat count: one row per (graha, sign-run) over a 460-day horizon anchored at build time, unconditional, every one of the 8 in-scope grahas (all but the Moon) contributes every sign-run it makes. Each graha''s share is proportional to its own real transit rate (Mercury/Venus/Sun ingress far more often than the slow outer bodies). 72 is the live-measured count for the canonical chart, matching target_floor and count_sql exactly, not an invented figure.'
 WHERE asset_id = 'ka_moorti_nirnaya'
   AND expected_volume_formula IS NULL;
