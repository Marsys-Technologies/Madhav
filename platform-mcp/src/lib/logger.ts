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
 * @module logger
 */

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
  console.log(JSON.stringify(compact))
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
  console.error(JSON.stringify(compact))
}
