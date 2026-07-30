-- Migration 486: brahma_mimamsa_prediction_ledger.message_part_id → ON DELETE SET NULL
-- =============================================================================
-- Campaign: SAMĀPTI · lane A4-LOOP-G1 · governing spec BRIEF_PB-3.1_MAKE_THE_LOOP_LIVE.md G1
--
-- Migration number: 486, REASSIGNED from the authored 474 by the Integrator at MERGE-LOCK
-- acquisition per SAMĀPTI conductor manual §5, exactly as this header's prior revision
-- instructed. Recomputed fresh from `origin/main` @ 0d919718 on 2026-07-30:
--     max(platform/migrations/)          = 474  (474_asset_throughput_incomplete_state.sql)
--     max(platform/supabase/migrations/) = 485  (485_bg_parihara_rules.sql)
--     => next free across BOTH dirs      = 486
-- The authored 474 did NOT hold: ṢAḌ-DARŚANA landed 474–485 while this lane was in flight,
-- and 474 is now occupied in platform/migrations/. No open PR holds 484–499, so 486 is free.
-- (Note for future readers: 484 is duplicated on main — 484_bg_muhurta_lattice.sql and
-- 484_bg_synthetic_cohort_md.sql both exist. That collision predates this lane and is not
-- corrected here; it is reported separately rather than silently renumbered by this PR.)
--
-- ── WHY ─────────────────────────────────────────────────────────────────────────────────
-- Migration 470 declared the FK with no ON DELETE action, i.e. the SQL default NO ACTION:
--
--     message_part_id  uuid REFERENCES message_parts(id)
--
-- That was harmless only while the ledger was EMPTY. PB-3.1 G1 makes the Paripraśna reading
-- route write a `detected` ledger row per candidate at turn-commit, so ledger rows now really
-- do reference `message_parts`. And the canonical turn writer
-- (`src/lib/pariprashna/store/writer.ts`, PB-2 lane M-2) rebuilds a turn's parts with
-- DELETE-then-INSERT:
--
--     DELETE FROM message_parts WHERE message_id = $1
--
-- With NO ACTION, that DELETE raises an FK violation the moment any of the turn's candidates
-- has a ledger row — which would abort the whole `writeTurn` transaction and LOSE THE TURN.
-- This is not hypothetical: it was reproduced as a hard failure by
-- `tests/pariprashna/samiksha/capture_turn_commit.db.test.ts`'s idempotency case against a
-- real Postgres before this migration existed:
--
--     error: update or delete on table "message_parts" violates foreign key constraint
--     "brahma_mimamsa_prediction_ledger_message_part_id_fkey"
--     on table "brahma_mimamsa_prediction_ledger"
--
-- ── WHY *SET NULL* AND NOT CASCADE ──────────────────────────────────────────────────────
-- CASCADE would be a data-integrity disaster: rewriting a turn's parts would silently DELETE
-- the human's confirmed prediction — including its committed confidence band, its copied D-16
-- stamp, and any recorded outcome. A ledger row is a HUMAN-OWNED historical claim; the whole
-- point of the Samīkṣā loop is that such a claim, once made, cannot quietly disappear.
--
-- SET NULL keeps the claim and drops only the turn ANCHOR. The schema already treats a null
-- `message_part_id` as a first-class, documented case — `review.ts`'s `resolveTurnAnchors`
-- says so explicitly: "Rows with no `message_part_id` (W-6 scripted / backfilled claims)
-- simply have no anchor." So the degraded state is one the review surface already renders
-- correctly (the "view source turn" link is simply absent), not a new broken shape.
--
-- Honest cost, stated rather than hidden: if a turn is ever rewritten, a prediction captured
-- from it loses its deep link back to the utterance. That is strictly better than the two
-- alternatives (lose the claim; or fail the reader's turn), and it is recoverable — the claim
-- text itself is preserved verbatim on the row.
--
-- Idempotent: drops the constraint by name if present, then re-adds it with the action.

BEGIN;

ALTER TABLE brahma_mimamsa_prediction_ledger
  DROP CONSTRAINT IF EXISTS brahma_mimamsa_prediction_ledger_message_part_id_fkey;

ALTER TABLE brahma_mimamsa_prediction_ledger
  ADD CONSTRAINT brahma_mimamsa_prediction_ledger_message_part_id_fkey
  FOREIGN KEY (message_part_id) REFERENCES message_parts(id) ON DELETE SET NULL;

COMMENT ON COLUMN brahma_mimamsa_prediction_ledger.message_part_id IS
  'FK → message_parts(id), the originating `prediction_candidate` part. ON DELETE SET NULL: '
  'rewriting a turn must never delete a human-owned claim, so the anchor is dropped and the '
  'claim kept (migration 486). NULL is a documented, renderable state (W-6 scripted claims).';

COMMIT;

-- DOWN (manual rollback — this project has no automated down-migration runner; listed for
-- audit + local throwaway-DB rollback testing only):
-- BEGIN;
-- ALTER TABLE brahma_mimamsa_prediction_ledger
--   DROP CONSTRAINT IF EXISTS brahma_mimamsa_prediction_ledger_message_part_id_fkey;
-- ALTER TABLE brahma_mimamsa_prediction_ledger
--   ADD CONSTRAINT brahma_mimamsa_prediction_ledger_message_part_id_fkey
--   FOREIGN KEY (message_part_id) REFERENCES message_parts(id);
-- COMMIT;
