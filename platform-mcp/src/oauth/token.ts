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

    // RATE-07 layer 2 (PARIŚEṢA-V4) — charged ONLY when a secret was actually
    // presented and therefore actually verified.
    //
    // ⚠️ WHY THE GUARD, AND A DISCLOSED PRE-EXISTING DEFECT: an earlier draft of
    // this code charged `params.client_id` unconditionally here, on the stated
    // premise that validateOAuthClient() above had "proven" it. An adversarial
    // security review showed that premise is FALSE. `validateClient`
    // (platform/src/lib/mcp/oauth/store.ts) verifies the secret only
    // `if (clientSecret !== undefined)`, and `validateOAuthClient`'s
    // JSON.stringify drops an undefined `client_secret` from the request body
    // entirely — so a client_credentials request carrying NO secret skips
    // verification and is reported valid. Charging on that would have handed
    // any anonymous caller a quota-poisoning primitive against a named client:
    // client_ids travel in authorize requests and redirects, so they are not
    // secret.
    //
    // Gating the charge on a presented secret makes THIS code's premise true.
    // It does NOT fix the underlying hole — that a secretless
    // client_credentials request is honoured at all, and receives real tokens
    // for the client's owner_uid — which is a pre-existing authentication
    // defect out of RATE-07's scope, disclosed in the PR for its own triage
    // rather than silently patched inside a rate-limiting change.
    //
    // The per-IP + route-global buckets were already charged by the
    // `oauthRateLimit('oauth_token')` middleware before this handler ran, so a
    // secretless caller is still rate limited — just not against a bucket
    // belonging to an identity it has not proven.
    // chargeValidatedSubject writes the 429/503 response itself when it denies.
    // Charged on `clientResult.owner_uid` — the identity the validation step
    // itself RESOLVED — rather than on `params.client_id`, which is request
    // input reached through the `params` alias. Same reason as above: the
    // subject of a post-validation bucket must come out of the validation
    // result, never back out of the request.
    if (params.client_secret) {
      if (!(await chargeValidatedSubject(res, 'oauth_token', 'principal', clientResult.owner_uid))) {
        return
      }
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

    // Authorization-code binding (SF-004, PARIŚEṢA-V4).
    //
    // RFC 6749 §4.1.3: the token endpoint MUST ensure the authorization code
    // was issued to the client identified by client_id, and — if redirect_uri
    // was included in the authorization request — MUST ensure it matches
    // exactly. `mcp_oauth_auth_codes.redirect_uri` is NOT NULL, so it was
    // always included; it is therefore REQUIRED here, not merely checked when
    // present. Exact string match only, same rule as /authorize — see
    // SF004_OAUTH_BINDING_CONTRACT_v1_0.md §2–§3. Before this fix, nothing
    // compared the redeeming request's client_id/redirect_uri against the
    // values stamped on the code at issuance — no client authentication of
    // any kind gated code redemption.
    if (params.client_id !== authCode.client_id) {
      res.status(400).json({ error: 'invalid_grant', error_description: 'client_id does not match the authorization code' })
      return
    }
    if (typeof params.redirect_uri !== 'string' || params.redirect_uri.length === 0) {
      res.status(400).json({ error: 'invalid_grant', error_description: 'redirect_uri required' })
      return
    }
    if (params.redirect_uri !== authCode.redirect_uri) {
      res.status(400).json({ error: 'invalid_grant', error_description: 'redirect_uri does not match the authorization code' })
      return
    }

    // PKCE verification (SF-003, PARIŚEṢA-V4).
    //
    // RFC 7636 §4.6: "the token endpoint MUST verify [code_verifier] ... if the
    // authorization request included the code_challenge parameter." If a
    // code_challenge was registered, code_verifier is REQUIRED at redemption — its
    // absence MUST be rejected, not silently accepted.
    //
    // The prior form of this check was `if (authCode.pkce_challenge &&
    // params.code_verifier)` — a bare `&&` guard around the whole verification. That
    // let an attacker who intercepted/stole an authorization code (redirect
    // interception, browser history, a malicious app on the same custom URI scheme)
    // simply OMIT code_verifier and redeem the code anyway, because the entire
    // verification block was skipped rather than failed. The client asked for PKCE
    // protection at /authorize; the server silently withdrew it at /token for anyone
    // who chose not to present a verifier. Fixed by splitting the `&&` into an outer
    // "was PKCE requested" gate with an inner "verifier missing -> reject" branch, so
    // a registered challenge can no longer be bypassed by omission.
    if (authCode.pkce_challenge) {
      // typeof guard (not just truthiness): a JSON body can carry a non-string
      // code_verifier (array/object). Without this, such a value can slip past a
      // bare falsiness check and a regex .test() (which coerces to string), then
      // throw inside crypto's .update() below — an unhandled exception instead of
      // a clean 400. Checking the type up front keeps every rejection in this
      // block a deliberate 400, never a crash.
      if (typeof params.code_verifier !== 'string' || params.code_verifier.length === 0) {
        res.status(400).json({ error: 'invalid_grant', error_description: 'code_verifier required' })
        return
      }

      // RFC 7636 §4.1: code_verifier is 43-128 characters from the unreserved
      // charset [A-Z a-z 0-9 - . _ ~]. Reject malformed input before it reaches
      // crypto rather than hashing garbage.
      if (!/^[A-Za-z0-9\-._~]{43,128}$/.test(params.code_verifier)) {
        res.status(400).json({ error: 'invalid_grant', error_description: 'code_verifier malformed' })
        return
      }

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
