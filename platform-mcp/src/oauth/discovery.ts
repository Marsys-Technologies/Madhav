/**
 * platform-mcp/src/oauth/discovery.ts
 *
 * GET /mcp/.well-known/oauth-authorization-server
 * GET /mcp/.well-known/openid-configuration
 *
 * OAuth discovery metadata for ChatGPT MCP discovery.
 * Per MCP authorization spec + ChatGPT connector requirements.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import type { Request, Response } from 'express'
import type { OAuthDiscoveryMetadata } from './types.js'

const BASE_URL = (process.env['MCP_BASE_URL'] ?? 'https://madhav.marsys.in/mcp').replace(/\/$/, '')

export interface ExtendedDiscoveryMetadata extends OAuthDiscoveryMetadata {
  registration_endpoint?: string
}

export function buildDiscoveryMetadata(): ExtendedDiscoveryMetadata {
  return {
    issuer: BASE_URL,
    authorization_endpoint: `${BASE_URL}/oauth/authorize`,
    token_endpoint: `${BASE_URL}/oauth/token`,
    // M5: dynamic client registration (RFC 7591)
    registration_endpoint: `${BASE_URL}/oauth/register`,
    // W5 L2: advertise the profile-selecting scopes (mcp:profile:full/compact/consult)
    // alongside the existing resource-shape scopes — see oauth/authorize.ts's VALID_SCOPES.
    scopes_supported: [
      'mcp:tools', 'mcp:resources', 'mcp:prompts',
      'mcp:profile:full', 'mcp:profile:compact', 'mcp:profile:consult',
    ],
    response_types_supported: ['code'],
    grant_types_supported: ['authorization_code', 'client_credentials', 'refresh_token'],
    token_endpoint_auth_methods_supported: ['client_secret_post', 'client_secret_basic', 'none'],
    code_challenge_methods_supported: ['S256'],
  }
}

export function handleOAuthDiscovery(_req: Request, res: Response): void {
  res.json(buildDiscoveryMetadata())
}

export function handleOpenIDConfiguration(_req: Request, res: Response): void {
  const meta = buildDiscoveryMetadata()
  // ChatGPT looks for OIDC-style discovery; map to our endpoints
  res.json({
    ...meta,
    // OIDC additions ChatGPT expects
    subject_types_supported: ['public'],
    id_token_signing_alg_values_supported: ['RS256'],
    claims_supported: ['sub', 'iss', 'aud', 'exp', 'iat'],
  })
}
