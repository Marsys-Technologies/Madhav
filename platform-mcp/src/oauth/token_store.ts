/**
 * platform-mcp/src/oauth/token_store.ts
 *
 * OAuth token lifecycle — DB-backed via platform API (M5).
 *
 * Replaces in-memory Maps (tokenStore, refreshStore) with calls to
 * platform's /api/mcp/oauth/tokens endpoints. Tokens survive restart and
 * work correctly across ≥2 Cloud Run instances.
 *
 * M5: in-memory Maps removed. Platform API is the single source of truth.
 *
 * L0FR Stream A — authored 2026-06-07; rewritten M5 2026-07-01.
 */

import {
  issueDbTokens,
  validateDbAccessToken,
  refreshDbAccessToken,
} from './oauth_platform_client.js'

export interface IssuedTokens {
  access_token: string
  refresh_token: string
  expires_in: number
  scope: string
}

// ── Token generation ──────────────────────────────────────────────────────────

/**
 * Issue new access + refresh tokens for a Firebase UID.
 * Stores SHA-256 hashes in the platform DB; returns plaintext tokens.
 */
export async function issueTokens(uid: string, scopes: string[]): Promise<IssuedTokens> {
  const tokens = await issueDbTokens(uid, scopes)
  if (!tokens) {
    throw new Error('[mcp:token_store] issueTokens: platform call failed')
  }
  return tokens
}

// ── Token record type (matches platform schema) ───────────────────────────────

export interface TokenRecord {
  uid: string
  scopes: string[]
}

/**
 * Validate an access token. Returns { uid, scopes } or null if expired/not found.
 * DB-backed: survives restart, works across instances.
 */
export async function validateAccessToken(token: string): Promise<TokenRecord | null> {
  return validateDbAccessToken(token)
}

/**
 * Refresh: exchange a refresh token for a new access token pair.
 * Returns new IssuedTokens or null if the refresh token is expired/invalid.
 */
export async function refreshAccessToken(refreshToken: string): Promise<IssuedTokens | null> {
  return refreshDbAccessToken(refreshToken)
}

/**
 * Revoke all tokens for a UID.
 * Note: revokeTokensForUid is called via the platform DELETE /api/mcp/oauth/tokens
 * endpoint. This export is kept for API surface compatibility.
 */
export async function revokeTokensForUid(uid: string): Promise<void> {
  // Implemented via platform API (called directly from routes that need revocation).
  // For backward compat the function exists; callers should prefer the platform route.
  const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
  const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''
  try {
    await fetch(`${PLATFORM_URL}/api/mcp/oauth/tokens`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      },
      body: JSON.stringify({ uid }),
      signal: AbortSignal.timeout(5_000),
    })
  } catch (err) {
    console.error('[mcp:token_store] revokeTokensForUid error:', err instanceof Error ? err.message : String(err))
  }
}
