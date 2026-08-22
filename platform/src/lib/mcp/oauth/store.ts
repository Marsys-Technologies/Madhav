/**
 * platform/src/lib/mcp/oauth/store.ts
 *
 * DB-backed OAuth store for MCP (M5).
 *
 * Replaces the in-memory Maps in platform-mcp/src/oauth/ with SQL operations
 * against mcp_oauth_clients / mcp_oauth_tokens / mcp_oauth_auth_codes (migration 383).
 *
 * Security invariants:
 *   - Secrets/tokens NEVER stored in plaintext — SHA-256 hashes at rest.
 *   - Auth codes are one-time-use (consumed_at stamps the use).
 *   - uid on an auth code may be NULL until the Firebase round-trip completes;
 *     the token endpoint rejects codes with uid = NULL (fail-closed, per M0).
 *   - DELETEs are always scoped (never unscoped DELETE FROM table).
 *
 * Callers: /api/mcp/oauth/* route handlers (platform API routes).
 *
 * M5 — MCP elevation arc (2026-07-01).
 */

'server-only'
import { createHash, randomBytes } from 'crypto'
import { query } from '@/lib/db/client'

// ── TTLs ──────────────────────────────────────────────────────────────────────

const ACCESS_TOKEN_TTL_SECONDS = 3600              // 1 hour
const REFRESH_TOKEN_TTL_SECONDS = 30 * 24 * 3600  // 30 days
const AUTH_CODE_TTL_SECONDS = 600                  // 10 minutes

// ── Hashing ──────────────────────────────────────────────────────────────────

export function sha256(value: string): string {
  return createHash('sha256').update(value).digest('hex')
}

export function generateToken(prefix: string): string {
  return `${prefix}_${randomBytes(32).toString('hex')}`
}

// ── Client operations ─────────────────────────────────────────────────────────

export interface OAuthClientRecord {
  client_id: string
  owner_uid: string
  redirect_uris: string[]
  scopes: string[]
  created_at: string
}

/**
 * Register a new OAuth client. Returns the client_id and plaintext secret
 * (the secret is only returned here; the hash is stored).
 */
export async function registerClient(params: {
  ownerUid: string
  redirectUris: string[]
  scopes?: string[]
}): Promise<{ client_id: string; client_secret: string }> {
  const clientId = `mcp_client_${randomBytes(16).toString('hex')}`
  const clientSecret = `mcp_cs_${randomBytes(32).toString('hex')}`
  const secretHash = sha256(clientSecret)
  const scopes = params.scopes ?? ['mcp:tools', 'mcp:resources', 'mcp:prompts']

  await query(
    `INSERT INTO mcp_oauth_clients (client_id, client_secret_hash, owner_uid, redirect_uris, scopes)
     VALUES ($1, $2, $3, $4, $5)`,
    [clientId, secretHash, params.ownerUid, params.redirectUris, scopes]
  )

  return { client_id: clientId, client_secret: clientSecret }
}

/**
 * Validate a client by ID + secret. Returns the client record or null.
 */
export async function validateClient(
  clientId: string,
  clientSecret?: string
): Promise<OAuthClientRecord | null> {
  const { rows } = await query<OAuthClientRecord & { client_secret_hash: string }>(
    `SELECT client_id, client_secret_hash, owner_uid, redirect_uris, scopes, created_at
     FROM mcp_oauth_clients
     WHERE client_id = $1`,
    [clientId]
  )
  const row = rows[0]
  if (!row) return null

  // SF-002 fix: this function has exactly one caller chain (the client_credentials
  // grant handler, via /api/mcp/oauth/clients/validate) -- the authorization_code+PKCE
  // flow never calls validateClient at all (it goes through consumeAuthCode + its own
  // PKCE verification instead, see platform-mcp/src/oauth/token.ts's
  // authorization_code branch). The prior "skip if no secret, for PKCE" comment
  // described a justification that does not apply to this function's actual (only)
  // caller. client_credentials grant REQUIRES client authentication per RFC 6749 §4.4 --
  // omitting a secret must never validate. Previously: JSON.stringify() dropping an
  // `undefined` client_secret key meant a request with NO secret at all skipped
  // verification entirely and returned the client record as valid, letting anyone who
  // knew a client_id (not secret-equivalent -- it appears in authorize/redirect URLs)
  // obtain real access+refresh tokens for that client's owner_uid.
  const incoming = sha256(clientSecret ?? '')
  if (clientSecret === undefined || incoming !== row.client_secret_hash) return null

  return {
    client_id: row.client_id,
    owner_uid: row.owner_uid,
    redirect_uris: row.redirect_uris,
    scopes: row.scopes,
    created_at: row.created_at,
  }
}

/**
 * SF-004 (PARIŚEṢA-V4): lookup-only client metadata for the /authorize
 * redirect_uri allowlist check. `/authorize` runs before any client secret is
 * available (it's a browser redirect, not a service-to-service call), so it
 * cannot go through `validateClient` — which correctly (SF-002) rejects
 * `clientSecret === undefined`. This function is the secretless sibling used
 * ONLY to fetch the registered allowlist.
 *
 * The SQL projection itself never selects `owner_uid` or `client_secret_hash`
 * — the omission is enforced here, not only by response shaping one layer up,
 * so a careless edit to the caller cannot leak either field. See
 * `SF004_OAUTH_BINDING_CONTRACT_v1_0.md` §4.
 */
export async function getClientMetadata(
  clientId: string
): Promise<{ redirect_uris: string[]; scopes: string[] } | null> {
  const { rows } = await query<{ redirect_uris: string[]; scopes: string[] }>(
    `SELECT redirect_uris, scopes
     FROM mcp_oauth_clients
     WHERE client_id = $1`,
    [clientId]
  )
  const row = rows[0]
  if (!row) return null
  return { redirect_uris: row.redirect_uris, scopes: row.scopes }
}

// ── Auth code operations ──────────────────────────────────────────────────────

export interface AuthCodeRecord {
  code: string               // plaintext (returned to caller; not stored)
  client_id: string
  redirect_uri: string
  uid?: string
  scopes: string[]
  pkce_challenge?: string
  pkce_challenge_method?: string
  expires_at: Date
}

/**
 * Create and store a new auth code. Returns the plaintext code (hash stored in DB).
 */
export async function createAuthCode(params: {
  clientId: string
  redirectUri: string
  scopes: string[]
  uid?: string
  pkceChallenge?: string
  pkceChallengeMethod?: string
}): Promise<string> {
  const code = `mcp_ac_${randomBytes(32).toString('hex')}`
  const codeHash = sha256(code)
  const expiresAt = new Date(Date.now() + AUTH_CODE_TTL_SECONDS * 1000)

  await query(
    `INSERT INTO mcp_oauth_auth_codes
       (code_hash, uid, client_id, redirect_uri, scopes, pkce_challenge, pkce_challenge_method, expires_at)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
    [
      codeHash,
      params.uid ?? null,
      params.clientId,
      params.redirectUri,
      params.scopes,
      params.pkceChallenge ?? null,
      params.pkceChallengeMethod ?? null,
      expiresAt,
    ]
  )

  return code
}

/**
 * Stamp the Firebase uid onto an existing auth code (after OAuth callback).
 */
export async function stampAuthCodeUid(code: string, uid: string): Promise<boolean> {
  const codeHash = sha256(code)
  const { rowCount } = await query(
    `UPDATE mcp_oauth_auth_codes
     SET uid = $1
     WHERE code_hash = $2
       AND consumed_at IS NULL
       AND expires_at > NOW()`,
    [uid, codeHash]
  )
  return (rowCount ?? 0) > 0
}

/**
 * Consume an auth code (one-time use). Returns the record or null if
 * expired, consumed, or not found.
 */
export async function consumeAuthCode(code: string): Promise<AuthCodeRecord | null> {
  const codeHash = sha256(code)

  const { rows } = await query<{
    uid: string | null
    client_id: string
    redirect_uri: string
    scopes: string[]
    pkce_challenge: string | null
    pkce_challenge_method: string | null
    expires_at: string
  }>(
    `UPDATE mcp_oauth_auth_codes
     SET consumed_at = NOW()
     WHERE code_hash = $1
       AND consumed_at IS NULL
       AND expires_at > NOW()
     RETURNING uid, client_id, redirect_uri, scopes, pkce_challenge, pkce_challenge_method, expires_at`,
    [codeHash]
  )

  const row = rows[0]
  if (!row) return null

  return {
    code,
    client_id: row.client_id,
    redirect_uri: row.redirect_uri,
    uid: row.uid ?? undefined,
    scopes: row.scopes,
    pkce_challenge: row.pkce_challenge ?? undefined,
    pkce_challenge_method: row.pkce_challenge_method ?? undefined,
    expires_at: new Date(row.expires_at),
  }
}

// ── Token operations ──────────────────────────────────────────────────────────

export interface TokenRecord {
  uid: string
  scopes: string[]
  expires_at: Date
  refresh_expires_at: Date | null
}

export interface IssuedTokens {
  access_token: string
  refresh_token: string
  expires_in: number
  scope: string
}

/**
 * Issue new access + refresh tokens for a Firebase UID.
 * Stores SHA-256 hashes in DB; returns the plaintext tokens to the caller.
 */
export async function issueTokens(uid: string, scopes: string[]): Promise<IssuedTokens> {
  const accessToken = generateToken('mcp_at')
  const refreshToken = generateToken('mcp_rt')
  const now = Date.now()
  const expiresAt = new Date(now + ACCESS_TOKEN_TTL_SECONDS * 1000)
  const refreshExpiresAt = new Date(now + REFRESH_TOKEN_TTL_SECONDS * 1000)

  await query(
    `INSERT INTO mcp_oauth_tokens
       (access_token_hash, refresh_token_hash, uid, scopes, expires_at, refresh_expires_at)
     VALUES ($1, $2, $3, $4, $5, $6)`,
    [
      sha256(accessToken),
      sha256(refreshToken),
      uid,
      scopes,
      expiresAt,
      refreshExpiresAt,
    ]
  )

  return {
    access_token: accessToken,
    refresh_token: refreshToken,
    expires_in: ACCESS_TOKEN_TTL_SECONDS,
    scope: scopes.join(' '),
  }
}

/**
 * Validate an access token. Returns the token record or null if expired/not found.
 */
export async function validateAccessToken(token: string): Promise<TokenRecord | null> {
  const { rows } = await query<{
    uid: string
    scopes: string[]
    expires_at: string
    refresh_expires_at: string | null
  }>(
    `SELECT uid, scopes, expires_at, refresh_expires_at
     FROM mcp_oauth_tokens
     WHERE access_token_hash = $1
       AND expires_at > NOW()`,
    [sha256(token)]
  )

  const row = rows[0]
  if (!row) return null

  return {
    uid: row.uid,
    scopes: row.scopes,
    expires_at: new Date(row.expires_at),
    refresh_expires_at: row.refresh_expires_at ? new Date(row.refresh_expires_at) : null,
  }
}

/**
 * Exchange a refresh token for new access + refresh tokens (token rotation).
 * Old tokens are revoked.
 */
export async function refreshAccessToken(refreshToken: string): Promise<IssuedTokens | null> {
  const refreshHash = sha256(refreshToken)

  // Look up the token record by refresh_token_hash.
  const { rows } = await query<{
    access_token_hash: string
    uid: string
    scopes: string[]
    refresh_expires_at: string | null
  }>(
    `SELECT access_token_hash, uid, scopes, refresh_expires_at
     FROM mcp_oauth_tokens
     WHERE refresh_token_hash = $1
       AND refresh_expires_at > NOW()`,
    [refreshHash]
  )

  const row = rows[0]
  if (!row) return null

  // Revoke old token pair (scoped DELETE).
  await query(
    `DELETE FROM mcp_oauth_tokens
     WHERE access_token_hash = $1`,
    [row.access_token_hash]
  )

  // Issue new tokens.
  return issueTokens(row.uid, row.scopes)
}

/**
 * Revoke all tokens for a UID (scoped DELETE).
 */
export async function revokeTokensForUid(uid: string): Promise<void> {
  await query(
    `DELETE FROM mcp_oauth_tokens WHERE uid = $1`,
    [uid]
  )
}
