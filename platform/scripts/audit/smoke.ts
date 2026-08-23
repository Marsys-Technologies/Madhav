#!/usr/bin/env tsx
/**
 * audit:smoke — writes 5 fake audit events + 2 fake predictions, reads them
 * back, and verifies the round-trip against live dev Cloud SQL.
 *
 * Run:  npm run audit:smoke
 * Requires DATABASE_URL to point to a running Cloud SQL Auth Proxy.
 */

import { readFileSync, existsSync } from 'fs'
import { join } from 'path'
import { isDirectEntrypoint } from '../lib/entrypoint'

function loadEnv(file: string): void {
  const p = join(process.cwd(), file)
  if (!existsSync(p)) return
  const lines = readFileSync(p, 'utf8').split('\n')
  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) continue
    const eqIdx = trimmed.indexOf('=')
    if (eqIdx < 0) continue
    const key = trimmed.slice(0, eqIdx).trim()
    const val = trimmed.slice(eqIdx + 1).trim().replace(/^["']|["']$/g, '')
    if (!process.env[key]) process.env[key] = val
  }
}

loadEnv('.env.local')
loadEnv('.env.rag')

import { Pool } from 'pg'
import type { AuditLogRow } from '../../src/lib/audit/types'
import type { PredictionRow } from '../../src/lib/prediction/types'

if (!process.env.DATABASE_URL) {
  console.error('DATABASE_URL not set. Start Cloud SQL Auth Proxy and set DATABASE_URL.')
  process.exit(1)
}

const pool = new Pool({ connectionString: process.env.DATABASE_URL })

function uuid(): string {
  return crypto.randomUUID()
}

// ── Fake data generators ──────────────────────────────────────────────────────

function fakeAuditEvent(queryId: string, i: number) {
  return {
    query_id: queryId,
    query_text: `Smoke test query #${i}`,
    query_class: 'interpretive',
    bundle_keys: JSON.stringify(['FORENSIC', 'MSR']),
    tools_called: JSON.stringify([{ tool: 'msr_sql', params_hash: 'sha256:smoke', latency_ms: 10, cached: false }]),
    validators_run: JSON.stringify([{ validator_id: 'p1_layer_separation', passed: true, message: 'ok' }]),
    synthesis_model: 'claude-haiku-4-5',
    synthesis_input_tokens: 100 * i,
    synthesis_output_tokens: 50 * i,
    disclosure_tier: 'super_admin',
    final_output: `Smoke test output for query ${i}`,
    audit_event_version: 1,
  }
}

function fakePrediction(queryId: string, i: number) {
  return {
    query_id: queryId,
    prediction_text: `Smoke test prediction #${i}: career event in 2026–2027`,
    confidence: 0.6 + i * 0.1,
    horizon_start: '2026-07-01',
    horizon_end: '2027-06-30',
    falsifier: `No career event observed by 2027-06-30`,
    subject: 'native:abhisek',
  }
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const smokeTag = `smoke-${Date.now()}`
  console.log(`\naudit:smoke  tag=${smokeTag}`)
  console.log('─'.repeat(60))

  const queryIds: string[] = Array.from({ length: 5 }, () => uuid())
  const predQueryIds = [queryIds[0], queryIds[1]]

  // ── Write 5 audit events ──
  console.log('Writing 5 audit events...')
  for (let i = 0; i < 5; i++) {
    const ev = fakeAuditEvent(queryIds[i], i + 1)
    await pool.query(
      `INSERT INTO audit_log
         (query_id, query_text, query_class, bundle_keys, tools_called,
          validators_run, synthesis_model, synthesis_input_tokens,
          synthesis_output_tokens, disclosure_tier, final_output, audit_event_version)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
       ON CONFLICT ON CONSTRAINT uq_audit_log_query_id DO UPDATE
         SET final_output = EXCLUDED.final_output`,
      [ev.query_id, ev.query_text, ev.query_class, ev.bundle_keys, ev.tools_called,
       ev.validators_run, ev.synthesis_model, ev.synthesis_input_tokens,
       ev.synthesis_output_tokens, ev.disclosure_tier, ev.final_output, ev.audit_event_version]
    )
    console.log(`  ✓ audit event ${i + 1}/5  query_id=${queryIds[i]}`)
  }

  // ── Write 2 predictions ──
  console.log('\nWriting 2 predictions...')
  const predIds: string[] = []
  for (let i = 0; i < 2; i++) {
    const p = fakePrediction(predQueryIds[i], i + 1)
    const result = await pool.query<{ id: string }>(
      `INSERT INTO prediction_ledger
         (query_id, prediction_text, confidence, horizon_start, horizon_end, falsifier, subject)
       VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING id`,
      [p.query_id, p.prediction_text, p.confidence, p.horizon_start, p.horizon_end, p.falsifier, p.subject]
    )
    predIds.push(result.rows[0].id)
    console.log(`  ✓ prediction ${i + 1}/2  id=${result.rows[0].id}`)
  }

  // ── Read back and verify ──
  console.log('\nReading back...')
  let auditOk = 0
  for (const qid of queryIds) {
    const r = await pool.query<AuditLogRow>(`SELECT * FROM audit_log WHERE query_id=$1`, [qid])
    if (r.rows.length === 1) auditOk++
  }

  let predOk = 0
  for (const pid of predIds) {
    const r = await pool.query<PredictionRow>(`SELECT * FROM prediction_ledger WHERE id=$1`, [pid])
    if (r.rows.length === 1 && r.rows[0].outcome === null) predOk++
  }

  console.log(`\nRESULT`)
  console.log('─'.repeat(60))
  console.log(`audit_log round-trip   : ${auditOk}/5 ${auditOk === 5 ? '✓' : '✗'}`)
  console.log(`prediction_ledger r/t  : ${predOk}/2 ${predOk === 2 ? '✓' : '✗'}`)

  const pass = auditOk === 5 && predOk === 2
  console.log(`\nSmoke: ${pass ? 'PASS ✓' : 'FAIL ✗'}`)

  if (!pass) process.exit(1)
}

if (isDirectEntrypoint(import.meta.url, process.argv[1])) {
  main()
    .catch(err => {
      console.error('smoke failed:', err)
      process.exit(1)
    })
    .finally(() => pool.end())
}
