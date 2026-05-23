/**
 * regenerate_golden.ts — Regenerates the golden fixture from the live DB.
 *
 * Connects to the platform DB via DATABASE_URL and runs a COUNT(*) per category
 * for the native's chart (abhisek-mohanty), then writes the result to
 * fixtures/abhisek-mohanty-golden.json.
 *
 * Usage:
 *   DATABASE_URL="postgres://..." npm run accuracy:regenerate-golden
 *   npx tsx test/accuracy/regenerate_golden.ts
 *
 * Requirements:
 *   - DATABASE_URL environment variable must be set (Postgres connection string).
 *   - pg package must be available (add to devDependencies if absent).
 *
 * MCPT v3.2 Phase 8 — Accuracy Harness (P8b)
 */

import { writeFileSync, dirname } from 'fs'
import { join } from 'path'
import { fileURLToPath } from 'url'
import { execSync } from 'child_process'

const __dirname = dirname(fileURLToPath(import.meta.url))
const FIXTURE_PATH = join(__dirname, 'fixtures/abhisek-mohanty-golden.json')

const CHART_ID = 'abhisek-mohanty'
const MCPT_VERSION = 'v3.3'
const EXPECTED_TOTAL_ROWS = 2717
const EXPECTED_CATEGORIES = 27

// ── Guard: DATABASE_URL required ─────────────────────────────────────────────

const DATABASE_URL = process.env['DATABASE_URL']

if (!DATABASE_URL) {
  console.error('\n[regenerate-golden] ERROR: DATABASE_URL environment variable is not set.')
  console.error('')
  console.error('  To regenerate the golden fixture from the live database:')
  console.error('')
  console.error('    DATABASE_URL="postgres://user:pass@host:5432/dbname" npm run accuracy:regenerate-golden')
  console.error('')
  console.error('  Or export it first:')
  console.error('')
  console.error('    export DATABASE_URL="postgres://user:pass@host:5432/dbname"')
  console.error('    npm run accuracy:regenerate-golden')
  console.error('')
  console.error('  The DATABASE_URL should point to your Supabase or Postgres instance.')
  console.error('  For local dev, use the connection string from your .env.local file.')
  process.exit(1)
}

// ── Check pg is available ────────────────────────────────────────────────────

async function checkPgAvailable(): Promise<boolean> {
  try {
    await import('pg')
    return true
  } catch {
    return false
  }
}

// ── DB query ─────────────────────────────────────────────────────────────────

async function queryCategoryRowCounts(
  databaseUrl: string
): Promise<Record<string, number>> {
  const pgAvailable = await checkPgAvailable()

  if (!pgAvailable) {
    console.error('\n[regenerate-golden] ERROR: pg package is not installed.')
    console.error('')
    console.error('  Install it with:')
    console.error('    npm install --save-dev pg @types/pg')
    console.error('')
    process.exit(1)
  }

  // Dynamic import after availability check
  const { Client } = await import('pg') as typeof import('pg')
  const client = new Client({ connectionString: databaseUrl })

  try {
    await client.connect()
    console.log('[regenerate-golden] Connected to database.')

    // Query: count rows per category for this chart
    const result = await client.query<{ category: string; row_count: string }>(
      `SELECT category, COUNT(*) as row_count
       FROM chart_facts
       WHERE chart_id = $1
       GROUP BY category
       ORDER BY category`,
      [CHART_ID]
    )

    const counts: Record<string, number> = {}
    for (const row of result.rows) {
      counts[row.category] = parseInt(row.row_count, 10)
    }

    console.log(`[regenerate-golden] Found ${result.rows.length} categories, ${Object.values(counts).reduce((a, b) => a + b, 0)} total rows.`)

    return counts
  } finally {
    await client.end()
  }
}

function getGitSha(): string {
  try {
    return execSync('git rev-parse --short HEAD', { stdio: ['pipe', 'pipe', 'pipe'] })
      .toString()
      .trim()
  } catch {
    return 'unknown'
  }
}

// ── Main ─────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log(`[regenerate-golden] Regenerating golden fixture for chart: ${CHART_ID}`)
  console.log(`[regenerate-golden] Database: ${DATABASE_URL.replace(/:[^:@]+@/, ':***@')}`)

  const counts = await queryCategoryRowCounts(DATABASE_URL)

  const totalRows = Object.values(counts).reduce((a, b) => a + b, 0)
  const categoryCount = Object.keys(counts).length

  console.log(`[regenerate-golden] Total rows: ${totalRows} (expected ~${EXPECTED_TOTAL_ROWS})`)
  console.log(`[regenerate-golden] Categories: ${categoryCount} (expected ${EXPECTED_CATEGORIES})`)

  // Build the fixture
  const fixture: Record<string, unknown> = {
    _meta: {
      chart_id: CHART_ID,
      generated_at: new Date().toISOString().split('T')[0],
      mcpt_version: MCPT_VERSION,
      total_rows: totalRows,
      categories: categoryCount,
      git_sha: getGitSha(),
      note: `Auto-generated from live DB on ${new Date().toISOString()}`,
    },
  }

  // Use actual DB counts as expected_min_rows, leaving a 5% buffer
  // (actual_rows is also stored for diff comparison)
  for (const [cat, count] of Object.entries(counts)) {
    const buffer = Math.max(1, Math.floor(count * 0.95))
    fixture[cat] = {
      expected_min_rows: buffer,
      actual_rows: count,
    }
  }

  writeFileSync(FIXTURE_PATH, JSON.stringify(fixture, null, 2))
  console.log(`\n[regenerate-golden] Golden fixture written to: ${FIXTURE_PATH}`)

  if (totalRows < EXPECTED_TOTAL_ROWS * 0.9) {
    console.warn(`\n[regenerate-golden] WARNING: Total row count ${totalRows} is >10% below expected ${EXPECTED_TOTAL_ROWS}.`)
    console.warn('[regenerate-golden] This may indicate a migration or data population issue.')
  }
}

main().catch(err => {
  console.error('[regenerate-golden] Fatal error:', err)
  process.exit(1)
})
