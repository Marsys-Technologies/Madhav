-- Migration 1152: kala_gochara_contacts.t_exact nullable — N3 truncated
--                 contacts are kept, never dropped (Pravāha A2.1, step
--                 truncated_contacts_kept).
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
-- if absent. GOCHARA_DESIGN_SPECS_v1_4 §6.1/§6.2 invariant 2 and oracle
-- O-SS-3 require the opposite: the contact keeps its identity with
-- coverage.truncated=true and NO fabricated t_exact. Identity for a no-exact
-- row is the floored t_in (ids.contact_id t_fallback rule, marked as a
-- substitution inside the payload so it can never collide with an exact
-- contact at the same minute).
--
-- Guard added, none weakened: exact_crossing must agree with t_exact's
-- nullability — a row claiming an exact crossing must carry the instant; a
-- truncated row must not carry one (a non-NULL t_exact on a no-exact row
-- would BE the fabrication this migration exists to prevent).
--
-- Scope: kala_gochara_contacts holds candidate '4.x' generations only; the
-- protected 'v1'/'3.0' corpus lives in kala_gochara_windows and is untouched.
-- Existing rows (all exact) satisfy the new CHECK trivially. Applied through
-- migrate.ts (transactional runner — no BEGIN/COMMIT here).

ALTER TABLE kala_gochara_contacts
  ALTER COLUMN t_exact DROP NOT NULL;

ALTER TABLE kala_gochara_contacts
  ADD CONSTRAINT kgc_t_exact_iff_exact_crossing
  CHECK (exact_crossing = (t_exact IS NOT NULL)) NOT VALID;

ALTER TABLE kala_gochara_contacts
  VALIDATE CONSTRAINT kgc_t_exact_iff_exact_crossing;
