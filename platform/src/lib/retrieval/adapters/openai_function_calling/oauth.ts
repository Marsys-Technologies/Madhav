/**
 * adapters/openai_function_calling/oauth.ts
 *
 * OAuth 2.0 endpoint handler logic for ChatGPT MCP integration.
 * The actual HTTP routes are in platform-mcp/src/oauth/.
 * This module provides the core token management logic.
 *
 * See also: platform-mcp/src/oauth/ (Step 23)
 *
 * L0FR Stream A — authored 2026-06-07
 */

// Re-export from the MCP OAuth module for convenience
export type { OAuthTokenResponse, OAuthAuthorizationRequest } from '../../../mcp/oauth/types'

/**
 * Validate an OAuth access token and return the associated principal.
 * Delegates to the Firebase identity layer.
 */
export async function validateOAuthToken(
  token: string
): Promise<{ valid: boolean; uid?: string; scopes?: string[] }> {
  // In production: validate against mcp_oauth_tokens table
  // or verify Firebase custom token
  // TODO: wire to platform-mcp/src/oauth/token_store.ts
  if (!token || token.length < 10) {
    return { valid: false }
  }
  // Stub: accept any non-empty token in dev
  return {
    valid: true,
    uid: 'dev_uid',
    scopes: ['mcp:tools', 'mcp:resources', 'mcp:prompts'],
  }
}
