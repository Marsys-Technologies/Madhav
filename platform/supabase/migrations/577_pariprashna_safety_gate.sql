-- Migration 577: pariprashna safety gate — SAFETY DECISIONS, REVIEWS, RETRACTIONS
-- Paripraśna P1 FOUNDATION, lane G1-A (PPR-12 · PPR-26 · MP §3.5.C) · 2026-08-19
--
-- ── WHY THIS EXISTS ────────────────────────────────────────────────────────────
-- SAFETY_PRIVACY_TENANCY_v0_1_PROPOSAL §0, verified 2026-08-18: "MP §3.5 is
-- binding governance. NONE OF IT IS ENFORCED AT THE SERVING LAYER TODAY. The
-- /api/pariprashna route contains no safety classifier, no mortality/self-harm
-- output gate... `ganita_ayurdaya_get` (longevity computation) is live on the
-- 125-tool MCP surface with no disclosure-class gate."
--
-- PPR-12 requires a SafetyPolicyGate that classifies every query BEFORE planning
-- and RECORDS ITS DECISION. A gate whose firing leaves no durable trace is not a
-- gate that can be audited, so the tables are the requirement, not bookkeeping
-- around it.
--
-- ── WHAT THIS MIGRATION ADDS (purely additive — seven NEW tables; no existing
--    table is altered, dropped, or re-typed) ────────────────────────────────────
--   1. `pariprashna_safety_decisions`            — the per-turn decision, hash-chained
--   2. `pariprashna_safety_reviews`              — HS-3/HS-4 review current state
--   3. `pariprashna_safety_review_passes`        — the two independent adversarial passes
--   4. `pariprashna_safety_review_events`        — append-only transition history
--   5. `pariprashna_safety_notifications`        — HS-2 cohort-native obligations
--   6. `pariprashna_predictive_samples`          — HS-6 §IS.8 sample pool
--   7. `pariprashna_retractions` (+ two child tables) — HS-5 retraction records
--
-- ── APPEND-ONLY, PER PPR-26 ────────────────────────────────────────────────────
-- "Safety decisions, retractions, and consent transitions MUST be written
-- append-only (INSERT-only grant or hash chain)." The INSERT-only grant depends
-- on the §7 role migration, which is lane G1-C. This lane therefore takes the
-- hash-chain option, exactly as G1-B did for consent: UPDATE/DELETE are blocked
-- by trigger on every append-only table here, and
-- `pariprashna_safety_decisions` additionally carries prev_hash/entry_hash that
-- `verifySafetyChain()` (src/lib/pariprashna/safety/audit.ts) re-derives link by
-- link — a real code path on which the integrity signal reads FALSE (§N.8).
--
-- `pariprashna_safety_reviews` is the one MUTABLE table here, deliberately: it
-- holds current state for convenience, and its history is the append-only
-- `_review_events` table. That is the same split G1-B used for
-- chart_subject_consent + chart_subject_consent_events.
--
-- ── WHAT NEVER ENTERS THESE TABLES ─────────────────────────────────────────────
-- The reader's question. §5's safe-logging rule ("audit logs reference content
-- by hash/id, never duplicate C1 bodies") and the question IS C1. Detections
-- carry a rule id and a sha256 of the matched span. There is no column here that
-- a query text could be written into, and that is a schema-level guarantee
-- rather than an application convention.
--
-- ── HASHING CONVENTION ─────────────────────────────────────────────────────────
-- sha256 hex over unit-separator (0x1F) joined canonical fields, IMPORTED from
-- `consent/hash_chain.ts` rather than re-implemented — one convention in the
-- Paripraśna surface, not two that can drift (§N.7 item 3).
--
-- ── FLAG-OFF ON ARRIVAL ────────────────────────────────────────────────────────
-- These tables exist but nothing writes them in production until
-- `PARIPRASHNA_SAFETY_GATE_ENABLED` is flipped ON
-- (platform/src/lib/config/feature_flags.ts, DEFAULT false). Applying this
-- migration is behavior-neutral: seven empty tables, zero writes.
--
-- Idempotent: every statement is IF NOT EXISTS / OR REPLACE. Safe to re-run.

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. pariprashna_safety_decisions — one row per turn, ALWAYS (PPR-12)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS pariprashna_safety_decisions (
  decision_id            UUID        PRIMARY KEY,
  chart_id               UUID        NOT NULL,
  turn_id                UUID        NOT NULL,
  -- Chain sequence, per chart. Serialized by an advisory lock in the writer.
  seq                    INTEGER     NOT NULL CHECK (seq >= 1),
  -- FALSE only when the flag was OFF: "no safety question was asked", which is
  -- NOT the same claim as "asked and found nothing" (§N.8).
  enforced               BOOLEAN     NOT NULL,
  classes_detected       TEXT[]      NOT NULL DEFAULT '{}',
  severity               TEXT        NOT NULL
                                     CHECK (severity IN ('none','advisory','review_required','hard_stop')),
  action                 TEXT        NOT NULL
                                     CHECK (action IN ('proceed','reframe','interstitial','seal_pending_signoff','hard_stop')),
  subject_kind           TEXT        NULL
                                     CHECK (subject_kind IS NULL OR subject_kind IN ('native_self','cohort','test')),
  -- Detections carry rule ids + sha256 span hashes. NEVER the matched text.
  detections             JSONB       NOT NULL DEFAULT '[]'::jsonb,
  evasion_markers        JSONB       NOT NULL DEFAULT '[]'::jsonb,
  excluded_capabilities  TEXT[]      NOT NULL DEFAULT '{}',
  llm_assist_ran         BOOLEAN     NOT NULL DEFAULT false,
  review_id              UUID        NULL,
  recorded_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  prev_hash              TEXT        NULL,
  entry_hash             TEXT        NOT NULL,

  CONSTRAINT pariprashna_safety_decisions_seq_uq UNIQUE (chart_id, seq),
  CONSTRAINT pariprashna_safety_decisions_genesis_chk
    CHECK ((seq = 1 AND prev_hash IS NULL) OR (seq > 1 AND prev_hash IS NOT NULL)),
  CONSTRAINT pariprashna_safety_decisions_hash_shape_chk
    CHECK (entry_hash ~ '^[0-9a-f]{64}$'),
  CONSTRAINT pariprashna_safety_decisions_detections_array_chk
    CHECK (jsonb_typeof(detections) = 'array'),
  -- A flag-OFF decision cannot claim to have classified anything.
  CONSTRAINT pariprashna_safety_decisions_unenforced_is_empty_chk
    CHECK (enforced OR (cardinality(classes_detected) = 0 AND action = 'proceed')),

  -- HARDENING ROUND, C-6: a SEALED READING MUST NAME ITS REVIEW.
  --
  -- The defect this closes: `reclassifyAfterPlan` (the PLAN-TIME escalation
  -- path) wrote its decision straight to this table without ever calling
  -- `openReview`. A turn that classified clean before planning and escalated
  -- after it therefore produced a `seal_pending_signoff` row with
  -- `review_id IS NULL` — no review record anywhere — while the reader was
  -- shown the acknowledgment that states "the review has been opened. Nothing
  -- has been discarded". There is no FK on `review_id`, so no query could find
  -- these; the reading was sealed and untracked and the user was told
  -- otherwise.
  --
  -- The application fix is in `gate.ts` (both paths now route through
  -- `openReviewForDecision`). This constraint is the part that makes the bug
  -- CLASS unrepresentable rather than merely fixed once: any future code path
  -- that seals without opening a review fails its INSERT loudly instead of
  -- writing a quiet lie into a hash-chained audit table.
  --
  -- Scoped to `enforced` rows because a flag-OFF row is `proceed` by the
  -- constraint above and can never reach these two actions anyway.
  CONSTRAINT pariprashna_safety_decisions_seal_requires_review_chk
    CHECK (action NOT IN ('seal_pending_signoff','interstitial') OR review_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS pariprashna_safety_decisions_chart_seq_idx
  ON pariprashna_safety_decisions (chart_id, seq);
CREATE INDEX IF NOT EXISTS pariprashna_safety_decisions_turn_idx
  ON pariprashna_safety_decisions (turn_id);
CREATE INDEX IF NOT EXISTS pariprashna_safety_decisions_action_idx
  ON pariprashna_safety_decisions (action) WHERE action <> 'proceed';

COMMENT ON TABLE pariprashna_safety_decisions IS
  'PPR-12. One row per Paripraśna turn — INCLUDING turns where nothing fired. '
  'A table holding only the turns that fired cannot answer "out of how many", '
  'and every rate this domain reports needs that denominator.';
COMMENT ON COLUMN pariprashna_safety_decisions.enforced IS
  'FALSE means the gate flag was OFF and NO classification ran. It is not a '
  'clean result; it is the absence of a check (CLAUDE.md §N.8).';
COMMENT ON COLUMN pariprashna_safety_decisions.detections IS
  'Array of {cls, severity, detector, rule, matched_span_hash, surface}. The '
  'matched TEXT is never stored — §5 safe-logging: audit rows reference C1 by '
  'hash, never duplicate it.';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 2-4. HS-3/HS-4 review: current state + passes + append-only event history
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS pariprashna_safety_reviews (
  review_id        UUID        PRIMARY KEY,
  chart_id         UUID        NOT NULL,
  turn_id          UUID        NOT NULL,
  state            TEXT        NOT NULL
                               CHECK (state IN (
                                 'seal_pending',
                                 'adversarial_pass_1_recorded',
                                 'adversarial_passes_complete',
                                 'released',
                                 'withheld',
                                 'interstitial_shown'
                               )),
  classes          TEXT[]      NOT NULL DEFAULT '{}',
  subject_kind     TEXT        NULL
                               CHECK (subject_kind IS NULL OR subject_kind IN ('native_self','cohort','test')),
  signed_off_by    TEXT        NULL,
  signed_off_at    TIMESTAMPTZ NULL,
  withheld_reason  TEXT        NULL,
  opened_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- MP §3.5.C: "double red-team AND explicit native sign-off" — two distinct
  -- controls, never collapsed. A released row MUST name its signer, at the DB
  -- level, so a release with no sign-off is not merely unlikely but impossible.
  CONSTRAINT pariprashna_safety_reviews_release_requires_signoff_chk
    CHECK (state <> 'released' OR (signed_off_by IS NOT NULL AND signed_off_at IS NOT NULL)),
  CONSTRAINT pariprashna_safety_reviews_withheld_requires_reason_chk
    CHECK (state <> 'withheld' OR withheld_reason IS NOT NULL),
  -- NCD-4/NCD-10: the interstitial exists ONLY for a proven native_self subject.
  --
  -- HARDENING ROUND, C-5 — THE NULL HOLE THIS USED TO HAVE.
  -- This constraint read `CHECK (state <> 'interstitial_shown' OR subject_kind
  -- = 'native_self')`. With `subject_kind IS NULL` the second disjunct is NULL,
  -- not FALSE, so the whole expression evaluates to NULL — and Postgres ACCEPTS
  -- a row whose CHECK is NULL. Reproduced against a scratch Postgres 15: the
  -- insert `('interstitial_shown', …, NULL)` succeeded.
  --
  -- That is not a theoretical hole. `subject_kind IS NULL` is TODAY'S DEFAULT:
  -- the consent lane returns null whenever SUBJECT_CONSENT_ENFORCEMENT is off,
  -- which it is. So the one row shape the constraint most needed to reject —
  -- "we never established who this subject is, show them the relaxed path
  -- anyway" — was the one shape it let through. The application layer
  -- (`interstitialApplies`) does get this right and treats null as not-proof;
  -- this constraint is supposed to be the reason that cannot be bypassed, and
  -- it was not.
  --
  -- `IS NOT DISTINCT FROM` is NULL-safe: it yields FALSE (never NULL) for a
  -- NULL left operand, so the disjunction is now three-valued-logic-proof.
  CONSTRAINT pariprashna_safety_reviews_interstitial_is_native_self_chk
    CHECK (state <> 'interstitial_shown' OR subject_kind IS NOT DISTINCT FROM 'native_self')
);

CREATE INDEX IF NOT EXISTS pariprashna_safety_reviews_state_idx
  ON pariprashna_safety_reviews (state) WHERE state IN ('seal_pending','adversarial_pass_1_recorded','adversarial_passes_complete');
CREATE INDEX IF NOT EXISTS pariprashna_safety_reviews_chart_idx
  ON pariprashna_safety_reviews (chart_id);

COMMENT ON TABLE pariprashna_safety_reviews IS
  'HS-3/HS-4 three-step path: seal-pending → two INDEPENDENT adversarial passes '
  '→ a SEPARATE sign-off. The CHECK constraints make "never collapsed" a '
  'database guarantee rather than an application convention.';

CREATE TABLE IF NOT EXISTS pariprashna_safety_review_passes (
  review_id            UUID        NOT NULL REFERENCES pariprashna_safety_reviews(review_id) ON DELETE RESTRICT,
  pass_ordinal         SMALLINT    NOT NULL CHECK (pass_ordinal IN (1,2)),
  reviewer_model_id    TEXT        NOT NULL,
  reviewer_context_id  TEXT        NOT NULL,
  verdict              TEXT        NOT NULL
                                   CHECK (verdict IN ('refuted','sustained','sustained_with_reservations')),
  findings             TEXT[]      NOT NULL DEFAULT '{}',
  recorded_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (review_id, pass_ordinal),
  -- The DETECTOR behind the word "independent": two passes on one review may not
  -- share a (model, context) pair. Honest about its limit — it cannot see through
  -- two aliases of one model, and the code comment says so.
  CONSTRAINT pariprashna_safety_review_passes_independence_uq
    UNIQUE (review_id, reviewer_model_id, reviewer_context_id)
);

COMMENT ON CONSTRAINT pariprashna_safety_review_passes_independence_uq
  ON pariprashna_safety_review_passes IS
  'HS-3 "two INDEPENDENT adversarial review passes (distinct models/contexts)". '
  'This is a real but WEAK detector: it rejects the same model+context twice, '
  'and cannot detect two names for one set of weights. Claimed no stronger.';

CREATE TABLE IF NOT EXISTS pariprashna_safety_review_events (
  event_id    BIGSERIAL   PRIMARY KEY,
  review_id   UUID        NOT NULL,
  from_state  TEXT        NULL,
  to_state    TEXT        NOT NULL,
  actor       TEXT        NOT NULL,
  payload     JSONB       NOT NULL DEFAULT '{}'::jsonb,
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS pariprashna_safety_review_events_review_idx
  ON pariprashna_safety_review_events (review_id, event_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- 5. pariprashna_safety_notifications — HS-2 cohort-native obligation
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS pariprashna_safety_notifications (
  notification_id UUID        PRIMARY KEY,
  chart_id        UUID        NOT NULL,
  turn_id         UUID        NOT NULL UNIQUE,
  decision_id     UUID        NOT NULL,
  reason          TEXT        NOT NULL,
  state           TEXT        NOT NULL DEFAULT 'pending'
                              CHECK (state IN ('pending','delivered','failed')),
  recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  delivered_at    TIMESTAMPTZ NULL,

  CONSTRAINT pariprashna_safety_notifications_delivered_ts_chk
    CHECK (state <> 'delivered' OR delivered_at IS NOT NULL)
);

COMMENT ON TABLE pariprashna_safety_notifications IS
  'HS-2 "native notified for cohort subjects". Rows are written in state '
  'pending. THERE IS NO DELIVERY TRANSPORT IN THIS CODEBASE YET — the obligation '
  'is durable and queryable, and marking it delivered without a delivery behind '
  'it would be exactly the §N.8 defect class. Carries NO question text.';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 6. pariprashna_predictive_samples — HS-6 §IS.8 sample pool
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS pariprashna_predictive_samples (
  sample_id                  UUID        PRIMARY KEY,
  chart_id                   UUID        NOT NULL,
  turn_id                    UUID        NOT NULL UNIQUE,
  prediction_candidate_count INTEGER     NOT NULL CHECK (prediction_candidate_count > 0),
  receipt_hash               TEXT        NULL,
  safety_classes             TEXT[]      NOT NULL DEFAULT '{}',
  state                      TEXT        NOT NULL DEFAULT 'pending_review'
                                         CHECK (state IN ('pending_review','reviewed','excluded')),
  sampled_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
  reviewed_at                TIMESTAMPTZ NULL,
  red_team_artifact_ref      TEXT        NULL,

  -- A sample marked reviewed MUST name the artifact that reviewed it. Without
  -- this the `reviewed` state would be a green signal with no detector.
  CONSTRAINT pariprashna_predictive_samples_reviewed_needs_artifact_chk
    CHECK (state <> 'reviewed' OR (red_team_artifact_ref IS NOT NULL AND reviewed_at IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS pariprashna_predictive_samples_pending_idx
  ON pariprashna_predictive_samples (sampled_at) WHERE state = 'pending_review';

COMMENT ON TABLE pariprashna_predictive_samples IS
  'HS-6 / MP §3.5.A.5. §IS.8 is a GOVERNANCE cadence with no runtime mechanism '
  'to wire into — this table is the half that was genuinely missing: the sample '
  'pool a red-team session draws from, and the record of which draws were '
  'reviewed. It makes the cadence''s input auditable; it cannot make the cadence run.';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 7. pariprashna_retractions — HS-5 (+ prediction notes, recipient obligations)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS pariprashna_retractions (
  retraction_id  UUID        PRIMARY KEY,
  chart_id       UUID        NOT NULL,
  turn_id        UUID        NOT NULL,
  receipt_hash   TEXT        NULL,
  scope          TEXT        NOT NULL
                             CHECK (scope IN ('whole_reading','specific_claim','prediction_only','calibration_language_only')),
  reason         TEXT        NOT NULL CHECK (length(btrim(reason)) > 0),
  evidence_ref   TEXT        NULL,
  initiated_by   TEXT        NOT NULL CHECK (length(btrim(initiated_by)) > 0),
  -- HS-5: "Retraction is a GOVERNANCE ACT (native-initiated or red-team-
  -- initiated), NOT an automated one." The CHECK is that sentence, enforced.
  initiator_kind TEXT        NOT NULL CHECK (initiator_kind IN ('native','red_team')),
  recorded_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS pariprashna_retractions_turn_idx
  ON pariprashna_retractions (turn_id, recorded_at);

COMMENT ON TABLE pariprashna_retractions IS
  'HS-5 reversibility (MP §3.5.A.6). APPEND-ONLY and receipt-linked: a '
  'retraction never edits the reading, it points at it — D-18 "corrections in '
  'place with the error visible". UPDATE/DELETE blocked by trigger.';

CREATE TABLE IF NOT EXISTS pariprashna_retraction_prediction_notes (
  retraction_id        UUID        NOT NULL REFERENCES pariprashna_retractions(retraction_id) ON DELETE RESTRICT,
  prediction_ledger_id TEXT        NOT NULL,
  noted_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (retraction_id, prediction_ledger_id)
);

COMMENT ON TABLE pariprashna_retraction_prediction_notes IS
  'HS-5 "a retraction note on any prediction ledger row the reading fed". A '
  'separate table rather than a column on the ledger: the ledger is C3 and is '
  'written by a different role (PPR-21/arm-3), so a safety-lane write into it '
  'would be a grant-wall violation. The join is the note.';

CREATE TABLE IF NOT EXISTS pariprashna_retraction_notifications (
  retraction_id    UUID        NOT NULL REFERENCES pariprashna_retractions(retraction_id) ON DELETE RESTRICT,
  disclosure_class TEXT        NOT NULL CHECK (disclosure_class IN ('cohort_subject','acharya_reviewer')),
  state            TEXT        NOT NULL DEFAULT 'pending' CHECK (state IN ('pending','delivered','failed')),
  recorded_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  delivered_at     TIMESTAMPTZ NULL,
  PRIMARY KEY (retraction_id, disclosure_class),
  CONSTRAINT pariprashna_retraction_notifications_delivered_ts_chk
    CHECK (state <> 'delivered' OR delivered_at IS NOT NULL)
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- 8. Append-only enforcement (PPR-26)
-- ═══════════════════════════════════════════════════════════════════════════════
-- A safety gate whose firing record is editable under the serving credential is
-- not "never invisible" (§5, verbatim). These triggers are the hash chain's
-- partner: the chain proves tampering happened, the trigger stops the ordinary
-- path from doing it at all.
--
-- `pariprashna_safety_reviews` is deliberately EXCLUDED — it is the mutable
-- current-state row whose history lives in `_review_events`. The delivery-state
-- columns on the two notification tables are likewise excluded, since a
-- delivery job must be able to move `pending` → `delivered`.

CREATE OR REPLACE FUNCTION pariprashna_safety_append_only_guard()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION
    'APPEND_ONLY_VIOLATION: % on % is blocked (PPR-26 — safety decisions and '
    'retractions are append-only; correct by appending, never by editing)',
    TG_OP, TG_TABLE_NAME
    USING ERRCODE = 'restrict_violation';
END;
$$;

DROP TRIGGER IF EXISTS trg_pariprashna_safety_decisions_append_only
  ON pariprashna_safety_decisions;
CREATE TRIGGER trg_pariprashna_safety_decisions_append_only
  BEFORE UPDATE OR DELETE ON pariprashna_safety_decisions
  FOR EACH ROW EXECUTE FUNCTION pariprashna_safety_append_only_guard();

DROP TRIGGER IF EXISTS trg_pariprashna_safety_review_events_append_only
  ON pariprashna_safety_review_events;
CREATE TRIGGER trg_pariprashna_safety_review_events_append_only
  BEFORE UPDATE OR DELETE ON pariprashna_safety_review_events
  FOR EACH ROW EXECUTE FUNCTION pariprashna_safety_append_only_guard();

DROP TRIGGER IF EXISTS trg_pariprashna_safety_review_passes_append_only
  ON pariprashna_safety_review_passes;
CREATE TRIGGER trg_pariprashna_safety_review_passes_append_only
  BEFORE UPDATE OR DELETE ON pariprashna_safety_review_passes
  FOR EACH ROW EXECUTE FUNCTION pariprashna_safety_append_only_guard();

DROP TRIGGER IF EXISTS trg_pariprashna_retractions_append_only
  ON pariprashna_retractions;
CREATE TRIGGER trg_pariprashna_retractions_append_only
  BEFORE UPDATE OR DELETE ON pariprashna_retractions
  FOR EACH ROW EXECUTE FUNCTION pariprashna_safety_append_only_guard();

DROP TRIGGER IF EXISTS trg_pariprashna_retraction_prediction_notes_append_only
  ON pariprashna_retraction_prediction_notes;
CREATE TRIGGER trg_pariprashna_retraction_prediction_notes_append_only
  BEFORE UPDATE OR DELETE ON pariprashna_retraction_prediction_notes
  FOR EACH ROW EXECUTE FUNCTION pariprashna_safety_append_only_guard();

-- ── ROLLBACK (manual; NOT executed by this file) ───────────────────────────────
--   DROP TRIGGER IF EXISTS trg_pariprashna_retraction_prediction_notes_append_only
--     ON pariprashna_retraction_prediction_notes;
--   DROP TRIGGER IF EXISTS trg_pariprashna_retractions_append_only ON pariprashna_retractions;
--   DROP TRIGGER IF EXISTS trg_pariprashna_safety_review_passes_append_only
--     ON pariprashna_safety_review_passes;
--   DROP TRIGGER IF EXISTS trg_pariprashna_safety_review_events_append_only
--     ON pariprashna_safety_review_events;
--   DROP TRIGGER IF EXISTS trg_pariprashna_safety_decisions_append_only
--     ON pariprashna_safety_decisions;
--   DROP FUNCTION IF EXISTS pariprashna_safety_append_only_guard();
--   DROP TABLE IF EXISTS pariprashna_retraction_notifications;
--   DROP TABLE IF EXISTS pariprashna_retraction_prediction_notes;
--   DROP TABLE IF EXISTS pariprashna_retractions;
--   DROP TABLE IF EXISTS pariprashna_predictive_samples;
--   DROP TABLE IF EXISTS pariprashna_safety_notifications;
--   DROP TABLE IF EXISTS pariprashna_safety_review_events;
--   DROP TABLE IF EXISTS pariprashna_safety_review_passes;
--   DROP TABLE IF EXISTS pariprashna_safety_reviews;
--   DROP TABLE IF EXISTS pariprashna_safety_decisions;
