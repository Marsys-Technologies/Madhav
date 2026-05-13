#!/usr/bin/env tsx
/**
 * CP.5 cutover smoke script.
 * Runs a probe against every (stack, callType, role) combination.
 * Run twice — once with AIOPS_OVERRIDES_ENABLED=false, once with =true.
 *
 * Usage:
 *   AIOPS_OVERRIDES_ENABLED=false npm run aiops:cutover-smoke
 *   AIOPS_OVERRIDES_ENABLED=true  npm run aiops:cutover-smoke
 *
 * Output: platform/scripts/aiops/cutover_smoke_report.json (appended)
 */

process.env.NEXT_RUNTIME = 'nodejs'

import { writeFileSync, readFileSync, existsSync } from 'fs'
import { join } from 'path'

const REPORT_PATH = join(import.meta.dirname, 'cutover_smoke_report.json')

const STACKS = ['nim', 'gemini', 'deepseek', 'gpt', 'anthropic', 'marsys'] as const
// Core pipeline + key eval types; skip checkpoint types (require pipeline context)
const CALL_TYPES = [
  'synthesis', 'planner_deep', 'planner_fast',
  'context_assembly', 'worker',
  'eval_judge', 'smoke_synth',
] as const
const ROLES = ['primary', 'fallback'] as const

interface SmokeRow {
  stack:        string
  call_type:    string
  role:         string
  model_id:     string | null
  status:       string
  latency_ms:   number | null
  error:        string | null
  flag_state:   string
}

async function main() {
  const flagState = process.env.AIOPS_OVERRIDES_ENABLED ?? 'false'
  console.log(`[aiops:cutover-smoke] flag_state=${flagState}`)

  const { runProbe } = await import('../../src/lib/aiops/probe/runner')

  const rows: SmokeRow[] = []
  let pass = 0, fail = 0, skip = 0

  for (const stack of STACKS) {
    for (const callType of CALL_TYPES) {
      for (const role of ROLES) {
        let result: SmokeRow
        try {
          const probe = await runProbe({ stack, callType, role })
          const ok = probe.status === 'pass'
          if (ok) pass++; else fail++
          result = {
            stack, call_type: callType, role,
            model_id:   probe.model_id ?? null,
            status:     probe.status,
            latency_ms: probe.latency_ms ?? null,
            error:      probe.error ?? null,
            flag_state: flagState,
          }
          console.log(`  [${ok ? 'OK  ' : 'FAIL'}] ${stack}/${callType}/${role} — ${probe.model_id ?? '?'} (${probe.latency_ms ?? '?'}ms)`)
        } catch (err) {
          // Anthropic auth_fail expected if no key configured
          const isAnthropicSkip = stack === 'anthropic' && String(err).includes('auth')
          if (isAnthropicSkip) skip++; else fail++
          result = {
            stack, call_type: callType, role,
            model_id:   null,
            status:     isAnthropicSkip ? 'skipped_auth' : 'error',
            latency_ms: null,
            error:      err instanceof Error ? err.message : String(err),
            flag_state: flagState,
          }
          console.log(`  [${isAnthropicSkip ? 'SKIP' : 'ERR '}] ${stack}/${callType}/${role} — ${result.error}`)
        }
        rows.push(result)
      }
    }
  }

  const total = pass + fail + skip
  console.log(`\n[aiops:cutover-smoke] total=${total} pass=${pass} fail=${fail} skip=${skip}`)

  // Read existing report or start fresh
  let existing: { runs: object[] } = { runs: [] }
  if (existsSync(REPORT_PATH)) {
    try {
      existing = JSON.parse(readFileSync(REPORT_PATH, 'utf8')) as { runs: object[] }
    } catch { /* corrupt — reset */ }
  }

  existing.runs.push({
    ran_at:    new Date().toISOString(),
    flag_state: flagState,
    total, pass, fail, skip,
    rows,
  })

  writeFileSync(REPORT_PATH, JSON.stringify(existing, null, 2))
  console.log(`[aiops:cutover-smoke] Report written to ${REPORT_PATH}`)

  // Exit non-zero only if non-Anthropic stacks have failures
  const nonAnthropicFails = rows.filter(r => r.stack !== 'anthropic' && r.status !== 'pass' && r.status !== 'skipped_auth')
  process.exit(nonAnthropicFails.length > 0 ? 1 : 0)
}

main().catch(err => {
  console.error('[aiops:cutover-smoke] Fatal:', err)
  process.exit(1)
})
