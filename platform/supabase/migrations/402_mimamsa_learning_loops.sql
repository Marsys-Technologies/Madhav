-- Migration 402: mimamsa learning loops — BA-P7B portal feedback surfaces
-- Three tables for the five portal learning loops (Steps 1–5).
-- NO path from mimamsa_resonance_feedback to priors/lifts/tradition-weights (QUARANTINE).

BEGIN;

-- ── 0. mimamsa_adjudication_log — Step 1 ask-card outcomes ──────────────────
-- Records native one-tap verdicts for UNRESOLVED closed prediction windows.
-- Referenced by mi_abhilekha resync to update mimamsa_calibration.

CREATE TABLE IF NOT EXISTS mimamsa_adjudication_log (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id        UUID        NOT NULL,
    prediction_id   TEXT        NOT NULL,
    outcome         TEXT        NOT NULL
                    CHECK (outcome IN ('happened', 'partial', 'didnt', 'cant_say')),
    verdict_mapped  TEXT        NOT NULL
                    CHECK (verdict_mapped IN ('CONFIRMED', 'PARTIAL', 'REFUTED', 'UNRESOLVED')),
    adjudicator_uid TEXT        NOT NULL,
    adjudicated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (chart_id, prediction_id)
);

COMMENT ON TABLE mimamsa_adjudication_log IS
  'BA-P7B Step 1: native one-tap outcomes for UNRESOLVED closed prediction windows. '
  'mi_abhilekha resync reads this table to update mimamsa_calibration verdict.';

CREATE INDEX IF NOT EXISTS idx_adjudication_chart ON mimamsa_adjudication_log(chart_id);

-- ── 1. prashna_followup_schedule — Loop B follow-up asks ─────────────────────
-- Every Q4 undertaking/election verdict auto-schedules a follow-up ask.
-- At fructification date, portal surfaces a one-tap outcome card.
-- Outcome flows to mi_pramana as prospective evidence.

CREATE TABLE IF NOT EXISTS prashna_followup_schedule (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id            UUID        NOT NULL,
    prediction_id       TEXT        NOT NULL,
    domain              TEXT        NOT NULL,
    composite_score     DOUBLE PRECISION,
    fructification_date DATE        NOT NULL,
    follow_up_prompt    TEXT        NOT NULL,
    status              TEXT        NOT NULL DEFAULT 'scheduled'
                        CHECK (status IN ('scheduled', 'sent', 'answered', 'expired')),
    answered_at         TIMESTAMPTZ,
    outcome             TEXT        CHECK (outcome IN ('happened', 'partial', 'didnt', 'cant_say')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (chart_id, prediction_id)
);

COMMENT ON TABLE prashna_followup_schedule IS
  'BA-P7B Loop B: auto-scheduled follow-up asks from Q4 prashna verdicts. '
  'Portal surfaces a one-tap outcome card at fructification_date. '
  'Outcome flows to mi_pramana as prospective evidence (not retrodiction).';

CREATE INDEX IF NOT EXISTS idx_prashna_followup_chart ON prashna_followup_schedule(chart_id);
CREATE INDEX IF NOT EXISTS idx_prashna_followup_status ON prashna_followup_schedule(status, fructification_date);

-- ── 2. mimamsa_snapshot_cosign — Step 4 native co-sign surface ───────────────
-- The native's retrospective veto over Pratinidhi-proposed calibration snapshots.
-- Two-key protocol: Pratinidhi proposes (key-1), native approves/revokes (key-2).

CREATE TABLE IF NOT EXISTS mimamsa_snapshot_cosign (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_id         TEXT        NOT NULL,
    chart_id            UUID        NOT NULL,
    action              TEXT        NOT NULL CHECK (action IN ('approved', 'revoked')),
    cosigner_uid        TEXT        NOT NULL,
    cosigned_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    judgment_ledger_ref TEXT,
    notes               TEXT,
    UNIQUE (snapshot_id, action)
);

COMMENT ON TABLE mimamsa_snapshot_cosign IS
  'BA-P7B Step 4: native retrospective co-sign (approve/revoke) of calibration snapshots '
  'proposed by Pratinidhi. Fulfils two-key protocol charter promise. '
  'cosigner_uid = native Firebase UID; judgment_ledger_ref links to JL entry.';

CREATE INDEX IF NOT EXISTS idx_mimamsa_cosign_snapshot ON mimamsa_snapshot_cosign(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_mimamsa_cosign_chart ON mimamsa_snapshot_cosign(chart_id);

-- ── 3. mimamsa_resonance_feedback — Step 5 QUARANTINED resonance capture ──────
-- Reading feedback (resonates / doesn't) stored here ONLY.
-- STRUCTURAL QUARANTINE: this table has NO FK to any weight/prior/calibration table.
-- Flows ONLY to manifestation-grammar presentation emphasis (S4).
-- A dependency check in platform/scripts/check-resonance-quarantine.ts proves this.

CREATE TABLE IF NOT EXISTS mimamsa_resonance_feedback (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id            UUID        NOT NULL,
    signal_ref          TEXT        NOT NULL,
    domain              TEXT,
    resonance           TEXT        NOT NULL CHECK (resonance IN ('resonates', 'doesnt_resonate', 'neutral')),
    context_note        TEXT,
    captured_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    session_id          TEXT,
    -- QUARANTINE: no columns referencing priors, lifts, tradition-weights, or calibration
    -- See: platform/scripts/check-resonance-quarantine.ts for structural proof
    CONSTRAINT quarantine_marker CHECK (true)
);

COMMENT ON TABLE mimamsa_resonance_feedback IS
  'BA-P7B Step 5 QUARANTINED: resonance feedback (resonates/doesnt) for presentation '
  'emphasis (S4 manifestation-grammar) ONLY. '
  'NO FK to priors, lifts, tradition_weights, brahma_class_priors, or mimamsa_calibration. '
  'Structural quarantine proven by platform/scripts/check-resonance-quarantine.ts.';

CREATE INDEX IF NOT EXISTS idx_mimamsa_resonance_chart ON mimamsa_resonance_feedback(chart_id);
CREATE INDEX IF NOT EXISTS idx_mimamsa_resonance_signal ON mimamsa_resonance_feedback(signal_ref);

COMMIT;
