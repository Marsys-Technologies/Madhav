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
// SATYA-ŚEṢA W3 (2026-07-25): the kala/gochara family (gochara_activation_get/
// forecast_get/election_avoidance_get, kala_windows_get, kala_bundle_get) is not
// registered via registry_bridge.ts's own server.tool() call sites, so none of
// it was ever in MCP_RESPONSE_BUDGET_KB — the budget_census_gate ran and passed
// without ever measuring this family (the EL-11/EL-42 census-escape the brief
// names). Two more source-text-parsed ledgers close it, same mechanism as the
// registry_bridge.ts one below, merged into one flat ledger by extractResponseBudgetLedger.
export const GOCHARA_WINDOWS_PATH = path.join(MCP_TOOLS_ROOT, 'retrieval', 'register_gochara_windows.ts')
export const RESPONSE_BUDGET_LIB_PATH = path.join(MCP_TOOLS_ROOT, '..', 'lib', 'response_budget.ts')

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
 * Extracts ONE `const <marker> = { tool_name: number, ... } as const` object-literal
 * ledger from `filePath` by source-text parsing (not an import — that would pull the
 * whole module graph, including the MCP SDK and DB proxy code for a file like
 * registry_bridge.ts, into a plain analysis script). Walks brace depth from the
 * declaration to the matching close, then regex-matches `key: number,` pairs,
 * skipping `//` comment lines. Shared by every ledger this gate reads — see
 * `extractResponseBudgetLedger` below for the merged, multi-file result.
 */
function extractLedgerFrom(filePath: string, constName: string): Record<string, number> {
  const src = readFileSync(filePath, 'utf-8')
  const startMarker = `const ${constName}`
  const startIdx = src.indexOf(startMarker)
  if (startIdx === -1) {
    throw new Error(`extractLedgerFrom: '${startMarker}' not found in ${filePath} — has the ledger been renamed/moved?`)
  }
  const braceOpen = src.indexOf('{', startIdx)
  if (braceOpen === -1) throw new Error(`extractLedgerFrom: no opening brace found after '${startMarker}' in ${filePath}`)
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

/**
 * The full budget_census_gate ledger: registry_bridge.ts's `MCP_RESPONSE_BUDGET_KB`
 * (every tool registered there) MERGED with two SATYA-ŚEṢA W3 additions for the
 * kala/gochara family, which is registered elsewhere and was never in the original
 * ledger (the census-escape the brief's EL-11/EL-42 names — a budget gate that runs
 * and passes without ever measuring an entire tool family is not a real gate for
 * that family): register_gochara_windows.ts's `GOCHARA_RESPONSE_BUDGET_KB`
 * (gochara_activation_get/forecast_get/election_avoidance_get) and
 * response_budget.ts's `KALA_TEMPORAL_FAMILY_BUDGET_KB` (kala_windows_get,
 * kala_bundle_get). No key collisions expected across the three (verified at
 * merge time below — a collision throws rather than silently picking one, since a
 * duplicate declared ceiling for the same tool name is itself a drift bug worth
 * surfacing, not resolving silently).
 */
export function extractResponseBudgetLedger(): Record<string, number> {
  const sources: Array<{ path: string; constName: string }> = [
    { path: REGISTRY_BRIDGE_PATH, constName: 'MCP_RESPONSE_BUDGET_KB' },
    { path: GOCHARA_WINDOWS_PATH, constName: 'GOCHARA_RESPONSE_BUDGET_KB' },
    { path: RESPONSE_BUDGET_LIB_PATH, constName: 'KALA_TEMPORAL_FAMILY_BUDGET_KB' },
  ]
  const merged: Record<string, number> = {}
  for (const { path: filePath, constName } of sources) {
    const partial = extractLedgerFrom(filePath, constName)
    for (const [name, kb] of Object.entries(partial)) {
      if (name in merged && merged[name] !== kb) {
        throw new Error(
          `extractResponseBudgetLedger: conflicting ceilings for '${name}' — ${merged[name]}KB vs ${kb}KB (from ${constName} in ${filePath})`
        )
      }
      merged[name] = kb
    }
  }
  return merged
}
