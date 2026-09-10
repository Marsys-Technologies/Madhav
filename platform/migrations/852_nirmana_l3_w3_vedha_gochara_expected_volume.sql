-- 852_nirmana_l3_w3_vedha_gochara_expected_volume.sql
--
-- NIRMĀṆA L3 Kāla — W3. Closes F-L3-4 for `ka_vedha_gochara`: `expected_volume_formula`,
-- `expected_volume_inputs` and `volume_explanation` were all NULL, leaving the already-correct
-- `target_floor` (176, an achieved-count floor per §N.4, unchanged by this migration) an
-- undocumented constant rather than a derived, auditable figure (C12: "derive, never pick").
--
-- `ka_vedha_gochara` is NOT a flat-count asset (unlike `ga_condition`, migration 851): its row
-- count is a function of live reference-table sizes AND which of those rules' gating conditions
-- are actually met by the transiting ephemeris over a scanned horizon, for THIS chart's natal
-- Moon. Same "not a flat count, describe the real computation" convention as L5's
-- `mi_adhilepa`/`mi_bhara` (migration 690) — derived here from the writer itself
-- (services/ka_vedha_gochara/writer.py), not guessed:
--
--   house_vedha:     one row per (graha, sign-run) pair where the graha's natal-Moon-relative
--                     house has a vedha-checkable rule in bg_transit_rules
--                     (rule_type='favourable', vedha_house IS NOT NULL) — live-measured 41 such
--                     rules across all 9 grahas today. Gated further by the horizon actually
--                     containing that graha in that sign (transit-dependent, not a fixed count).
--   sarvatobhadra:    one row per (graha, nakshatra-run) pair where the graha dwells in the
--                     SBC vedha nakshatra of the natal Moon's nakshatra (opposite_nakshatra_id,
--                     or a DB-sourced grid pair if ever populated) during the horizon.
--   latta:            one row per (graha, nakshatra-run) pair where the graha's Latta point
--                     (bg_phaladeepika_latta; live-measured 8 rows, Ketu deliberately absent —
--                     see the writer's own docstring) lands on the natal Moon's nakshatra
--                     during the horizon.
--
-- Horizon is chart-build-time-relative, not calendar-fixed (HORIZON_BACK_DAYS=60,
-- HORIZON_FORWARD_DAYS=400 — 460 days total, day-grade, matching ka_kota_chakra/
-- ka_moorti_nirnaya's own convention), so the exact count legitimately drifts run-to-run as
-- "today" moves and different transits fall inside vs. outside the window — an honest
-- volume_explanation states this rather than implying a fixed formula the writer does not have.
--
-- Live-measured for the canonical chart (482012f1-710e-4a25-994a-93821f5871aa), re-verified this
-- cycle via `count(*) FROM kala_vedha_gochara WHERE chart_id=... GROUP BY vedha_kind`:
--   house_vedha     132
--   sarvatobhadra    24
--   latta            20
--   -----------------------
--   TOTAL           176   (matches target_floor and count_sql exactly)
--
-- Per migration 690's own recorded practice (and its still-open cross-layer question on
-- `asset_registry_seed.ts`'s narrower `validateFormulas` grammar): this formula is intentionally
-- prose+structured-inputs, not a `COUNT()`/`ACTUAL()`/arithmetic literal the seed's parser
-- accepts, because the real computation is transit-dependent and cannot be reduced to one. This
-- migration does not touch the seed; the row is DB-authoritative and seed-divergent in the same
-- documented, already-flagged way migration 690's six rows are.
--
-- No self-transaction wrapper (transaction ownership belongs to platform/scripts/migrate.ts,
-- matching migration 670/850's convention for this range, not migration 851's) — self-caught this
-- cycle: an earlier draft of this file DID include BEGIN;/COMMIT;, and the paired test's
-- execute-then-rollback pattern could not undo it (the file's own embedded COMMIT closed that
-- transaction before the test's outer `conn.rollback()` ran), so a first test run against the
-- local Cloud SQL proxy silently persisted this migration's values for real outside of any
-- deploy. Caught immediately by re-querying the live row after the "rolled back" test claimed
-- success, reverted by hand (UPDATE ... SET ... = NULL WHERE asset_id = 'ka_vedha_gochara'),
-- and fixed at root here rather than left for the next session to rediscover.

UPDATE asset_registry
   SET expected_volume_formula = 'HORIZON_GATED(house_vedha_transits) + HORIZON_GATED(sarvatobhadra_dwellings) + HORIZON_GATED(latta_dwellings), not a flat count',
       expected_volume_inputs = jsonb_build_object(
         'kind', 'horizon_gated_transit_count',
         'chart_scoped', true,
         'horizon_back_days', 60,
         'horizon_forward_days', 400,
         'horizon_total_days', 460,
         'horizon_anchor', 'chart build time (today), not calendar-fixed',
         'components', jsonb_build_object(
           'house_vedha', jsonb_build_object(
             'gate', 'bg_transit_rules WHERE rule_type=''favourable'' AND vedha_house IS NOT NULL',
             'live_gating_rule_count', 41,
             'live_gating_graha_count', 9,
             'per_row', 'one row per (graha, sign-run) pair whose natal-Moon-relative house matches a gating rule and whose sign-run falls inside the horizon'
           ),
           'sarvatobhadra', jsonb_build_object(
             'gate', 'graha dwells in the SBC vedha nakshatra of the natal Moon nakshatra (opposite_nakshatra_id or DB-sourced grid pair)',
             'per_row', 'one row per (graha, nakshatra-run) pair matching the vedha nakshatra inside the horizon'
           ),
           'latta', jsonb_build_object(
             'gate', 'bg_phaladeepika_latta (Ketu deliberately absent — no counting rule found in source)',
             'live_gating_rule_count', 8,
             'per_row', 'one row per (graha, nakshatra-run) pair whose Latta point lands on the natal Moon nakshatra inside the horizon'
           )
         ),
         'derivation', 'derived from services/ka_vedha_gochara/writer.py directly, not guessed, and not reducible to one closed-form arithmetic expression because it is transit-dependent',
         'observed_2026_09_07', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', jsonb_build_object(
             'house_vedha', 132, 'sarvatobhadra', 24, 'latta', 20, 'total', 176
           )
         ),
         'supersedes', 'NULL (F-L3-4)'
       ),
       volume_explanation = 'Not a flat count: one row per (graha, transit-run) triple whose natal-Moon-relative gating condition (a vedha-checkable house rule, an SBC vedha-nakshatra dwelling, or a Latta-point dwelling) is met somewhere inside a 460-day horizon anchored at build time. The exact count legitimately varies run-to-run as the horizon slides and different transits fall inside vs. outside the window. 176 (132 house_vedha + 24 sarvatobhadra + 20 latta) is the live-measured count for the canonical chart, matching target_floor and count_sql exactly, not an invented figure.'
 WHERE asset_id = 'ka_vedha_gochara'
   AND expected_volume_formula IS NULL;
