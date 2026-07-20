/**
 * rescan_dark_tables_widened_surface.ts — W1 addendum (docs/w1-addendum-taxonomy)
 *
 * Re-runs the L1b/L1d dark-table serving-route search with a WIDENED scan surface,
 * per the native's §F gate ruling item 4 ("census re-scan as a W1 addendum,
 * platform-mcp/src/tools/ included in the scan surface this time, re-checking all 77
 * former-dark verdicts"). The original W1 L1b harvest (`e1_registry_extractor.ts`)
 * only scanned `platform/src/lib/retrieval/registry/layers/**` + `synthesis/**` for a
 * capability's static `table_hint`. That scope missed at least 2 confirmed
 * false-darks (`bg_dignity_reference`, `chart_panchanga`) whose serving routes live in
 * `platform-mcp/src/tools/register_p1_reference.ts` and
 * `platform/src/lib/tools/brahma/l1/query_panchanga.ts` — both outside the original
 * scan's two directories.
 *
 * WIDENED SURFACE (this script):
 *   - platform/src/lib/retrieval/          (original scope, kept)
 *   - platform-mcp/src/tools/              (NEW — MCP tool handlers)
 *   - platform-mcp/src/resources/          (NEW — MCP resource handlers)
 *   - platform/src/lib/tools/              (NEW — the query_panchanga.ts precedent)
 *   - platform/src/app/api/                (NEW — any route serving a table directly)
 *
 * This script is MECHANICAL EVIDENCE ONLY (step 2a of the addendum task): "does any
 * file in the widened surface reference this table's literal name". It does NOT
 * decide OPERATIONAL vs GATED vs RETIRED vs genuine SERVE gap — those calls require
 * reading migration files (to see whether a hit is a real SELECT/serving read vs a
 * DELETE-only cockpit-clear reference, an admin-only write path, a doc-comment, or a
 * substring collision with an unrelated capability name) and are recorded with full
 * citations in `00_ARCHITECTURE/briefs/retrieval_impl/TABLE_CONCEPT_DISPOSITIONS_v2_0.md`.
 * Treat this script's JSON output as "candidate evidence to inspect", not a verdict —
 * exactly the caveat the original adjudication_queue.json carried for its own
 * table_hint scan ("a DARK row means no TS-registry route found, not provably
 * unreachable by any means").
 *
 * Run: npx tsx platform/scripts/census/rescan_dark_tables_widened_surface.ts
 *   (from the `platform/` package directory; no DB credential required — pure
 *   static grep over the checked-out source tree.)
 */

import * as fs from 'fs'
import * as path from 'path'

const REPO_ROOT = path.resolve(__dirname, '..', '..', '..')
const PLATFORM_ROOT = path.resolve(__dirname, '..', '..')

const SCAN_DIRS = [
  path.join(PLATFORM_ROOT, 'src/lib/retrieval'),
  path.join(REPO_ROOT, 'platform-mcp/src/tools'),
  path.join(REPO_ROOT, 'platform-mcp/src/resources'),
  path.join(PLATFORM_ROOT, 'src/lib/tools'),
  path.join(PLATFORM_ROOT, 'src/app/api'),
]

const ADJUDICATION_QUEUE_JSON = path.join(
  PLATFORM_ROOT,
  'src/generated/harvest/adjudication_queue.json',
)

interface Hit {
  file: string
  line: number
  text: string
}

function walk(dir: string, out: string[]): void {
  if (!fs.existsSync(dir)) return
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      if (entry.name === 'node_modules' || entry.name === '.next') continue
      walk(full, out)
    } else if (/\.(ts|tsx)$/.test(entry.name)) {
      out.push(full)
    }
  }
}

function scanFiles(files: string[], table: string): Hit[] {
  const hits: Hit[] = []
  for (const file of files) {
    const content = fs.readFileSync(file, 'utf8')
    if (!content.includes(table)) continue
    const lines = content.split('\n')
    lines.forEach((line, idx) => {
      if (line.includes(table)) {
        hits.push({
          file: path.relative(REPO_ROOT, file),
          line: idx + 1,
          text: line.trim().slice(0, 200),
        })
      }
    })
  }
  return hits
}

function main(): void {
  if (!fs.existsSync(ADJUDICATION_QUEUE_JSON)) {
    console.error(`Missing ${ADJUDICATION_QUEUE_JSON} — run L1b's harvest first.`)
    process.exit(1)
  }
  const queue = JSON.parse(fs.readFileSync(ADJUDICATION_QUEUE_JSON, 'utf8'))
  const rows: Array<{ type?: string; table_name?: string }> = queue.rows ?? []
  const tables: string[] = rows
    .filter((r) => r.type === 'DARK')
    .map((r) => r.table_name)
    .filter((t): t is string => Boolean(t))

  const tableList: string[] =
    tables.length > 0
      ? tables
      : // Fallback: static list mirrored from ADJUDICATION_QUEUE.md if the JSON shape
        // differs from expectation — keeps this script runnable standalone.
        []

  if (tableList.length === 0) {
    console.error(
      'Could not extract table list from adjudication_queue.json (unexpected shape) — ' +
        'pass table names on argv instead: rescan_dark_tables_widened_surface.ts t1 t2 ...',
    )
    process.exit(1)
  }

  const allFiles: string[] = []
  for (const dir of SCAN_DIRS) walk(dir, allFiles)

  const results: Record<string, Hit[]> = {}
  for (const t of tableList) {
    results[t] = scanFiles(allFiles, t)
  }

  const summary = {
    generated_at: new Date().toISOString(),
    scan_dirs: SCAN_DIRS.map((d) => path.relative(REPO_ROOT, d)),
    files_scanned: allFiles.length,
    tables_scanned: tableList.length,
    tables_with_hits: Object.values(results).filter((h) => h.length > 0).length,
    tables_with_zero_hits: Object.entries(results)
      .filter(([, h]) => h.length === 0)
      .map(([t]) => t),
    results,
  }

  const outPath = path.join(
    PLATFORM_ROOT,
    'src/generated/harvest/widened_surface_rescan.json',
  )
  fs.mkdirSync(path.dirname(outPath), { recursive: true })
  fs.writeFileSync(outPath, JSON.stringify(summary, null, 2))
  console.log(`Wrote ${outPath}`)
  console.log(
    `${summary.tables_with_hits}/${summary.tables_scanned} tables have >=1 widened-surface hit; ` +
      `${summary.tables_with_zero_hits.length} remain zero-hit even under the widened scan.`,
  )
}

main()
