-- Migration 467: pariprashna canonical message parts — PB-2 (SMṚTI) lane M-1
-- Created: 2026-07-28
--
-- Numbering note: highest numbered file across BOTH migration dirs combined is 466
-- (supabase/migrations/466_brahma_prospective_ledger_lapsed_unobserved.sql). 467 is the
-- next free number per platform/supabase/migrations/README.md's guidance. This dir
-- (platform/supabase/migrations) is the ACTIVE migration directory; migrate.ts reads it
-- plus the legacy platform/migrations and de-duplicates by filename.
--
-- Context: Paripraśna Build campaign wave PB-2 lane M-1 ("canonical schema"). This lane
-- replaces the /api/pariprashna route's turn.commit persistence (a single opaque
-- `conversation_messages.parts_json` jsonb blob) with canonical, kind-typed
-- `message_parts` rows — one row per part, seq-ordered, closed `kind` enum. This is a
-- GREEN-FIELD shape: no existing rows are migrated. Legacy `parts_json` rows are
-- RETAINED, untouched, and unread by the new path. M-1 lands the schema only; the route
-- is NOT rewired here (that is lane M-2's persistence seam).
--
-- ADDITIVE-ONLY guarantees (never breaks existing rows):
--   1. Three new columns on conversation_messages, all NULLABLE with no default — so
--      every pre-existing legacy row reads NULL for them (an ADD COLUMN of a nullable,
--      defaultless column is a catalog-only change in Postgres: no table rewrite, no row
--      lock beyond a brief ACCESS EXCLUSIVE for the catalog update, instantly reversible
--      by DROP COLUMN). Legacy rows keep NULL; new pariprashna-route rows always set them.
--        - schema_version int   : canonical-shape version stamp (NULL = legacy blob row)
--        - model_id text        : the answering model id (e.g. claude-opus-4-8[1m])
--        - provider text        : the model provider (e.g. anthropic)
--   2. A NEW table message_parts (fresh CREATE TABLE — cannot affect any existing row).
--
-- `kind` is a CLOSED enum enforced by a CHECK constraint. The seven kinds mirror the
-- canonical part vocabulary the M-1 DAL (platform/src/lib/pariprashna/store) validates
-- with Zod:
--   text | reasoning | tool_call | tool_result | citation | prediction_candidate | attachment
--
-- Natural-key note: the requested "(message_id, seq)" index is created here as a UNIQUE
-- index. seq is the per-message ordering key; two parts of the same message must not
-- share a seq or the canonical serializer's seq-ordering (and PB-2 lane M-2's
-- byte-equality gate) would be ambiguous. UNIQUE is a strict superset of the requested
-- plain index — it satisfies the index requirement AND enforces the natural key that the
-- delete-then-insert idempotency pattern (§N.3) and the M-2 gate both rely on.
--
-- Idempotency: per §N.4 "surgical migrations only" — ADD COLUMN IF NOT EXISTS,
-- CREATE TABLE IF NOT EXISTS, CREATE UNIQUE INDEX IF NOT EXISTS throughout. Safe to
-- re-run. The FK to conversation_messages(id) is created inline in the CREATE TABLE, so
-- it is skipped on a re-run when the table already exists (no duplicate-constraint error).

BEGIN;

-- (1) Additive columns on the existing message table. Nullable, no default => legacy
--     rows are unaffected and read NULL; the M-1 writer always populates them.
ALTER TABLE conversation_messages
  ADD COLUMN IF NOT EXISTS schema_version int,
  ADD COLUMN IF NOT EXISTS model_id       text,
  ADD COLUMN IF NOT EXISTS provider        text;

COMMENT ON COLUMN conversation_messages.schema_version IS
  'PB-2/M-1: canonical message-parts schema version. NULL on legacy parts_json blob '
  'rows; set (>=1) on new pariprashna-route rows persisted as message_parts.';
COMMENT ON COLUMN conversation_messages.model_id IS
  'PB-2/M-1: answering model id for canonical rows (NULL on legacy rows).';
COMMENT ON COLUMN conversation_messages.provider IS
  'PB-2/M-1: model provider for canonical rows (NULL on legacy rows).';

-- (2) New canonical kind-typed parts table.
CREATE TABLE IF NOT EXISTS message_parts (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id    uuid NOT NULL REFERENCES conversation_messages(id),
  seq           int NOT NULL,
  kind          text NOT NULL CHECK (kind IN (
                  'text',
                  'reasoning',
                  'tool_call',
                  'tool_result',
                  'citation',
                  'prediction_candidate',
                  'attachment'
                )),
  body          jsonb NOT NULL,
  model_visible boolean NOT NULL,
  created_at    timestamptz NOT NULL DEFAULT now()
);

-- Requested (message_id, seq) index — UNIQUE, enforcing the per-message ordering key.
CREATE UNIQUE INDEX IF NOT EXISTS idx_message_parts_message_seq
  ON message_parts(message_id, seq);

COMMENT ON TABLE message_parts IS
  'PB-2/M-1 (Paripraśna SMṚTI): canonical, kind-typed message parts — one row per part, '
  'seq-ordered within a message, closed `kind` enum. Replaces the opaque '
  'conversation_messages.parts_json blob for the /api/pariprashna route only. Bodies are '
  'Zod-validated per kind by platform/src/lib/pariprashna/store. Green-field: legacy '
  'parts_json rows are never migrated into this table.';

COMMIT;

-- DOWN (manual rollback — this project has no automated down-migration runner; drops are
-- listed for audit + local throwaway-DB rollback testing only):
-- BEGIN;
-- DROP TABLE IF EXISTS message_parts;
-- ALTER TABLE conversation_messages
--   DROP COLUMN IF EXISTS provider,
--   DROP COLUMN IF EXISTS model_id,
--   DROP COLUMN IF EXISTS schema_version;
-- COMMIT;
