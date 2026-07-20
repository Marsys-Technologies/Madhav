/**
 * service_token.ts — shared service-to-service token guard.
 *
 * Every /api/mcp/*, /api/retrieval/capability, and /api/auth/verify-session
 * route validates the `X-MCP-Internal-Token` header against
 * `process.env.MCP_INTERNAL_TOKEN` before doing any work. This was
 * previously 20 duplicated local copies of the same function (RETRIEVAL_
 * PLANE_ELEVATION_PLAN_v1_0.md §9.1, GT-44) — consolidated here.
 *
 * FAIL-CLOSED, UNCONDITIONALLY: if MCP_INTERNAL_TOKEN is unset or empty,
 * every request is rejected — there is no NODE_ENV==='development' bypass.
 * A local dev environment must set MCP_INTERNAL_TOKEN in its own .env
 * (see platform/.env.local.example); relying on an env-name string match
 * is a pattern that misconfigured production code can also satisfy.
 */

import 'server-only'

/**
 * Validate the X-MCP-Internal-Token header against MCP_INTERNAL_TOKEN.
 * Returns false (reject) whenever the header is missing/mismatched, or
 * whenever MCP_INTERNAL_TOKEN itself is unset/empty — no exceptions.
 */
export function validateServiceToken(req: Request): boolean {
  const token = req.headers.get('x-mcp-internal-token')
  const expected = process.env.MCP_INTERNAL_TOKEN
  if (!expected) {
    console.error('[mcp:service_token] MCP_INTERNAL_TOKEN not set — rejecting all service-token requests (fail-closed)')
    return false
  }
  return token === expected
}
