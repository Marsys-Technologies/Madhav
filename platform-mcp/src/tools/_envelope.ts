/**
 * _envelope.ts — Shared MCP result serializer.
 *
 * Every MCP tool returns a content array with a single text item whose value
 * is a JSON-serialized envelope. This module centralises that serialisation so
 * the 21 tool files don't each duplicate `JSON.stringify(envelope, null, 2)`.
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

/** Base shape every MCP tool envelope must satisfy. */
export interface McpEnvelope {
  ok: boolean
  [key: string]: unknown
}

/** Return type for a successful MCP tool call. */
export interface McpOkResult {
  content: Array<{ type: string; text: string }>
  isError?: never
}

/** Return type for a failed MCP tool call. */
export interface McpErrorResult {
  content: Array<{ type: string; text: string }>
  isError: true
}

/**
 * Wraps a successful envelope into the MCP content array format.
 * Does NOT set `isError` — omitting the field is the MCP-SDK convention for success.
 */
export function okResult(envelope: McpEnvelope): McpOkResult {
  return {
    content: [{ type: 'text', text: serialize(envelope) }],
  }
}

/**
 * Wraps a failed envelope into the MCP content array format with `isError: true`.
 * The envelope should still carry `ok: false` for consistency.
 */
export function errorResult(envelope: McpEnvelope): McpErrorResult {
  return {
    content: [{ type: 'text', text: serialize(envelope) }],
    isError: true,
  }
}

function serialize(envelope: McpEnvelope): string {
  if (process.env['MCP_VERBOSE'] === 'true') {
    return JSON.stringify(envelope, null, 2)
  }
  return JSON.stringify(envelope)
}
