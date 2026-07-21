/**
 * platform-mcp/src/oauth/authorize.ts
 *
 * POST /mcp/oauth/authorize — initiates OAuth flow; redirects through Firebase auth.
 * GET  /mcp/oauth/callback  — Firebase auth callback; stamps uid onto auth code.
 *
 * Per MCP authorization spec: https://modelcontextprotocol.io/specification/server/authorization
 *
 * M5: in-memory authCodes Map replaced with DB-backed auth codes via platform API.
 * M5: real Firebase round-trip via FIREBASE_AUTH_URL redirect + __session cookie verify.
 *
 * Flow:
 *   1. POST /authorize → validate params → create DB auth code → redirect to Firebase login
 *      (Firebase login URL embeds code in `state` param).
 *   2. Firebase callback → GET /callback with __session cookie set.
 *   3. GET /callback → verify __session via platform /api/auth/verify-session
 *      → stamp uid onto auth code → redirect to client redirect_uri?code=...
 *
 * L0FR Stream A — authored 2026-06-07; rewritten M5 2026-07-01.
 */

import type { Request, Response } from 'express'
import type { OAuthAuthorizationRequest } from './types.js'
import {
  createDbAuthCode,
  stampDbAuthCodeUid,
  consumeDbAuthCode,
  type ConsumedAuthCode,
} from './oauth_platform_client.js'
import crypto from 'crypto'

const FIREBASE_AUTH_URL = process.env['FIREBASE_AUTH_URL'] ??
  'https://madhav.marsys.in/__/auth/handler'

const MCP_BASE_URL = (process.env['MCP_BASE_URL'] ?? 'https://madhav.marsys.in/mcp').replace(/\/$/, '')
const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

// W5 L2: profile-selecting scopes (OT-10 "OAuth scope selects the projection"). A grant
// may combine one resource-shape scope (mcp:tools) with at most one profile scope; a
// client that requests none of the three profile scopes gets 'consult' (see
// lib/mcp_profile.ts's resolveProfileFromScopes — safe by default, not enforced here).
const VALID_SCOPES = [
  'mcp:tools', 'mcp:resources', 'mcp:prompts',
  'mcp:profile:full', 'mcp:profile:compact', 'mcp:profile:consult',
]

// ── generateAuthCode / consumeAuthCode retained as the public interface ────────
// These now delegate to the DB-backed platform API.

/**
 * Generate an auth code (DB-backed). Returns the plaintext code or null on error.
 * Used by the authorize endpoint AND by tests/dev that need a code directly.
 */
export async function generateAuthCode(params: {
  clientId: string
  redirectUri: string
  scopes: string[]
  uid?: string
  codeChallenge?: string
  codeChallengeMethod?: string
}): Promise<string | null> {
  return createDbAuthCode({
    clientId: params.clientId,
    redirectUri: params.redirectUri,
    scopes: params.scopes,
    uid: params.uid,
    pkceChallenge: params.codeChallenge,
    pkceChallengeMethod: params.codeChallengeMethod,
  })
}

/**
 * Consume an auth code (DB-backed, one-time use). Returns the record or null.
 * Used by the token endpoint.
 */
export async function consumeAuthCode(code: string): Promise<ConsumedAuthCode | null> {
  return consumeDbAuthCode(code)
}

// ── Session verification via platform ────────────────────────────────────────

/**
 * Verify the Firebase __session cookie by calling the platform's session
 * verification endpoint. Returns the Firebase uid or null.
 *
 * The platform already has firebase-admin configured; we delegate rather than
 * running it in the sidecar (no FIREBASE_ADMIN_CREDENTIALS needed in sidecar).
 *
 * Header check (M5/M0.5 lesson): asserts the X-MCP-Internal-Token is actually sent.
 */
async function verifySessionCookieViaPlat(sessionCookie: string): Promise<string | null> {
  try {
    const res = await fetch(`${PLATFORM_URL}/api/auth/verify-session`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,  // actually sent (M5/M0.5 §6 lesson)
      },
      body: JSON.stringify({ session: sessionCookie }),
      signal: AbortSignal.timeout(5_000),
    })
    if (!res.ok) return null
    const data = (await res.json()) as { uid?: string }
    return data.uid ?? null
  } catch (err) {
    console.error('[mcp:authorize] verifySessionCookie error:', err instanceof Error ? err.message : String(err))
    return null
  }
}

// ── State cookie name for CSRF protection ────────────────────────────────────

const STATE_COOKIE = 'mcp_oauth_state'

// ── OAuth authorize handler ──────────────────────────────────────────────────

/**
 * Handle POST /mcp/oauth/authorize
 * Creates a DB-backed auth code and redirects to Firebase login.
 */
export async function handleAuthorize(req: Request, res: Response): Promise<void> {
  const params = req.body as OAuthAuthorizationRequest

  if (!params.client_id || !params.redirect_uri) {
    res.status(400).json({ error: 'invalid_request', error_description: 'client_id and redirect_uri required' })
    return
  }

  if (params.response_type !== 'code') {
    res.status(400).json({ error: 'unsupported_response_type' })
    return
  }

  const requestedScopes = (params.scope ?? 'mcp:tools').split(' ')
  const grantedScopes = requestedScopes.filter(s => VALID_SCOPES.includes(s))

  if (grantedScopes.length === 0) {
    res.status(400).json({ error: 'invalid_scope' })
    return
  }

  // Create a DB-backed auth code (uid is null until Firebase callback).
  const code = await generateAuthCode({
    clientId: params.client_id,
    redirectUri: params.redirect_uri,
    scopes: grantedScopes,
    codeChallenge: params.code_challenge,
    codeChallengeMethod: params.code_challenge_method,
  })

  if (!code) {
    res.status(500).json({ error: 'server_error', error_description: 'Failed to create auth code' })
    return
  }

  // Build state: encodes the code + original redirect_uri + optional state param.
  // Signed with a nonce to prevent CSRF (the nonce is stored in a cookie).
  const nonce = crypto.randomBytes(16).toString('hex')
  const statePayload = JSON.stringify({
    code,
    redirect_uri: params.redirect_uri,
    original_state: params.state ?? '',
    nonce,
  })
  const encodedState = Buffer.from(statePayload).toString('base64url')

  // Set CSRF nonce in a cookie (HttpOnly, SameSite=Lax).
  res.cookie(STATE_COOKIE, nonce, {
    httpOnly: true,
    sameSite: 'lax',
    maxAge: 600,    // 10 minutes
    secure: process.env['NODE_ENV'] === 'production',
  })

  // Redirect to Firebase auth, with our callback URL and state.
  const callbackUrl = `${MCP_BASE_URL}/oauth/callback`
  const firebaseLoginUrl = new URL(FIREBASE_AUTH_URL)
  firebaseLoginUrl.searchParams.set('redirect_uri', callbackUrl)
  firebaseLoginUrl.searchParams.set('state', encodedState)

  res.redirect(302, firebaseLoginUrl.toString())
}

// ── OAuth callback handler ────────────────────────────────────────────────────

/**
 * Handle GET /mcp/oauth/callback
 * Verifies __session cookie, stamps uid onto the auth code, redirects to client.
 */
export async function handleCallback(req: Request, res: Response): Promise<void> {
  const encodedState = typeof req.query['state'] === 'string' ? req.query['state'] : null
  const sessionCookie = req.cookies?.['__session'] as string | undefined

  if (!encodedState) {
    res.status(400).json({ error: 'invalid_request', error_description: 'state param missing' })
    return
  }

  // Decode state.
  let statePayload: { code: string; redirect_uri: string; original_state: string; nonce: string }
  try {
    statePayload = JSON.parse(Buffer.from(encodedState, 'base64url').toString('utf8')) as typeof statePayload
  } catch {
    res.status(400).json({ error: 'invalid_request', error_description: 'state param malformed' })
    return
  }

  // CSRF nonce check.
  const storedNonce = req.cookies?.[STATE_COOKIE] as string | undefined
  if (!storedNonce || storedNonce !== statePayload.nonce) {
    res.status(400).json({ error: 'invalid_request', error_description: 'state nonce mismatch (CSRF protection)' })
    return
  }

  // Verify Firebase __session cookie via platform.
  if (!sessionCookie) {
    // No session cookie: redirect back to Firebase login (not an error — user may need to sign in first).
    const callbackUrl = `${MCP_BASE_URL}/oauth/callback`
    const firebaseLoginUrl = new URL(FIREBASE_AUTH_URL)
    firebaseLoginUrl.searchParams.set('redirect_uri', callbackUrl)
    firebaseLoginUrl.searchParams.set('state', encodedState)
    res.redirect(302, firebaseLoginUrl.toString())
    return
  }

  const uid = await verifySessionCookieViaPlat(sessionCookie)
  if (!uid) {
    res.status(401).json({ error: 'access_denied', error_description: 'Firebase session verification failed' })
    return
  }

  // Stamp the verified uid onto the auth code.
  const stamped = await stampDbAuthCodeUid(statePayload.code, uid)
  if (!stamped) {
    res.status(400).json({ error: 'invalid_grant', error_description: 'Auth code expired or not found' })
    return
  }

  // Clear CSRF cookie.
  res.clearCookie(STATE_COOKIE)

  // Redirect to the client's redirect_uri with the code.
  const redirectUrl = new URL(statePayload.redirect_uri)
  redirectUrl.searchParams.set('code', statePayload.code)
  if (statePayload.original_state) {
    redirectUrl.searchParams.set('state', statePayload.original_state)
  }

  res.redirect(302, redirectUrl.toString())
}
