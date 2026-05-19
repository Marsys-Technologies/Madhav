-- R8-S3: pg_trgm trigram search on conversation_messages.parts_json
-- Enables body-level conversation search via GET /api/conversations/search.
-- Uses an expression index on parts_json::text so no column schema change required.
-- Idempotent: all statements use IF NOT EXISTS / IF EXISTS guards.

-- Enable the pg_trgm extension (no-op if already enabled).
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- GIN trigram index on the text representation of parts_json.
-- Covers ILIKE and similarity() queries over message body text.
CREATE INDEX IF NOT EXISTS idx_conv_messages_body_trgm
  ON conversation_messages USING GIN ((parts_json::text) gin_trgm_ops);

-- Also index conversations title for the combined title+body search.
CREATE INDEX IF NOT EXISTS idx_conversations_title_trgm
  ON conversations USING GIN (title gin_trgm_ops)
  WHERE title IS NOT NULL;
