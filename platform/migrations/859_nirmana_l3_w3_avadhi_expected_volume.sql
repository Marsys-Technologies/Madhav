-- 859_nirmana_l3_w3_avadhi_expected_volume.sql
--
-- NIRMĀṆA L3 Kāla — W3. Closes F-L3-4 for `ka_avadhi`: `expected_volume_formula`,
-- `expected_volume_inputs` and `volume_explanation` were all NULL, leaving the already-correct
-- `target_floor` (1169, an achieved-count floor per §N.4, unchanged by this migration) an
-- undocumented constant rather than a derived, auditable figure (C12: "derive, never pick").
--
-- No self-transaction wrapper (transaction ownership belongs to platform/scripts/migrate.ts,
-- matching migration 670/850/852-858's convention for this range).
--
-- `ka_avadhi` (Period Dossiers, pipeline/orchestrator/writers/ka_avadhi.py) is NOT a flat count.
-- Derived here from the writer's own SQL directly, not guessed: one row per (system_id, level_n,
-- period) drawn from `chart_dashas` for `level_n IN (1, 2)` (MD + AD only, no PD), restricted to
-- `system_id = ANY(_DASHA_SYSTEMS)` where `_DASHA_SYSTEMS` declares 7 names (vimshottari, yogini,
-- ashtottari, chara, naisargika, mudda, kalachakra) -- an exact-match array filter
-- (writer.py:80,93), not a wildcard.
--
-- **Honest gap surfaced, not fixed, not asserted as a root cause here:** live `chart_dashas` for
-- the canonical chart carries 9 distinct `system_id` values, and only 6 of the 7 names in
-- `_DASHA_SYSTEMS` have an EXACT match (`vimshottari`, `yogini`, `ashtottari`, `naisargika`,
-- `mudda`, `kalachakra` -- confirmed live below). The 7th, `'chara'`, has zero exact matches;
-- `chart_dashas` instead carries a `'chara_karaka'` system_id, whose relationship to the classical
-- Jaimini Chara (rāśi) Daśā this writer's `_DASHA_SYSTEMS` entry names is UNCLEAR from this
-- migration's own investigation alone -- "chara karaka" is the Jaimini movable-significator concept
-- (Atmakaraka etc.), a DIFFERENT technique from Chara Daśā, so this may be an honest L1-side gap
-- (no Chara Daśā ever built) rather than a naming bug in `ka_avadhi` itself. Recorded as a Held
-- item in `L3_STATE.md` for follow-up, not resolved or guessed at here. `vimshottari_kp` and
-- `narayana` (the other 2 of the 9 live system_ids) are simply outside `_DASHA_SYSTEMS`'s declared
-- scope, which is a deliberate choice, not a gap.
--
-- The row count is therefore this native's own lifetime MD+AD period count, summed across the 6
-- systems that DO exactly match, each system contributing a different number of periods per its own
-- classical cycle length (Vimshottari=120y, Yogini=36y, Ashtottari=108y, Naisargika/Mudda/Kalachakra
-- each with their own convention) -- not reducible to one closed-form arithmetic identity.
--
-- Live-measured for the canonical chart (482012f1-710e-4a25-994a-93821f5871aa), re-verified this
-- cycle via `count(*) FROM kala_avadhi WHERE chart_id=... GROUP BY system_id, level_n`:
--   vimshottari   MD 13, AD 104   = 117
--   yogini        MD 35, AD 273   = 308
--   ashtottari    MD 13, AD  91   = 104
--   naisargika    MD  8, AD  62   =  70
--   mudda         MD 48, AD 432   = 480
--   kalachakra    MD  9, AD  81   =  90
--   -------------------------------------
--   TOTAL                        1169   (matches target_floor and count_sql exactly)
--
-- Per migration 690/852-858's own recorded practice: this formula is intentionally
-- prose+structured-inputs, not a `COUNT()`/`ACTUAL()`/arithmetic literal the seed's
-- `validateFormulas` parser accepts, because the real computation is native-lifetime- and
-- per-system-cycle-length-dependent across 6 independently-counted dasha systems. This migration
-- does not touch the seed; the row is DB-authoritative and seed-divergent in the same documented,
-- already-flagged way migration 690's six rows (and migrations 852-858's one row each) are.

UPDATE asset_registry
   SET expected_volume_formula = 'SUM_OVER_6_MATCHING_DASHA_SYSTEMS(MD_count + AD_count), not a flat count',
       expected_volume_inputs = jsonb_build_object(
         'kind', 'multi_system_lifetime_dasha_count',
         'chart_scoped', true,
         'levels', 'level_n IN (1, 2) only (MD + AD, no PD)',
         'declared_systems', jsonb_build_array('vimshottari', 'yogini', 'ashtottari', 'chara', 'naisargika', 'mudda', 'kalachakra'),
         'systems_with_an_exact_live_match', jsonb_build_array('vimshottari', 'yogini', 'ashtottari', 'naisargika', 'mudda', 'kalachakra'),
         'unresolved_gap', jsonb_build_object(
           'declared_name', 'chara',
           'live_chart_dashas_has_instead', 'chara_karaka',
           'note', 'Jaimini chara karaka (movable significators) is a different technique from Chara (rasi) Dasha. Whether this is an honest L1-side build gap or a naming mismatch in ka_avadhi is NOT resolved by this migration, recorded as a Held item for follow-up, per section N.7: an honest null/unresolved beats an invented judgment'
         ),
         'per_row', 'one row per (system_id, level_n, period) for the 6 exactly-matching systems',
         'derivation', 'derived from pipeline/orchestrator/writers/ka_avadhi.py directly, not guessed, and not reducible to one closed-form arithmetic expression because each of the 6 matching systems has its own classical cycle length and period count for this native''s lifetime',
         'observed_2026_09_07', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', jsonb_build_object(
             'vimshottari', 117, 'yogini', 308, 'ashtottari', 104, 'naisargika', 70,
             'mudda', 480, 'kalachakra', 90, 'total', 1169
           )
         ),
         'supersedes', 'NULL (F-L3-4)'
       ),
       volume_explanation = 'Not a flat count: one row per (system_id, level_n, period) summed across the 6 of 7 declared dasha systems that have an exact live system_id match in chart_dashas (vimshottari, yogini, ashtottari, naisargika, mudda, kalachakra), MD+AD levels only. The 7th declared system, chara, has no exact match today. chart_dashas instead carries chara_karaka, a related but distinct Jaimini concept, an honest, unresolved gap recorded as a Held item, not silently absorbed or guessed at. 1169 is the live-measured count for the canonical chart, matching target_floor and count_sql exactly, not an invented figure.'
 WHERE asset_id = 'ka_avadhi'
   AND expected_volume_formula IS NULL;
