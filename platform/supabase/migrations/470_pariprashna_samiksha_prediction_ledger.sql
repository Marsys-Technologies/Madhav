-- Migration 470: brahma_mimamsa_prediction_ledger — PB-3 (SAMĪKṢĀ) lane L-1
-- Created: 2026-07-28
--
-- Numbering note: highest numbered file across BOTH migration dirs combined is 469
-- (supabase/migrations/469_phala_phaladesa_narration_model_allowlist_drift.sql). 470 is
-- the next free number. This dir (platform/supabase/migrations) is the ACTIVE migration
-- directory; migrate.ts reads it plus the legacy platform/migrations and de-duplicates by
-- filename.
--
-- Context: Paripraśna Build campaign wave PB-3 lane L-1 ("the ledger schema"). Creates the
-- fresh conversational prediction ledger the OT-11 reconciliation ruling (MEMO_PB-3_0)
-- fixed by name: `brahma_mimamsa_prediction_ledger` — the exact name §14.3 always
-- specified but no live table satisfied. This is the ONLY table the conversational
-- prediction loop (detect → confirm → track → resolve) writes to from PB-3 onward.
-- See LEDGER_MAP_PB-3.md for why this table exists and how it differs from
-- mimamsa_predictions / mcp_predictions / brahma_prospective_ledger.
--
-- The full §14.3/§14.2 field set is present FROM ROW ONE (per L-1's charge): a Brier-ready
-- numeric confidence (numrange — NEVER text; that was the X-5 lesson mcp_predictions
-- embodied), a daterange window, the D-16 provenance stamp COPIED (never FK'd/joined) at
-- confirmation time, co-located outcome columns, and the lifecycle state set.
--
-- ── LIFECYCLE STATES ────────────────────────────────────────────────────────────────────
-- BRIEF_PB-3 §F1 labels this an "8-state lifecycle" but its own prose then names NINE
-- distinct state tokens:
--   detected → confirmed → open → window_closed → outcome_recorded   (5 progression states)
--   exits: dismissed / lapsed / unverifiable                          (3 exit states)
--   + lapsed_unconfirmed                                              (1 candidate-aging state)
-- = 9 tokens. The "8-state" label is the brief's shorthand (it counts the progression + the
-- three standard exits and treats `lapsed_unconfirmed` as the aging-out marker layered on
-- top, per W-1). We enumerate ALL NINE in the CHECK constraint: omitting any single named
-- token would break a consuming lane (L-2 writes `detected` and ages candidates to
-- `lapsed_unconfirmed` per W-1; L-4 moves `open`→`window_closed`; L-3/L-5 resolve to
-- `outcome_recorded`/`unverifiable`; dismissal → `dismissed`; unresolved-after-close →
-- `lapsed`). The legal TRANSITION matrix between these states is the DAL's single source of
-- truth (platform/src/lib/pariprashna/samiksha/transitions.ts) — this CHECK gates the enum
-- domain only, not the transitions.
--
-- ── IMMUTABILITY ────────────────────────────────────────────────────────────────────────
-- A confirmed ledger row is an immutable historical claim (D-16(d)). The BEFORE-UPDATE
-- trigger `trg_bmpl_freeze_confirmed` forbids any UPDATE that would change the copied stamp
-- fields (build_id, priors_version, formula_versions, ranking_config, now_context_date) OR
-- the settled claim fields (claim_text, domain, "window", confidence, direction) once the
-- row has advanced past `detected`. Lifecycle progression and outcome recording remain
-- mutable (that is the whole point of the ledger); only the historical claim + its stamp are
-- frozen. A `detected` candidate row is still editable (the pre-confirmation edit path).
--
-- ── count_sql / asset_registry ──────────────────────────────────────────────────────────
-- This table is DELIBERATELY NOT registered in asset_registry. asset_registry's `layer`
-- CHECK admits only the six build layers (brahmagyan..mimamsa) and its rows describe
-- orchestrator-built, per-chart chart assets whose count_sql the cockpit stats route reads.
-- This is a conversational ledger that accretes from confirmed chat predictions — it is not
-- built by a WriterBase in the build DAG, so classifying it under a build layer would
-- misrepresent it. This follows the established precedent of every prior Paripraśna /
-- conversational table (migrations 458 brahma_prospective_ledger, 467 message_parts, 468
-- conversation_summaries) — none register in asset_registry. The §N.4 "cockpit truth"
-- count_sql intent is honored two ways instead: (a) the canonical chart-scoped count query
-- is recorded as a table COMMENT below; (b) the DAL exposes countLedgerRows(chartId).
--   count_sql (canonical): SELECT count(*) FROM brahma_mimamsa_prediction_ledger WHERE chart_id = $1
--
-- ADDITIVE-ONLY: this migration only CREATEs a new table, its indexes, and its trigger.
-- It touches no existing table or row. Idempotent (IF NOT EXISTS / CREATE OR REPLACE /
-- DROP TRIGGER IF EXISTS before CREATE TRIGGER). Safe to re-run.

BEGIN;

CREATE TABLE IF NOT EXISTS brahma_mimamsa_prediction_ledger (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Identity / linkage
  chart_id              uuid NOT NULL,
  -- FK → PB-2's canonical message_parts.id (the prediction_candidate part the claim was
  -- detected on). NULLABLE: a W-6 scripted/forced gate claim, or a backfilled claim, may
  -- have no originating part. ON DELETE RESTRICT (default) — a ledger row outlives casual
  -- part deletion; the historical claim must not be silently orphaned-and-dropped.
  message_part_id       uuid REFERENCES message_parts(id),

  -- ── Settled claim core (immutable once the row is past `detected`) ──
  claim_text            text NOT NULL,
  domain                text,
  -- daterange, per §14.3 ("window daterange") — one range column, never two loose dates.
  "window"              daterange,
  -- numrange, per §14.3 ("confidence numrange") — Brier-ready. NEVER text (the X-5 lesson:
  -- mcp_predictions' text-enum confidence was Brier-unusable). NULLABLE until the confirm
  -- step elicits a probability (§14.3: "Confirm elicits a probability if none stated").
  confidence            numrange,
  direction             text,

  -- ── Grounding / provenance references ──
  technique_refs        text[]  NOT NULL DEFAULT '{}',
  grounding_fact_ids    text[]  NOT NULL DEFAULT '{}',
  created_from_channel  text    NOT NULL DEFAULT 'pariprashna',

  -- ── Lifecycle (see header; 9 tokens, "8-state" label) ──
  lifecycle_status      text    NOT NULL DEFAULT 'detected'
                          CHECK (lifecycle_status IN (
                            'detected',
                            'confirmed',
                            'open',
                            'window_closed',
                            'outcome_recorded',
                            'dismissed',
                            'lapsed',
                            'unverifiable',
                            'lapsed_unconfirmed'
                          )),

  -- ── D-16 provenance stamp, COPIED at confirmation time (never a live FK/join) ──
  -- These five mirror TurnProvenanceStamp (platform/src/lib/pariprashna/provenance/stamp.ts,
  -- PB-2 lane M-6). getLastTurnStamp() is read at confirmation and its values are snapshotted
  -- here. They are frozen by trg_bmpl_freeze_confirmed once the row is past `detected`.
  build_id              text,
  priors_version        text,
  formula_versions      jsonb,
  ranking_config        jsonb,
  now_context_date      date,
  stamp_copied_at       timestamptz,   -- audit: when the stamp snapshot was taken

  -- ── Outcome (co-located; Brier inputs) ──
  -- outcome: the qualitative resolution. 'unverifiable' is the Brier-EXCLUDED marker.
  outcome               text
                          CHECK (outcome IS NULL OR outcome IN (
                            'happened', 'did_not_happen', 'partial', 'unverifiable'
                          )),
  -- outcome_value: the numeric Brier input in [0,1] paired against the stated `confidence`
  -- to compute (confidence − outcome)². 1.0 = happened, 0.0 = did-not, fractional = partial.
  -- MUST be NULL when the outcome is 'unverifiable' (Brier-excluded) — enforced below. L-5
  -- consumes this to compute Brier; L-1 only guarantees the schema supports it cleanly.
  outcome_value         numeric
                          CHECK (outcome_value IS NULL OR (outcome_value >= 0 AND outcome_value <= 1)),
  outcome_note          text,
  outcome_recorded_at   timestamptz,

  -- Brier-exclusion integrity: an 'unverifiable' outcome carries no numeric value.
  CONSTRAINT bmpl_unverifiable_has_no_value
    CHECK (outcome IS DISTINCT FROM 'unverifiable' OR outcome_value IS NULL),

  -- ── Bookkeeping ──
  confirmed_at          timestamptz,
  dismissed_reason      text,
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE brahma_mimamsa_prediction_ledger IS
  'PB-3/L-1 (Paripraśna SAMĪKṢĀ): the conversational prediction ledger. One row per '
  'human-confirmed, time-indexed claim from a real /api/pariprashna reading, tracked '
  'detected→confirmed→open→window_closed→outcome_recorded (exits dismissed/lapsed/'
  'unverifiable/lapsed_unconfirmed). confidence is a Brier-ready numrange (never text); '
  'the D-16 provenance stamp (build_id/priors_version/formula_versions/ranking_config/'
  'now_context_date) is COPIED at confirmation, never referenced. Immutable-once-confirmed '
  'via trg_bmpl_freeze_confirmed. count_sql: SELECT count(*) FROM '
  'brahma_mimamsa_prediction_ledger WHERE chart_id = $1. Not an asset_registry asset '
  '(conversational, not build-DAG). Authority map: LEDGER_MAP_PB-3.md.';

-- ── Indexes ──
CREATE INDEX IF NOT EXISTS idx_bmpl_chart
  ON brahma_mimamsa_prediction_ledger (chart_id);
CREATE INDEX IF NOT EXISTS idx_bmpl_lifecycle
  ON brahma_mimamsa_prediction_ledger (lifecycle_status);
CREATE INDEX IF NOT EXISTS idx_bmpl_message_part
  ON brahma_mimamsa_prediction_ledger (message_part_id);
-- GIST on the daterange for the L-4 daily job's window-boundary sweep (upper("window") < now()).
CREATE INDEX IF NOT EXISTS idx_bmpl_window_gist
  ON brahma_mimamsa_prediction_ledger USING gist ("window");

-- ── Immutability guard: freeze stamp + settled-claim fields once past `detected`. ──
CREATE OR REPLACE FUNCTION bmpl_freeze_confirmed() RETURNS trigger AS $fn$
BEGIN
  -- Always keep updated_at fresh on any mutation.
  NEW.updated_at := now();

  -- Before confirmation (still a `detected` candidate) the claim + stamp are editable.
  IF OLD.lifecycle_status = 'detected' THEN
    RETURN NEW;
  END IF;

  -- Past `detected`: the copied stamp and the settled claim core are frozen forever.
  IF NEW.build_id           IS DISTINCT FROM OLD.build_id
     OR NEW.priors_version   IS DISTINCT FROM OLD.priors_version
     OR NEW.formula_versions IS DISTINCT FROM OLD.formula_versions
     OR NEW.ranking_config   IS DISTINCT FROM OLD.ranking_config
     OR NEW.now_context_date IS DISTINCT FROM OLD.now_context_date
     OR NEW.claim_text       IS DISTINCT FROM OLD.claim_text
     OR NEW.domain           IS DISTINCT FROM OLD.domain
     OR NEW."window"         IS DISTINCT FROM OLD."window"
     OR NEW.confidence       IS DISTINCT FROM OLD.confidence
     OR NEW.direction        IS DISTINCT FROM OLD.direction
  THEN
    RAISE EXCEPTION
      'brahma_mimamsa_prediction_ledger: stamp and settled claim fields are immutable once '
      'a row is confirmed (row %, status %). Lifecycle and outcome columns remain mutable.',
      OLD.id, OLD.lifecycle_status
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;

  RETURN NEW;
END;
$fn$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_bmpl_freeze_confirmed ON brahma_mimamsa_prediction_ledger;
CREATE TRIGGER trg_bmpl_freeze_confirmed
  BEFORE UPDATE ON brahma_mimamsa_prediction_ledger
  FOR EACH ROW EXECUTE FUNCTION bmpl_freeze_confirmed();

COMMIT;

-- DOWN (manual rollback — this project has no automated down-migration runner; listed for
-- audit + local throwaway-DB rollback testing only):
-- BEGIN;
-- DROP TRIGGER IF EXISTS trg_bmpl_freeze_confirmed ON brahma_mimamsa_prediction_ledger;
-- DROP FUNCTION IF EXISTS bmpl_freeze_confirmed();
-- DROP TABLE IF EXISTS brahma_mimamsa_prediction_ledger;
-- COMMIT;
