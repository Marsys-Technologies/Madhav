/**
 * e2_db_truth_extractor.ts — the "actual" side of the W1 Lane L1b harvest pipeline
 * (W-25, RETRIEVAL_PLANE_ELEVATION_PLAN §9.6-2, extractor E2).
 *
 * Queries the LIVE database (via the read-only `retrieval_census_ro` role, W0.5) for
 * real schema truth: every table in `public`, its inferred layer prefix (chart_facts,
 * bg_/ga_/ganita_ [L0/L1], bodha_ [L2], kala_ [L3], phala_ [L4], mimamsa_ [L5], plus
 * an "other" bucket for tables that match none of those prefixes), and a real row
 * count.
 *
 * Row-count method (explicit per table, never silently estimated where an exact
 * count is cheap):
 *   - EXACT COUNT(*) for tables under EXACT_COUNT_THRESHOLD reltuples (cheap).
 *   - pg_class.reltuples ESTIMATE for tables at/above the threshold (chart_facts
 *     alone is 276K+ rows per W0.5 — an unindexed COUNT(*) sweep across all of
 *     public would be needlessly expensive on a shared read-only role).
 * Every row in the output records WHICH method produced its count
 * (`count_method: 'exact' | 'estimate'`) — never presented as one undifferentiated
 * number (§N.6 density-signaling discipline: the method is data, not narration).
 *
 * Output: platform/src/generated/harvest/e2_db_truth.json
 *
 * Run:
 *   cloud-sql-proxy --port 6544 madhav-astrology:asia-south1:amjis-postgres &
 *   export HARVEST_DB_PASSWORD=$(gcloud secrets versions access latest \
 *     --secret=retrieval-census-ro-db-password --project=madhav-astrology)
 *   npx tsx scripts/harvest/e2_db_truth_extractor.ts
 */
import { writeFileSync, mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { openHarvestClient } from './_db'

const __dirname = dirname(fileURLToPath(import.meta.url))
const OUTPUT_PATH = join(__dirname, '..', '..', 'src', 'generated', 'harvest', 'e2_db_truth.json')

/** Tables at/above this reltuples estimate use the cheap pg_class estimate, not COUNT(*). */
const EXACT_COUNT_THRESHOLD = 20_000

// Layer-prefix map, per the brief's explicit list plus the two additional L1
// prefixes (`ga_*`, `ganita_*`) that this repo's schema actually uses alongside
// `chart_*` (confirmed by direct information_schema enumeration below).
const LAYER_PREFIXES: Array<{ layer: string; prefixes: string[] }> = [
  { layer: 'L0', prefixes: ['bg_', 'brahma_'] },
  { layer: 'L1', prefixes: ['chart_', 'ga_', 'ganita_'] },
  { layer: 'L2', prefixes: ['bodha_'] },
  { layer: 'L3', prefixes: ['kala_'] },
  { layer: 'L4', prefixes: ['phala_'] },
  { layer: 'L5', prefixes: ['mimamsa_'] },
]

function layerFor(tableName: string): string {
  for (const { layer, prefixes } of LAYER_PREFIXES) {
    if (prefixes.some((p) => tableName.startsWith(p))) return layer
  }
  return 'OTHER'
}

interface TableRow {
  table_name: string
  layer: string
  row_count: number
  count_method: 'exact' | 'estimate'
  reltuples_raw: number
}

async function main(): Promise<void> {
  const client = await openHarvestClient()
  try {
    console.log('[E2] connected as read-only role; enumerating public schema tables...')

    const tablesRes = await client.query<{ table_name: string }>(
      `SELECT table_name FROM information_schema.tables
       WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
       ORDER BY table_name`,
    )
    const allTableNames = tablesRes.rows.map((r) => r.table_name)
    console.log(`[E2] ${allTableNames.length} base tables in public schema`)

    // reltuples estimate for every table in one shot (cheap: reads pg_class, not data).
    const reltuplesRes = await client.query<{ relname: string; reltuples: string }>(
      `SELECT c.relname, c.reltuples
       FROM pg_class c
       JOIN pg_namespace n ON n.oid = c.relnamespace
       WHERE n.nspname = 'public' AND c.relkind = 'r'`,
    )
    const reltuplesByName = new Map<string, number>()
    for (const r of reltuplesRes.rows) reltuplesByName.set(r.relname, Number(r.reltuples))

    const rows: TableRow[] = []
    let exactCount = 0
    let estimateCount = 0
    for (const table_name of allTableNames) {
      const estimate = reltuplesByName.get(table_name) ?? 0
      const layer = layerFor(table_name)
      if (estimate < EXACT_COUNT_THRESHOLD) {
        // Cheap: exact count on a small/empty table.
        const exact = await client.query<{ n: string }>(
          `SELECT count(*)::text AS n FROM "${table_name}"`,
        )
        rows.push({
          table_name,
          layer,
          row_count: Number(exact.rows[0]!.n),
          count_method: 'exact',
          reltuples_raw: estimate,
        })
        exactCount++
      } else {
        rows.push({
          table_name,
          layer,
          row_count: Math.round(estimate),
          count_method: 'estimate',
          reltuples_raw: estimate,
        })
        estimateCount++
      }
    }

    rows.sort((a, b) => a.table_name.localeCompare(b.table_name))

    const byLayer: Record<string, { table_count: number; row_total: number }> = {}
    for (const r of rows) {
      byLayer[r.layer] ??= { table_count: 0, row_total: 0 }
      byLayer[r.layer]!.table_count++
      byLayer[r.layer]!.row_total += r.row_count
    }

    const out = {
      extractor: 'E2 — DB truth',
      generated_at: new Date().toISOString(),
      db: {
        instance: 'madhav-astrology:asia-south1:amjis-postgres',
        database: 'amjis',
        role: 'retrieval_census_ro (SELECT-only)',
      },
      method: {
        exact_count_threshold_reltuples: EXACT_COUNT_THRESHOLD,
        exact_count_tables: exactCount,
        estimate_count_tables: estimateCount,
        estimate_source: 'pg_class.reltuples (last ANALYZE, not live-exact for those tables)',
      },
      summary: {
        total_tables: rows.length,
        by_layer: byLayer,
      },
      tables: rows,
    }

    mkdirSync(dirname(OUTPUT_PATH), { recursive: true })
    writeFileSync(OUTPUT_PATH, JSON.stringify(out, null, 2) + '\n')
    console.log(`[E2] wrote ${rows.length} tables (${exactCount} exact / ${estimateCount} estimate) -> ${OUTPUT_PATH}`)
    console.log('[E2] by_layer:', byLayer)
  } finally {
    await client.end()
  }
}

main().catch((err) => {
  console.error('[E2] failed:', err)
  process.exit(1)
})
