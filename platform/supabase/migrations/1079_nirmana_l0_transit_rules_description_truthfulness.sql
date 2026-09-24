-- Migration 1079: correct bg_transit_rules' registry description, which migration
-- 1078 left asserting a table-wide provenance the table does not have.
--
-- FOUND BY INDEPENDENT REVIEW of PR #2727 (the reviewer required by the L0 repair
-- scope, outside the Sangam/Kshetra/Gochara streams). Migration 1078's
-- `english_description` reads "...from Phaladeepika Adh. XXVI (page-anchored) and
-- Saravali/Jataka Parijata (double-transit)", dropping BPHS Ch.29 from the source
-- list. That is FALSE: 19 rows still carry the refuted "BPHS Ch.29 (Gochara Phala
-- — Transit Results)" citation — 18 `unfavourable` rows plus 1 `favourable` row
-- that has no vedha pair. Those 19 sit OUTSIDE L0 repair item 1's predicate
-- (`rule_type='favourable' AND vedha_house IS NOT NULL`), which is the only set
-- that was row-by-row verified against Phaladipika slokas 3-8; re-citing them
-- would have been an unverified claim, so they were correctly left alone. The
-- defect is only that 1078's prose then described the table as though they did not
-- exist — a cockpit/registry reader would report a clean Phaladipika lineage over
-- 19 BPHS-cited rows. This is exactly the §N.7 narration-fidelity class the repair
-- itself was carried out to fix, reproduced in the repair's own metadata.
--
-- 1078 IS APPLIED and is NEVER edited (CLAUDE.md §N.4). This is a NEW migration.
-- It touches `english_description` only: the integrity contract hashes table ROWS,
-- not registry prose, so `integrity_check_sql` is untouched and stays valid.
--
-- Census behind the replacement text, measured live on production 2026-09-24:
--   36  favourable+vedha  Phaladipika Adh. XXVI page-anchored (PG322:C1/PG323:C1)
--                         = 35 re-cited by item 1 + 1 inserted by item 2 (Mercury 8->1)
--    6  favourable+vedha  UNSOURCED (Rahu/Ketu; item 3, ruling N-14)
--   19  18 unfavourable + 1 favourable-without-vedha, still "BPHS Ch.29"
--    5  Phaladeepika Ch.26 (chapter-level, unfavourable)
--    3  Phaladeepika Adh. XXVI Slokas 2, 8 & 21 (Venus unfavourable, F-145)
--    7  double_transit (Phaladeepika ch.26 §double-gochara / Saravali / Jataka Parijata)
--   --  76 total
--
-- ── TWO PROSE CORRECTIONS TO MIGRATION 1075, recorded here because 1075 is
-- applied and cannot be edited (same reviewer, MED findings) ───────────────────
-- (a) 1075's header says its 10-arcsec tolerance is "roughly 640x tighter than the
--     177.3 arcsec true-vs-mean separation". That conflates two different figures.
--     177.3 arcsec (0.049248 deg) is the margin from the TRUE node to the Rohini
--     pada-4 boundary. The actual TRUE-vs-MEAN separation at the forensic instant
--     is 50.049248 - 49.033044 = 1.016204 deg = 3658.3 arcsec. So the tolerance is
--     ~366x tighter than the separation it must catch, not 640x. The 10-arcsec
--     VALUE is unaffected and remains correct and amply conservative; only 1075's
--     stated arithmetic was wrong.
-- (b) 1075's header describes the new check as detecting "a true-vs-mean node-frame
--     mixup". Scoped honestly, it detects a mixup in the PROBE's own node constant
--     and ayanamsha configuration: the check calls swe.calc_ut(MEAN_NODE) itself and
--     compares against a pinned longitude. It does NOT read `ephemeris_daily`, so it
--     cannot detect the stored frame drifting. The store is covered by migration
--     1076's row-level `node_mode`/`epoch_convention` declaration, which has no
--     probe of its own — a real, disclosed gap, not a covered one.
--
-- Registry metadata only; transaction ownership belongs to migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  prior_description constant text :=
    '76 classical transit rules: 43 favourable, 26 unfavourable, and 7 double-transit rules from Phaladeepika Adh. XXVI (page-anchored) and Saravali/Jataka Parijata (double-transit). L0 repair 2026-09: re-cited off the refuted "BPHS Ch.29", corrected 3 Venus vedha pairs, inserted the missing Mercury 8th-house pair, marked 6 Rahu/Ketu rows honestly unsourced.';
  truthful_description constant text :=
    '76 classical transit rules: 43 favourable, 26 unfavourable, 7 double-transit. Citation state after the 2026-09 L0 repair, measured not asserted: 36 favourable-with-vedha rows carry page-anchored Phaladipika Adh. XXVI citations (PG322:C1/PG323:C1); 6 Rahu/Ketu favourable-with-vedha rows are declared UNSOURCED (the served corpus carries no house-transit vedha doctrine for the nodes); 19 rows (18 unfavourable + 1 favourable with no vedha pair) STILL carry the refuted "BPHS Ch.29" — they lie outside the repair''s row-by-row verified predicate and were deliberately not re-cited on an unverified basis; the remaining 15 cite Phaladeepika Ch.26, Adh. XXVI slokas 2/8/21, Saravali or Jataka Parijata.';
BEGIN
  SELECT * INTO registry_row
  FROM asset_registry WHERE asset_id = 'bg_transit_rules' FOR UPDATE;

  IF NOT FOUND OR (
    registry_row.target_floor = 76
    AND registry_row.english_description = prior_description
  ) IS NOT TRUE THEN
    RAISE EXCEPTION
      'migration 1079 refuses: bg_transit_rules registry does not match migration 1078''s applied state (already corrected, or 1078 never applied)';
  END IF;

  UPDATE asset_registry
  SET english_description = truthful_description
  WHERE asset_id = 'bg_transit_rules';

  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 1079 expected 1 row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_transit_rules'
      AND english_description = truthful_description
      AND target_floor = 76
  ) THEN
    RAISE EXCEPTION 'migration 1079 postflight registry mismatch';
  END IF;
END $$;

-- =============================================================================
-- VERIFY (falsifier — run after apply). The description must agree with a live
-- recount, so this is checkable rather than merely readable:
--   SELECT count(*) FROM bg_transit_rules
--    WHERE classical_citation = 'BPHS Ch.29 (Gochara Phala — Transit Results)';
--   -- expect 19, which is the number the description states
--   SELECT count(*) FROM bg_transit_rules WHERE classical_citation LIKE 'UNSOURCED%';
--   -- expect 6
--   SELECT count(*) FROM bg_transit_rules WHERE classical_citation LIKE 'Phaladipika Adh. XXVI, Sloka%';
--   -- expect 36
--
-- DOWN (manual rollback — restores migration 1078's description):
--   BEGIN;
--   UPDATE asset_registry SET english_description =
--     '76 classical transit rules: 43 favourable, 26 unfavourable, and 7 double-transit rules from Phaladeepika Adh. XXVI (page-anchored) and Saravali/Jataka Parijata (double-transit). L0 repair 2026-09: re-cited off the refuted "BPHS Ch.29", corrected 3 Venus vedha pairs, inserted the missing Mercury 8th-house pair, marked 6 Rahu/Ketu rows honestly unsourced.'
--    WHERE asset_id = 'bg_transit_rules';
--   COMMIT;
-- =============================================================================
