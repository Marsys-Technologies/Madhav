-- 383_mcp_oauth.sql
-- M5: DB-backed OAuth for MCP (replaces in-memory Maps in platform-mcp).
--
-- Three tables replace in-memory state so tokens survive restarts and
-- work correctly across ≥2 Cloud Run instances.
--
-- Security invariants:
--   - Secrets and tokens are NEVER stored in plaintext — sha256 hashes at rest.
--   - client_secret_hash: SHA-256(secret) — compare by hashing the incoming value.
--   - access_token_hash / refresh_token_hash: SHA-256(token) — same pattern.
--   - code_hash: SHA-256(code) — one-time-use; consumed_at stamps the use.
--
-- Rollback:
--   DROP TABLE IF EXISTS mcp_oauth_auth_codes;
--   DROP TABLE IF EXISTS mcp_oauth_tokens;
--   DROP TABLE IF EXISTS mcp_oauth_clients;

-- ── mcp_oauth_clients ─────────────────────────────────────────────────────────
-- One row per registered OAuth client (connector).
-- Dynamic registration (POST /oauth/register) writes here.
-- test_client hardcode in token.ts is replaced by a row in this table.

CREATE TABLE IF NOT EXISTS mcp_oauth_clients (
  client_id          TEXT        PRIMARY KEY,
  client_secret_hash TEXT        NOT NULL,      -- SHA-256(client_secret); never plaintext
  owner_uid          TEXT        NOT NULL,       -- Firebase uid of the registering user
  redirect_uris      TEXT[]      NOT NULL DEFAULT '{}',
  scopes             TEXT[]      NOT NULL DEFAULT '{"mcp:tools","mcp:resources","mcp:prompts"}',
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE mcp_oauth_clients IS
  'Registered MCP OAuth 2.0 clients. client_secret stored as SHA-256 hash — never plaintext. '
  'M5 — MCP elevation arc (production OAuth).';

-- Index for owner lookup (list my clients).
CREATE INDEX IF NOT EXISTS idx_mcp_oauth_clients_owner
  ON mcp_oauth_clients(owner_uid);

-- ── mcp_oauth_tokens ──────────────────────────────────────────────────────────
-- Issued access + refresh token pairs.
-- access_token and refresh_token are stored as SHA-256 hashes.
-- The raw tokens are issued to the client; only the hash is persisted.

CREATE TABLE IF NOT EXISTS mcp_oauth_tokens (
  access_token_hash   TEXT        PRIMARY KEY,   -- SHA-256(access_token)
  refresh_token_hash  TEXT        UNIQUE,        -- SHA-256(refresh_token); null if no refresh
  uid                 TEXT        NOT NULL,       -- Firebase uid
  scopes              TEXT[]      NOT NULL DEFAULT '{"mcp:tools"}',
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at          TIMESTAMPTZ NOT NULL,       -- access token expiry (1 h)
  refresh_expires_at  TIMESTAMPTZ              -- refresh token expiry (30 d); null = no refresh
);

COMMENT ON TABLE mcp_oauth_tokens IS
  'Active MCP OAuth access + refresh tokens. Both stored as SHA-256 hashes — never plaintext. '
  'Survives restart + multi-instance. M5 — MCP elevation arc.';

-- Index for uid-scoped revocation (revokeTokensForUid).
CREATE INDEX IF NOT EXISTS idx_mcp_oauth_tokens_uid
  ON mcp_oauth_tokens(uid);

-- Index for expired token sweeping.
CREATE INDEX IF NOT EXISTS idx_mcp_oauth_tokens_expires
  ON mcp_oauth_tokens(expires_at);

-- ── mcp_oauth_auth_codes ──────────────────────────────────────────────────────
-- Auth codes issued by the authorize endpoint; one-time use.
-- code is stored as SHA-256(code); consumed_at stamps use.
-- uid is stamped after Firebase session verification completes.

CREATE TABLE IF NOT EXISTS mcp_oauth_auth_codes (
  code_hash              TEXT        PRIMARY KEY,   -- SHA-256(code)
  uid                    TEXT,                      -- NULL until Firebase round-trip completes
  client_id              TEXT        NOT NULL REFERENCES mcp_oauth_clients(client_id) ON DELETE CASCADE,
  redirect_uri           TEXT        NOT NULL,
  scopes                 TEXT[]      NOT NULL DEFAULT '{}',
  pkce_challenge         TEXT,                      -- S256 code_challenge (base64url)
  pkce_challenge_method  TEXT,                      -- 'S256' or 'plain'
  created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at             TIMESTAMPTZ NOT NULL,       -- 10 minutes
  consumed_at            TIMESTAMPTZ                -- NULL until consumed; one-time use
);

COMMENT ON TABLE mcp_oauth_auth_codes IS
  'One-time MCP OAuth authorization codes. code stored as SHA-256 hash. '
  'uid stamped after Firebase session verification. consumed_at prevents replay. '
  'M5 — MCP elevation arc.';

-- Index for expiry cleanup.
CREATE INDEX IF NOT EXISTS idx_mcp_oauth_auth_codes_expires
  ON mcp_oauth_auth_codes(expires_at)
  WHERE consumed_at IS NULL;
