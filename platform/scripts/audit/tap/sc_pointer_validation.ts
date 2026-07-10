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
 * registered — via `server.tool('name', ...)` OR the `regAlias`/`globalAlias`
 * helper indirection used by register_p1_aliases.ts (see
 * lib/mcp_registered_tools.ts for why both shapes must be handled — a
 * literal-only regex here produced two Ring-2-caught false positives in the
 * first cut of this file), then (2) enumerates every `instrument: '<name>'`
 * pointer literal across the TS source tree (registry_bridge.ts's `recover`
 * hints, query_remedies.ts drill_pointers, holistic_bundle.ts's `recover`,
 * etc.), and (3) flags any pointer whose named instrument is not in the
 * registered set.
 *
 * No DB required — runs anywhere, always.
 * Run: npx tsx platform/scripts/audit/tap/sc_pointer_validation.ts
 */
import path from 'node:path'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { printReport, lineHash, type LawResult } from './lib/tap_db'
import { collectRegisteredTools } from './lib/mcp_registered_tools'

const REPO_ROOT = path.join(__dirname, '../../../..')
const SCAN_ROOTS = [
  path.join(REPO_ROOT, 'platform-mcp/src'),
  path.join(REPO_ROOT, 'platform/src/lib/retrieval'),
]

// Known asset-id-in-tool-pointer-field mislabels (SC-19 class): these are
// not "tool not found", they're a field-type violation. Tracked separately.
const KNOWN_ASSET_ID_POINTERS = new Set(['bo_upaya'])

// Ring-2 fix: keyed on (instrument, file, line-hash) — NOT instrument name
// alone. A name-only key would let a brand-new pointer occurrence quietly
// inherit QUARANTINED status just because some OTHER file already has a
// baselined pointer to the same (bad) instrument name; hashing the exact
// matched line means every new occurrence — new file or new line in an
// already-baselined file — must be explicitly added to the baseline.
type BaselineEntry = { instrument: string; register_row: string; note: string }
function loadPointerBaseline(): BaselineEntry[] {
  const raw = readFileSync(path.join(__dirname, 'sc_pointer_baseline.json'), 'utf-8')
  return JSON.parse(raw).entries as BaselineEntry[]
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

type PointerHit = { file: string; line: number; hash: string; instrument: string }

function collectPointerHits(): PointerHit[] {
  const files: string[] = []
  for (const root of SCAN_ROOTS) walkTs(root, files)
  const hits: PointerHit[] = []
  for (const f of files) {
    const src = readFileSync(f, 'utf-8')
    const lines = src.split('\n')
    for (let i = 0; i < lines.length; i++) {
      const m = lines[i].match(/instrument:\s*['"]([a-zA-Z0-9_.]+)['"]/)
      if (m) {
        hits.push({ file: path.relative(REPO_ROOT, f), line: i + 1, hash: lineHash(lines[i]), instrument: m[1] })
      }
    }
  }
  return hits
}

function main() {
  const registered = collectRegisteredTools()
  const hits = collectPointerHits()
  const baseline = loadPointerBaseline()
  // Baseline no longer records file/line (it's a pre-2026-07-10-Ring-2
  // artifact keyed by instrument name only, since the exact line varies by
  // codebase state at any given time) — so we key baseline lookups by
  // instrument, but STILL require the exact (file, hash) of every live hit
  // to have been seen before by recording a "confirmed occurrences" ledger
  // alongside it (occurrences.json), regenerated each time an instrument's
  // baseline entry is (re)confirmed. See sc_pointer_occurrences.json.
  const occurrences = loadOccurrences()
  const results: LawResult[] = []

  results.push({
    id: 'SC-pointer:registered-count',
    title: 'Live MCP tool registry size (statically resolved)',
    status: registered.size >= 50 ? 'PASS' : 'FAIL',
    detail: `${registered.size} tool names resolved from server.tool()/regAlias()/globalAlias() call sites under platform-mcp/src/tools (see lib/mcp_registered_tools.ts).`,
  })

  const byInstrument = new Map<string, PointerHit[]>()
  for (const h of hits) {
    if (!byInstrument.has(h.instrument)) byInstrument.set(h.instrument, [])
    byInstrument.get(h.instrument)!.push(h)
  }

  let unresolvedCount = 0
  let assetIdMislabelCount = 0
  for (const [instrument, instrumentHits] of byInstrument) {
    if (registered.has(instrument)) continue // resolves fine — not reported (would be noisy at 100+ healthy pointers)
    const uniqueFiles = [...new Set(instrumentHits.map((h) => h.file))]
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
    const known = baseline.find((b) => b.instrument === instrument)
    const newOccurrences = instrumentHits.filter((h) => !occurrences.has(`${instrument}:${h.file}:${h.hash}`))
    if (!known) {
      results.push({
        id: `SC-pointer:${instrument}`,
        title: `Pointer instrument '${instrument}' does not resolve to a registered MCP tool`,
        status: 'FAIL',
        detail: `${uniqueFiles.length} occurrence(s) in: ${uniqueFiles.join(', ')}. NOT in sc_pointer_baseline.json — new regression, or file it as a register row and add a baseline entry if pre-existing.`,
      })
    } else if (newOccurrences.length > 0) {
      results.push({
        id: `SC-pointer:${instrument}`,
        title: `Pointer instrument '${instrument}' does not resolve to a registered MCP tool`,
        status: 'FAIL',
        detail: `Instrument '${instrument}' is baselined, but ${newOccurrences.length} occurrence(s) are at (file, line) combinations NOT in sc_pointer_occurrences.json: ${newOccurrences.map((h) => `${h.file}:${h.line}`).join(', ')} — a NEW pointer to an already-known-bad instrument still needs an explicit occurrence entry (Ring-2 discipline: name-only baselining is too coarse).`,
        register_rows: [known.register_row],
      })
    } else {
      results.push({
        id: `SC-pointer:${instrument}`,
        title: `Pointer instrument '${instrument}' does not resolve to a registered MCP tool`,
        status: 'QUARANTINED',
        detail: `${uniqueFiles.length} occurrence(s), all previously confirmed in sc_pointer_occurrences.json: ${uniqueFiles.join(', ')}. ${known.note}`,
        register_rows: [known.register_row],
      })
    }
  }

  results.push({
    id: 'SC-pointer:summary',
    title: 'Boot-time pointer resolution summary',
    status: 'PASS',
    detail: `${byInstrument.size} distinct pointer instruments found across ${hits.length} occurrences; ${unresolvedCount} unresolved (non-asset-id; see baseline for per-instrument status), ${assetIdMislabelCount} asset-id-in-tool-field.`,
  })

  process.exit(printReport('Boot-time pointer validation (SC-17/18/19)', results))
}

type OccurrenceEntry = { instrument: string; file: string; line_hash: string }
function loadOccurrences(): Set<string> {
  const raw = readFileSync(path.join(__dirname, 'sc_pointer_occurrences.json'), 'utf-8')
  const entries = JSON.parse(raw).entries as OccurrenceEntry[]
  return new Set(entries.map((e) => `${e.instrument}:${e.file}:${e.line_hash}`))
}

main()
