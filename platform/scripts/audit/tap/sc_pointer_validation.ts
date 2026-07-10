/**
 * sc_pointer_validation.ts — boot-time pointer validation (SC-17, SC-18, SC-19)
 * ==============================================================================
 * Task item 6 / TAP-5 "Law-7": register/registry rows referencing serving
 * surfaces (drill_pointers, `recover`/`refine`/`build_state` hints) must
 * actually resolve to a tool that is live on the MCP server.
 *
 * Register rows (MARSYS_DEFECT_GAP_REGISTER_v2_0.md §11.3):
 *   SC-17 `bodha_bundle_get` recover-pointer targets a tool that was never
 *         registered (rename never shipped; live tool =
 *         holistic_bundle_chart_facts). holistic_bundle.ts:73
 *   SC-18 Budget-trim recover pointers name INTERNAL capability names, not
 *         MCP tools (get_dignity/get_avasthas/get_divisionals/query_signals…)
 *         — fires exactly when data was withheld, pointing the caller at a
 *         tool-not-found. registry_bridge.ts:2098-2493
 *   SC-19 `instrument:'bo_upaya'` puts an asset id in a tool-pointer field.
 *         query_remedies.ts:272
 *
 * This is a pure static check: it (1) enumerates every tool actually
 * registered via `server.tool('name', ...)` across platform-mcp/src/tools,
 * then (2) enumerates every `instrument: '<name>'` pointer literal across
 * the TS source tree (registry_bridge.ts's `recover` hints, query_remedies.ts
 * drill_pointers, holistic_bundle.ts's `recover`, etc.), and (3) flags any
 * pointer whose named instrument is not in the registered set.
 *
 * No DB required — runs anywhere, always.
 * Run: npx tsx platform/scripts/audit/tap/sc_pointer_validation.ts
 */
import path from 'node:path'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { printReport, type LawResult } from './lib/tap_db'

const REPO_ROOT = path.join(__dirname, '../../../..')
const MCP_TOOLS_ROOT = path.join(REPO_ROOT, 'platform-mcp/src/tools')
const SCAN_ROOTS = [
  path.join(REPO_ROOT, 'platform-mcp/src'),
  path.join(REPO_ROOT, 'platform/src/lib/retrieval'),
]

// Known asset-id-in-tool-pointer-field mislabels (SC-19 class): these are
// not "tool not found", they're a field-type violation. Tracked separately.
const KNOWN_ASSET_ID_POINTERS = new Set(['bo_upaya'])

type BaselineEntry = { instrument: string; register_row: string; note: string }
function loadPointerBaseline(): Map<string, BaselineEntry> {
  const raw = readFileSync(path.join(__dirname, 'sc_pointer_baseline.json'), 'utf-8')
  const entries = JSON.parse(raw).entries as BaselineEntry[]
  return new Map(entries.map((e) => [e.instrument, e]))
}

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

function collectRegisteredTools(): Set<string> {
  const files: string[] = []
  walkTs(MCP_TOOLS_ROOT, files)
  const names = new Set<string>()
  for (const f of files) {
    const src = readFileSync(f, 'utf-8')
    // server.tool(\n  'name', ...) or server.tool(NAME_CONST, ...) — only the
    // string-literal form is statically resolvable; constant-form call sites
    // (e.g. kala_temporal.ts's server.tool(TOOL_NAME, ...)) are handled below.
    for (const m of src.matchAll(/server\.tool\(\s*['"]([a-zA-Z0-9_]+)['"]/g)) {
      names.add(m[1])
    }
  }
  // kala_temporal.ts registers via a TOOL_NAME constant — resolve it directly
  // since it's the one known non-literal call site (avoids a false negative).
  try {
    const kt = readFileSync(path.join(MCP_TOOLS_ROOT, 'retrieval/kala_temporal.ts'), 'utf-8')
    const m = kt.match(/const TOOL_NAME = ['"]([a-zA-Z0-9_]+)['"]/)
    if (m) names.add(m[1])
  } catch {
    /* file may not exist in this codebase version — non-fatal */
  }
  return names
}

type PointerHit = { file: string; instrument: string }

function collectPointerHits(): PointerHit[] {
  const files: string[] = []
  for (const root of SCAN_ROOTS) walkTs(root, files)
  const hits: PointerHit[] = []
  for (const f of files) {
    const src = readFileSync(f, 'utf-8')
    for (const m of src.matchAll(/instrument:\s*['"]([a-zA-Z0-9_.]+)['"]/g)) {
      hits.push({ file: path.relative(REPO_ROOT, f), instrument: m[1] })
    }
  }
  return hits
}

function main() {
  const registered = collectRegisteredTools()
  const hits = collectPointerHits()
  const baseline = loadPointerBaseline()
  const results: LawResult[] = []

  results.push({
    id: 'SC-pointer:registered-count',
    title: 'Live MCP tool registry size (statically resolved)',
    status: registered.size >= 50 ? 'PASS' : 'FAIL',
    detail: `${registered.size} tool names resolved from server.tool() call sites under platform-mcp/src/tools.`,
  })

  const byInstrument = new Map<string, string[]>()
  for (const h of hits) {
    if (!byInstrument.has(h.instrument)) byInstrument.set(h.instrument, [])
    byInstrument.get(h.instrument)!.push(h.file)
  }

  let unresolvedCount = 0
  let assetIdMislabelCount = 0
  for (const [instrument, files] of byInstrument) {
    const uniqueFiles = [...new Set(files)]
    if (registered.has(instrument)) continue // resolves fine — not reported (would be noisy at 100+ healthy pointers)
    if (KNOWN_ASSET_ID_POINTERS.has(instrument)) {
      assetIdMislabelCount++
      results.push({
        id: `SC-19:${instrument}`,
        title: `Pointer instrument '${instrument}' is an asset id, not a tool name`,
        status: 'QUARANTINED',
        detail: `${uniqueFiles.length} occurrence(s) in: ${uniqueFiles.join(', ')}.`,
        register_rows: ['SC-19'],
      })
      continue
    }
    unresolvedCount++
    const known = baseline.get(instrument)
    results.push({
      id: `SC-pointer:${instrument}`,
      title: `Pointer instrument '${instrument}' does not resolve to a registered MCP tool`,
      status: known ? 'QUARANTINED' : 'FAIL',
      detail: known
        ? `${uniqueFiles.length} occurrence(s) in: ${uniqueFiles.join(', ')}. ${known.note}`
        : `${uniqueFiles.length} occurrence(s) in: ${uniqueFiles.join(', ')}. NOT in sc_pointer_baseline.json — new regression, or file it as a register row and add a baseline entry if pre-existing.`,
      register_rows: known ? [known.register_row] : [],
    })
  }

  results.push({
    id: 'SC-pointer:summary',
    title: 'Boot-time pointer resolution summary',
    status: 'PASS',
    detail: `${byInstrument.size} distinct pointer instruments found across ${hits.length} occurrences; ${unresolvedCount} unresolved (non-asset-id; see baseline for per-instrument status), ${assetIdMislabelCount} asset-id-in-tool-field.`,
  })

  process.exit(printReport('Boot-time pointer validation (SC-17/18/19)', results))
}

main()
