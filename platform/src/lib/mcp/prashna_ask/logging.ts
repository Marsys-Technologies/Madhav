import 'server-only'

const SAFE_LOG_TOOL_NAME = /^[a-z0-9_:/.-]{1,160}$/i

export const MCP_BYOK_TOOL_FAILURE_CODES = [
  'MCP_TOOL_DISPATCH_FAILED',
  'MCP_MANAGED_CONTINUATION_FAILED',
  'MCP_INQUIRY_CONTINUATION_FAILED',
] as const

export type McpByokToolFailureCode = typeof MCP_BYOK_TOOL_FAILURE_CODES[number]

/** Closed logger: callers cannot supply an exception, provider message, or arbitrary fields. */
export function logSafeByokToolFailure(
  code: McpByokToolFailureCode,
  traceId: string,
  toolName: string,
): void {
  const safeToolName = SAFE_LOG_TOOL_NAME.test(toolName) ? toolName : 'unresolved'
  console.error(`[mcp:prashna_ask] ${code} trace=${traceId} tool=${safeToolName}`)
}
