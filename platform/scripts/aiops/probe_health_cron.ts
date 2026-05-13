#!/usr/bin/env tsx
/**
 * Cron script: probe all known model IDs and upsert health rows.
 * Run via: npm run aiops:health
 * Intended to be invoked by a cron or CI job on a regular cadence (e.g. every 6h).
 */

// Must be set before any imports that check NODE_ENV or next internals
process.env.NEXT_RUNTIME = 'nodejs'

import { probeAllModels } from '../../src/lib/aiops/health/bulk'

async function main() {
  console.log('[aiops:health] Starting bulk model health probe…')
  const start = Date.now()

  const report = await probeAllModels()
  const elapsed = Date.now() - start

  console.log(`[aiops:health] Done in ${elapsed}ms`)
  console.log(`  total=${report.total}  pass=${report.pass}  fail=${report.fail}  timeout=${report.timeout}`)

  if (report.fail > 0 || report.timeout > 0) {
    const bad = report.results.filter(r => r.status !== 'pass')
    for (const r of bad) {
      console.warn(`  [${r.status.toUpperCase()}] ${r.model_id} — ${r.error ?? ''}`)
    }
  }

  // Exit non-zero if majority failing so CI/cron can alert
  const failRate = (report.fail + report.timeout) / Math.max(report.total, 1)
  process.exit(failRate > 0.5 ? 1 : 0)
}

main().catch(err => {
  console.error('[aiops:health] Fatal:', err)
  process.exit(1)
})
