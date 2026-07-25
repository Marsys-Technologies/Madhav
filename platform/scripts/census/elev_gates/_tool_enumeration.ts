/**
 * _tool_enumeration.ts — static, mechanical enumeration of every MCP tool registered
 * on the live server, plus the `MCP_RESPONSE_BUDGET_KB` per-tool ceiling ledger.
 *
 * Reads `platform-mcp/src/tools/**` (read-only source-text scan — this lane's manifest
 * does not include write access there, so it never imports/executes that package,
 * only greps it, matching the task-1 instruction: "Grep platform-mcp/src/tools/... to
 * enumerate the registered tool list programmatically rather than hand-maintaining a
 * list"). Mirrors (independently — see _mcp_client.ts header for why this is not a
 * shared import) the three registration shapes already established in
 * `platform/scripts/audit/tap/lib/mcp_registered_tools.ts`:
 *   1. `server.tool('name', ...)`               — direct literal call sites.
 *   2. `regAlias(server, 'name', ...)` / `globalAlias(server, 'name', ...)` — the
 *      chart-scoped / global alias helpers (register_p1_aliases.ts).
 *   3. `server.tool(TOOL_NAME, ...)` where `const TOOL_NAME = 'name'` is declared in
 *      the SAME file — resolved per-file, not hardcoded to one filename.
 */
import { readFileSync, readdirSync, statSync } from 'node:fs'
import path from 'node:path'

// This file lives at platform/scripts/census/elev_gates/ — five levels up is the repo root.
const REPO_ROOT = path.join(__dirname, '..', '..', '..', '..')
export const MCP_TOOLS_ROOT = path.join(REPO_ROOT, 'platform-mcp/src/tools')
export const REGISTRY_BRIDGE_PATH = path.join(MCP_TOOLS_ROOT, 'registry_bridge.ts')

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
    let st
    try {
      st = statSync(full)
    } catch {
      continue
    }
    if (st.isDirectory()) walkTs(full, out)
    else if (entry.endsWith('.ts') && !entry.endsWith('.test.ts')) out.push(full)
  }
}

export type RegisteredTool = {
  name: string
  source_files: string[]
}

/** Every `.ts` file under platform-mcp/src/tools (excluding *.test.ts), read once. */
export function listToolSourceFiles(): string[] {
  const files: string[] = []
  walkTs(MCP_TOOLS_ROOT, files)
  return files.sort()
}

/** Statically resolves every live tool name -> the file(s) that register it. */
export function collectRegisteredTools(): Map<string, RegisteredTool> {
  const byName = new Map<string, RegisteredTool>()
  const add = (name: string, file: string) => {
    const existing = byName.get(name)
    if (existing) {
      if (!existing.source_files.includes(file)) existing.source_files.push(file)
    } else {
      byName.set(name, { name, source_files: [file] })
    }
  }
  for (const f of listToolSourceFiles()) {
    const src = readFileSync(f, 'utf-8')
    for (const m of src.matchAll(/server\.tool\(\s*['"]([a-zA-Z0-9_]+)['"]/g)) add(m[1]!, f)
    for (const m of src.matchAll(/\b(?:regAlias|globalAlias)\(\s*server,\s*['"]([a-zA-Z0-9_]+)['"]/g)) add(m[1]!, f)
    if (/server\.tool\(\s*TOOL_NAME\s*,/.test(src)) {
      const m = src.match(/const TOOL_NAME\s*=\s*['"]([a-zA-Z0-9_]+)['"]/)
      if (m) add(m[1]!, f)
    }
  }
  return byName
}

/**
 * Extracts the `MCP_RESPONSE_BUDGET_KB` object literal from registry_bridge.ts by
 * source-text parsing (not an import — that would pull the whole registry_bridge.ts
 * module graph, including the MCP SDK and DB proxy code, into a plain analysis
 * script). The object is a flat `{ tool_name: number, ... } as const` literal
 * (confirmed by reading the file — see registry_bridge.ts ~L303-348); this walks
 * brace depth from the declaration to the matching close, then regex-matches
 * `key: number,` pairs, skipping `//` comment lines.
 */
export function extractResponseBudgetLedger(): Record<string, number> {
  const src = readFileSync(REGISTRY_BRIDGE_PATH, 'utf-8')
  const startMarker = 'const MCP_RESPONSE_BUDGET_KB'
  const startIdx = src.indexOf(startMarker)
  if (startIdx === -1) {
    throw new Error(`extractResponseBudgetLedger: '${startMarker}' not found in ${REGISTRY_BRIDGE_PATH} — has the ledger been renamed/moved?`)
  }
  const braceOpen = src.indexOf('{', startIdx)
  if (braceOpen === -1) throw new Error('extractResponseBudgetLedger: no opening brace found after declaration')
  let depth = 0
  let i = braceOpen
  for (; i < src.length; i++) {
    if (src[i] === '{') depth++
    else if (src[i] === '}') {
      depth--
      if (depth === 0) break
    }
  }
  const block = src.slice(braceOpen + 1, i)
  const ledger: Record<string, number> = {}
  for (const rawLine of block.split('\n')) {
    const line = rawLine.trim()
    if (!line || line.startsWith('//')) continue
    const m = line.match(/^([a-zA-Z0-9_]+)\s*:\s*(\d+)\s*,?\s*(\/\/.*)?$/)
    if (m) ledger[m[1]!] = Number(m[2])
  }
  return ledger
}
