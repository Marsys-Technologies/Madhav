#!/usr/bin/env tsx
/**
 * AD.5 cutover smoke — adapter layer parity verification.
 *
 * Strategy: exercises the adapter dispatch logic via the project's existing
 * vitest equivalence suite (48 cases). This avoids the `server-only`
 * module boundary that blocks direct tsx import of @/lib/adapters.
 * The suite already mocks AI SDK internals deterministically, making it
 * the canonical flag-off ↔ flag-on parity oracle.
 *
 * Two modes:
 *   ADAPTERS_ENABLED=false npx tsx scripts/aiops/cutover_smoke_adapters.ts
 *   ADAPTERS_ENABLED=true  npx tsx scripts/aiops/cutover_smoke_adapters.ts
 *   ADAPTERS_SMOKE_PARITY=true npx tsx scripts/aiops/cutover_smoke_adapters.ts
 *
 * Output: 00_ARCHITECTURE/aiops/phase_2/cutover_evidence/smoke_{flag}.json
 */

import { execSync } from 'child_process'
import { writeFileSync, readFileSync, existsSync, mkdirSync } from 'fs'
import { join } from 'path'

const REPO_ROOT = join(
  typeof __dirname !== 'undefined' ? __dirname : new URL('.', import.meta.url).pathname,
  '../../..',
)
const EVIDENCE_DIR = join(REPO_ROOT, '00_ARCHITECTURE/aiops/phase_2/cutover_evidence')

function ensureDir(dir: string) {
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true })
}

interface SmokeReport {
  ran_at: string
  flag_state: string
  mode: 'equivalence_suite'
  suite_file: string
  total: number
  pass: number
  fail: number
  failed_tests: string[]
  exit_code: number
}

function runParityCheck() {
  const offPath = join(EVIDENCE_DIR, 'smoke_false.json')
  const onPath  = join(EVIDENCE_DIR, 'smoke_true.json')

  if (!existsSync(offPath) || !existsSync(onPath)) {
    console.error('[parity] Both flag runs required first.')
    process.exit(1)
  }

  const off: SmokeReport = JSON.parse(readFileSync(offPath, 'utf8'))
  const on:  SmokeReport = JSON.parse(readFileSync(onPath,  'utf8'))

  const offFailed = new Set(off.failed_tests)
  const onFailed  = new Set(on.failed_tests)

  // Parity: the same tests pass and fail in both flag states
  const onlyInOff = [...offFailed].filter(t => !onFailed.has(t))
  const onlyInOn  = [...onFailed].filter(t => !offFailed.has(t))
  const mismatched = onlyInOff.length + onlyInOn.length

  const report = {
    checked_at: new Date().toISOString(),
    mismatched,
    off_pass: off.pass,
    on_pass: on.pass,
    only_failing_flag_off: onlyInOff,
    only_failing_flag_on: onlyInOn,
  }
  ensureDir(EVIDENCE_DIR)
  writeFileSync(join(EVIDENCE_DIR, 'parity_report.json'), JSON.stringify(report, null, 2))

  if (mismatched > 0) {
    console.error(`[parity] FAIL — ${mismatched} tests have different outcomes between flag states`)
    console.error('  only_failing_off:', onlyInOff)
    console.error('  only_failing_on:',  onlyInOn)
    process.exit(1)
  }

  console.log(`[parity] PASS — flag-off (${off.pass}/${off.total}) and flag-on (${on.pass}/${on.total}) have identical pass/fail pattern`)
}

function runSmoke() {
  const flagState = process.env.ADAPTERS_ENABLED ?? 'false'
  const suiteFile = 'src/lib/adapters/__tests__/equivalence/runtime_equivalence.test.ts'
  console.log(`[aiops:cutover-smoke-adapters] ADAPTERS_ENABLED=${flagState}`)
  console.log(`[aiops:cutover-smoke-adapters] running equivalence suite: ${suiteFile}`)

  ensureDir(EVIDENCE_DIR)

  let exitCode = 0
  let stdout = ''
  try {
    stdout = execSync(
      `ADAPTERS_ENABLED=${flagState} npx vitest run --reporter=verbose ${suiteFile} 2>&1`,
      { cwd: join(REPO_ROOT, 'platform'), encoding: 'utf8' }
    )
  } catch (err: unknown) {
    exitCode = (err as { status?: number }).status ?? 1
    stdout = (err as { stdout?: string }).stdout ?? ''
  }

  // Parse vitest verbose output for pass/fail counts
  const passMatch = stdout.match(/Tests\s+(\d+) passed/)
  const failMatch = stdout.match(/(\d+) failed/)
  const totalMatch = stdout.match(/Tests\s+\d+.*?(\d+)\)/)
  const pass  = passMatch  ? parseInt(passMatch[1],  10) : 0
  const fail  = failMatch  ? parseInt(failMatch[1],  10) : 0
  const total = pass + fail

  // Extract failed test names
  const failedTests: string[] = []
  for (const m of stdout.matchAll(/✗ (.+)/g)) {
    failedTests.push(m[1].trim())
  }

  const report: SmokeReport = {
    ran_at: new Date().toISOString(),
    flag_state: flagState,
    mode: 'equivalence_suite',
    suite_file: suiteFile,
    total, pass, fail,
    failed_tests: failedTests,
    exit_code: exitCode,
  }

  const outPath = join(EVIDENCE_DIR, `smoke_${flagState}.json`)
  writeFileSync(outPath, JSON.stringify(report, null, 2))
  console.log(`\n[aiops:cutover-smoke-adapters] pass=${pass} fail=${fail} total=${total}`)
  console.log(`[aiops:cutover-smoke-adapters] Written → ${outPath}`)

  if (exitCode !== 0) {
    console.error(`[aiops:cutover-smoke-adapters] FAIL — equivalence suite non-zero exit (${exitCode})`)
    process.exit(exitCode)
  }
  console.log('[aiops:cutover-smoke-adapters] PASS — equivalence suite all green')
}

if (process.env.ADAPTERS_SMOKE_PARITY === 'true') {
  runParityCheck()
} else {
  runSmoke()
}
