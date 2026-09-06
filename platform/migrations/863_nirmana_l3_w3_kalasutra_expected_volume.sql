-- 863_nirmana_l3_w3_kalasutra_expected_volume.sql
--
-- NIRMĀṆA L3 Kāla — W3. Closes F-L3-4 for `ka_kalasutra`: `expected_volume_formula`,
-- `expected_volume_inputs` and `volume_explanation` were all NULL, leaving the already-correct
-- `target_floor` (335403, an achieved-count floor per §N.4, unchanged by this migration) an
-- undocumented constant rather than a derived, auditable figure (C12: "derive, never pick").
--
-- No self-transaction wrapper (transaction ownership belongs to platform/scripts/migrate.ts,
-- matching migration 670/850/852-862's convention for this range).
--
-- `ka_kalasutra` (bounded activation artifact builder,
-- pipeline/orchestrator/writers/ka_kalasutra.py) is NOT a flat count. Derived here from the
-- writer's own logic directly, not guessed: it reads ALL `kala_activation_predicates` rows for
-- this chart (ka_yojaka's own output -- confirmed live below, the predicate count matches
-- `ka_yojaka`'s own `target_floor` exactly) and, per CR-109 (writer.py:135-140), emits ONE ROW
-- PER MATCHED IN-LIFE DAŚĀ PERIOD (`windows.period_windows`) that predicate's rule resolves
-- against -- not one collapsed row per predicate. A predicate whose rule resolves to ZERO
-- matched periods still emits exactly one row (the all-None fallback), so every predicate
-- contributes AT LEAST one row.
--
-- Live-measured for the canonical chart (482012f1-710e-4a25-994a-93821f5871aa), re-verified this
-- cycle via a `GROUP BY signal_id` breakdown over `kala_activation`, cross-checked against
-- `kala_activation_predicates`:
--   predicates (= ka_yojaka.target_floor)                50104
--   predicates resolving to exactly 1 row (fallback/single-period)   9347
--   predicates resolving to exactly 8 rows (8 matched in-life periods)  40757
--   -----------------------------------------------------------------------
--   9347 x 1 + 40757 x 8 = 9347 + 326056                             335403
--   (matches target_floor and count_sql exactly; 9347 + 40757 = 50104, the full predicate count,
--   confirming every predicate is accounted for in exactly one of these two buckets for this
--   chart -- this migration does not claim these are the ONLY two possible bucket sizes for
--   every chart, only that they are the two observed live today.)
--
-- Per migration 690/852-862's own recorded practice: this formula is intentionally
-- prose+structured-inputs, not a `COUNT()`/`ACTUAL()`/arithmetic literal the seed's
-- `validateFormulas` parser accepts, because the real per-predicate expansion factor is
-- rule-and-dasha-timeline-dependent, not a single multiplier. This migration does not touch the
-- seed; the row is DB-authoritative and seed-divergent in the same documented, already-flagged
-- way migration 690's six rows (and migrations 852-862's rows) are.

UPDATE asset_registry
   SET expected_volume_formula = 'SUM_OVER_PREDICATES(count of matched in-life dasha periods, minimum 1), not a flat count',
       expected_volume_inputs = jsonb_build_object(
         'kind', 'predicate_expansion_count',
         'chart_scoped', true,
         'predicate_source', 'kala_activation_predicates WHERE chart_id=$chart (ka_yojaka''s own output)',
         'per_row', 'one row per (predicate, matched in-life dasha period). A predicate with zero matched periods still emits exactly one all-None fallback row, so every predicate contributes at least 1 row',
         'derivation', 'derived from pipeline/orchestrator/writers/ka_kalasutra.py directly (CR-109), not guessed, and not reducible to one closed-form arithmetic expression because the per-predicate expansion factor depends on that predicate''s own dasha_eligibility_rule against this chart''s dasha timeline',
         'observed_2026_09_07', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', jsonb_build_object(
             'total_predicates', 50104,
             'predicates_with_1_row', 9347,
             'predicates_with_8_rows', 40757,
             'total_activation_rows', 335403
           )
         ),
         'supersedes', 'NULL (F-L3-4)'
       ),
       volume_explanation = 'Not a flat count: one row per (predicate, matched in-life dasha period), a predicate resolving to zero matched periods still emits exactly one all-None fallback row. For the canonical chart, 50104 predicates (ka_yojaka''s own row count) split into 9347 that resolve to exactly 1 row and 40757 that resolve to exactly 8 rows, summing to 335403 (9347 + 40757x8), matching target_floor and count_sql exactly, not an invented figure.'
 WHERE asset_id = 'ka_kalasutra'
   AND expected_volume_formula IS NULL;
