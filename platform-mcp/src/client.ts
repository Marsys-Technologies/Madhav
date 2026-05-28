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
 *   callPlatformPrimitive() → /api/mcp/primitives/{toolName}
 *
 * (callPlatform / callPlatformPlan deleted by Stream A unit 3.legacy_delete
 * 2026-05-28 — /api/mcp/execute endpoint retired alongside the legacy
 * synthesis orchestrator trio.)
 *
 * Environment variables:
 *   PLATFORM_URL          — base URL of the amjis-web Cloud Run service
 *   MCP_INTERNAL_TOKEN    — shared secret for X-MCP-Internal-Token header
 *   SERVICE_TOKEN         — static identity token override (local dev only)
 */

import type { McpEnvelope, PlatformCallResult, Principal } from './types.js'
import { GoogleAuth, type IdTokenClient } from 'google-auth-library'

// ── Configuration ─────────────────────────────────────────────────────────────

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

// ── Identity token acquisition (Wave 4 4.edge_and_infra_hygiene) ─────────────
//
// Service-to-service auth uses google-auth-library to mint OIDC ID tokens
// scoped to the target audience (PLATFORM_URL). google-auth-library handles:
//   - GCP metadata server in production (under amjis-mcp-runtime SA).
//   - Application Default Credentials (ADC) for local dev / `gcloud auth`.
//   - Token caching + refresh.
//
// Falls back to:
//   - SERVICE_TOKEN env var (explicit override for tests).
//   - MCP_INTERNAL_TOKEN as a Bearer token (legacy / non-GCP environments).

let cachedIdTokenClient: IdTokenClient | null = null

async function getIdTokenClient(): Promise<IdTokenClient> {
  if (cachedIdTokenClient) return cachedIdTokenClient
  const auth = new GoogleAuth()
  cachedIdTokenClient = await auth.getIdTokenClient(PLATFORM_URL)
  return cachedIdTokenClient
}

/**
 * Fetch a Cloud Run service-to-service identity token via google-auth-library.
 * The returned token is an OIDC ID token bound to the PLATFORM_URL audience;
 * Cloud Run's IAM gate (`run.invoker` role on amjis-web for amjis-mcp-runtime)
 * accepts it.
 */
async function fetchIdentityToken(): Promise<string> {
  // Explicit override (tests + local dev).
  const staticToken = process.env['SERVICE_TOKEN']
  if (staticToken) return staticToken

  try {
    const client = await getIdTokenClient()
    const headers = await client.getRequestHeaders(PLATFORM_URL)
    const authHeader = (headers as Record<string, string>)['Authorization'] ?? ''
    // Strip the leading "Bearer " prefix to return only the raw token.
    if (authHeader.startsWith('Bearer ')) return authHeader.slice(7)
    return authHeader
  } catch (err) {
    // Not running on GCP and no ADC — fall back to internal token.
    if (MCP_INTERNAL_TOKEN) return MCP_INTERNAL_TOKEN
    console.warn(
      '[mcp:client] No identity token available; calls will likely fail auth.',
      err instanceof Error ? err.message : String(err)
    )
    return ''
  }
}

// Exposed for tests — lets the test suite reset the cached client between cases.
export function __resetIdentityTokenCacheForTests(): void {
  cachedIdTokenClient = null
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
        // X-MCP-Audience-Tier header removed (Stream A 3.tier_excision 2026-05-28).
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

/**
 * Call /api/mcp/asset to read a canonical artifact by canonical_id.
 * Used by the read_asset MCP tool.
 *
 * @param params    { canonical_id, section? }
 * @param principal The resolved principal.
 * @returns         The HTTP status code and parsed McpEnvelope.
 */
export async function callPlatformAsset(
  params: { canonical_id: string; section?: string },
  principal: Principal
): Promise<PlatformCallResult> {
  const identityToken = await fetchIdentityToken()
  return platformFetch({
    url: `${PLATFORM_URL}/api/mcp/asset`,
    body: params,
    principal,
    identityToken,
  })
}

/**
 * Call /api/mcp/trace/{trace_id} to retrieve the full step ledger for a trace.
 * Used by the get_trace MCP tool.
 *
 * @param traceId   The trace ID (query_id) from a prior MCP response.
 * @param principal The resolved principal.
 * @returns         The HTTP status code and parsed McpEnvelope.
 */
export async function callPlatformTrace(
  traceId: string,
  principal: Principal
): Promise<PlatformCallResult> {
  const identityToken = await fetchIdentityToken()
  const url = `${PLATFORM_URL}/api/mcp/trace/${encodeURIComponent(traceId)}`

  let response: Response
  try {
    response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${identityToken}`,
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
        'X-MCP-User': principal.user_uid,
        // X-MCP-Audience-Tier header removed (Stream A 3.tier_excision 2026-05-28).
        'X-MCP-Key-Id': principal.key_id,
      },
      signal: AbortSignal.timeout(30_000),
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

/**
 * Call /api/mcp/writes/{action} for write operations (log_prediction, record_outcome,
 * flag_disagreement). Used by the write MCP tools (MCP-4-S1).
 *
 * @param action    One of: log_prediction, record_outcome, flag_disagreement.
 * @param params    Action-specific parameters (entry body).
 * @param principal The resolved principal.
 * @returns         The HTTP status code and parsed McpEnvelope.
 */
export async function callPlatformWrites(
  action: 'log_prediction' | 'record_outcome' | 'flag_disagreement',
  params: Record<string, unknown>,
  principal: Principal
): Promise<PlatformCallResult> {
  const identityToken = await fetchIdentityToken()
  return platformFetch({
    url: `${PLATFORM_URL}/api/mcp/writes/${encodeURIComponent(action)}`,
    body: params,
    principal,
    identityToken,
  })
}

/**
 * Call /api/mcp/recent to retrieve recent MCP query history for the calling principal.
 * Used by the list_recent_queries MCP tool.
 *
 * @param params    { limit?, since? }
 * @param principal The resolved principal.
 * @returns         The HTTP status code and parsed McpEnvelope.
 */
export async function callPlatformRecent(
  params: { limit?: number; since?: string },
  principal: Principal
): Promise<PlatformCallResult> {
  const identityToken = await fetchIdentityToken()

  const searchParams = new URLSearchParams()
  if (params.limit !== undefined) searchParams.set('limit', String(params.limit))
  if (params.since) searchParams.set('since', params.since)

  const queryString = searchParams.toString()
  const url = `${PLATFORM_URL}/api/mcp/recent${queryString ? `?${queryString}` : ''}`

  let response: Response
  try {
    response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${identityToken}`,
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
        'X-MCP-User': principal.user_uid,
        // X-MCP-Audience-Tier header removed (Stream A 3.tier_excision 2026-05-28).
        'X-MCP-Key-Id': principal.key_id,
      },
      signal: AbortSignal.timeout(30_000),
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
