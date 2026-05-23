/**
 * Builds a human-readable canonical summary of an MCP tool call.
 * Format: "tool_name(param1=val1, param2=val2)"
 * Long values are truncated to 50 chars.
 *
 * Used by MCP primitive and execute routes to populate query_summary
 * in query_trace_steps data_summary, replacing generic "<tool> call" strings.
 */

export function buildTraceSummary(
  toolName: string,
  params: Record<string, unknown>
): string {
  const paramStr = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null)
    .map(([k, v]) => {
      const val = Array.isArray(v) ? v.join(',') : String(v)
      const truncated = val.length > 50 ? val.slice(0, 47) + '...' : val
      return `${k}=${truncated}`
    })
    .join(', ')
  return paramStr ? `${toolName}(${paramStr})` : toolName
}
