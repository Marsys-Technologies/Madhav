-- migration 187: set bg_yogas target_floor to achieved row count.
-- Brief aspiration: 250 (HELD per brief §3a, corpus_verse mechanism).
-- Achieved: 175 rows in brahma_yoga_catalog seeded Tier 1 campaign 2026-06-09
--           after chapter-filter bug fix (remediation 2026-06-09).
-- Breakdown: 81 inline core (§3.1–§3.5 closed-set, source-cited) +
--            94 corpus-verse rows from Saravali/BPHS/Phaladeepika.
-- Pre-fix state: 86 rows (81 core + 5 corpus-extracted).
-- Chapter filter bug: YOGA_CHAPTERS dict targeted PDF page numbers 30-45 (bphs),
--   27-51 (saravali), 4-11 (phaladeepika) — these are introductory/preface PDF pages;
--   correct yoga content is at pages ~355-415 (bphs), ~16-35 (phaladeepika), 52-80+ (saravali).
-- Fix: dropped chapter filter entirely; keyword filter lower(content_en) LIKE '%yoga%'
--   expanded scanned pool from ~37 chunks to 403 chunks across all three texts.
-- Pre-dedup candidates (regex hits): 291; inline-core dedup skipped: 80; new distinct: 94.
-- Floor policy: floors-are-aspirational; target_floor set to ACHIEVED count (175).
BEGIN;
UPDATE asset_registry
   SET target_floor = 175,
       volume_explanation = 'bg_yogas: 175 rows in brahma_yoga_catalog seeded Tier 1 campaign 2026-06-09. '
                         || '81 inline closed-set core (PMP×5, lunar/solar×6, Nabhasa×32, named×19, raja/dhana/sannyasa/aristha×19) '
                         || '+ 94 corpus-verse rows from bphs+saravali+phaladeepika. '
                         || 'Pre-dedup candidates: 291. Post-dedup new: 94. '
                         || 'Chapter filter bug fixed 2026-06-09 remediation — '
                         || 'BPHS pages 30-45 (wrong) replaced by keyword-only filter; '
                         || 'expanded scan from 37 to 403 yoga-keyword chunks. '
                         || 'Brief aspiration was 250 (HELD). Floor set to achieved count per floors-are-aspirational policy.'
 WHERE asset_id = 'bg_yogas';
COMMIT;
