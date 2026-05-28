/**
 * observability/trace.ts — W3C-traceparent propagation primitives for the
 * web → sidecar → mcp request boundary.
 *
 * Cloud Trace consumes any incoming `traceparent` header in the W3C format
 * (https://www.w3.org/TR/trace-context/) and stitches the spans automatically.
 * We therefore do NOT need a full OpenTelemetry SDK in-process — we only need
 * to (a) parse any incoming traceparent and (b) propagate (or mint) it on
 * outgoing fetch() calls to downstream services.
 *
 * The shape of the W3C traceparent header is:
 *   version "-" trace-id "-" parent-id "-" trace-flags
 *   00     -  32 hex     -  16 hex   - 2 hex
 *
 * Module is additive — no behaviour change unless callers wire it in.
 *
 * Stream B / unit 4.observability (Wave 4 platform-modernization).
 */

import 'server-only'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface TraceContext {
  /** 32-hex lowercased trace id (W3C). */
  traceId: string
  /** 16-hex lowercased span id of the current span (becomes parent on outgoing). */
  spanId: string
  /** 2-hex trace flags (default '01' = sampled). */
  flags: string
}

/** A finished span ready to be reported. Kept local — Cloud Trace stitches via traceparent. */
export interface SpanRecord {
  name: string
  traceId: string
  spanId: string
  parentSpanId: string | null
  startMs: number
  endMs: number
  attributes: Record<string, string | number | boolean | undefined>
  status: 'ok' | 'error'
  error?: string
}

// ── Hex helpers (no Buffer dep — runs in Edge as well) ────────────────────────

const HEX = '0123456789abcdef'

function randomHex(bytes: number): string {
  // crypto.getRandomValues exists in both Node 18+ and Edge runtimes.
  const arr = new Uint8Array(bytes)
  ;(globalThis.crypto ?? require('node:crypto').webcrypto).getRandomValues(arr)
  let out = ''
  for (const b of arr) {
    out += HEX[(b >> 4) & 0xf] + HEX[b & 0xf]
  }
  return out
}

export function newTraceId(): string {
  // 16 random bytes → 32 hex.
  return randomHex(16)
}

export function newSpanId(): string {
  // 8 random bytes → 16 hex.
  return randomHex(8)
}

// ── Parse / serialize traceparent ─────────────────────────────────────────────

const TRACEPARENT_RE =
  /^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$/

/**
 * Parse a W3C traceparent header. Returns null if header missing or malformed.
 * Both trace-id and span-id must NOT be all-zero (W3C §3.2.2.3).
 */
export function parseTraceparent(headerValue: string | null | undefined): TraceContext | null {
  if (!headerValue) return null
  const trimmed = headerValue.trim().toLowerCase()
  const m = TRACEPARENT_RE.exec(trimmed)
  if (!m) return null
  const [, version, traceId, spanId, flags] = m
  if (version === 'ff') return null // reserved
  if (traceId === '0'.repeat(32)) return null
  if (spanId === '0'.repeat(16)) return null
  return { traceId, spanId, flags }
}

/**
 * Serialize a TraceContext into a W3C traceparent header value.
 */
export function serializeTraceparent(ctx: TraceContext): string {
  return `00-${ctx.traceId}-${ctx.spanId}-${ctx.flags}`
}

// ── Public API: start / continue a span ───────────────────────────────────────

/**
 * Begin a child span under an inbound trace, or mint a new trace if no
 * traceparent was provided. The returned `traceparent` is what you forward to
 * the next downstream service via fetch headers.
 */
export function startSpan(
  spanName: string,
  inboundTraceparent: string | null | undefined,
  attributes: Record<string, string | number | boolean | undefined> = {},
): {
  ctx: TraceContext
  parent: TraceContext | null
  span: Pick<SpanRecord, 'name' | 'traceId' | 'spanId' | 'parentSpanId' | 'attributes'> & {
    startMs: number
  }
  /** Header value to forward to downstream services. */
  traceparent: string
} {
  const parent = parseTraceparent(inboundTraceparent ?? null)
  const traceId = parent?.traceId ?? newTraceId()
  const spanId = newSpanId()
  const flags = parent?.flags ?? '01'
  const ctx: TraceContext = { traceId, spanId, flags }

  return {
    ctx,
    parent,
    span: {
      name: spanName,
      traceId,
      spanId,
      parentSpanId: parent?.spanId ?? null,
      startMs: Date.now(),
      attributes: { ...attributes },
    },
    traceparent: serializeTraceparent(ctx),
  }
}

/**
 * Close a span. Logs in structured JSON so Cloud Logging surfaces it; Cloud
 * Trace stitches via the traceparent in the request headers, so we do not
 * need to POST to a separate ingestion endpoint.
 */
export function endSpan(
  span: { name: string; traceId: string; spanId: string; parentSpanId: string | null; startMs: number; attributes: Record<string, string | number | boolean | undefined> },
  status: 'ok' | 'error' = 'ok',
  error?: string,
): SpanRecord {
  const record: SpanRecord = {
    name: span.name,
    traceId: span.traceId,
    spanId: span.spanId,
    parentSpanId: span.parentSpanId,
    startMs: span.startMs,
    endMs: Date.now(),
    attributes: span.attributes,
    status,
    ...(error ? { error } : {}),
  }
  // Cloud Logging picks up `logging.googleapis.com/trace` and links to Trace.
  const project = process.env['GCP_PROJECT'] ?? ''
  const cloudTraceField =
    project && record.traceId
      ? { 'logging.googleapis.com/trace': `projects/${project}/traces/${record.traceId}` }
      : {}
  // Keep this on console.log so structured logging picks it up.
  // eslint-disable-next-line no-console
  console.log(
    JSON.stringify({
      severity: status === 'ok' ? 'INFO' : 'ERROR',
      message: `span:${record.name}`,
      span: record,
      ...cloudTraceField,
    }),
  )
  return record
}

// ── fetch() wrapper that propagates the trace ─────────────────────────────────

/**
 * Drop-in replacement for fetch() that injects a `traceparent` header derived
 * from the given context. If the caller already set a traceparent header on
 * `init.headers`, that wins (we do not clobber).
 */
export async function fetchWithTrace(
  ctx: TraceContext,
  input: RequestInfo | URL,
  init: RequestInit = {},
): Promise<Response> {
  // Mint a fresh child span id for the outgoing hop so the downstream sees us
  // as its parent. Reuse the existing trace id + flags.
  const childCtx: TraceContext = {
    traceId: ctx.traceId,
    spanId: newSpanId(),
    flags: ctx.flags,
  }
  const headers = new Headers(init.headers ?? {})
  if (!headers.has('traceparent')) {
    headers.set('traceparent', serializeTraceparent(childCtx))
  }
  return fetch(input, { ...init, headers })
}
