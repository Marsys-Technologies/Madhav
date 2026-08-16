// FAIL fixture — dualOutput defined with toolName = 'unknown_tool' default.
// Defect: any call site that omits toolName inherits 'unknown_tool', making
// recover_via pointers in errors useless (F-43 root cause).

function dualOutput(data: unknown, toolName = 'unknown_tool') {
  const structuredContent = { type: 'object' as const, object: data }
  return { structuredContent, content: [{ type: 'text' as const, text: JSON.stringify(data) }] }
}

function errOut(tool: string, msg: string) {
  return { ...dualOutput({ ok: false, error: msg, tool }), isError: true as const }
}

// BAD: bare call — inherits 'unknown_tool' default
export async function catalogAssetsList(args: Record<string, unknown>) {
  try {
    const data = { ok: true, rows: [] }
    return dualOutput(data)  // missing toolName
  } catch (err) {
    return errOut('catalog_assets_list', String(err))
  }
}
