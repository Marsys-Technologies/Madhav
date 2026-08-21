/**
 * platform-mcp/src/oauth/token.ts
 *
 * POST /mcp/oauth/token
 * Supports grant_type=authorization_code AND grant_type=client_credentials.
 *
 * M5: hardcoded test_client replaced with DB lookup via platform API.
 * M5: authorization_code grant uses DB-backed code consumption.
 * M5: token issuance is DB-backed (tokens survive restart + multi-instance).
 *
 * One identity core: both grant types yield a uid from which resolveMcpPrincipal
 * can build the Principal {user_uid, role}.
 *
 * L0FR Stream A — authored 2026-06-07; rewritten M5 2026-07-01.
 */

import type { Request, Response } from 'express'
import type { OAuthTokenRequest, OAuthTokenResponse } from './types.js'
import { issueTokens, refreshAccessToken } from './token_store.js'
import { consumeAuthCode } from './authorize.js'
import { validateOAuthClient } from './oauth_platform_client.js'
import { chargeValidatedSubject } from '../lib/oauth_rate_limit.js'

export async function handleToken(req: Request, res: Response): Promise<void> {
  const params = req.body as OAuthTokenRequest

  if (!params.grant_type) {
    res.status(400).json({ error: 'invalid_request', error_description: 'grant_type required' })
    return
  }

  // ── grant_type: client_credentials ──────────────────────────────────────────
  if (params.grant_type === 'client_credentials') {
    if (!params.client_id) {
      res.status(400).json({ error: 'invalid_request', error_description: 'client_id required' })
      return
    }

    // DB-backed client validation (replaces hardcoded CLIENT_REGISTRY Map).
    const clientResult = await validateOAuthClient(params.client_id, params.client_secret)
    if (!clientResult.valid) {
      res.status(401).json({ error: 'invalid_client' })
      return
    }

    // Fail-closed: owner_uid must be a real Firebase uid.
    if (!clientResult.owner_uid || clientResult.owner_uid === 'anonymous') {
      res.status(400).json({ error: 'invalid_client', error_description: 'client has no verified owner_uid' })
      return
    }

    // RATE-07 layer 2 (PARIŚEṢA-V4): the client_id has now been proven — its
    // secret was checked above — so a per-client bucket can be charged without
    // creating a quota-poisoning primitive. Charging on `params.client_id`
    // BEFORE validateOAuthClient() would have let any anonymous caller exhaust a
    // named client's token quota just by naming it. The route-wide IP + global
    // buckets were already charged by the `oauthRateLimit('oauth_token')`
    // middleware in server.ts before this handler ran.
    // chargeValidatedSubject writes the 429/503 response itself when it denies.
    if (!(await chargeValidatedSubject(res, 'oauth_token', 'client', params.client_id))) {
      return
    }

    let tokens: Awaited<ReturnType<typeof issueTokens>>
    try {
      tokens = await issueTokens(clientResult.owner_uid, clientResult.scopes)
    } catch {
      res.status(500).json({ error: 'server_error', error_description: 'Token issuance failed' })
      return
    }

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

  // ── grant_type: authorization_code ──────────────────────────────────────────
  if (params.grant_type === 'authorization_code') {
    if (!params.code) {
      res.status(400).json({ error: 'invalid_request', error_description: 'code required' })
      return
    }

    // DB-backed code consumption (replaces in-memory authCodes Map).
    const authCode = await consumeAuthCode(params.code)
    if (!authCode) {
      res.status(400).json({ error: 'invalid_grant', error_description: 'code expired or invalid' })
      return
    }

    // PKCE verification.
    if (authCode.pkce_challenge && params.code_verifier) {
      const crypto = await import('crypto')
      const challenge = crypto.createHash('sha256')
        .update(params.code_verifier)
        .digest('base64url')
      if (challenge !== authCode.pkce_challenge) {
        res.status(400).json({ error: 'invalid_grant', error_description: 'code_verifier mismatch' })
        return
      }
    }

    // M0 fail-closed behaviour preserved (M5: uid is now a real Firebase uid from the callback).
    // The auth code uid is NULL until the Firebase round-trip in handleCallback completes.
    if (!authCode.uid || authCode.uid === 'anonymous') {
      res.status(400).json({
        error: 'invalid_grant',
        error_description: 'authorization code carries no verified uid; complete the OAuth flow via the browser',
      })
      return
    }

    let tokens: Awaited<ReturnType<typeof issueTokens>>
    try {
      tokens = await issueTokens(authCode.uid, authCode.scopes)
    } catch {
      res.status(500).json({ error: 'server_error', error_description: 'Token issuance failed' })
      return
    }

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

  // ── grant_type: refresh_token ────────────────────────────────────────────────
  if (params.grant_type === 'refresh_token') {
    if (!params.refresh_token) {
      res.status(400).json({ error: 'invalid_request' })
      return
    }

    const newTokens = await refreshAccessToken(params.refresh_token)
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
