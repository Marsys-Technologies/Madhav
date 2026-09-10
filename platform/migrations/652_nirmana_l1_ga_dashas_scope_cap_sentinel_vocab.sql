-- 652_nirmana_l1_ga_dashas_scope_cap_sentinel_vocab.sql
--
-- NIRMĀṆA v2.1 · L1 Gaṇita · F-A10 (L1_W1_ANALYSIS_BATCH_A.md; route recorded
-- in L1_W2_DECIDE_v1_0.md §2.1: `ga_dashas` is `changed`, this is one of its
-- two named MUST fixes alongside F-A12).
--
-- THE FINDING: `write_dasha_scope_cap_sentinels()` writes two documented
-- "intentionally not computed" placeholder rows (Prana Dasha 5th level; KP
-- sub-period levels beyond sub_sub) with `verification_pass_status =
-- 'scope_cap_sentinel'`. That literal is not in `chart_dashas`'s CHECK
-- constraint (`two_pass_verified | classical_match | divergent_flagged |
-- single`), so EVERY sentinel write violates it -- confirmed live before
-- writing this migration: 0 rows with `system_id = 'scope_cap'` on all three
-- built charts, despite the writer having run on all three. The Prana row
-- separately violates `cd_level_n_max4` (`level_n` capped at 4; Prana is
-- level 5) -- a savepoint fix (2026-08-06, SD-DASHA-1) already made that
-- failure non-fatal to the rest of the build, but deliberately left it
-- unresolved: representing a 5th level inside a 1-4 domain is a semantic
-- question reserved for the native, not a vocabulary gap. This migration
-- fixes only the KP row's failure, which IS a vocabulary gap -- the KP
-- sentinel's own `level_n = 4` already satisfies `cd_level_n_max4`.
--
-- WHY A NEW VOCABULARY VALUE, NOT ONE OF THE FOUR EXISTING TIERS: none of
-- `two_pass_verified` / `classical_match` / `divergent_flagged` / `single`
-- mean "not computed, out of scope" -- they are all real-computation quality
-- tiers, and asserting one of them for a placeholder row would be exactly
-- the false verification claim §N.8 forbids (a scope-cap sentinel was never
-- computed once, let alone twice or classically matched). `scope_cap_sentinel`
-- is a distinct, honest fifth category: not a stronger or weaker computation,
-- a documented absence of one.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

ALTER TABLE chart_dashas
  DROP CONSTRAINT chart_dashas_verification_pass_status_check;

ALTER TABLE chart_dashas
  ADD CONSTRAINT chart_dashas_verification_pass_status_check
  CHECK (verification_pass_status = ANY (ARRAY[
    'two_pass_verified'::text,
    'classical_match'::text,
    'divergent_flagged'::text,
    'single'::text,
    'scope_cap_sentinel'::text
  ]));

-- ---------------------------------------------------------------------------
-- Verify against the LIVE constraint definition (pg_get_constraintdef), not a
-- literal restating what this file just wrote -- a self-check against its own
-- assumption would pass even if the ALTER above silently no-opped or the
-- constraint were renamed/dropped by something else in the same deploy.
-- ---------------------------------------------------------------------------
DO $$
DECLARE
  live_def text;
BEGIN
  SELECT pg_get_constraintdef(oid) INTO live_def
    FROM pg_constraint
   WHERE conrelid = 'chart_dashas'::regclass
     AND conname = 'chart_dashas_verification_pass_status_check';

  IF live_def IS NULL THEN
    RAISE EXCEPTION 'migration 652: chart_dashas_verification_pass_status_check does not exist after the ALTER -- rewrite failed';
  END IF;
  IF live_def NOT LIKE '%scope_cap_sentinel%' THEN
    RAISE EXCEPTION 'migration 652: live constraint definition does not admit scope_cap_sentinel -- got: %', live_def;
  END IF;
  IF live_def NOT LIKE '%two_pass_verified%' OR live_def NOT LIKE '%classical_match%'
     OR live_def NOT LIKE '%divergent_flagged%' OR live_def NOT LIKE '%single%' THEN
    RAISE EXCEPTION 'migration 652: rewrite dropped one of the four pre-existing tiers -- got: %', live_def;
  END IF;
END $$;
