-- 853_nirmana_l3_w3_kota_chakra_expected_volume.sql
--
-- NIRMĀṆA L3 Kāla — W3. Closes F-L3-4 for `ka_kota_chakra`: `expected_volume_formula`,
-- `expected_volume_inputs` and `volume_explanation` were all NULL, leaving the already-correct
-- `target_floor` (588, an achieved-count floor per §N.4, unchanged by this migration) an
-- undocumented constant rather than a derived, auditable figure (C12: "derive, never pick").
--
-- No self-transaction wrapper (transaction ownership belongs to platform/scripts/migrate.ts,
-- matching migration 670/850/852's convention for this range) — deliberately, having just
-- self-caught the hazard of an embedded BEGIN;/COMMIT; defeating the paired test's
-- execute-then-rollback pattern on migration 852 in the immediately preceding cycle.
--
-- `ka_kota_chakra` is NOT a flat-count asset, but it is simpler than `ka_vedha_gochara`
-- (migration 852): derived here from the writer itself (services/ka_kota_chakra/writer.py), not
-- guessed. There is NO rule-matching gate — every one of the 9 grahas contributes rows
-- unconditionally. One row is emitted per (graha, nakshatra-run): a maximal contiguous run of
-- calendar days during which that graha occupies the SAME nakshatra, over a 460-day
-- build-time-anchored horizon (HORIZON_BACK_DAYS=60, HORIZON_FORWARD_DAYS=400 — the same
-- convention as ka_vedha_gochara/ka_moorti_nirnaya). The row count per graha is therefore
-- proportional to that graha's own nakshatra-transit RATE over the horizon, not a shared
-- constant: the Moon transits a nakshatra roughly once a day (27 nakshatras in ~27.3 days), so it
-- alone drives most of the total; Rahu/Ketu (mean nodes) move the slowest and drive almost none of
-- it.
--
-- Live-measured for the canonical chart (482012f1-710e-4a25-994a-93821f5871aa), re-verified this
-- cycle via `count(*) FROM kala_kota_chakra WHERE chart_id=... GROUP BY graha`:
--   Moon        442
--   Mercury      41
--   Venus        35
--   Sun          35
--   Mars         18
--   Jupiter       7
--   Saturn        4
--   Ketu          3
--   Rahu          3
--   -----------------
--   TOTAL       588   (matches target_floor and count_sql exactly)
--
-- Per migration 690/852's own recorded practice: this formula is intentionally prose+structured-
-- inputs, not a `COUNT()`/`ACTUAL()`/arithmetic literal the seed's `validateFormulas` parser
-- accepts, because the real computation is transit-rate-dependent and cannot be reduced to a
-- single closed-form arithmetic identity across all 9 grahas. This migration does not touch the
-- seed; the row is DB-authoritative and seed-divergent in the same documented, already-flagged way
-- migration 690's six rows (and migration 852's one row) are.

UPDATE asset_registry
   SET expected_volume_formula = 'SUM_OVER_GRAHAS(nakshatra_transit_runs_in_horizon), not a flat count',
       expected_volume_inputs = jsonb_build_object(
         'kind', 'horizon_gated_transit_run_count',
         'chart_scoped', true,
         'horizon_back_days', 60,
         'horizon_forward_days', 400,
         'horizon_total_days', 460,
         'horizon_anchor', 'chart build time (today), not calendar-fixed',
         'gate', 'none, unconditional: all 9 grahas contribute every run',
         'per_row', 'one row per (graha, nakshatra-run): a maximal contiguous run of days during which that graha occupies the same nakshatra, inside the horizon',
         'derivation', 'derived from services/ka_kota_chakra/writer.py and services/ka_kota_chakra/logic.py::detect_ring_runs directly, not guessed, and not reducible to one closed-form arithmetic expression because each graha''s row count is proportional to its own transit rate',
         'observed_2026_09_07', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', jsonb_build_object(
             'Moon', 442, 'Mercury', 41, 'Venus', 35, 'Sun', 35, 'Mars', 18,
             'Jupiter', 7, 'Saturn', 4, 'Ketu', 3, 'Rahu', 3, 'total', 588
           )
         ),
         'supersedes', 'NULL (F-L3-4)'
       ),
       volume_explanation = 'Not a flat count: one row per (graha, nakshatra-run) over a 460-day horizon anchored at build time, unconditional, every graha contributes every run it makes, with no rule-matching gate. Each graha''s share is proportional to its own real transit rate (the Moon alone drives most of the total, the slow-moving nodes drive almost none). 588 is the live-measured count for the canonical chart, matching target_floor and count_sql exactly, not an invented figure.'
 WHERE asset_id = 'ka_kota_chakra'
   AND expected_volume_formula IS NULL;
