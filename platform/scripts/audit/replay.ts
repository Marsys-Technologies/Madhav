#!/usr/bin/env tsx
/**
 * audit:replay — inspect full audit event history from the dev Cloud SQL DB.
 *
 * Usage:
 *   npm run audit:replay -- --query-id=<uuid>
 *   npm run audit:replay -- --last=5
 *
 * Reads from the audit_log and (optionally) prediction_ledger tables.
 * Requires DATABASE_URL to be set (Cloud SQL Auth Proxy for local dev).
 */

// Load env from .env.local or .env.rag if present
import { readFileSync, existsSync } from 'fs'
import { join } from 'path'

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
import { isDirectEntrypoint } from '../lib/entrypoint'

// ── CLI arg parsing ───────────────────────────────────────────────────────────

const args = process.argv.slice(2)
const queryIdArg = args.find(a => a.startsWith('--query-id='))?.split('=')[1]
const lastArg = args.find(a => a.startsWith('--last='))?.split('=')[1]

if (!queryIdArg && !lastArg) {
  console.error('Usage: npm run audit:replay -- --query-id=<uuid> | --last=N')
  process.exit(1)
}

// ── DB connection ─────────────────────────────────────────────────────────────

if (!process.env.DATABASE_URL) {
  console.error('DATABASE_URL not set. Start Cloud SQL Auth Proxy and set DATABASE_URL.')
  process.exit(1)
}

const pool = new Pool({ connectionString: process.env.DATABASE_URL })

// ── Formatters ────────────────────────────────────────────────────────────────

function formatAuditRow(row: AuditLogRow): string {
  const lines: string[] = [
    `\n${'─'.repeat(72)}`,
    `AUDIT LOG ENTRY`,
    `${'─'.repeat(72)}`,
    `id               : ${row.id}`,
    `query_id         : ${row.query_id}`,
    `created_at       : ${row.created_at}`,
    `query_class      : ${row.query_class}`,
    `synthesis_model  : ${row.synthesis_model}`,
    `tokens in/out    : ${row.synthesis_input_tokens} / ${row.synthesis_output_tokens}`,
    `disclosure_tier  : ${row.disclosure_tier}`,
    `audit_ev_version : ${row.audit_event_version}`,
    ``,
    `QUERY TEXT:`,
    `  ${row.query_text}`,
    ``,
    `BUNDLE KEYS:`,
    `  ${(row.bundle_keys as unknown as string[]).join(', ')}`,
    ``,
    `TOOLS CALLED:`,
    ...(row.tools_called as unknown as Array<{ tool: string; cached: boolean; latency_ms: number }>)
      .map(t => `  ${t.tool}  cached=${t.cached}  latency=${t.latency_ms}ms`),
    ``,
    `VALIDATORS:`,
    ...(row.validators_run as unknown as Array<{ validator_id: string; passed: boolean; message: string }>)
      .map(v => `  ${v.validator_id}  passed=${v.passed}  msg=${v.message}`),
    ``,
    `FINAL OUTPUT (first 500 chars):`,
    `  ${String(row.final_output).slice(0, 500)}`,
  ]
  return lines.join('\n')
}

function formatPredictionRow(row: PredictionRow): string {
  return [
    ``,
    `  PREDICTION ${row.id}`,
    `  confidence    : ${row.confidence}`,
    `  horizon       : ${row.horizon_start} → ${row.horizon_end}`,
    `  subject       : ${row.subject}`,
    `  falsifier     : ${row.falsifier}`,
    `  outcome       : ${row.outcome ?? '(pending)'}`,
    `  text (first 200): ${row.prediction_text.slice(0, 200)}`,
  ].join('\n')
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  try {
    let auditRows: AuditLogRow[]

    if (queryIdArg) {
      const result = await pool.query<AuditLogRow>(
        `SELECT * FROM audit_log WHERE query_id = $1`,
        [queryIdArg]
      )
      auditRows = result.rows
      if (auditRows.length === 0) {
        console.log(`No audit row found for query_id=${queryIdArg}`)
        return
      }
    } else {
      const n = parseInt(lastArg!, 10)
      if (isNaN(n) || n < 1) {
        console.error('--last must be a positive integer')
        process.exit(1)
      }
      const result = await pool.query<AuditLogRow>(
        `SELECT * FROM audit_log ORDER BY created_at DESC LIMIT $1`,
        [n]
      )
      auditRows = result.rows
      if (auditRows.length === 0) {
        console.log('No audit rows found.')
        return
      }
    }

    for (const row of auditRows) {
      console.log(formatAuditRow(row))

      // Show any predictions linked to this query
      const preds = await pool.query<PredictionRow>(
        `SELECT * FROM prediction_ledger WHERE query_id = $1 ORDER BY created_at`,
        [row.query_id]
      )
      if (preds.rows.length > 0) {
        console.log(`\nLINKED PREDICTIONS (${preds.rows.length}):`)
        preds.rows.forEach(p => console.log(formatPredictionRow(p)))
      }
    }

    console.log(`\n${'─'.repeat(72)}`)
    console.log(`Displayed ${auditRows.length} audit row(s).`)
  } finally {
    await pool.end()
  }
}

if (isDirectEntrypoint(import.meta.url, process.argv[1])) {
  main().catch(err => {
    console.error('replay failed:', err)
    process.exit(1)
  })
}
