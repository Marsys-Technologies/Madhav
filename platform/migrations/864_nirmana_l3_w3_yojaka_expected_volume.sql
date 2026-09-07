-- 864_nirmana_l3_w3_yojaka_expected_volume.sql
--
-- NIRMĀṆA L3 Kāla — W3. Closes F-L3-4 for `ka_yojaka`: `expected_volume_formula`,
-- `expected_volume_inputs` and `volume_explanation` were all NULL, leaving the already-correct
-- `target_floor` (50104, an achieved-count floor per §N.4, unchanged by this migration) an
-- undocumented constant rather than a derived, auditable figure (C12: "derive, never pick").
--
-- No self-transaction wrapper (transaction ownership belongs to platform/scripts/migrate.ts,
-- matching migration 670/850/852-863's convention for this range).
--
-- `ka_yojaka` (activation-predicate bridge, pipeline/orchestrator/writers/ka_yojaka.py) is the
-- SIMPLEST volume derivation in this whole F-L3-4 batch: it is a genuine one-row-per-signal
-- pass-through, confirmed by reading the full per-signal loop (writer.py:184-294) end to end --
-- every signal reaches `enriched.append(...)` unconditionally; there is NO `continue`/`break`
-- anywhere in that loop that could skip a signal. `enriched` is then converted 1:1 into `rows`
-- (writer.py:320-321) and batch-inserted. So:
--
--   row_count(ka_yojaka) = COUNT(bodha_msr_signals WHERE chart_id = $chart)
--
-- exactly, for any chart, always -- not an approximation and not merely "usually" 1:1. (A
-- secondary FALLBACK enrichment loop at writer.py:308-318 does contain a `continue`, but that
-- loop only fills in a missing `constituent_lords` field on an ALREADY-`enriched` predicate; it
-- runs AFTER `enriched.append` and cannot remove a row that already made it in.)
--
-- Live-verified for the canonical chart (482012f1-710e-4a25-994a-93821f5871aa): `bodha_msr_signals`
-- holds exactly 50104 rows for this chart, matching `ka_yojaka`'s own `target_floor` and
-- `count_sql` result exactly.
--
-- Per migration 690/852-863's own recorded practice: even though this one IS a simple identity
-- (unlike the other assets in this batch), it is still cross-layer (`bodha_msr_signals` is an L2
-- Bodha table, not L3's own), chart-varying, and not something the seed's own
-- `validateFormulas`/`ACTUAL()`/arithmetic grammar can express directly against another layer's
-- table without a dedicated primitive -- so this migration states it in prose + structured inputs,
-- consistent with every other row in this batch, rather than attempt a one-off exception.

UPDATE asset_registry
   SET expected_volume_formula = 'COUNT(bodha_msr_signals WHERE chart_id = $chart), exact 1:1 pass-through, no skip anywhere in the per-signal loop',
       expected_volume_inputs = jsonb_build_object(
         'kind', 'one_to_one_signal_passthrough',
         'chart_scoped', true,
         'source_table', 'bodha_msr_signals',
         'source_layer', 'L2 Bodha (cross-layer read)',
         'per_row', 'exactly one row per bodha_msr_signals row for this chart, unconditionally. Confirmed no continue/break in the per-signal loop (writer.py:184-294) before enriched.append',
         'derivation', 'derived from pipeline/orchestrator/writers/ka_yojaka.py directly, not guessed. This is a true identity for every chart, not merely observed to match for the canonical one',
         'observed_2026_09_07', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', jsonb_build_object('bodha_msr_signals', 50104, 'kala_activation_predicates', 50104)
         ),
         'supersedes', 'NULL (F-L3-4)'
       ),
       volume_explanation = 'A true 1:1 pass-through, not merely a flat count that happens to match: every bodha_msr_signals row for this chart produces exactly one kala_activation_predicates row, confirmed by reading the writer''s full per-signal loop end to end (no skip path exists between reading a signal and emitting its row). 50104 is the live-measured count for the canonical chart, matching target_floor and count_sql exactly, not an invented figure.'
 WHERE asset_id = 'ka_yojaka'
   AND expected_volume_formula IS NULL;
