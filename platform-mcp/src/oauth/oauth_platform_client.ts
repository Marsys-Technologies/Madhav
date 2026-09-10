/**
 * platform-mcp/src/oauth/oauth_platform_client.ts
 *
 * HTTP client for calling platform OAuth API routes.
 * All OAuth DB operations (client registration, code create/consume,
 * token issue/validate/refresh) route through the platform API —
 * the MCP sidecar has no direct DB access.
 *
 * Pattern mirrors lib/session.ts (M3): HTTP to platform with X-MCP-Internal-Token.
 *
 * M5 — MCP elevation arc (production OAuth, 2026-07-01).
 */

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

function serviceHeaders(extra?: Record<string, string>): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
    ...extra,
  }
}

// ── Client registration ───────────────────────────────────────────────────────

export interface ClientRegistrationResult {
  client_id: string
  client_secret: string
}

/**
 * Register a new OAuth client. Returns client_id + plaintext client_secret.
 * The secret is only returned here; subsequent calls use it to validate.
 */
export async function registerOAuthClient(params: {
  ownerUid: string
  redirectUris: string[]
  scopes?: string[]
}): Promise<ClientRegistrationResult | null> {
  try {
    const res = await fetch(`${PLATFORM_URL}/api/mcp/oauth/clients`, {
      method: 'POST',
      headers: serviceHeaders({ 'X-MCP-User': params.ownerUid }),
      body: JSON.stringify({
        redirect_uris: params.redirectUris,
        scopes: params.scopes,
      }),
      signal: AbortSignal.timeout(10_000),
    })
    if (!res.ok) {
      console.error(`[mcp:oauth_client] registerOAuthClient failed: ${res.status}`)
      return null
    }
    return (await res.json()) as ClientRegistrationResult
  } catch (err) {
    console.error('[mcp:oauth_client] registerOAuthClient error:', err instanceof Error ? err.message : String(err))
    return null
  }
}

/**
 * Validate a client_id + optional client_secret.
 * Returns { valid, owner_uid, scopes } or { valid: false }.
 */
export async function validateOAuthClient(
  clientId: string,
  clientSecret?: string
): Promise<{ valid: true; owner_uid: string; scopes: string[] } | { valid: false }> {
  try {
    const res = await fetch(`${PLATFORM_URL}/api/mcp/oauth/clients/validate`, {
      method: 'POST',
      headers: serviceHeaders(),
      body: JSON.stringify({ client_id: clientId, client_secret: clientSecret }),
      signal: AbortSignal.timeout(5_000),
    })
    if (!res.ok) return { valid: false }
    return (await res.json()) as { valid: true; owner_uid: string; scopes: string[] } | { valid: false }
  } catch (err) {
    console.error('[mcp:oauth_client] validateOAuthClient error:', err instanceof Error ? err.message : String(err))
    return { valid: false }
  }
}

/**
 * SF-004 (PARIŚEṢA-V4): lookup-only client metadata for the /authorize
 * redirect_uri allowlist check. Calls the platform's `metadata_only` mode —
 * fully separate from `validateOAuthClient`'s secret-required call above.
 * Returns ONLY redirect_uris + scopes, never owner_uid. See
 * SF004_OAUTH_BINDING_CONTRACT_v1_0.md §4.
 */
export async function fetchOAuthClientMetadata(
  clientId: string
): Promise<{ found: true; redirect_uris: string[]; scopes: string[] } | { found: false }> {
  try {
    const res = await fetch(`${PLATFORM_URL}/api/mcp/oauth/clients/validate`, {
      method: 'POST',
      headers: serviceHeaders(),
      body: JSON.stringify({ client_id: clientId, metadata_only: true }),
      signal: AbortSignal.timeout(5_000),
    })
    if (!res.ok) return { found: false }
    return (await res.json()) as { found: true; redirect_uris: string[]; scopes: string[] } | { found: false }
  } catch (err) {
    console.error('[mcp:oauth_client] fetchOAuthClientMetadata error:', err instanceof Error ? err.message : String(err))
    return { found: false }
  }
}

// ── Auth code operations ──────────────────────────────────────────────────────

/**
 * Create an auth code in the DB. Returns the plaintext code.
 */
export async function createDbAuthCode(params: {
  clientId: string
  redirectUri: string
  scopes: string[]
  uid?: string
  pkceChallenge?: string
  pkceChallengeMethod?: string
}): Promise<string | null> {
  try {
    const res = await fetch(`${PLATFORM_URL}/api/mcp/oauth/codes`, {
      method: 'POST',
      headers: serviceHeaders(),
      body: JSON.stringify({
        client_id: params.clientId,
        redirect_uri: params.redirectUri,
        scopes: params.scopes,
        uid: params.uid,
        pkce_challenge: params.pkceChallenge,
        pkce_challenge_method: params.pkceChallengeMethod,
      }),
      signal: AbortSignal.timeout(5_000),
    })
    if (!res.ok) {
      console.error(`[mcp:oauth_client] createDbAuthCode failed: ${res.status}`)
      return null
    }
    const data = (await res.json()) as { code: string }
    return data.code
  } catch (err) {
    console.error('[mcp:oauth_client] createDbAuthCode error:', err instanceof Error ? err.message : String(err))
    return null
  }
}

/**
 * Stamp the Firebase uid onto an existing auth code after OAuth callback.
 */
export async function stampDbAuthCodeUid(code: string, uid: string): Promise<boolean> {
  try {
    const res = await fetch(`${PLATFORM_URL}/api/mcp/oauth/codes`, {
      method: 'PATCH',
      headers: serviceHeaders(),
      body: JSON.stringify({ code, uid }),
      signal: AbortSignal.timeout(5_000),
    })
    return res.ok
  } catch (err) {
    console.error('[mcp:oauth_client] stampDbAuthCodeUid error:', err instanceof Error ? err.message : String(err))
    return false
  }
}

export interface ConsumedAuthCode {
  client_id: string
  redirect_uri: string
  uid?: string
  scopes: string[]
  pkce_challenge?: string
  pkce_challenge_method?: string
}

/**
 * Consume an auth code (one-time-use). Returns the record or null if expired/consumed.
 */
export async function consumeDbAuthCode(code: string): Promise<ConsumedAuthCode | null> {
  try {
    const res = await fetch(`${PLATFORM_URL}/api/mcp/oauth/codes/consume`, {
      method: 'POST',
      headers: serviceHeaders(),
      body: JSON.stringify({ code }),
      signal: AbortSignal.timeout(5_000),
    })
    if (!res.ok) return null
    const data = (await res.json()) as { record: ConsumedAuthCode }
    return data.record
  } catch (err) {
    console.error('[mcp:oauth_client] consumeDbAuthCode error:', err instanceof Error ? err.message : String(err))
    return null
  }
}

// ── Token operations ──────────────────────────────────────────────────────────

export interface IssuedTokens {
  access_token: string
  refresh_token: string
  expires_in: number
  scope: string
}

/**
 * Issue a new access + refresh token pair for a Firebase uid.
 */
export async function issueDbTokens(uid: string, scopes: string[]): Promise<IssuedTokens | null> {
  try {
    const res = await fetch(`${PLATFORM_URL}/api/mcp/oauth/tokens`, {
      method: 'POST',
      headers: serviceHeaders(),
      body: JSON.stringify({ uid, scopes }),
      signal: AbortSignal.timeout(5_000),
    })
    if (!res.ok) {
      console.error(`[mcp:oauth_client] issueDbTokens failed: ${res.status}`)
      return null
    }
    return (await res.json()) as IssuedTokens
  } catch (err) {
    console.error('[mcp:oauth_client] issueDbTokens error:', err instanceof Error ? err.message : String(err))
    return null
  }
}

/**
 * Validate an OAuth access token. Returns { valid, uid, scopes } or null.
 */
export async function validateDbAccessToken(
  token: string
): Promise<{ uid: string; scopes: string[] } | null> {
  try {
    const res = await fetch(`${PLATFORM_URL}/api/mcp/oauth/tokens/validate`, {
      method: 'GET',
      headers: serviceHeaders({ 'X-MCP-OAuth-Token': token }),
      signal: AbortSignal.timeout(5_000),
    })
    if (!res.ok) return null
    const data = (await res.json()) as { valid: boolean; uid?: string; scopes?: string[] }
    if (!data.valid || !data.uid) return null
    return { uid: data.uid, scopes: data.scopes ?? [] }
  } catch (err) {
    console.error('[mcp:oauth_client] validateDbAccessToken error:', err instanceof Error ? err.message : String(err))
    return null
  }
}

/**
 * Refresh an access token using a refresh token. Returns new token pair or null.
 */
export async function refreshDbAccessToken(refreshToken: string): Promise<IssuedTokens | null> {
  try {
    const res = await fetch(`${PLATFORM_URL}/api/mcp/oauth/tokens/refresh`, {
      method: 'POST',
      headers: serviceHeaders(),
      body: JSON.stringify({ refresh_token: refreshToken }),
      signal: AbortSignal.timeout(5_000),
    })
    if (!res.ok) return null
    return (await res.json()) as IssuedTokens
  } catch (err) {
    console.error('[mcp:oauth_client] refreshDbAccessToken error:', err instanceof Error ? err.message : String(err))
    return null
  }
}
