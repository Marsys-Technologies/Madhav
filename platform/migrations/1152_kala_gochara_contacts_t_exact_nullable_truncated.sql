-- Migration 1152: kala_gochara_contacts.t_exact nullable — N3 truncated
--                 contacts are kept, never dropped (Pravāha A2.1, step
--                 truncated_contacts_kept; reworked after the A2.2 review).
-- Created: 2026-09-30. Author: pravaha/a2-kernel-geometry (Stream A, A2.1).
--
-- Numbering: 1152 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4). Verified free by a fresh scan of every origin/* ref across
-- BOTH platform/migrations/ and platform/supabase/migrations/ (2026-09-30:
-- max in use is 1151; no 1152 anywhere); `npm run guard:migration-numbers`
-- green on this branch.
--
-- What this fixes: migration 1081 created kala_gochara_contacts with
-- t_exact NOT NULL. That made a contact whose exact centre lies outside the
-- requested horizon (N3 — a truncated span whose presence inside the horizon
-- is real and observed) unpersistable, and step06 dropped such episodes as
-- if absent. Oracle O-SS-3 requires the opposite: the contact is kept with
-- NO fabricated t_exact and its truncation mark. Identity for a no-exact row
-- is the floored t_in (ids.contact_id t_fallback rule, marked as a
-- substitution inside the payload so it can never collide with an exact
-- contact at the same minute). NOTE (A2.2 scope ruling): the full §6.1
-- physical-identity contract (physical tuple, occurrence ordinals,
-- truncated→exact enrichment lineage) is A5.3/A5.1 registered-writer scope
-- and is deliberately NOT claimed here.
--
-- Also widened: truncated_at_horizon's CHECK now admits 'both' (a span
-- clipped at BOTH horizon edges). This is a value-domain EXTENSION for a
-- state the kernel has always produced and previously had to erase to NULL
-- (Kimi review #2: one physical span must carry one truncation mark on both
-- of its rows); no protective invariant is weakened — the anti-fabrication
-- CHECK below is added in the same migration.
--
-- Guard added, none weakened: exact_crossing must agree with t_exact's
-- nullability — a row claiming an exact crossing must carry the instant; a
-- truncated row must not carry one (a non-NULL t_exact on a no-exact row
-- would BE the fabrication this migration exists to prevent).
--
-- Scope (corrected per the A2.2 reviews): kala_gochara_contacts holds the
-- PUBLISHED '4.0' rows as well as candidates — the new CHECK therefore
-- applies to existing rows. Whether existing rows satisfy it is NOT inferred
-- from 1081's NOT NULL (t_exact NOT NULL does not prove exact_crossing=true);
-- it is PROVEN by the read-only preflight beside this file
-- (scripts/kala_gochara_cutover/preflight_1152_existing_rows_satisfy_check.sql),
-- which is a REQUIRED pre-application check: it must return zero rows on
-- production before this migration is applied. The protected 'v1'/'3.0'
-- corpus lives in kala_gochara_windows and is untouched. Null-exact and
-- residence rows are produced only for candidate generations >= '4.1'
-- (producer gate in step06_enumerate_episodes.candidate_keeps_candidate_only_rows).
--
-- Operational properties (corrected per the A2.2 closure check):
--   * SINGLE-RUN: the tracked runner (migrate.ts) skips applied migrations;
--     the SQL itself is NOT replay-idempotent — a second run fails at ADD
--     CONSTRAINT (the name already exists). Never apply it by hand twice.
--   * ONE TRANSACTION, BLOCKING WHILE HELD: migrate.ts executes the whole
--     file in a single transaction, so the ACCESS EXCLUSIVE lock taken by the
--     ALTER TABLEs is held through VALIDATE CONSTRAINT until commit — this
--     migration blocks writes (and, on ACCESS EXCLUSIVE, reads of the table)
--     for its full duration. No "brief lock then nonblocking validation"
--     split exists here; duration depends on the table's row volume at
--     application time, which is measured by ops, not asserted here.
--   * Bounded application: the SET LOCAL statements below bound lock waiting
--     and statement time inside the runner's transaction; on lock_timeout
--     the transaction aborts cleanly (nothing applied — rerun after the
--     table is quiet).
--   * IRREVERSIBLE IN PRACTICE: once truncated (t_exact NULL) rows exist,
--     restoring NOT NULL would require deleting exactly the rows this
--     migration exists to keep — i.e. recreating the N3 absence-fabrication.
--     There is no rollback that preserves the new data; the only honest
--     reversal is a scoped Clear of the candidate generation that owns them
--     (plan §6.4), never a row delete under a published label.
--
-- Applied through migrate.ts (transactional runner — no BEGIN/COMMIT here).

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

ALTER TABLE kala_gochara_contacts
  ALTER COLUMN t_exact DROP NOT NULL;

ALTER TABLE kala_gochara_contacts
  ADD CONSTRAINT kgc_t_exact_iff_exact_crossing
  CHECK (exact_crossing = (t_exact IS NOT NULL)) NOT VALID;

ALTER TABLE kala_gochara_contacts
  VALIDATE CONSTRAINT kgc_t_exact_iff_exact_crossing;

ALTER TABLE kala_gochara_contacts
  DROP CONSTRAINT kala_gochara_contacts_truncated_at_horizon_check;

ALTER TABLE kala_gochara_contacts
  ADD CONSTRAINT kala_gochara_contacts_truncated_at_horizon_check
  CHECK (truncated_at_horizon IN ('start','end','both') OR truncated_at_horizon IS NULL) NOT VALID;

ALTER TABLE kala_gochara_contacts
  VALIDATE CONSTRAINT kala_gochara_contacts_truncated_at_horizon_check;
