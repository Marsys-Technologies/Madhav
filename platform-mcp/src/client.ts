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

// ── Retry helper (M-11) ───────────────────────────────────────────────────────

/**
 * Wrap fetch with 2-retry exponential backoff for transient 5xx / network errors.
 * 4xx responses are returned immediately without retry (auth/validation — not transient).
 */
async function fetchWithRetry(url: string, opts: RequestInit, maxRetries = 2): Promise<Response> {
  let lastError: unknown
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const resp = await fetch(url, opts)
      if (resp.status < 500) return resp  // 4xx and 2xx: no retry
      if (attempt === maxRetries) return resp
      await new Promise(r => setTimeout(r, 500 * Math.pow(2, attempt)))  // 500ms, 1000ms
    } catch (err) {
      lastError = err
      if (attempt === maxRetries) throw err
      await new Promise(r => setTimeout(r, 500 * Math.pow(2, attempt)))
    }
  }
  throw lastError
}

// ── Common fetch helper ───────────────────────────────────────────────────────

interface PlatformFetchOptions {
  url: string
  body: Record<string, unknown>
  principal: Principal
  identityToken: string
  /** M8: request-scoped trace ID for end-to-end log correlation. */
  requestId?: string
}

async function platformFetch(opts: PlatformFetchOptions): Promise<PlatformCallResult> {
  const { url, body, principal, identityToken, requestId } = opts

  let response: Response
  try {
    response = await fetchWithRetry(url, {
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
        // M8: trace propagation — platform logs will carry this ID for correlation.
        ...(requestId ? { 'X-Request-ID': requestId } : {}),
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
 * flag_disagreement, prospective_ledger_file). Used by the write MCP tools (MCP-4-S1).
 *
 * `prospective_ledger_file` added by ṢAḌ-DARŚANA W4 Lane S (KALA_W4_UPAYA_DESIGN_v1_0.md
 * §4.4) — the route already implements this action (platform/src/app/api/mcp/writes/
 * [action]/route.ts); this was purely a TS union gap. `lib/intervention_filing.ts`'s
 * `fileInterventionFalsifier` is the sole in-repo caller.
 *
 * `intervention_ledger_record` added by the W4 gate-discharge-prep lane (the serve-time
 * write path into `mimamsa_intervention_ledger`, closing the gap PR #1055 disclosed) —
 * `lib/intervention_filing.ts`'s `recordInterventionLedgerEntry` is the sole in-repo caller.
 *
 * @param action    One of: log_prediction, record_outcome, flag_disagreement,
 *                  prospective_ledger_file, intervention_ledger_record.
 * @param params    Action-specific parameters (entry body).
 * @param principal The resolved principal.
 * @returns         The HTTP status code and parsed McpEnvelope.
 */
export async function callPlatformWrites(
  action: 'log_prediction' | 'record_outcome' | 'flag_disagreement' | 'prospective_ledger_file' | 'intervention_ledger_record',
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

/**
 * Call /api/mcp/bundles/{bundleName} for composite bundle tool invocations.
 * The bundle endpoint returns SSE events; this helper collects them and returns
 * the data from the final `bundle.completed` (or `bundle.error`) event as a
 * PlatformCallResult, letting callers use the same envelope handling as primitives.
 *
 * @param bundleName  The bundle name (e.g. "holistic_bundle").
 * @param params      Bundle-specific parameters (chart_id, etc).
 * @param principal   The resolved principal.
 * @returns           { status, envelope } — envelope.result = bundle.completed data.
 */
export async function callPlatformBundle(
  bundleName: string,
  params: Record<string, unknown>,
  principal: Principal
): Promise<PlatformCallResult> {
  const identityToken = await fetchIdentityToken()
  const url = `${PLATFORM_URL}/api/mcp/bundles/${encodeURIComponent(bundleName)}`

  let response: Response
  try {
    response = await fetchWithRetry(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${identityToken}`,
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
        'X-MCP-User': principal.user_uid,
        'X-MCP-Key-Id': principal.key_id,
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(params),
      signal: AbortSignal.timeout(125_000),
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return { status: 503, envelope: buildClientErrorEnvelope(`Platform unreachable: ${message}`) }
  }

  if (!response.ok) {
    try {
      const errBody = await response.json() as McpEnvelope
      return { status: response.status, envelope: errBody }
    } catch {
      return {
        status: response.status,
        envelope: buildClientErrorEnvelope(`Bundle endpoint error: ${response.status}`),
      }
    }
  }

  // Parse SSE stream: collect all events, return data from bundle.completed or bundle.error
  let sseText: string
  try {
    sseText = await response.text()
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return { status: 502, envelope: buildClientErrorEnvelope(`Failed to read bundle SSE stream: ${message}`) }
  }

  // Walk SSE events line-by-line; keep last bundle.completed or first bundle.error
  let completedData: unknown = null
  let errorData: unknown = null
  let currentEvent = ''
  let currentData = ''

  for (const line of sseText.split('\n')) {
    if (line.startsWith('event: ')) {
      currentEvent = line.slice('event: '.length).trim()
    } else if (line.startsWith('data: ')) {
      currentData = line.slice('data: '.length).trim()
    } else if (line === '') {
      if (currentEvent && currentData) {
        try {
          const parsed = JSON.parse(currentData)
          if (currentEvent === 'bundle.completed') completedData = parsed
          if (currentEvent === 'bundle.error' && !errorData) errorData = parsed
        } catch { /* ignore malformed SSE data line */ }
      }
      currentEvent = ''
      currentData = ''
    }
  }

  if (errorData !== null) {
    const errMsg = (errorData as Record<string, unknown>)['error'] as string | undefined
    return {
      status: 500,
      envelope: buildClientErrorEnvelope(errMsg ?? 'Bundle execution error'),
    }
  }

  if (completedData === null) {
    return {
      status: 502,
      envelope: buildClientErrorEnvelope('Bundle returned no bundle.completed event'),
    }
  }

  return {
    status: 200,
    envelope: { ok: true, trace_id: '', result: completedData } as McpEnvelope,
  }
}

/**
 * Call /api/mcp/surface-spec to retrieve the per-family MCP surface constraints.
 *
 * The MCP fork calls this at startup (or lazily on first request) to learn:
 *   - max_tools: how many tools to register for this family
 *   - tool_name_pattern: valid name regex (cross-family: no hyphens)
 *   - requires_dual_output: whether to return structuredContent + text block
 *   - strip_mcp_constructs: whether to strip MCP-only fields (DeepSeek)
 *   - transport: expected transport mode
 *
 * R2.2 — consumes the published seam output from getMcpSurfaceSpec(family).
 *
 * Auth: service-to-service identity token + MCP_INTERNAL_TOKEN only.
 * No per-user Principal needed (surface spec is chart-agnostic + family-static).
 *
 * @param family  One of: 'anthropic' | 'gemini' | 'openai' | 'deepseek' | 'universal'
 *                Omit or pass unknown value → platform resolves to 'universal'.
 */
export async function callPlatformSurfaceSpec(
  family?: string
): Promise<PlatformCallResult> {
  const identityToken = await fetchIdentityToken()

  const searchParams = new URLSearchParams()
  if (family) searchParams.set('family', family)
  const qs = searchParams.toString()
  const url = `${PLATFORM_URL}/api/mcp/surface-spec${qs ? `?${qs}` : ''}`

  let response: Response
  try {
    response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${identityToken}`,
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      },
      signal: AbortSignal.timeout(10_000),
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
