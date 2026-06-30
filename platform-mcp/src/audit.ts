/**
 * audit.ts — Nightly audit job for Brahma architecture.
 *
 * Run as a Cloud Run job: `node dist/audit.js`
 * Distinct from the server entrypoint (dist/server.js).
 *
 * WS-0 (2026-06-04): Rebased from legacy chart_facts/msr_signals/data_source_expected
 * to Brahma 6-layer tables (ganita_*, bodha_*, kala_*, phala_*, mimamsa_*).
 * data_source_expected and mcp_audit_findings tables dropped — findings now log to stdout.
 *
 * R2.1 (2026-06-30): Repointed from direct pg.Pool to callPlatformPrimitive so that
 * all DB access routes through the registry surface.
 *
 * Requires: PLATFORM_URL + SERVICE_TOKEN (or GCP ADC) environment variables.
 */

import { callPlatformPrimitive } from './client.js'
import type { Principal, McpEnvelopeError } from './types.js'

// Audit job runs as the internal service principal — no user-facing key.
const AUDIT_PRINCIPAL: Principal = {
  user_uid: 'audit-job',
  key_id:   'audit-internal',
  role:     'super_admin',
}

// Brahma layer row-count checks — delegated to the platform primitive.
const BRAHMA_CHECKS: { label: string; minExpected: number }[] = [
  { label: 'ganita_positions',    minExpected: 1 },
  { label: 'ganita_dashas',       minExpected: 1 },
  { label: 'bodha_signals',       minExpected: 0 },
  { label: 'kala_timeline',       minExpected: 0 },
  { label: 'phala_anchors',       minExpected: 0 },
  { label: 'mimamsa_predictions', minExpected: 0 },
]

async function run(): Promise<void> {
  console.log('[audit] Starting nightly Brahma audit run...')

  let findings = 0
  for (const check of BRAHMA_CHECKS) {
    const { status, envelope } = await callPlatformPrimitive(
      'audit_row_count',
      { table: check.label },
      AUDIT_PRINCIPAL,
    )
    if (status !== 200 || !envelope.ok) {
      console.warn(`[audit] class_1: ${check.label} — primitive error: ${(envelope as McpEnvelopeError).error?.message ?? status}`)
      findings++
      continue
    }
    const result = envelope.result as { count: number } | undefined
    const actual = result?.count ?? 0
    if (actual === 0 && check.minExpected > 0) {
      console.warn(`[audit] class_1: ${check.label} = 0 rows (expected >= ${check.minExpected})`)
      findings++
    } else {
      console.log(`[audit] ok: ${check.label} = ${actual} rows`)
    }
  }

  console.log(`[audit] Emitted ${findings} findings (stdout only — mcp_audit_findings removed in WS-0).`)
  console.log('[audit] Nightly audit complete.')
  process.exit(0)
}

run().catch((err) => {
  console.error('[audit] FATAL:', err)
  process.exit(1)
})
