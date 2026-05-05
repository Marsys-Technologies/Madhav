import 'server-only'
import { createOpenAI } from '@ai-sdk/openai'
import type { LanguageModel } from 'ai'

// ─────────────────────────────────────────────────────────────────────────────
// PlannerCompatibilityError — thrown when NIM rejects toolChoice or
// response_format. These errors are DETERMINISTIC: retrying will always fail.
// The circuit breaker (planner_circuit_breaker.ts) fast-opens on this type.
// ─────────────────────────────────────────────────────────────────────────────

export class PlannerCompatibilityError extends Error {
  readonly isCompatibilityError = true
  constructor(message: string, cause?: unknown) {
    super(message)
    this.name = 'PlannerCompatibilityError'
    if (cause) this.cause = cause
  }
}

/** Patterns that indicate a deterministic NIM toolChoice/format rejection. */
const COMPAT_ERROR_PATTERNS = [
  /does not support tool.?choice/i,
  /does not support response.?format/i,
  /tool.?choice.*not supported/i,
  /response.?format.*not supported/i,
  /function.?call.*not supported/i,
  /parallel.?tool.?calls.*not supported/i,
]

/**
 * Classify an error message against known NIM compatibility rejection patterns.
 * Returns true if the error is a deterministic toolChoice/format incompatibility.
 */
export function isNimCompatibilityError(err: unknown): boolean {
  const msg = err instanceof Error ? err.message : String(err)
  return COMPAT_ERROR_PATTERNS.some(pat => pat.test(msg))
}

/**
 * Re-throw as PlannerCompatibilityError if the error matches a NIM
 * toolChoice/response_format rejection pattern; otherwise rethrow as-is.
 * Call this in catch blocks around NIM planner invocations.
 */
export function classifyNimError(err: unknown): never {
  if (isNimCompatibilityError(err)) {
    throw new PlannerCompatibilityError(
      `NIM model rejected toolChoice/response_format: ${err instanceof Error ? err.message : String(err)}`,
      err,
    )
  }
  throw err
}

/**
 * Retry guard: returns false for PlannerCompatibilityError (deterministic
 * failures that will always fail — retrying wastes latency and quota).
 * Returns true for transient errors (rate-limits, timeouts, 5xx).
 */
export function shouldRetryNimError(err: unknown): boolean {
  if (err instanceof PlannerCompatibilityError) return false
  if (err && typeof err === 'object' && (err as Record<string, unknown>).isCompatibilityError) return false
  return true
}

// ─────────────────────────────────────────────────────────────────────────────
// PlanInputJsonSchema pre-flight validation
// ─────────────────────────────────────────────────────────────────────────────

export interface PlanInputSchemaValidation {
  valid: boolean
  warnings: string[]
}

/**
 * Pre-flight check for PlanInputJsonSchema shape before sending to NIM.
 * Logs a warning (non-blocking) if the schema looks malformed.
 * Does NOT throw — a malformed schema should still attempt the call;
 * the API will surface a cleaner error than a pre-flight abort.
 */
export function validatePlanInputJsonSchema(schema: unknown): PlanInputSchemaValidation {
  const warnings: string[] = []

  if (schema === null || schema === undefined) {
    warnings.push('PlanInputJsonSchema is null/undefined')
    return { valid: false, warnings }
  }

  if (typeof schema !== 'object') {
    warnings.push(`PlanInputJsonSchema is not an object (got ${typeof schema})`)
    return { valid: false, warnings }
  }

  const s = schema as Record<string, unknown>

  if (s.type !== 'object') {
    warnings.push(`PlanInputJsonSchema.type expected 'object', got '${s.type}'`)
  }

  if (!s.properties || typeof s.properties !== 'object') {
    warnings.push('PlanInputJsonSchema.properties is missing or not an object')
  } else {
    const props = s.properties as Record<string, unknown>
    if (!props.tool_calls) {
      warnings.push('PlanInputJsonSchema.properties.tool_calls is missing — NIM planner will likely fail schema validation')
    }
  }

  return { valid: warnings.length === 0, warnings }
}

// ─────────────────────────────────────────────────────────────────────────────
// Planner mode logging
// ─────────────────────────────────────────────────────────────────────────────

export type PlannerMode = 'toolchoice' | 'schema'

/**
 * Emit a structured log entry noting which planner path is being used.
 * 'toolchoice' = generateText with toolChoice:'required' (standard NIM path).
 * 'schema'     = generateObject with response_format:json_schema (non-NIM path).
 * Call once per planner invocation before the LLM call to enable per-request tracing.
 */
export function logPlannerMode(mode: PlannerMode, modelId: string, queryId?: string): void {
  if (process.env.NODE_ENV === 'test') return
  console.log(JSON.stringify({
    event: 'planner_mode_selected',
    planner_mode: mode,
    model_id: modelId,
    query_id: queryId ?? null,
    ts: Date.now(),
  }))
}

/**
 * NVIDIA NIM provider — OpenAI-compatible endpoint.
 * Models: Nemotron Ultra 253B, Qwen3-235B-A22B, Llama-3.1-8B, DeepSeek V4 Pro.
 * API key: NVIDIA_NIM_API_KEY env variable (required when NIM stack is active).
 * Free tier available at https://integrate.api.nvidia.com/v1 (rate-limited).
 *
 * TIMEOUT GUARD
 * NIM's free tier is queue-based: a request may sit in queue for an extended
 * period before the endpoint sends back any HTTP headers at all. Without a
 * hard timeout the AI SDK's default fetch waits indefinitely, then retries
 * up to 3 times (AI_RetryError after 3 × headers-timeout ≈ 5+ minutes of
 * silence on a busy queue or a model ID that doesn't exist).
 *
 * We pass a custom fetch wrapper that aborts after NIM_HEADERS_TIMEOUT_MS
 * with no HTTP response headers. Combined with maxRetries: 0 on synthesis
 * streamText calls and planner generateText calls this caps the hang at
 * ~90 s → fast error → user can retry or switch stacks rather than waiting
 * indefinitely. 90 s chosen to accommodate NIM queue waits (worst observed:
 * ~46 s end-to-end under load; original 30 s limit fired too early).
 */
const NVIDIA_NIM_BASE_URL = 'https://integrate.api.nvidia.com/v1'

/**
 * Abort if NIM doesn't send HTTP headers within this window.
 *
 * Why 110s: NIM free-tier is queue-based. Under load the endpoint can take
 * 30–60s before sending *any* HTTP headers (the request sits in queue before
 * a GPU slot opens). The original 30s limit caused AbortError → AI SDK retry
 * → the queued-then-aborted request returned 500 on retry → PlannerError.
 * 90s was raised to 110s after the 120B Nemotron synthesis model exceeded 90s
 * on a busy queue. 110s stays within the 120s route maxDuration with ~10s
 * buffer for pre-synthesis overhead (planner + classify + retrieve).
 * Once headers arrive, the response body streams at full GPU throughput and
 * is not affected by this deadline.
 */
const NIM_HEADERS_TIMEOUT_MS = 110_000

/**
 * Wrap the platform fetch so every NIM request races against a hard deadline.
 * If the caller's init already carries a signal (AI SDK retry/abort), we
 * race both signals so whichever fires first wins.
 */
function nimFetch(url: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const timeoutSignal = AbortSignal.timeout(NIM_HEADERS_TIMEOUT_MS)
  const signal =
    init?.signal
      ? (AbortSignal as unknown as { any: (signals: AbortSignal[]) => AbortSignal }).any
        ? (AbortSignal as unknown as { any: (signals: AbortSignal[]) => AbortSignal }).any([
            init.signal as AbortSignal,
            timeoutSignal,
          ])
        : timeoutSignal           // Node < 20: fall back to timeout-only
      : timeoutSignal
  return fetch(url, { ...init, signal })
}

let _client: ReturnType<typeof createOpenAI> | null = null

function getClient(): ReturnType<typeof createOpenAI> {
  if (!_client) {
    _client = createOpenAI({
      baseURL: NVIDIA_NIM_BASE_URL,
      apiKey: process.env.NVIDIA_NIM_API_KEY ?? '',
      fetch: nimFetch,
    })
  }
  return _client
}

export function getNvidiaModel(modelId: string): LanguageModel {
  return getClient().chat(modelId) as LanguageModel
}
