/**
 * client.ts — HTTP client for calling the MARSYS platform from the MCP server.
 *
 * All outbound calls from platform-mcp → platform route through this module.
 * This centralises:
 *   - Service-to-service identity token acquisition (GCP metadata server or
 *     SERVICE_TOKEN env var for local dev).
 *   - X-MCP-* principal headers (resolved from Bearer key validation).
 *   - Error handling: network errors return clean error envelopes; no
 *     thrown exceptions propagate to the MCP tool layer.
 *
 * Exports:
 *   callPlatform()          → /api/mcp/execute   (ask_madhav, execute_plan)
 *   callPlatformPlan()      → /api/mcp/plan       (plan_query)
 *   callPlatformPrimitive() → /api/mcp/primitives/{toolName}
 *
 * Environment variables:
 *   PLATFORM_URL          — base URL of the amjis-web Cloud Run service
 *   MCP_INTERNAL_TOKEN    — shared secret for X-MCP-Internal-Token header
 *   SERVICE_TOKEN         — static identity token override (local dev only)
 */

import type { McpToolCall, McpEnvelope, PlatformCallResult, Principal } from './types.js'

// ── Configuration ─────────────────────────────────────────────────────────────

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

// ── Identity token acquisition ────────────────────────────────────────────────

/**
 * Fetch a Cloud Run service-to-service identity token.
 *
 * In production: queries the GCP metadata server for an OIDC token with
 * audience set to the platform URL.
 *
 * In local dev: falls back to the SERVICE_TOKEN env var, then to the
 * MCP_INTERNAL_TOKEN (which is used as the X-MCP-Internal-Token header
 * on the platform side, not as a Bearer token, but works for local routing).
 */
async function fetchIdentityToken(): Promise<string> {
  // Local dev override
  const staticToken = process.env['SERVICE_TOKEN']
  if (staticToken) return staticToken

  // GCP metadata server
  const metadataUrl =
    `http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity` +
    `?audience=${encodeURIComponent(PLATFORM_URL)}`

  try {
    const response = await fetch(metadataUrl, {
      headers: { 'Metadata-Flavor': 'Google' },
      signal: AbortSignal.timeout(3000),
    })
    if (!response.ok) {
      throw new Error(`Metadata server returned ${response.status}`)
    }
    return await response.text()
  } catch (err) {
    // Not running on GCP — use internal token as the bearer
    if (MCP_INTERNAL_TOKEN) return MCP_INTERNAL_TOKEN
    console.warn('[mcp:client] No identity token available; calls will likely fail auth.')
    return ''
  }
}

// ── Error envelope helper ─────────────────────────────────────────────────────

function buildClientErrorEnvelope(
  message: string,
  errorClass: 'internal' | 'auth' | 'validation' = 'internal'
): McpEnvelope {
  return {
    ok: false,
    trace_id: '',
    error: {
      class: errorClass,
      message,
      remediation: 'Check platform-mcp logs for details',
    },
  }
}

// ── Common fetch helper ───────────────────────────────────────────────────────

interface PlatformFetchOptions {
  url: string
  body: Record<string, unknown>
  principal: Principal
  identityToken: string
}

async function platformFetch(opts: PlatformFetchOptions): Promise<PlatformCallResult> {
  const { url, body, principal, identityToken } = opts

  let response: Response
  try {
    response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Service-to-service auth (Layer 1)
        'Authorization': `Bearer ${identityToken}`,
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
        // Resolved principal (Layer 2)
        'X-MCP-User': principal.user_uid,
        'X-MCP-Audience-Tier': principal.audience_tier,
        'X-MCP-Key-Id': principal.key_id,
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(125_000),  // slightly above platform maxDuration=120s
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return {
      status: 503,
      envelope: buildClientErrorEnvelope(`Platform unreachable: ${message}`),
    }
  }

  let envelope: McpEnvelope
  try {
    envelope = (await response.json()) as McpEnvelope
  } catch {
    return {
      status: 502,
      envelope: buildClientErrorEnvelope('Platform returned non-JSON response'),
    }
  }

  return { status: response.status, envelope }
}

// ── Exported call functions ───────────────────────────────────────────────────

/**
 * Call /api/mcp/execute for ask_madhav or execute_plan.
 *
 * @param toolCall  The tool name and params to send to the platform.
 * @param principal The resolved principal (user_uid, audience_tier, key_id).
 * @returns         The HTTP status code and parsed McpEnvelope.
 */
export async function callPlatform(
  toolCall: McpToolCall,
  principal: Principal
): Promise<PlatformCallResult> {
  const identityToken = await fetchIdentityToken()
  return platformFetch({
    url: `${PLATFORM_URL}/api/mcp/execute`,
    body: { tool: toolCall.tool, params: toolCall.params },
    principal,
    identityToken,
  })
}

/**
 * Call /api/mcp/plan for plan_query (planner only, no execution).
 *
 * @param query     The question to plan.
 * @param principal The resolved principal.
 * @returns         The HTTP status code and parsed McpEnvelope (result = PipelinePlan).
 */
export async function callPlatformPlan(
  query: string,
  principal: Principal
): Promise<PlatformCallResult> {
  const identityToken = await fetchIdentityToken()
  // The /api/mcp/execute endpoint handles plan_query as a tool dispatch.
  return platformFetch({
    url: `${PLATFORM_URL}/api/mcp/execute`,
    body: { tool: 'plan_query', params: { query } },
    principal,
    identityToken,
  })
}

/**
 * Call /api/mcp/primitives/{toolName} for surgical primitive tool invocations.
 * (Phase MCP-3-S1 creates these endpoints; this function is wired but may
 * return 404 until that session ships.)
 *
 * @param toolName  The primitive tool name (e.g. "chart_facts_query").
 * @param params    Tool-specific parameters.
 * @param principal The resolved principal.
 * @returns         The HTTP status code and parsed McpEnvelope.
 */
export async function callPlatformPrimitive(
  toolName: string,
  params: Record<string, unknown>,
  principal: Principal
): Promise<PlatformCallResult> {
  const identityToken = await fetchIdentityToken()
  return platformFetch({
    url: `${PLATFORM_URL}/api/mcp/primitives/${encodeURIComponent(toolName)}`,
    body: { params },
    principal,
    identityToken,
  })
}
