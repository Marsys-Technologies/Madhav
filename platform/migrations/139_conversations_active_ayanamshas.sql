-- Migration 139: conversations.active_ayanamshas — per-conversation ayanamsha selection
-- [BUILD-ORCH-J-01] INF7-S1
-- Idempotent: yes (ADD COLUMN IF NOT EXISTS + backfill via UPDATE WHERE IS NULL)

BEGIN;

-- ── 1. Add column ─────────────────────────────────────────────────────────────
ALTER TABLE conversations
  ADD COLUMN IF NOT EXISTS active_ayanamshas JSONB
    DEFAULT '["lahiri","true_chitra","kp","raman","surya_siddhanta"]'::jsonb;

-- ── 2. Backfill existing NULL rows ────────────────────────────────────────────
UPDATE conversations
   SET active_ayanamshas = '["lahiri","true_chitra","kp","raman","surya_siddhanta"]'::jsonb
 WHERE active_ayanamshas IS NULL;

-- ── 3. GIN index for @> containment queries ───────────────────────────────────
CREATE INDEX IF NOT EXISTS conversations_active_ayanamshas_gin
    ON conversations USING gin (active_ayanamshas);

COMMIT;
