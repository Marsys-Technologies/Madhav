/**
 * audit.ts — Nightly audit job for MCPT v3.2.
 *
 * Run as a Cloud Run job: `node dist/audit.js`
 * Distinct from the server entrypoint (dist/server.js).
 *
 * What it does:
 *   1. For each row in data_source_expected, counts actual rows in chart_facts
 *      (and other tables) and updates the actual_rows column.
 *   2. Emits a row to mcp_audit_findings for any category whose actual_rows
 *      falls below expected_rows (severity=warn) or is zero (severity=class_1).
 *   3. Refreshes all 4 perf-system materialized views from migration 082.
 *
 * Requires: DATABASE_URL environment variable (Cloud SQL or direct postgres URL).
 */

import pg from 'pg'

const { Pool } = pg

const DATABASE_URL = process.env['DATABASE_URL']
if (!DATABASE_URL) {
  console.error('[audit] ERROR: DATABASE_URL not set. Exiting.')
  process.exit(1)
}

const pool = new Pool({ connectionString: DATABASE_URL })

interface DataSourceExpectedRow {
  id: string
  tool_name: string
  category: string
  expected_rows: number
  actual_rows: number | null
}

// Category → table + WHERE predicate for counting actual rows.
// Covers chart_facts categories and the 3 non-chart_facts tools.
const CATEGORY_QUERY: Record<string, string> = {
  // chart_facts categories
  house:                   `SELECT COUNT(*) FROM chart_facts WHERE category = 'house'`,
  planet:                  `SELECT COUNT(*) FROM chart_facts WHERE category = 'planet'`,
  dasha_vimshottari:       `SELECT COUNT(*) FROM chart_facts WHERE category = 'dasha_vimshottari'`,
  dasha_chara:             `SELECT COUNT(*) FROM chart_facts WHERE category = 'dasha_chara'`,
  saham:                   `SELECT COUNT(*) FROM chart_facts WHERE category = 'saham'`,
  sensitive_point:         `SELECT COUNT(*) FROM chart_facts WHERE category = 'sensitive_point'`,
  birth_metadata:          `SELECT COUNT(*) FROM chart_facts WHERE category = 'birth_metadata'`,
  strength_extra:          `SELECT COUNT(*) FROM chart_facts WHERE category = 'strength_extra'`,
  yoga:                    `SELECT COUNT(*) FROM chart_facts WHERE category = 'yoga'`,
  shadbala:                `SELECT COUNT(*) FROM chart_facts WHERE category = 'shadbala'`,
  ashtakavarga_sav:        `SELECT COUNT(*) FROM chart_facts WHERE category = 'ashtakavarga_sav'`,
  ashtakavarga_bav:        `SELECT COUNT(*) FROM chart_facts WHERE category = 'ashtakavarga_bav'`,
  kp_cusp:                 `SELECT COUNT(*) FROM chart_facts WHERE category = 'kp_cusp'`,
  kp_planet:               `SELECT COUNT(*) FROM chart_facts WHERE category = 'kp_planet'`,
  kp_significator:         `SELECT COUNT(*) FROM chart_facts WHERE category = 'kp_significator'`,
  bhava_bala:              `SELECT COUNT(*) FROM chart_facts WHERE category = 'bhava_bala'`,
  upagraha:                `SELECT COUNT(*) FROM chart_facts WHERE category = 'upagraha'`,
  varshphal:               `SELECT COUNT(*) FROM chart_facts WHERE category = 'varshphal'`,
  tajaka_yoga:             `SELECT COUNT(*) FROM chart_facts WHERE category = 'tajaka_yoga'`,
  school_convergence:      `SELECT COUNT(*) FROM chart_facts WHERE category = 'school_convergence'`,
  aspect:                  `SELECT COUNT(*) FROM chart_facts WHERE category = 'aspect'`,
  arudha:                  `SELECT COUNT(*) FROM chart_facts WHERE category = 'arudha'`,
  deity_assignment:        `SELECT COUNT(*) FROM chart_facts WHERE category = 'deity_assignment'`,
  // non-chart_facts tools
  msr_signals:             `SELECT COUNT(*) FROM msr_signals`,
  lel_query:               `SELECT COUNT(*) FROM life_events`,
  query_panchanga:         `SELECT COUNT(*) FROM panchanga_daily`,
  query_signals:           `SELECT COUNT(*) FROM msr_signals`,
}

async function countActualRows(category: string, toolName: string): Promise<number | null> {
  // For non-chart_facts tools, use the tool_name as the key
  const key = toolName !== 'query_chart_facts' ? toolName : category
  const query = CATEGORY_QUERY[key]
  if (!query) {
    console.warn(`[audit] No count query for tool=${toolName} category=${category} — skipping`)
    return null
  }
  const result = await pool.query(query)
  return parseInt(result.rows[0].count as string, 10)
}

async function emitFinding(
  toolName: string,
  category: string,
  expected: number,
  actual: number,
  severity: 'warn' | 'class_1'
): Promise<void> {
  const description = severity === 'class_1'
    ? `Zero rows for ${toolName}/${category}: expected ${expected}, got ${actual}`
    : `Row count shortfall for ${toolName}/${category}: expected ${expected}, got ${actual}`

  await pool.query(
    `INSERT INTO mcp_audit_findings (trace_id, tool_name, check_class, severity, description, evidence)
     VALUES ($1, $2, $3, $4, $5, $6)`,
    [
      `audit-nightly-${new Date().toISOString()}`,
      toolName,
      'data_coverage',
      severity,
      description,
      JSON.stringify({ expected_rows: expected, actual_rows: actual, category }),
    ]
  )
}

async function refreshMaterializedViews(): Promise<void> {
  const views = [
    'mv_tool_metrics_24h',
    'mv_data_source_coverage',
    'mv_session_summary',
    'mv_tool_grounding_24h',
  ]
  for (const view of views) {
    console.log(`[audit] Refreshing ${view}...`)
    await pool.query(`REFRESH MATERIALIZED VIEW CONCURRENTLY ${view}`)
    console.log(`[audit] ${view} refreshed.`)
  }
}

async function run(): Promise<void> {
  console.log('[audit] Starting nightly audit run...')

  const { rows }: { rows: DataSourceExpectedRow[] } = await pool.query(
    `SELECT id, tool_name, category, expected_rows, actual_rows FROM data_source_expected ORDER BY tool_name, category`
  )

  console.log(`[audit] ${rows.length} data_source_expected rows to process.`)

  let updated = 0
  let findings = 0

  for (const row of rows) {
    const actual = await countActualRows(row.category, row.tool_name)
    if (actual === null) continue

    await pool.query(
      `UPDATE data_source_expected SET actual_rows = $1, updated_at = now() WHERE id = $2`,
      [actual, row.id]
    )
    updated++

    if (actual === 0) {
      await emitFinding(row.tool_name, row.category, row.expected_rows, actual, 'class_1')
      findings++
      console.warn(`[audit] class_1: ${row.tool_name}/${row.category} = 0 rows (expected ${row.expected_rows})`)
    } else if (actual < row.expected_rows) {
      await emitFinding(row.tool_name, row.category, row.expected_rows, actual, 'warn')
      findings++
      console.warn(`[audit] warn: ${row.tool_name}/${row.category} = ${actual} rows (expected ${row.expected_rows})`)
    } else {
      console.log(`[audit] ok: ${row.tool_name}/${row.category} = ${actual} rows`)
    }
  }

  console.log(`[audit] Updated ${updated} rows. Emitted ${findings} findings.`)

  await refreshMaterializedViews()

  console.log('[audit] Nightly audit complete.')
  await pool.end()
  process.exit(0)
}

run().catch((err) => {
  console.error('[audit] FATAL:', err)
  pool.end().finally(() => process.exit(1))
})
