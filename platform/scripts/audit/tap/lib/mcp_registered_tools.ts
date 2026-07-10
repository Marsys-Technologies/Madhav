/**
 * mcp_registered_tools.ts — shared static enumeration of every MCP tool name
 * actually registered on the live server.
 *
 * Ring-2 review finding (post-bacade1c): the original per-script copy of
 * this logic only matched literal `server.tool('name', ...)` call sites. It
 * missed the `regAlias(server, '<name>', ...)` / `globalAlias(server, '<name>',
 * ...)` helper pattern used by register_p1_aliases.ts (own header comment:
 * "The 47 aliases implemented in this file cover the remaining 47 of the 53
 * baseline tools") — those helpers call `server.tool(name, ...)` internally
 * with `name` passed in as a parameter, so the literal-string regex never
 * saw them. That produced two false-positive "unresolved pointer" findings
 * (phala_predictive_anchors_get, bodha_remedies_get — both ARE registered,
 * via regAlias at register_p1_aliases.ts:416 and :393) in the first cut of
 * sc_pointer_validation.ts.
 *
 * This module is the single source of truth for "is `name` a live tool" —
 * both sc_pointer_validation.ts and mcp_tool_smoke.ts import it so the fix
 * can't drift between the two call sites again.
 */
import path from 'node:path'
import { readFileSync, readdirSync, statSync } from 'node:fs'

const REPO_ROOT = path.join(__dirname, '../../../../..')
const MCP_TOOLS_ROOT = path.join(REPO_ROOT, 'platform-mcp/src/tools')

function walkTs(dir: string, out: string[]): void {
  let entries: string[]
  try {
    entries = readdirSync(dir)
  } catch {
    return
  }
  for (const entry of entries) {
    if (entry === 'node_modules' || entry === '.git') continue
    const full = path.join(dir, entry)
    const st = statSync(full)
    if (st.isDirectory()) walkTs(full, out)
    else if (entry.endsWith('.ts')) out.push(full)
  }
}

/**
 * Statically resolves every tool name registered on the live MCP server by
 * scanning platform-mcp/src/tools for three registration shapes:
 *   1. `server.tool('name', ...)`               — direct literal call sites.
 *   2. `regAlias(server, 'name', ...)`           — chart-scoped alias helper
 *      (register_p1_aliases.ts), which itself calls `server.tool(name, ...)`.
 *   3. `globalAlias(server, 'name', ...)`        — global-scope alias helper,
 *      same file, same delegation pattern.
 *   4. `server.tool(TOOL_NAME, ...)` where `const TOOL_NAME = 'name'` is
 *      declared in the same file (the one known non-literal direct call
 *      site, kala_temporal.ts).
 */
export function collectRegisteredTools(): Set<string> {
  const files: string[] = []
  walkTs(MCP_TOOLS_ROOT, files)
  const names = new Set<string>()
  for (const f of files) {
    const src = readFileSync(f, 'utf-8')
    for (const m of src.matchAll(/server\.tool\(\s*['"]([a-zA-Z0-9_]+)['"]/g)) names.add(m[1])
    for (const m of src.matchAll(/\b(?:regAlias|globalAlias)\(\s*server,\s*['"]([a-zA-Z0-9_]+)['"]/g)) names.add(m[1])
  }
  try {
    const kt = readFileSync(path.join(MCP_TOOLS_ROOT, 'retrieval/kala_temporal.ts'), 'utf-8')
    const m = kt.match(/const TOOL_NAME = ['"]([a-zA-Z0-9_]+)['"]/)
    if (m) names.add(m[1])
  } catch {
    /* file may not exist in this codebase version — non-fatal */
  }
  return names
}
