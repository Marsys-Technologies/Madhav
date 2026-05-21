/**
 * auth.ts — Bearer key validation for the platform-mcp MCP server.
 *
 * Validates incoming Bearer tokens from MCP clients (Claude Chat, Cowork)
 * by calling back to the platform's /api/mcp/keys/validate endpoint.
 *
 * Architecture decision (MCP_BRIEF §5.1, Item 8): call-through to platform
 * is the correct approach — the MCP server has no direct DB connection.
 * Validation is delegated to the platform, which uses the same PBKDF2-SHA256
 * verification and timing-safe comparison that MCP-1-S1 implemented.
 *
 * Returns: Principal on success, null on any auth failure.
 * Never throws — callers receive null on error.
 */

import type { Principal, KeyValidateResponse } from './types.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

/**
 * Validate the Authorization header from an incoming MCP request.
 *
 * Calls GET /api/mcp/keys/validate with the raw Authorization header forwarded.
 * Uses the X-MCP-Internal-Token service secret so the platform trusts the caller.
 *
 * @param authorizationHeader  The raw "Authorization" header value (e.g. "Bearer mcp_prod_...").
 * @returns  Principal on success, null on any failure (invalid key, network error, etc.).
 */
export async function validateMcpKeyFromHeader(
  authorizationHeader: string | undefined
): Promise<Principal | null> {
  if (!authorizationHeader) return null

  try {
    const response = await fetch(`${PLATFORM_URL}/api/mcp/keys/validate`, {
      method: 'GET',
      headers: {
        'Authorization': authorizationHeader,
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      },
      signal: AbortSignal.timeout(5000),
    })

    if (!response.ok) {
      // 401 from the platform means our service token is wrong (config issue)
      console.error(`[mcp:auth] Validate endpoint returned ${response.status}`)
      return null
    }

    const data = (await response.json()) as KeyValidateResponse

    if (!data.valid || !data.user_uid || !data.audience_tier || !data.key_id) {
      return null
    }

    return {
      user_uid: data.user_uid,
      audience_tier: data.audience_tier,
      key_id: data.key_id,
    }
  } catch (err) {
    console.error('[mcp:auth] Key validation network error:', err instanceof Error ? err.message : String(err))
    return null
  }
}
