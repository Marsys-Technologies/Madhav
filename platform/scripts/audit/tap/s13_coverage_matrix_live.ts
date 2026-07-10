/**
 * s13_coverage_matrix_live.ts — S-13 / TAP-5 Law-1 CI gate
 * ===========================================================
 * Register row: S-13 (MARSYS_DEFECT_GAP_REGISTER_v2_0.md §SECTION 4) —
 * "Coverage-matrix CI gate enumerates a stale hardcoded category snapshot" —
 * coverage_matrix.ts's CHART_FACTS_CATEGORIES list was authored 2026-06-16
 * and never regenerated; it is missing categories that exist live (SC-5:
 * "matrix stuck at 158 categories vs 187 emitted").
 *
 * Fix per the register: "Derive the gate list from live
 * `SELECT DISTINCT fact_category FROM chart_facts` (or writer manifests) at
 * gate time." This script IS that fix, run as a CI-enforced check.
 *
 * It diffs the live category set (queried from chart_facts for the native
 * chart) against the hardcoded CHART_FACTS_CATEGORIES export in
 * coverage_matrix.ts and fails if the live set contains categories the
 * static list has never seen — the exact failure mode S-13 describes.
 *
 * Requires DATABASE_URL (or Cloud SQL Auth Proxy) — see lib/tap_db.ts.
 * Run: npx tsx --conditions=react-server platform/scripts/audit/tap/s13_coverage_matrix_live.ts
 */
import path from 'node:path'
import { readFileSync } from 'node:fs'
import { connectTapDb, printReport, NATIVE_CHART_ID, type LawResult } from './lib/tap_db'

const COVERAGE_MATRIX_PATH = path.join(
  __dirname,
  '../../../src/lib/retrieval/registry/layers/L1_ganita/coverage_matrix.ts'
)

function loadStaticCategories(): Set<string> {
  const src = readFileSync(COVERAGE_MATRIX_PATH, 'utf-8')
  const marker = 'CHART_FACTS_CATEGORIES'
  const start = src.indexOf(marker)
  if (start === -1) throw new Error(`${marker} not found in coverage_matrix.ts`)
  const arrStart = src.indexOf('[', start)
  const arrEnd = src.indexOf(']', arrStart)
  const body = src.slice(arrStart, arrEnd)
  const items = [...body.matchAll(/'([a-z0-9_]+)'/g)].map((m) => m[1])
  return new Set(items)
}

async function main() {
  const db = await connectTapDb()
  const results: LawResult[] = []

  if (!db.available) {
    console.log(JSON.stringify({ battery: 'S-13 live coverage matrix', skipped: true, reason: db.reason }, null, 2))
    process.exit(printReport('S-13 live coverage matrix', [], db.reason))
    return
  }

  const staticCategories = loadStaticCategories()
  const { rows } = await db.query<{ fact_category: string }>(
    `SELECT DISTINCT fact_category FROM chart_facts WHERE chart_id = $1 ORDER BY 1`,
    [NATIVE_CHART_ID]
  )
  const liveCategories = new Set(rows.map((r) => r.fact_category))

  const missingFromStatic = [...liveCategories].filter((c) => !staticCategories.has(c))
  const staleInStatic = [...staticCategories].filter((c) => !liveCategories.has(c))

  results.push({
    id: 'S-13',
    title: `coverage_matrix.ts CHART_FACTS_CATEGORIES (${staticCategories.size}) vs live chart_facts.fact_category (${liveCategories.size})`,
    status: missingFromStatic.length === 0 ? 'PASS' : 'FAIL',
    detail:
      missingFromStatic.length === 0
        ? 'Static list covers every live category.'
        : `${missingFromStatic.length} live categories absent from the static gate list (S-2/S-3-class categories can never fail CI): ${missingFromStatic.slice(0, 20).join(', ')}${missingFromStatic.length > 20 ? ', …' : ''}`,
    register_rows: ['S-13', 'SC-5'],
  })

  if (staleInStatic.length > 0) {
    results.push({
      id: 'S-13-stale',
      title: 'Static categories with no live rows for the native chart',
      status: 'QUARANTINED',
      detail: `${staleInStatic.length} categories in the static list have zero live rows (may be chart-specific/rare, not necessarily wrong): ${staleInStatic.slice(0, 20).join(', ')}`,
      register_rows: ['S-13'],
    })
  }

  process.exit(printReport('S-13 live coverage matrix', results))
}

main().catch((err) => {
  console.error('s13_coverage_matrix_live FATAL:', err)
  process.exit(4)
})
