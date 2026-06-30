/**
 * platform-mcp/src/oauth/token.ts
 *
 * POST /mcp/oauth/token
 * Supports grant_type=authorization_code AND grant_type=client_credentials.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import type { Request, Response } from 'express'
import type { OAuthTokenRequest, OAuthTokenResponse } from './types.js'
import { issueTokens } from './token_store.js'
import { consumeAuthCode } from './authorize.js'

// Client registry (replace with DB in production — table: mcp_oauth_clients)
interface ClientRecord {
  client_id: string
  client_secret: string
  scopes: string[]
  owner_uid: string
}

const CLIENT_REGISTRY = new Map<string, ClientRecord>([
  [
    'test_client',
    {
      client_id: 'test_client',
      client_secret: process.env['MCP_TEST_SECRET'] ?? 'dev_secret',
      scopes: ['mcp:tools', 'mcp:resources', 'mcp:prompts'],
      owner_uid: 'test_uid',
    },
  ],
])

function validateClient(clientId: string, clientSecret?: string): ClientRecord | null {
  const client = CLIENT_REGISTRY.get(clientId)
  if (!client) return null
  if (clientSecret && client.client_secret !== clientSecret) return null
  return client
}

export async function handleToken(req: Request, res: Response): Promise<void> {
  const params = req.body as OAuthTokenRequest

  if (!params.grant_type) {
    res.status(400).json({ error: 'invalid_request', error_description: 'grant_type required' })
    return
  }

  // grant_type: client_credentials
  if (params.grant_type === 'client_credentials') {
    const client = validateClient(params.client_id, params.client_secret)
    if (!client) {
      res.status(401).json({ error: 'invalid_client' })
      return
    }

    const tokens = issueTokens(client.owner_uid, client.scopes)
    const response: OAuthTokenResponse = {
      access_token: tokens.access_token,
      token_type: 'Bearer',
      expires_in: tokens.expires_in,
      refresh_token: tokens.refresh_token,
      scope: tokens.scope,
    }
    res.json(response)
    return
  }

  // grant_type: authorization_code
  if (params.grant_type === 'authorization_code') {
    if (!params.code) {
      res.status(400).json({ error: 'invalid_request', error_description: 'code required' })
      return
    }

    const authCode = consumeAuthCode(params.code)
    if (!authCode) {
      res.status(400).json({ error: 'invalid_grant', error_description: 'code expired or invalid' })
      return
    }

    // PKCE verification
    if (authCode.code_challenge && params.code_verifier) {
      const crypto = await import('crypto')
      const challenge = crypto.createHash('sha256')
        .update(params.code_verifier)
        .digest('base64url')
      if (challenge !== authCode.code_challenge) {
        res.status(400).json({ error: 'invalid_grant', error_description: 'code_verifier mismatch' })
        return
      }
    }

    // M0: fail-closed — do not mint a token with 'anonymous' uid; it would fail the
    // entitlement gate opaquely. Full DB-backed OAuth with verified uid is M5.
    if (!authCode.uid || authCode.uid === 'anonymous') {
      res.status(400).json({ error: 'invalid_grant', error_description: 'authorization code carries no verified uid; full OAuth identity is not yet supported (M5)' })
      return
    }
    const tokens = issueTokens(authCode.uid, authCode.scopes)
    const response: OAuthTokenResponse = {
      access_token: tokens.access_token,
      token_type: 'Bearer',
      expires_in: tokens.expires_in,
      refresh_token: tokens.refresh_token,
      scope: tokens.scope,
    }
    res.json(response)
    return
  }

  // grant_type: refresh_token
  if (params.grant_type === 'refresh_token') {
    if (!params.refresh_token) {
      res.status(400).json({ error: 'invalid_request' })
      return
    }

    const { refreshAccessToken } = await import('./token_store.js')
    const newTokens = refreshAccessToken(params.refresh_token)
    if (!newTokens) {
      res.status(400).json({ error: 'invalid_grant', error_description: 'refresh_token expired or invalid' })
      return
    }

    res.json({
      access_token: newTokens.access_token,
      token_type: 'Bearer',
      expires_in: newTokens.expires_in,
      refresh_token: newTokens.refresh_token,
      scope: newTokens.scope,
    } as OAuthTokenResponse)
    return
  }

  res.status(400).json({ error: 'unsupported_grant_type' })
}
