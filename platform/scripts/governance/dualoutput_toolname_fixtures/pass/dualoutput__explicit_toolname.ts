// PASS fixture — dualOutput with a real tool name default (not 'unknown_tool').

const TOOL_NAME = 'kala_now_get'

function dualOutput(data: unknown, toolName = 'kala_now_get') {
  const structuredContent = { type: 'object' as const, object: data }
  return { structuredContent, content: [{ type: 'text' as const, text: JSON.stringify(data) }] }
}

function errOut(tool: string, msg: string) {
  return { ...dualOutput({ ok: false, error: msg, tool }, tool), isError: true as const }
}

// GOOD: explicitly passes TOOL_NAME
export async function kalaNowGet() {
  const result = { ok: true, reading: {} }
  return dualOutput(result, TOOL_NAME)
}
