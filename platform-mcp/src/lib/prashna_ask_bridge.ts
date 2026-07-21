/**
 * prashna_ask_bridge.ts — thin HTTP client for the prashna_ask engine route.
 *
 * W6 redesign (Task 4). The REAL engine invocation (callPipelinePlanner, budget
 * arbitration, NO-LEAKAGE enforcement, cost-cap tracking) lives on the `platform`
 * side at `platform/src/app/api/mcp/prashna_ask/route.ts` — investigation for
 * this task found `platform-mcp` has no import path to the FROZEN engine
 * (`callPipelinePlanner` / `compileFloorForPlan` only run inside the `platform`
 * deployable). So this file's ONLY job is the HTTP call to that route, using the
 * EXACT SAME service-to-service auth pattern `client.ts` already uses for
 * `/api/mcp/primitives/{toolName}` (OIDC identity token via
 * `GoogleAuth.getIdTokenClient(PLATFORM_URL)`, `X-MCP-Internal-Token`,
 * `X-MCP-User` / `X-MCP-Key-Id` principal headers). No job tracking, no MCP
 * protocol concerns — those live in `tools/register_prashna_ask.ts`.
 *
 * Response typing matches EXACTLY what the route returns (read in full before
 * writing this file):
 *   - outcome 'plan'                — normal/partial completion (completeness receipt).
 *   - outcome 'clarification_needed' — planner needs more scope from the caller.
 *   - ok: false                     — an McpEnvelope-shaped error (auth/validation/
 *                                      entitlement_denied/orchestrator_error/internal).
 *
 * Environment variables (identical to client.ts):
 *   PLATFORM_URL          — base URL of the amjis-web Cloud Run service.
 *   MCP_INTERNAL_TOKEN    — shared secret for X-MCP-Internal-Token header.
 *   SERVICE_TOKEN         — static identity token override (local dev + tests).
 */

import { GoogleAuth, type IdTokenClient } from 'google-auth-library'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

// Generous timeout: the route runs synchronously up to its own maxDuration=320s
// (a few minutes for elevated entitlements) — this bridge must not time out first.
const ENGINE_CALL_TIMEOUT_MS = 300_000

// ── Response types (mirrors platform/src/app/api/mcp/prashna_ask/route.ts) ────

export interface PrashnaAskToolDispatchOutcome {
  tool_name: string
  status: 'done' | 'error'
  result_count: number
  latency_ms: number
}

export interface PrashnaAskCompleteness {
  status: 'complete' | 'partial'
  tools_dispatched: PrashnaAskToolDispatchOutcome[]
  unserved_tools: string[]
  unresolved_tools: string[]
  stripped_leaked_capabilities: string[]
  cap_tripped: string | null
}

export interface PrashnaAskPlanOutcome {
  ok: true
  trace_id: string
  chart_id: string
  outcome: 'plan'
  query_class: string
  query_intent_summary: string
  completeness: PrashnaAskCompleteness
  judgment_flags: string[]
  results: Array<{ tool_name: string; bundle: unknown }>
}

export interface PrashnaAskClarificationOutcome {
  ok: true
  trace_id: string
  outcome: 'clarification_needed'
  question: string
  missing_scope_dims: string[]
  suggested_options: unknown[]
}

export interface PrashnaAskErrorOutcome {
  ok: false
  trace_id: string
  error: {
    class: string
    message: string
    remediation?: string
  }
  denial?: unknown
}

export type PrashnaAskEngineResponse =
  | PrashnaAskPlanOutcome
  | PrashnaAskClarificationOutcome
  | PrashnaAskErrorOutcome

export interface CallPrashnaAskEngineInput {
  chartId: string
  question: string
  principal: { userUid: string; keyId: string }
}

// ── Identity token acquisition (identical pattern to client.ts) ──────────────

let cachedIdTokenClient: IdTokenClient | null = null

async function getIdTokenClient(): Promise<IdTokenClient> {
  if (cachedIdTokenClient) return cachedIdTokenClient
  const auth = new GoogleAuth()
  cachedIdTokenClient = await auth.getIdTokenClient(PLATFORM_URL)
  return cachedIdTokenClient
}

async function fetchIdentityToken(): Promise<string> {
  // Explicit override (tests + local dev) — same precedence as client.ts.
  const staticToken = process.env['SERVICE_TOKEN']
  if (staticToken) return staticToken

  try {
    const client = await getIdTokenClient()
    const headers = await client.getRequestHeaders(PLATFORM_URL)
    const authHeader = (headers as Record<string, string>)['Authorization'] ?? ''
    if (authHeader.startsWith('Bearer ')) return authHeader.slice(7)
    return authHeader
  } catch (err) {
    if (MCP_INTERNAL_TOKEN) return MCP_INTERNAL_TOKEN
    console.warn(
      '[mcp:prashna_ask_bridge] No identity token available; call will likely fail auth.',
      err instanceof Error ? err.message : String(err)
    )
    return ''
  }
}

// Exposed for tests — lets the test suite reset the cached client between cases.
export function __resetPrashnaAskBridgeTokenCacheForTests(): void {
  cachedIdTokenClient = null
}

function buildBridgeErrorEnvelope(
  message: string,
  errorClass: 'internal' | 'auth' = 'internal'
): PrashnaAskErrorOutcome {
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

/**
 * Call POST /api/mcp/prashna_ask on the platform — the actual engine invocation.
 * Never throws: network / parse errors are returned as a PrashnaAskErrorOutcome.
 */
export async function callPrashnaAskEngine(
  input: CallPrashnaAskEngineInput
): Promise<PrashnaAskEngineResponse> {
  const identityToken = await fetchIdentityToken()

  let response: Response
  try {
    response = await fetch(`${PLATFORM_URL}/api/mcp/prashna_ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${identityToken}`,
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
        'X-MCP-User': input.principal.userUid,
        'X-MCP-Key-Id': input.principal.keyId,
      },
      body: JSON.stringify({ chart_id: input.chartId, question: input.question }),
      signal: AbortSignal.timeout(ENGINE_CALL_TIMEOUT_MS),
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return buildBridgeErrorEnvelope(`Platform unreachable: ${message}`)
  }

  let body: unknown
  try {
    body = await response.json()
  } catch {
    return buildBridgeErrorEnvelope('Platform returned non-JSON response')
  }

  // The route always returns a well-formed envelope (success shape or
  // McpEnvelope-shaped error) on every status code it emits — pass it through
  // as-is rather than re-deriving error shaping here.
  return body as PrashnaAskEngineResponse
}
