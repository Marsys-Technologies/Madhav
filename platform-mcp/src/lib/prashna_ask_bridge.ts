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

// ── Streamed-progress types (W6 Part 2) ──────────────────────────────────────
//
// Mirrors the `{"event":"progress",...}` NDJSON line shape the platform route
// (`platform/src/app/api/mcp/prashna_ask/route.ts`) now emits per completed
// tool-dispatch iteration — see that file's dispatch-loop `emitProgress()`.

export interface PrashnaAskProgressEvent {
  tools_dispatched_count: number
  cap_ceiling: { maxCalls: number; maxWallClockMs: number }
  elapsed_ms: number
  last_tool: string
}

export type PrashnaAskOnProgress = (progress: PrashnaAskProgressEvent) => void

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
 *
 * W6 Part 2: the platform route now streams NDJSON (one `{"event":"progress",...}`
 * line per completed tool-dispatch iteration, ending with one
 * `{"event":"final",...}` line carrying the full response body) instead of a
 * single JSON blob. This function reads the response body as a stream, decodes
 * it incrementally, and:
 *   - calls `onProgress` (if supplied) for each parsed `"event":"progress"` line
 *     AS IT ARRIVES — not batched at the end;
 *   - resolves with the parsed `"event":"final"` line's payload (the `event`
 *     discriminator stripped), which is byte-for-byte the same shape this
 *     function always returned.
 * The early-return paths on the route (400/401/clarification_needed/fault) are
 * still a single JSON object with no `event` field at all — a line with no
 * `event` key is treated as the terminal payload directly, so those paths work
 * unchanged. `onProgress` is optional and purely additive: a caller that
 * doesn't pass it sees no change in behavior or return type.
 */
export async function callPrashnaAskEngine(
  input: CallPrashnaAskEngineInput,
  onProgress?: PrashnaAskOnProgress
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

  // Defensive fallback for a caller/test double that doesn't expose a
  // streamable `.body` (e.g. an environment without ReadableStream support) —
  // fall back to the pre-streaming whole-body read. Real fetch() Response
  // objects (Node 18+, the platform's actual NDJSON stream) always have `.body`.
  if (!response.body) {
    let body: unknown
    try {
      body = await response.json()
    } catch {
      return buildBridgeErrorEnvelope('Platform returned non-JSON response')
    }
    return body as PrashnaAskEngineResponse
  }

  let final: PrashnaAskEngineResponse | null = null

  const processLine = (raw: string): void => {
    const line = raw.trim()
    if (!line) return
    let parsed: Record<string, unknown>
    try {
      parsed = JSON.parse(line)
    } catch {
      // A malformed NDJSON line is skipped rather than aborting the whole
      // read — if the stream never yields a resolvable final/blob line, the
      // `final === null` check below reports the honest empty-stream error.
      return
    }
    if (parsed['event'] === 'progress') {
      onProgress?.(parsed as unknown as PrashnaAskProgressEvent)
      return
    }
    if (parsed['event'] === 'final') {
      const rest: Record<string, unknown> = { ...parsed }
      delete rest['event']
      final = rest as unknown as PrashnaAskEngineResponse
      return
    }
    // No `event` discriminator at all — one of the route's non-streamed
    // early-return paths (400/401/clarification_needed/fault), which return a
    // single plain JSON object body, not NDJSON.
    final = parsed as unknown as PrashnaAskEngineResponse
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      let newlineIndex: number
      while ((newlineIndex = buffer.indexOf('\n')) >= 0) {
        processLine(buffer.slice(0, newlineIndex))
        buffer = buffer.slice(newlineIndex + 1)
      }
    }
    buffer += decoder.decode()
    if (buffer.trim()) processLine(buffer)
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return buildBridgeErrorEnvelope(`Error reading platform response stream: ${message}`)
  }

  if (final === null) {
    return buildBridgeErrorEnvelope('Platform returned a non-JSON or empty response stream')
  }
  return final
}
