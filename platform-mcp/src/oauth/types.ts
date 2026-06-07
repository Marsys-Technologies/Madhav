/**
 * MCP OAuth 2.0 types for platform-mcp
 * Mirrors platform/src/lib/mcp/oauth/types.ts — kept local to avoid cross-package imports.
 * L0FR Stream A — authored 2026-06-07
 */

export interface OAuthTokenResponse {
  access_token: string
  token_type: 'Bearer'
  expires_in: number    // seconds (3600 = 1 hour)
  refresh_token?: string
  scope: string
}

export interface OAuthAuthorizationRequest {
  response_type: 'code'
  client_id: string
  redirect_uri: string
  scope: string
  state?: string
  code_challenge?: string
  code_challenge_method?: 'S256' | 'plain'
}

export interface OAuthTokenRequest {
  grant_type: 'authorization_code' | 'client_credentials' | 'refresh_token'
  client_id: string
  client_secret?: string
  code?: string
  redirect_uri?: string
  refresh_token?: string
  code_verifier?: string
}

export interface OAuthDiscoveryMetadata {
  issuer: string
  authorization_endpoint: string
  token_endpoint: string
  jwks_uri?: string
  scopes_supported: string[]
  response_types_supported: string[]
  grant_types_supported: string[]
  token_endpoint_auth_methods_supported: string[]
  code_challenge_methods_supported: string[]
}
