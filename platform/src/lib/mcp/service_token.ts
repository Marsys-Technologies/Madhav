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
import { constantTimeEquals } from '@/lib/mcp/constant_time'
import { verifyOidcToken } from '@/lib/auth/oidc'

/**
 * Validate the X-MCP-Internal-Token header against MCP_INTERNAL_TOKEN.
 * Returns false (reject) whenever the header is missing/mismatched, or
 * whenever MCP_INTERNAL_TOKEN itself is unset/empty — no exceptions.
 *
 * SF-005: this compares a raw shared secret on a publicly-routable route,
 * so a plain `===` (which short-circuits at the first differing byte) is
 * an observable timing side-channel. Comparison goes through
 * `constantTimeEquals` (hash-then-`timingSafeEqual`) instead. `token` is
 * checked for null before the compare so the constant-time path only ever
 * receives strings.
 */
export function validateServiceToken(req: Request): boolean {
  const token = req.headers.get('x-mcp-internal-token')
  const expected = process.env.MCP_INTERNAL_TOKEN
  if (!expected) {
    console.error('[mcp:service_token] MCP_INTERNAL_TOKEN not set — rejecting all service-token requests (fail-closed)')
    return false
  }
  if (token === null) return false
  return constantTimeEquals(token, expected)
}

/**
 * Pūrṇa's internal MCP routes require both the rotated shared service secret and
 * a Google-signed identity token bound to the web service and MCP runtime SA.
 * The explicit local-only escape hatch keeps non-GCP development possible; it
 * is ignored in production and is never set by the deployment workflow.
 */
export async function validateMcpServiceRequest(req: Request): Promise<boolean> {
  if (!validateServiceToken(req)) return false
  if (process.env.NODE_ENV !== 'production'
      && process.env.MCP_CALLER_OIDC_DISABLED_FOR_LOCAL_DEV === 'true') return true

  const expectedAudience = process.env.MCP_CALLER_OIDC_AUDIENCE
  const expectedServiceAccount = process.env.MCP_CALLER_OIDC_SERVICE_ACCOUNT
  const authorization = req.headers.get('authorization')
  if (!expectedAudience || !expectedServiceAccount || !authorization?.startsWith('Bearer ')) {
    return false
  }

  try {
    return Boolean(await verifyOidcToken(authorization.slice('Bearer '.length), {
      expectedAudience,
      expectedServiceAccount,
    }))
  } catch {
    return false
  }
}
