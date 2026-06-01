-- Migration 008: Per-native namespacing
-- Adds native_id to core tables to support multi-native data isolation,
-- adds panel_metadata to messages for UI panel state, and creates composite
-- indices for efficient per-native queries.
--
-- All steps are idempotent (ADD COLUMN IF NOT EXISTS, CREATE INDEX ... IF NOT EXISTS).
--
-- ROLLBACK:
-- ALTER TABLE messages DROP COLUMN IF EXISTS panel_metadata;
-- ALTER TABLE messages DROP COLUMN IF EXISTS native_id;
-- ALTER TABLE conversations DROP COLUMN IF EXISTS native_id;
-- ALTER TABLE documents DROP COLUMN IF EXISTS native_id;
-- ALTER TABLE reports DROP COLUMN IF EXISTS native_id;
-- ALTER TABLE pyramid_layers DROP COLUMN IF EXISTS native_id;
-- ALTER TABLE charts DROP COLUMN IF EXISTS native_id;
-- DROP INDEX IF EXISTS idx_messages_native_conversation;
-- DROP INDEX IF EXISTS idx_documents_native_layer_name;
-- DROP INDEX IF EXISTS idx_reports_native_domain;

-- ─── Step 1: Add native_id to core tables ─────────────────────────────────────

ALTER TABLE public.charts
  ADD COLUMN IF NOT EXISTS native_id VARCHAR(64) NOT NULL DEFAULT 'abhisek';

ALTER TABLE public.pyramid_layers
  ADD COLUMN IF NOT EXISTS native_id VARCHAR(64) NOT NULL DEFAULT 'abhisek';

ALTER TABLE public.documents
  ADD COLUMN IF NOT EXISTS native_id VARCHAR(64) NOT NULL DEFAULT 'abhisek';

ALTER TABLE public.conversations
  ADD COLUMN IF NOT EXISTS native_id VARCHAR(64) NOT NULL DEFAULT 'abhisek';

ALTER TABLE public.reports
  ADD COLUMN IF NOT EXISTS native_id VARCHAR(64) NOT NULL DEFAULT 'abhisek';

ALTER TABLE public.messages
  ADD COLUMN IF NOT EXISTS native_id VARCHAR(64) NOT NULL DEFAULT 'abhisek';

-- ─── Step 2: Add panel_metadata to messages ───────────────────────────────────

ALTER TABLE public.messages
  ADD COLUMN IF NOT EXISTS panel_metadata JSONB NULL;

-- ─── Step 3: Composite indices for per-native queries ────────────────────────

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_native_conversation
  ON public.messages(native_id, conversation_id, created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_native_layer_name
  ON public.documents(native_id, layer, name);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_native_domain
  ON public.reports(native_id, domain);
