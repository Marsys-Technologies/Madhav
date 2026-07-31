/**
 * logger.ts — Structured JSON logging for the MCP sidecar (M8 observability).
 *
 * Every log entry is a JSON object written to stdout/stderr:
 * {
 *   timestamp: ISO 8601,
 *   request_id: trace propagated from request (X-Request-ID) or generated,
 *   service: 'marsys-mcp',
 *   level: 'info' | 'warn' | 'error',
 *   tool?: string,        // MCP tool name (if in tool context)
 *   chart_id?: string,    // chart being accessed (if scoped)
 *   user_uid?: string,    // resolved principal uid
 *   key_id?: string,      // resolved principal key_id
 *   latency_ms?: number,  // elapsed time for the operation
 *   outcome?: string,     // 'ok' | 'error' | 'rate_limited' | 'auth_denied'
 *   message: string,
 *   error?: string,       // error message if outcome === 'error'
 * }
 *
 * Cloud Run captures stdout/stderr and routes to Cloud Logging.
 * The request_id is propagated via X-Request-ID header to the platform,
 * enabling end-to-end trace correlation: MCP sidecar → platform → sidecar.
 *
 * B-MCP-LOG-REDACT (DVA Ruling 64 / SAMAPTI_DVARAPALA_LEDGER.md INC-4): every
 * entry passes through `redactCredentials()` before it is written. This module
 * never itself logs a raw request URL today (the auth query-string leak this
 * ruling addresses is Cloud Run's own automatic `httpRequest.requestUrl`
 * capture, mitigated separately via a Cloud Logging exclusion filter — see
 * `infra/logging/`), but this is defense-in-depth: if any future code path ever
 * passes an `api_key=`-bearing URL or message into `log()`/`logWarn()`/
 * `logError()`, it is redacted before it reaches stdout/stderr — and stdout/
 * stderr are ALSO captured into Cloud Logging by Cloud Run, as jsonPayload/
 * textPayload entries distinct from the httpRequest field.
 *
 * @module logger
 */

/**
 * Redact credential-bearing query-parameter values from a string before it is
 * logged. Matches `api_key=<value>` case-insensitively, wherever it appears — as
 * a query string, inside an error message, etc. — and replaces the value with
 * `[REDACTED]`, leaving the parameter name and everything else in the string intact.
 */
export function redactCredentials(value: string): string {
  return value.replace(/(api[_-]?key=)[^&\s"'\\]+/gi, '$1[REDACTED]')
}

/**
 * Recursively apply `redactCredentials()` to every string value in a plain object.
 * Log entries are flat-ish JSON; this is intentionally shallow-recursive, not a
 * general deep-clone.
 */
function redactEntry<T>(entry: T): T {
  if (typeof entry === 'string') {
    return redactCredentials(entry) as unknown as T
  }
  if (Array.isArray(entry)) {
    return entry.map((v) => redactEntry(v)) as unknown as T
  }
  if (entry !== null && typeof entry === 'object') {
    const out: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(entry as Record<string, unknown>)) {
      out[k] = redactEntry(v)
    }
    return out as T
  }
  return entry
}

export interface LogEntry {
  timestamp: string
  request_id: string
  service: 'marsys-mcp'
  level: 'info' | 'warn' | 'error'
  tool?: string
  chart_id?: string
  user_uid?: string
  key_id?: string
  latency_ms?: number
  outcome?: 'ok' | 'error' | 'rate_limited' | 'auth_denied'
  message: string
  error?: string
}

/**
 * Generate a compact request-scoped trace ID.
 * Format: mcp-<timestamp_hex>-<random_hex>
 * Example: mcp-0196d3a4-a2f9c8e1
 */
export function generateRequestId(): string {
  const ts = Date.now().toString(16)
  const rand = Math.floor(Math.random() * 0xffffffff).toString(16).padStart(8, '0')
  return `mcp-${ts}-${rand}`
}

/**
 * Write a structured log entry as JSON to stdout via console.log.
 * Cloud Run captures stdout and routes it to Cloud Logging.
 */
export function log(entry: Omit<LogEntry, 'timestamp' | 'service'>): void {
  const full: LogEntry = {
    timestamp: new Date().toISOString(),
    service: 'marsys-mcp',
    ...entry,
  }
  // Filter undefined fields for compact JSON
  const compact = Object.fromEntries(
    Object.entries(full).filter(([, v]) => v !== undefined)
  )
  // eslint-disable-next-line no-console
  console.log(JSON.stringify(redactEntry(compact)))
}

/**
 * Log a warning entry (level: 'warn').
 */
export function logWarn(entry: Omit<LogEntry, 'timestamp' | 'service' | 'level'>): void {
  log({ ...entry, level: 'warn' })
}

/**
 * Log an error entry (level: 'error') via console.error so Cloud Run
 * routes it to the ERROR severity in Cloud Logging.
 */
export function logError(entry: Omit<LogEntry, 'timestamp' | 'service' | 'level'>): void {
  const full: LogEntry = {
    timestamp: new Date().toISOString(),
    service: 'marsys-mcp',
    level: 'error',
    ...entry,
  }
  const compact = Object.fromEntries(
    Object.entries(full).filter(([, v]) => v !== undefined)
  )
  // eslint-disable-next-line no-console
  console.error(JSON.stringify(redactEntry(compact)))
}
