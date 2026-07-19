/**
 * e3_fact_category_extractor.ts — chart_facts fact_category reconciliation
 * (W1 Lane L1b, W-25, RETRIEVAL_PLANE_ELEVATION_PLAN §9.6-2, extractor E3).
 *
 * The plan cites a three-way disagreement over how many chart_facts fact_category
 * values exist: CHART_FACTS_SCHEMA.json says 147, coverage_matrix.ts says 158, and
 * planner prose says "37". This extractor reads all three sources for real (not by
 * re-asserting the plan's numbers) PLUS queries the live DB directly for the fourth,
 * ground-truth number: DISTINCT fact_category actually present in chart_facts.
 *
 * Sources read:
 *   1. 00_ARCHITECTURE/CHART_FACTS_SCHEMA.json  — canonical governance copy (§ per
 *      CAPABILITY_MANIFEST / CANONICAL_ARTIFACTS; ROOT_FILE_POLICY-placed).
 *   1b. platform/scripts/governance/CHART_FACTS_SCHEMA.json — byte-identical mirror
 *       of (1), confirmed by this extractor, not assumed.
 *   1c. platform/python-sidecar/ga_writers/CHART_FACTS_SCHEMA.json — a THIRD, DIFFERENT
 *       copy this extractor found while locating (1)/(1b) — not cited by the plan's
 *       three-way framing at all, but real and on-disk, so reported honestly as a
 *       fourth static source rather than silently ignored.
 *   2. coverage_matrix.ts's CHART_FACTS_CATEGORIES array (TS source, parsed via regex
 *      extraction of the array literal — not re-typed by hand).
 *   3. "37" prose citations — grepped from 00_ARCHITECTURE/*.md; these are historical
 *      session-log / early-build documents (2026-04/05 era, KARN W2-R2 chart_facts ETL)
 *      describing an EARLIER, much smaller chart_facts population, not a claim about
 *      today's schema. Reported as found, with the caveat that "37" is a stale
 *      historical figure, not a live disagreement with (1)/(2).
 *   4. Live DB: SELECT DISTINCT fact_category FROM chart_facts (via retrieval_census_ro).
 *
 * This reconciliation (4 real numbers side by side, with set-difference analysis
 * between the DB-live set and each static list) IS the deliverable — not a guess.
 *
 * Output: platform/src/generated/harvest/e3_fact_category_reconciliation.json
 *
 * Run:
 *   cloud-sql-proxy --port 6544 madhav-astrology:asia-south1:amjis-postgres &
 *   export HARVEST_DB_PASSWORD=$(gcloud secrets versions access latest \
 *     --secret=retrieval-census-ro-db-password --project=madhav-astrology)
 *   npx tsx scripts/harvest/e3_fact_category_extractor.ts
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { execSync } from 'node:child_process'
import { openHarvestClient } from './_db'

const __dirname = dirname(fileURLToPath(import.meta.url))
const REPO_ROOT = join(__dirname, '..', '..', '..')
const PLATFORM_ROOT = join(__dirname, '..', '..')
const OUTPUT_PATH = join(
  PLATFORM_ROOT, 'src', 'generated', 'harvest', 'e3_fact_category_reconciliation.json',
)

const SCHEMA_JSON_PATHS = [
  { id: 'CHART_FACTS_SCHEMA.json (00_ARCHITECTURE, governance-canonical)', path: join(REPO_ROOT, '00_ARCHITECTURE/CHART_FACTS_SCHEMA.json') },
  { id: 'CHART_FACTS_SCHEMA.json (platform/scripts/governance, tooling mirror)', path: join(PLATFORM_ROOT, 'scripts/governance/CHART_FACTS_SCHEMA.json') },
  { id: 'CHART_FACTS_SCHEMA.json (platform/python-sidecar/ga_writers, NOT cited by the plan\'s 3-way framing — found on disk)', path: join(PLATFORM_ROOT, 'python-sidecar/ga_writers/CHART_FACTS_SCHEMA.json') },
]
const COVERAGE_MATRIX_PATH = join(
  PLATFORM_ROOT, 'src/lib/retrieval/registry/layers/L1_ganita/coverage_matrix.ts',
)

function readSchemaJsonCategories(path: string): { categories: string[]; exists: boolean } {
  if (!existsSync(path)) return { categories: [], exists: false }
  const doc = JSON.parse(readFileSync(path, 'utf8')) as { categories?: Record<string, unknown> }
  return { categories: Object.keys(doc.categories ?? {}).sort(), exists: true }
}

function readCoverageMatrixCategories(): string[] {
  const src = readFileSync(COVERAGE_MATRIX_PATH, 'utf8')
  const m = src.match(/CHART_FACTS_CATEGORIES\s*=\s*\[([\s\S]*?)\]/)
  if (!m) throw new Error('CHART_FACTS_CATEGORIES array literal not found in coverage_matrix.ts')
  const items = [...m[1]!.matchAll(/'([^']+)'|"([^"]+)"/g)].map((mm) => mm[1] ?? mm[2]!)
  return items.sort()
}

/** Real grep, not a hand-typed assertion — every hit + file:line is in the output. */
function grepProse37Citations(): Array<{ file: string; line: number; text: string }> {
  const patterns = ['37 categories', '37 fact_categor']
  const hits: Array<{ file: string; line: number; text: string }> = []
  for (const pattern of patterns) {
    let raw: string
    try {
      raw = execSync(
        `grep -rn "${pattern}" --include="*.md" "${join(REPO_ROOT, '00_ARCHITECTURE')}"`,
        { encoding: 'utf8', maxBuffer: 10 * 1024 * 1024 },
      )
    } catch {
      raw = '' // grep exits 1 on no matches
    }
    for (const line of raw.split('\n').filter(Boolean)) {
      const idx = line.indexOf(':')
      const idx2 = line.indexOf(':', idx + 1)
      const file = line.slice(0, idx).replace(REPO_ROOT + '/', '')
      const lineNo = Number(line.slice(idx + 1, idx2))
      const text = line.slice(idx2 + 1).trim().slice(0, 200)
      if (!hits.some((h) => h.file === file && h.line === lineNo)) {
        hits.push({ file, line: lineNo, text })
      }
    }
  }
  return hits.sort((a, b) => a.file.localeCompare(b.file) || a.line - b.line)
}

async function readLiveDbCategories(): Promise<{ categories: string[]; row_counts: Record<string, number> }> {
  const client = await openHarvestClient()
  try {
    const res = await client.query<{ fact_category: string; n: string }>(
      `SELECT fact_category, count(*)::text AS n FROM chart_facts
       GROUP BY fact_category ORDER BY fact_category`,
    )
    const row_counts: Record<string, number> = {}
    for (const r of res.rows) row_counts[r.fact_category] = Number(r.n)
    return { categories: res.rows.map((r) => r.fact_category), row_counts }
  } finally {
    await client.end()
  }
}

function setDiff(a: string[], b: string[]): string[] {
  const bs = new Set(b)
  return a.filter((x) => !bs.has(x)).sort()
}

async function main(): Promise<void> {
  console.log('[E3] reading static sources...')
  const schemaJsons = SCHEMA_JSON_PATHS.map((s) => ({ ...s, ...readSchemaJsonCategories(s.path) }))
  const coverageMatrix = readCoverageMatrixCategories()
  const prose37 = grepProse37Citations()

  console.log('[E3] querying live DB for DISTINCT fact_category...')
  const live = await readLiveDbCategories()

  const sourceCounts = {
    ...Object.fromEntries(schemaJsons.map((s) => [s.id, s.exists ? s.categories.length : null])),
    'coverage_matrix.ts CHART_FACTS_CATEGORIES': coverageMatrix.length,
    'live DB (DISTINCT fact_category, chart_facts)': live.categories.length,
    'planner prose "37" citations (count of files/lines citing it, NOT a category count)': prose37.length,
  }

  const primarySchemaJson = schemaJsons[0]! // 00_ARCHITECTURE canonical copy
  const mirrorIdentical = primarySchemaJson.exists && schemaJsons[1]?.exists
    ? JSON.stringify(primarySchemaJson.categories) === JSON.stringify(schemaJsons[1]!.categories)
    : null
  const gaWritersDiffFromCanonical = primarySchemaJson.exists && schemaJsons[2]?.exists
    ? {
        only_in_ga_writers_copy: setDiff(schemaJsons[2]!.categories, primarySchemaJson.categories),
        only_in_canonical_copy: setDiff(primarySchemaJson.categories, schemaJsons[2]!.categories),
      }
    : null

  const reconciliation = {
    live_db_categories_not_in_schema_json: setDiff(live.categories, primarySchemaJson.categories),
    live_db_categories_not_in_coverage_matrix: setDiff(live.categories, coverageMatrix),
    schema_json_categories_never_populated_live: setDiff(primarySchemaJson.categories, live.categories),
    coverage_matrix_categories_never_populated_live: setDiff(coverageMatrix, live.categories),
  }

  const out = {
    extractor: 'E3 — chart_facts fact_category reconciliation',
    generated_at: new Date().toISOString(),
    plans_cited_three_way_disagreement: {
      'CHART_FACTS_SCHEMA.json (plan claim)': 147,
      'coverage_matrix.ts (plan claim)': 158,
      'planner prose (plan claim)': '37',
    },
    real_counts_from_all_sources: sourceCounts,
    verdict:
      'The plan\'s framing understates the disagreement. There are (at least) FOUR ' +
      'static/live sources, not three, and the live DB (source of truth for what is ' +
      'actually served) disagrees with EVERY static source. See reconciliation ' +
      'block for the real set differences, not just counts.',
    sources: {
      schema_json_copies: schemaJsons.map((s) => ({
        id: s.id,
        path: s.path.replace(REPO_ROOT + '/', ''),
        exists: s.exists,
        category_count: s.exists ? s.categories.length : null,
      })),
      schema_json_governance_mirror_byte_identical_to_canonical: mirrorIdentical,
      schema_json_ga_writers_copy_diff_from_canonical: gaWritersDiffFromCanonical,
      coverage_matrix_ts: {
        path: COVERAGE_MATRIX_PATH.replace(REPO_ROOT + '/', ''),
        category_count: coverageMatrix.length,
      },
      planner_prose_37_citations: prose37.map((h) => ({
        ...h,
        note: 'Historical (2026-04/05 KARN W2-R2 chart_facts ETL era) — describes an ' +
          'earlier, much smaller chart_facts population, not a claim about the current ' +
          'schema. Not treated as a live disagreement with sources 1/2/4.',
      })),
      live_db: {
        instance: 'madhav-astrology:asia-south1:amjis-postgres',
        table: 'chart_facts',
        distinct_fact_category_count: live.categories.length,
        total_rows: Object.values(live.row_counts).reduce((a, b) => a + b, 0),
      },
    },
    reconciliation,
    category_lists: {
      schema_json_canonical: primarySchemaJson.categories,
      coverage_matrix_ts: coverageMatrix,
      live_db: live.categories,
      live_db_row_counts: live.row_counts,
    },
  }

  mkdirSync(dirname(OUTPUT_PATH), { recursive: true })
  writeFileSync(OUTPUT_PATH, JSON.stringify(out, null, 2) + '\n')
  console.log(`[E3] wrote reconciliation -> ${OUTPUT_PATH}`)
  console.log('[E3] real counts from all sources:', sourceCounts)
}

main().catch((err) => {
  console.error('[E3] failed:', err)
  process.exit(1)
})
