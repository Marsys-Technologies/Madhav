/**
 * audit.ts — Nightly audit job for Brahma architecture.
 *
 * Run as a Cloud Run job: `node dist/audit.js`
 * Distinct from the server entrypoint (dist/server.js).
 *
 * WS-0 (2026-06-04): Rebased from legacy chart_facts/msr_signals/data_source_expected
 * to Brahma 6-layer tables (ganita_N, bodha_N, kala_N, phala_N, mimamsa_N).
 * data_source_expected and mcp_audit_findings tables dropped — findings now log to stdout.
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

// Brahma layer row-count checks.
const BRAHMA_CHECKS: { label: string; query: string; minExpected: number }[] = [
  { label: 'ganita_positions',    query: `SELECT COUNT(*) FROM ganita_positions`,    minExpected: 1 },
  { label: 'ganita_dashas',       query: `SELECT COUNT(*) FROM ganita_dashas`,       minExpected: 1 },
  { label: 'bodha_signals',       query: `SELECT COUNT(*) FROM bodha_signals`,       minExpected: 0 },
  { label: 'kala_timeline',       query: `SELECT COUNT(*) FROM kala_timeline`,       minExpected: 0 },
  { label: 'phala_anchors',       query: `SELECT COUNT(*) FROM phala_anchors`,       minExpected: 0 },
  { label: 'mimamsa_predictions', query: `SELECT COUNT(*) FROM mimamsa_predictions`, minExpected: 0 },
]

async function run(): Promise<void> {
  console.log('[audit] Starting nightly Brahma audit run...')

  let findings = 0
  for (const check of BRAHMA_CHECKS) {
    const result = await pool.query(check.query)
    const actual = parseInt(result.rows[0].count as string, 10)
    if (actual === 0 && check.minExpected > 0) {
      console.warn(`[audit] class_1: ${check.label} = 0 rows (expected >= ${check.minExpected})`)
      findings++
    } else {
      console.log(`[audit] ok: ${check.label} = ${actual} rows`)
    }
  }

  console.log(`[audit] Emitted ${findings} findings (stdout only — mcp_audit_findings removed in WS-0).`)
  console.log('[audit] Nightly audit complete.')
  await pool.end()
  process.exit(0)
}

run().catch((err) => {
  console.error('[audit] FATAL:', err)
  pool.end().finally(() => process.exit(1))
})
