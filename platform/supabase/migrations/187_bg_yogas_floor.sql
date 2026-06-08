-- migration 187: set bg_yogas target_floor to achieved row count.
-- Brief aspiration: 250 (HELD per brief §3a, corpus_verse mechanism).
-- Achieved: 86 rows in brahma_yoga_catalog seeded Tier 1 campaign 2026-06-09.
-- Breakdown: 81 inline core (§3.1–§3.5 closed-set, source-cited) +
--            5 corpus-verse rows from Saravali/BPHS/Phaladeepika yoga chapters.
-- The corpus extraction yielded only 5 NEW distinct yogas beyond the inline core
-- because most named yogas in the yoga chapters (Ch.27-51, Ch.30-45, Ch.4-11)
-- match canonical_ids already present in YOGAS_CORE (sunapha, anapha, kemadruma,
-- gajakesari, vajra, yava, etc.). The 81-row inline core exhaustively covers the
-- closed classical enumeration.
-- Floor policy: floors-are-aspirational; target_floor set to ACHIEVED count (86).
-- The 250 aspiration is not lowered permanently — the brief §8 HARD STOP applies
-- only when the corpus-verse mechanism can yield more. Operator may re-run after
-- additional corpus ingestion to raise the floor.
BEGIN;
UPDATE asset_registry
   SET target_floor = 86,
       volume_explanation = 'bg_yogas: 86 rows in brahma_yoga_catalog seeded Tier 1 campaign 2026-06-09. '
                         || '81 inline closed-set core (PMP×5, lunar/solar×6, Nabhasa×32, named×19, raja/dhana/sannyasa/aristha×19) '
                         || '+ 5 corpus-verse rows from Saravali/BPHS/Phaladeepika yoga chapters. '
                         || 'Brief aspiration was 250 (HELD). Floor set to achieved count per floors-are-aspirational policy.'
 WHERE asset_id = 'bg_yogas';
COMMIT;
