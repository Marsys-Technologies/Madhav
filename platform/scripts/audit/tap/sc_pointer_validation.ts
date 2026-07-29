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
 *   SC-23 `query_classical_texts` — the never-filed "NEW-P2" this harness
 *         itself discovered on 2026-07-10; intended target verified as
 *         `ref_rules_search`. register_d9_judgment.ts:1146
 *
 * All four register rows are FIXED in production as of 2026-07-30 (SAMĀPTI
 * lane A2), so this check now runs as a RATCHET AT ZERO: the baseline and
 * occurrence ledgers are empty, and any unresolved pointer at all is a FAIL.
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
 * ── DECLARED BOUNDS OF THIS CHECK (CLAUDE.md §N.8 — a detector that
 *    overclaims its coverage is itself an earned-signal violation) ──
 *  a) It is a LINE-LEVEL REGEX over source text, not a type-aware analysis. A
 *     pointer built from a variable or template expression
 *     (`instrument: toolName`) is INVISIBLE to it. It catches literals only.
 *  b) It SKIPS matches inside comments (line comments, block-comment bodies,
 *     JSDoc continuation lines).
 *     Rationale: prose documenting a dead pointer is not itself a dead
 *     pointer, and before this exclusion existed the check actively punished
 *     in-code documentation of the very defect class it polices. The cost of
 *     the exclusion is that a pointer inside COMMENTED-OUT code is not
 *     flagged — acceptable, because commented-out code serves nothing.
 *  c) It scans TEST FIXTURES as well as production source, by design and per
 *     the convention documented at `platform-mcp/src/lib/kala_envelope.test.ts`
 *     and `platform-mcp/src/tools/kala_views/ritual.test.ts`: a fixture naming
 *     a non-existent tool is modelling a response the real capability can
 *     never produce. Findings are nonetheless CLASSIFIED by surface
 *     (`production` vs `test_fixture`) in the report, because the two have
 *     very different blast radius and the absence of that distinction is what
 *     let a unit-test placeholder (`instrument: 'x'`) read as a serving-surface
 *     regression for three weeks.
 *  d) It proves nothing about whether a REGISTERED tool works — only that the
 *     name resolves. Live behaviour is mcp_tool_smoke.ts's job.
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
// Empty since the SC-19 fix (query_remedies.ts:562-568 moved the asset id to
// its own `asset_id` field); retained as the mechanism, not as a live list.
const KNOWN_ASSET_ID_POINTERS = new Set<string>([])

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

type Surface = 'production' | 'test_fixture'
type PointerHit = { file: string; line: number; hash: string; instrument: string; surface: Surface }

/** Bound (c): a fixture is any `*.test.ts` or anything under a `__tests__/` dir. */
function classifySurface(relPath: string): Surface {
  return relPath.includes('__tests__/') || relPath.endsWith('.test.ts') ? 'test_fixture' : 'production'
}

/**
 * Bound (b): true when `matchIndex` in `line` sits inside a comment. Handles the
 * three shapes that occur in this tree — a whole-line `//`, a JSDoc/block
 * continuation line whose first non-space char is `*`, and a trailing `//`
 * before the match on an otherwise-code line. Deliberately conservative: it
 * only ever EXCLUDES a match, never manufactures one.
 */
function isInComment(line: string, matchIndex: number): boolean {
  const before = line.slice(0, matchIndex)
  const trimmedLeading = line.trimStart()
  if (trimmedLeading.startsWith('//')) return true
  if (trimmedLeading.startsWith('*')) return true // JSDoc / block-comment body line
  if (trimmedLeading.startsWith('/*')) return true
  if (before.includes('//')) return true // trailing line comment ahead of the match
  return false
}

function collectPointerHits(): PointerHit[] {
  const files: string[] = []
  for (const root of SCAN_ROOTS) walkTs(root, files)
  const hits: PointerHit[] = []
  for (const f of files) {
    const src = readFileSync(f, 'utf-8')
    const lines = src.split('\n')
    const rel = path.relative(REPO_ROOT, f)
    for (let i = 0; i < lines.length; i++) {
      const m = lines[i].match(/instrument:\s*['"]([a-zA-Z0-9_.]+)['"]/)
      if (m && !isInComment(lines[i], m.index ?? 0)) {
        hits.push({
          file: rel,
          line: i + 1,
          hash: lineHash(lines[i]),
          instrument: m[1],
          surface: classifySurface(rel),
        })
      }
    }
  }
  return hits
}

/**
 * The full battery, as data. Exported so tap5_seam_conservation.ts's Law-7 row
 * can report this check's REAL result instead of asserting a hardcoded
 * QUARANTINED status with no detector behind it (the §N.8 defect this file's
 * own repair lane was opened to fix).
 */
export function runPointerValidation(): LawResult[] {
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
  const liveUnresolvedInstruments = new Set<string>()
  const liveOccurrenceKeys = new Set<string>()
  for (const [instrument, instrumentHits] of byInstrument) {
    if (registered.has(instrument)) continue // resolves fine — not reported (would be noisy at 100+ healthy pointers)
    const uniqueFiles = [...new Set(instrumentHits.map((h) => h.file))]
    const prodHits = instrumentHits.filter((h) => h.surface === 'production')
    const testHits = instrumentHits.filter((h) => h.surface === 'test_fixture')
    // Bound (c): surface classification, so a reader can triage a FAIL without
    // opening every file. A production hit is a live serving defect; a
    // fixture-only hit is a test modelling an impossible capability response.
    const surfaceNote = `Surfaces: ${prodHits.length} production, ${testHits.length} test_fixture.`
    if (KNOWN_ASSET_ID_POINTERS.has(instrument)) {
      assetIdMislabelCount++
      results.push({
        id: `SC-19:${instrument}`,
        title: `Pointer instrument '${instrument}' is an asset id, not a tool name`,
        status: 'QUARANTINED',
        detail: `${uniqueFiles.length} occurrence(s) in: ${uniqueFiles.join(', ')}. ${surfaceNote}`,
        register_rows: ['SC-19'],
      })
      continue
    }
    unresolvedCount++
    liveUnresolvedInstruments.add(instrument)
    const known = baseline.find((b) => b.instrument === instrument)
    const newOccurrences = instrumentHits.filter((h) => !occurrences.has(`${instrument}:${h.file}:${h.hash}`))
    for (const h of instrumentHits) liveOccurrenceKeys.add(`${instrument}:${h.file}:${h.hash}`)
    if (!known) {
      results.push({
        id: `SC-pointer:${instrument}`,
        title: `Pointer instrument '${instrument}' does not resolve to a registered MCP tool`,
        status: 'FAIL',
        detail: `${uniqueFiles.length} occurrence(s) in: ${instrumentHits.map((h) => `${h.file}:${h.line}`).join(', ')}. ${surfaceNote} NOT in sc_pointer_baseline.json — new regression, or file it as a register row and add a baseline entry if pre-existing.`,
      })
    } else if (newOccurrences.length > 0) {
      results.push({
        id: `SC-pointer:${instrument}`,
        title: `Pointer instrument '${instrument}' does not resolve to a registered MCP tool`,
        status: 'FAIL',
        detail: `Instrument '${instrument}' is baselined, but ${newOccurrences.length} occurrence(s) are at (file, line) combinations NOT in sc_pointer_occurrences.json: ${newOccurrences.map((h) => `${h.file}:${h.line}`).join(', ')} — a NEW pointer to an already-known-bad instrument still needs an explicit occurrence entry (Ring-2 discipline: name-only baselining is too coarse). ${surfaceNote}`,
        register_rows: [known.register_row],
      })
    } else {
      results.push({
        id: `SC-pointer:${instrument}`,
        title: `Pointer instrument '${instrument}' does not resolve to a registered MCP tool`,
        status: 'QUARANTINED',
        detail: `${uniqueFiles.length} occurrence(s), all previously confirmed in sc_pointer_occurrences.json: ${uniqueFiles.join(', ')}. ${surfaceNote} ${known.note}`,
        register_rows: [known.register_row],
      })
    }
  }

  // ── RATCHET-TIGHTENING GUARD (SAMĀPTI A2) ────────────────────────────────
  // A quarantine that can outlive its defect is indistinguishable from a
  // silenced check. Before this guard, four instruments (bodha_bundle_get,
  // get_dignity, get_avasthas, get_strength) sat QUARANTINED in the baseline
  // for 20 days AFTER their production pointers were fixed, so the report
  // could not answer "which SC rows are actually still open?" — the exact
  // failure mode the "document the quarantine with an expiry" ask was aimed
  // at, solved structurally instead of by a date that nobody re-reads: an
  // entry expires the moment the defect it describes stops reproducing.
  const staleBaseline = baseline.filter((b) => !liveUnresolvedInstruments.has(b.instrument))
  results.push({
    id: 'SC-pointer:baseline-freshness',
    title: 'Every sc_pointer_baseline.json entry still reproduces against the live tree',
    status: staleBaseline.length === 0 ? 'PASS' : 'FAIL',
    detail:
      staleBaseline.length === 0
        ? `All ${baseline.length} baseline entry/entries still reproduce (ratchet is tight${baseline.length === 0 ? ' — baseline is empty, i.e. ZERO tolerated unresolved pointers' : ''}).`
        : `${staleBaseline.length} baseline entry/entries no longer reproduce and MUST be deleted from sc_pointer_baseline.json (their defect is fixed; carrying them hides which register rows are genuinely open): ${staleBaseline.map((b) => `${b.instrument} (${b.register_row})`).join(', ')}.`,
  })

  const staleOccurrences = [...occurrences].filter((k) => !liveOccurrenceKeys.has(k))
  results.push({
    id: 'SC-pointer:occurrence-freshness',
    title: 'Every sc_pointer_occurrences.json entry still matches a live unresolved-pointer hit',
    status: staleOccurrences.length === 0 ? 'PASS' : 'FAIL',
    detail:
      staleOccurrences.length === 0
        ? `All ${occurrences.size} occurrence entry/entries still match a live hit.`
        : `${staleOccurrences.length} occurrence entry/entries are stale (the line moved, was fixed, or the file was deleted) and MUST be removed from sc_pointer_occurrences.json: ${staleOccurrences.slice(0, 20).join(', ')}${staleOccurrences.length > 20 ? `, … (+${staleOccurrences.length - 20} more)` : ''}.`,
  })

  results.push({
    id: 'SC-pointer:summary',
    title: 'Boot-time pointer resolution summary',
    status: 'PASS',
    detail: `${byInstrument.size} distinct pointer instruments found across ${hits.length} occurrences; ${unresolvedCount} unresolved (non-asset-id; see baseline for per-instrument status), ${assetIdMislabelCount} asset-id-in-tool-field.`,
  })

  return results
}

function main() {
  process.exit(printReport('Boot-time pointer validation (SC-17/18/19)', runPointerValidation()))
}

type OccurrenceEntry = { instrument: string; file: string; line_hash: string }
function loadOccurrences(): Set<string> {
  const raw = readFileSync(path.join(__dirname, 'sc_pointer_occurrences.json'), 'utf-8')
  const entries = JSON.parse(raw).entries as OccurrenceEntry[]
  return new Set(entries.map((e) => `${e.instrument}:${e.file}:${e.line_hash}`))
}

// Only self-execute when invoked directly, so tap5_seam_conservation.ts can
// import runPointerValidation() without this module calling process.exit().
if (require.main === module) main()
