-- 858_nirmana_l3_w3_jivana_parva_expected_volume.sql
--
-- NIRMĀṆA L3 Kāla — W3. Closes F-L3-4 for `ka_jivana_parva`: `expected_volume_formula`,
-- `expected_volume_inputs` and `volume_explanation` were all NULL, leaving the already-correct
-- `target_floor` (100, an achieved-count floor per §N.4, unchanged by this migration -- and,
-- despite matching `ka_bhavishya_lekha`'s own 100 exactly, this is a coincidence of two
-- DIFFERENT derivations, not the same cap: see below) an undocumented constant rather than a
-- derived, auditable figure (C12: "derive, never pick").
--
-- No self-transaction wrapper (transaction ownership belongs to platform/scripts/migrate.ts,
-- matching migration 670/850/852-857's convention for this range).
--
-- `ka_jivana_parva` (life-arc biographical chapter artifact,
-- pipeline/orchestrator/writers/ka_jivana_parva.py) is NOT a flat count and is NOT the same shape
-- as any prior asset in this batch: it is the SUM of three independently-derived Vimshottari
-- dasha-level counts, each with its own clipping rule:
--
--   MD (level_n=1): all mahādaśā spans for this chart's Vimshottari/lahiri_chitrapaksha
--     system+ayanamsha, birth-date-clipped (T-9: a row ending before birth is dropped outright;
--     one straddling birth has its served start raised to birth_date.year -- see writer.py's own
--     module docstring for why: `chart_dashas` legitimately carries a pre-birth theoretical start
--     for the first mahādaśā, which must not be served as a lived chapter).
--   AD (level_n=2): all antardaśā spans within those same MDs, same birth-date clip.
--   PD (level_n=3): pratyantardaśā spans **whose date range spans `as_of_date` (today)** --
--     `WHERE level_n=3 AND start_date <= as_of_date AND end_date >= as_of_date` (writer.py:274-283).
--     **Correction to the writer's own inline comment, not the writer's behavior:** the comment
--     at writer.py:267-268 says this "naturally returns ... the currently-running Antardasha
--     (~9 rows)", but the actual filter matches only PD spans that COVER today, which for
--     non-overlapping pratyantardaśās is the SINGLE currently-active PD, not all ~9 siblings of
--     the current AD -- confirmed live below (1 row, not ~9). This migration documents the real,
--     verified behavior; it does not touch the writer or its comment.
--
-- The row count is therefore NOT reducible to one formula: MD/AD count is native-lifetime- and
-- ayanamsha-cycle-dependent (how many Vimshottari mahādaśās/antardaśās this specific native's
-- lifetime, clipped at birth, actually covers), and PD count is a build-time snapshot (0 or 1,
-- almost never more, since PDs of one AD do not overlap).
--
-- Live-measured for the canonical chart (482012f1-710e-4a25-994a-93821f5871aa), re-verified this
-- cycle via `count(*) FROM kala_jivana_parva WHERE chart_id=... GROUP BY parva_level`:
--   MD (level 1)     10
--   AD (level 2)     89
--   PD (level 3)      1
--   -------------------
--   TOTAL           100   (matches target_floor and count_sql exactly -- coincidentally equal to
--                          ka_bhavishya_lekha's own 100, migration 857, which is a top-N cap; this
--                          asset has no cap at all, it is a genuine, uncapped sum)
--
-- Per migration 690/852-857's own recorded practice: this formula is intentionally
-- prose+structured-inputs, not a `COUNT()`/`ACTUAL()`/arithmetic literal the seed's
-- `validateFormulas` parser accepts, because the real computation is native-lifetime- and
-- build-time-dependent across three independently-clipped dasha levels. This migration does not
-- touch the seed; the row is DB-authoritative and seed-divergent in the same documented,
-- already-flagged way migration 690's six rows (and migrations 852-857's one row each) are.

UPDATE asset_registry
   SET expected_volume_formula = 'COUNT(birth-clipped MD) + COUNT(birth-clipped AD) + COUNT(PD spanning as_of_date), not a flat count and not capped',
       expected_volume_inputs = jsonb_build_object(
         'kind', 'multi_level_birth_and_time_clipped_count',
         'chart_scoped', true,
         'system_scope', 'system_id=''vimshottari'', ayanamsha_id=''lahiri_chitrapaksha'' only (writer.py comment: without this scope the raw chart_dashas query would return level-1/2 rows across all 7 dasha systems x all 5 ayanamshas)',
         'levels', jsonb_build_object(
           'md', jsonb_build_object('level_n', 1, 'clip', 'birth-date clipped (T-9): rows ending before birth dropped, rows straddling birth served from birth_date.year'),
           'ad', jsonb_build_object('level_n', 2, 'clip', 'same birth-date clip as MD, scoped within each MD span'),
           'pd', jsonb_build_object('level_n', 3, 'clip', 'start_date <= as_of_date AND end_date >= as_of_date, the single PD spanning build time, corrected from the writer''s own stale ~9-rows inline comment, see this migration''s own header')
         ),
         'derivation', 'derived from pipeline/orchestrator/writers/ka_jivana_parva.py directly, not guessed, and not reducible to one closed-form arithmetic expression because MD/AD count depends on this native''s own lifetime span against the Vimshottari cycle, and PD count is a build-time snapshot',
         'observed_2026_09_07', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', jsonb_build_object(
             'md', 10, 'ad', 89, 'pd', 1, 'total', 100
           )
         ),
         'supersedes', 'NULL (F-L3-4)'
       ),
       volume_explanation = 'Not a flat count and not a cap (unlike ka_bhavishya_lekha''s coincidentally-identical 100, migration 857): the sum of three independently birth/time-clipped Vimshottari dasha-level counts, mahadashas and antardashas surviving the birth-date clip, plus the single pratyantardasha whose span currently covers build time (corrected from the writer''s own inline comment, which claims approximately nine PD rows but the actual filter returns only the one PD spanning as_of_date). 100 (10 MD + 89 AD + 1 PD) is the live-measured count for the canonical chart, matching target_floor and count_sql exactly, not an invented figure.'
 WHERE asset_id = 'ka_jivana_parva'
   AND expected_volume_formula IS NULL;
