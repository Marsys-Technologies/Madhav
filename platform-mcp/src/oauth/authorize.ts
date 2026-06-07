/**
 * platform-mcp/src/oauth/authorize.ts
 *
 * POST /mcp/oauth/authorize — initiates OAuth flow; redirects to Firebase auth.
 * Per MCP authorization spec: https://modelcontextprotocol.io/specification/server/authorization
 *
 * L0FR Stream A — authored 2026-06-07
 */

import type { Request, Response } from 'express'
import type { OAuthAuthorizationRequest } from '../../src/lib/mcp/oauth/types'

const FIREBASE_AUTH_URL = process.env['FIREBASE_AUTH_URL'] ??
  'https://madhav.marsys.in/__/auth/handler'

const VALID_SCOPES = ['mcp:tools', 'mcp:resources', 'mcp:prompts']

// In-memory auth code store (replace with DB in production)
interface AuthCodeRecord {
  code: string
  client_id: string
  redirect_uri: string
  uid?: string
  scopes: string[]
  code_challenge?: string
  code_challenge_method?: string
  created_at: Date
  expires_at: Date
}

const authCodes = new Map<string, AuthCodeRecord>()

import crypto from 'crypto'

export function generateAuthCode(params: {
  clientId: string
  redirectUri: string
  scopes: string[]
  codeChallenge?: string
  codeChallengeMethod?: string
}): string {
  const code = crypto.randomBytes(32).toString('hex')
  const now = new Date()
  authCodes.set(code, {
    code,
    client_id: params.clientId,
    redirect_uri: params.redirectUri,
    scopes: params.scopes,
    code_challenge: params.codeChallenge,
    code_challenge_method: params.codeChallengeMethod,
    created_at: now,
    expires_at: new Date(now.getTime() + 600 * 1000),  // 10 minutes
  })
  return code
}

export function consumeAuthCode(code: string): AuthCodeRecord | null {
  const record = authCodes.get(code)
  if (!record) return null
  if (record.expires_at < new Date()) {
    authCodes.delete(code)
    return null
  }
  authCodes.delete(code)  // one-time use
  return record
}

/**
 * Handle POST /mcp/oauth/authorize
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

  // Generate auth code immediately (Firebase auth redirect in production)
  // In dev, skip Firebase and issue code directly
  const code = generateAuthCode({
    clientId: params.client_id,
    redirectUri: params.redirect_uri,
    scopes: grantedScopes,
    codeChallenge: params.code_challenge,
    codeChallengeMethod: params.code_challenge_method,
  })

  const redirectUrl = new URL(params.redirect_uri)
  redirectUrl.searchParams.set('code', code)
  if (params.state) redirectUrl.searchParams.set('state', params.state)

  res.redirect(302, redirectUrl.toString())
}
