/**
 * _envelope.ts — Shared MCP result serializer.
 *
 * Every MCP tool returns a content array with a single text item whose value
 * is a JSON-serialized envelope. This module centralises that serialisation so
 * tool files don't each duplicate `JSON.stringify(envelope, null, 2)`.
 *
 * Serialisation behaviour:
 *   MCP_VERBOSE=true  → pretty-print (JSON.stringify with 2-space indent)
 *   default           → compact (no extra whitespace)
 *
 * Usage:
 *   import { okResult, errorResult } from './_envelope.js'
 *
 *   // success path
 *   return okResult({ ok: true, result: rows, trace_id, epistemics })
 *
 *   // error / forbidden path
 *   return errorResult({ ok: false, error: 'Forbidden', message: '...' })
 */

/**
 * Wraps a successful envelope into the MCP content array format.
 * Does NOT set `isError` — omitting the field is the MCP-SDK convention for success.
 */
export function okResult(envelope: unknown): { content: Array<{ type: 'text'; text: string }> } {
  return {
    content: [{ type: 'text', text: serialize(envelope) }],
  }
}

/**
 * Wraps a failed envelope into the MCP content array format with `isError: true`.
 * The envelope should still carry `ok: false` for consistency.
 */
export function errorResult(envelope: unknown): {
  content: Array<{ type: 'text'; text: string }>
  isError: true
} {
  return {
    content: [{ type: 'text', text: serialize(envelope) }],
    isError: true,
  }
}

function serialize(envelope: unknown): string {
  if (process.env['MCP_VERBOSE'] === 'true') {
    return JSON.stringify(envelope, null, 2)
  }
  return JSON.stringify(envelope)
}
