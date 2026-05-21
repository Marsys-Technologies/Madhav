-- Migration 070: MCP API Keys table
-- Introduced by MCP workstream Phase MCP-1 (2026-05-21).
-- Stores hashed bearer tokens for MCP server authentication.
-- Each key is bound to a Firebase UID (profiles.id) and an audience_tier.

CREATE TABLE IF NOT EXISTS mcp_api_keys (
  -- Short prefix shown to the user, used as lookup key.
  -- Format: mcp_<env>_<8-char-prefix> (the first 8 chars after the env prefix).
  key_id        text        PRIMARY KEY,
  -- bcrypt hash of the full key (everything after the key_id prefix).
  key_hash      text        NOT NULL,
  -- Foreign key to Firebase UID; references profiles.id.
  user_uid      text        NOT NULL,
  -- Access tier for MCP calls originating from this key.
  audience_tier text        NOT NULL CHECK (audience_tier IN ('client', 'super_admin')),
  -- Future per-tool scoping; empty array = all tools permitted.
  scopes        text[]      NOT NULL DEFAULT '{}',
  created_at    timestamptz NOT NULL DEFAULT now(),
  -- Updated by auth.ts on every successful validation.
  last_used_at  timestamptz,
  -- Non-null when the key has been revoked; auth.ts rejects revoked keys.
  revoked_at    timestamptz,
  -- Human-readable label, e.g. "claude-chat-laptop".
  label         text
);

-- Fast lookup of a single user's keys (GET /api/mcp/keys).
CREATE INDEX IF NOT EXISTS mcp_api_keys_user_uid_idx
  ON mcp_api_keys (user_uid);

-- Fast auth lookup: given a key_id, check that the key is not revoked.
-- The compound index on (key_id, revoked_at) is intentional so the DB can
-- satisfy the common query "WHERE key_id = $1 AND revoked_at IS NULL" using
-- index-only scan. Partial indexes on NULLs vary by Postgres version; use
-- the compound form for compatibility.
CREATE INDEX IF NOT EXISTS mcp_api_keys_auth_lookup_idx
  ON mcp_api_keys (key_id, revoked_at);
