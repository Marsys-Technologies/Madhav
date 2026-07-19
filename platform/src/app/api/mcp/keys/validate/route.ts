/**
 * /api/mcp/keys/validate — Bearer token validation endpoint for the MCP server.
 *
 * Called by platform-mcp/src/auth.ts to validate an incoming Bearer key from
 * an external client before forwarding the request to /api/mcp/execute.
 *
 * Auth model: the MCP server calls this endpoint using the same
 * X-MCP-Internal-Token service-to-service header it uses for /api/mcp/execute.
 * This ensures only the trusted amjis-mcp service can call the validation endpoint.
 *
 * Request:
 *   GET /api/mcp/keys/validate
 *   Authorization: Bearer <external-api-key>
 *   X-MCP-Internal-Token: <service-secret>
 *
 * Response (200 always; check valid field):
 *   { valid: true,  user_uid, key_id }  — on success
 *   { valid: false, error: "reason" }   — on failure
 *
 * audience_tier removed (Stream A 3.tier_excision 2026-05-28).
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { validateMcpKey } from '@/lib/mcp/auth'
import { validateServiceToken } from '@/lib/mcp/service_token'

export async function GET(request: Request) {
  // Service-to-service auth
  if (!validateServiceToken(request)) {
    return NextResponse.json({ valid: false, error: 'Unauthorized' }, { status: 401 })
  }

  // Validate the Bearer key in the Authorization header
  const authHeader = request.headers.get('authorization')
  const principal = await validateMcpKey(authHeader)

  if (!principal) {
    return NextResponse.json({ valid: false, error: 'Invalid or revoked API key' })
  }

  return NextResponse.json({
    valid: true,
    user_uid: principal.user_uid,
    // audience_tier removed (Stream A 3.tier_excision 2026-05-28).
    key_id: principal.key_id,
    role: principal.role,
    // M6: per-key model family binding (null = undeclared → universal-best).
    model_family: principal.model_family ?? null,
  })
}
