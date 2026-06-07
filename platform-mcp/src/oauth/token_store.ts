/**
 * platform-mcp/src/oauth/token_store.ts
 *
 * OAuth token lifecycle management.
 * Underlying identity: Firebase Authentication.
 * This layer is a protocol bridge — Firebase is the authority.
 *
 * L0FR Stream A — authored 2026-06-07
 * Per source data §4 (MCP OAuth 2.0 specification)
 */

import crypto from 'crypto'

const ACCESS_TOKEN_TTL_SECONDS = 3600       // 1 hour
const REFRESH_TOKEN_TTL_SECONDS = 30 * 24 * 3600  // 30 days

// In-memory store (replace with DB in production — table: mcp_oauth_tokens)
interface TokenRecord {
  access_token: string
  refresh_token: string
  uid: string
  scopes: string[]
  created_at: Date
  expires_at: Date
  refresh_expires_at: Date
}

const tokenStore = new Map<string, TokenRecord>()
const refreshStore = new Map<string, string>()  // refresh_token → access_token

// ── Token generation ──────────────────────────────────────────────────────────

function generateToken(prefix: string = 'mcp'): string {
  return `${prefix}_${crypto.randomBytes(32).toString('hex')}`
}

export interface IssuedTokens {
  access_token: string
  refresh_token: string
  expires_in: number
  scope: string
}

/**
 * Issue new access + refresh tokens for a Firebase UID.
 */
export function issueTokens(uid: string, scopes: string[]): IssuedTokens {
  const accessToken = generateToken('mcp_at')
  const refreshToken = generateToken('mcp_rt')
  const now = new Date()

  const record: TokenRecord = {
    access_token: accessToken,
    refresh_token: refreshToken,
    uid,
    scopes,
    created_at: now,
    expires_at: new Date(now.getTime() + ACCESS_TOKEN_TTL_SECONDS * 1000),
    refresh_expires_at: new Date(now.getTime() + REFRESH_TOKEN_TTL_SECONDS * 1000),
  }

  tokenStore.set(accessToken, record)
  refreshStore.set(refreshToken, accessToken)

  return {
    access_token: accessToken,
    refresh_token: refreshToken,
    expires_in: ACCESS_TOKEN_TTL_SECONDS,
    scope: scopes.join(' '),
  }
}

/**
 * Validate an access token. Returns the token record or null.
 */
export function validateAccessToken(token: string): TokenRecord | null {
  const record = tokenStore.get(token)
  if (!record) return null
  if (record.expires_at < new Date()) {
    tokenStore.delete(token)
    return null
  }
  return record
}

/**
 * Refresh: exchange a refresh token for a new access token.
 */
export function refreshAccessToken(refreshToken: string): IssuedTokens | null {
  const oldAccessToken = refreshStore.get(refreshToken)
  if (!oldAccessToken) return null

  const record = tokenStore.get(oldAccessToken)
  if (!record) return null
  if (record.refresh_expires_at < new Date()) {
    tokenStore.delete(oldAccessToken)
    refreshStore.delete(refreshToken)
    return null
  }

  // Revoke old tokens
  tokenStore.delete(oldAccessToken)
  refreshStore.delete(refreshToken)

  // Issue new tokens
  return issueTokens(record.uid, record.scopes)
}

/**
 * Revoke all tokens for a UID.
 */
export function revokeTokensForUid(uid: string): void {
  for (const [token, record] of tokenStore.entries()) {
    if (record.uid === uid) {
      tokenStore.delete(token)
      refreshStore.delete(record.refresh_token)
    }
  }
}
