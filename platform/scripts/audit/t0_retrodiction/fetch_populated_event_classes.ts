#!/usr/bin/env -S npx tsx
/**
 * fetch_populated_event_classes.ts — D-4b Lane F-1 (resonance-map coverage).
 *
 * Small, real, committed CLI script: live-queries `gochara_resonance_map`
 * for the set of `event_class` values actually populated for a chart (via
 * `event_class_resolution.ts`'s `fetchPopulatedEventClasses`, this same
 * lane) and writes the result as JSON — either to stdout or to a file path
 * given as the second CLI arg.
 *
 * Exists as its own script (rather than being called inline from an ad-hoc
 * driver like `bakeoff_results/b1_driver_v1_0.ts`) because that driver lives
 * outside `platform/` and cannot resolve a bare `import 'pg'` (Node walks up
 * from the IMPORTING FILE's own directory looking for `node_modules`, and
 * `platform/node_modules` is never an ancestor of a
 * `00_ARCHITECTURE/llm_consumption_audit/...` path) — the same reason that
 * driver already reads its other substrate (dasha periods) from pre-fetched
 * SCRATCH JSON files rather than querying the DB directly. This script is
 * the thing that produces one of those files.
 *
 * Read-only: SELECT DISTINCT event_class only, no write to any table.
 *
 * Run with (from platform/): node_modules/.bin/tsx --env-file=.env.local
 *   scripts/audit/t0_retrodiction/fetch_populated_event_classes.ts <chart_id> [out_file]
 * (same DATABASE_URL / tsx-CLI-not-node---import discipline as
 * run_a5_dry_run.ts's own header — see that file's comment for why.)
 */
import { writeFileSync } from 'node:fs'
import { Pool } from 'pg'
import { fetchPopulatedEventClasses } from './lib/a3_scoring_harness/event_class_resolution'

async function main() {
  const chartId = process.argv[2]
  const outFile = process.argv[3]
  if (!chartId) {
    console.error('usage: fetch_populated_event_classes.ts <chart_id> [out_file]')
    process.exit(1)
  }

  const pool = new Pool({ connectionString: process.env.DATABASE_URL })
  try {
    const classes = await fetchPopulatedEventClasses(pool, chartId)
    const json = JSON.stringify(classes, null, 2)
    if (outFile) {
      writeFileSync(outFile, json)
      console.error(`[fetch_populated_event_classes] chart_id=${chartId}: wrote ${classes.length} populated event_class value(s) to ${outFile}: ${classes.join(', ')}`)
    } else {
      console.log(json)
    }
  } finally {
    await pool.end()
  }
}

main().catch((err) => {
  console.error('[fetch_populated_event_classes] FATAL:', err)
  process.exit(1)
})
