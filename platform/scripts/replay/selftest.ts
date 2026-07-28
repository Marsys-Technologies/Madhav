#!/usr/bin/env tsx
/**
 * Paripraśna acceptance harness — automated red-then-green self-test.
 *
 * The brief's hard requirement: "every battery item must be demonstrated to
 * FAIL first (red) against a deliberately seeded violation... and only then
 * shown to pass green — a gate that cannot fail is decoration."
 *
 * Each gate spec already contains an in-suite "RED PROOF" test that asserts
 * the harness's detector fires on its own seeded violation — that test
 * passes on every normal run (it's a permanent regression guard: if someone
 * weakens a detector until it stops catching its bug, THAT test goes red in
 * CI). This script performs the more literal demonstration: it forces the
 * gate's own MAIN assertion (not the always-passing proof test) to run
 * against the seeded violation via `PARIPRASHNA_VIOLATE=<key>` (which every
 * gate spec's main test honors via `mainRunViolate(key)` — see
 * tests/pariprashna/gates/_helpers.ts) and confirms the whole spec file's
 * run FAILS, then re-runs it clean and confirms it PASSES.
 *
 * Run: `npm run pariprashna:selftest`. Exits non-zero if any gate is
 * "decoration" (its red run didn't actually fail) or "broken" (its green
 * run doesn't pass).
 */
import { spawnSync } from 'child_process'

interface GateCase {
  gate: string
  file: string
  violateKey: string
}

const CASES: GateCase[] = [
  { gate: 'G-CLS', file: 'tests/pariprashna/gates/g-cls.spec.ts', violateKey: 'cls' },
  { gate: 'G-CARET', file: 'tests/pariprashna/gates/g-caret.spec.ts', violateKey: 'caret' },
  { gate: 'G-TRANSMUTE', file: 'tests/pariprashna/gates/g-transmute.spec.ts', violateKey: 'transmute' },
  { gate: 'G-RAF', file: 'tests/pariprashna/gates/g-raf.spec.ts', violateKey: 'raf' },
  { gate: 'G-VIEWPORT', file: 'tests/pariprashna/gates/g-viewport.spec.ts', violateKey: 'viewport' },
  { gate: 'G-PILL', file: 'tests/pariprashna/gates/g-pill.spec.ts', violateKey: 'pill' },
  { gate: 'G-AXE', file: 'tests/pariprashna/gates/g-axe.spec.ts', violateKey: 'axe' },
  { gate: 'G-MOBILE', file: 'tests/pariprashna/gates/g-mobile.spec.ts', violateKey: 'mobile-tap' },
]

function runPlaywright(file: string, violate: string | null): { exitCode: number; grepLine: string } {
  const args = [
    'playwright', 'test', file,
    '--config=tests/pariprashna/playwright.config.ts',
    '--project=chromium',
    '--reporter=list',
  ]
  const env = { ...process.env }
  if (violate) env.PARIPRASHNA_VIOLATE = violate
  else delete env.PARIPRASHNA_VIOLATE

  const result = spawnSync('npx', args, { env, encoding: 'utf8' })
  const output = `${result.stdout}\n${result.stderr}`
  const summaryLine = output.split('\n').find((l) => /passed|failed/.test(l)) ?? '(no summary line found)'
  return { exitCode: result.status ?? 1, grepLine: summaryLine.trim() }
}

interface Row {
  gate: string
  redExitCode: number
  redSummary: string
  redOk: boolean
  greenExitCode: number
  greenSummary: string
  greenOk: boolean
}

function main(): void {
  const rows: Row[] = []

  for (const c of CASES) {
    console.log(`\n=== ${c.gate} (${c.file}) ===`)

    console.log(`-- RED run: PARIPRASHNA_VIOLATE=${c.violateKey} --`)
    const red = runPlaywright(c.file, c.violateKey)
    console.log(`   exit=${red.exitCode}  ${red.grepLine}`)

    console.log('-- GREEN run: clean (no violation) --')
    const green = runPlaywright(c.file, null)
    console.log(`   exit=${green.exitCode}  ${green.grepLine}`)

    rows.push({
      gate: c.gate,
      redExitCode: red.exitCode,
      redSummary: red.grepLine,
      redOk: red.exitCode !== 0, // RED means the spec run must FAIL
      greenExitCode: green.exitCode,
      greenSummary: green.grepLine,
      greenOk: green.exitCode === 0, // GREEN means the spec run must PASS
    })
  }

  console.log('\n\n=== Paripraśna gate battery — red-then-green self-test summary ===\n')
  console.log(
    ['Gate', 'RED (violated) exit', 'RED as expected?', 'GREEN (clean) exit', 'GREEN as expected?'].join(' | '),
  )
  let allOk = true
  for (const r of rows) {
    if (!r.redOk || !r.greenOk) allOk = false
    console.log(
      [
        r.gate,
        `${r.redExitCode} (${r.redSummary})`,
        r.redOk ? 'YES — failed as required' : 'NO — DECORATION (did not fail!)',
        `${r.greenExitCode} (${r.greenSummary})`,
        r.greenOk ? 'YES — passed as required' : 'NO — BROKEN (did not pass!)',
      ].join(' | '),
    )
  }

  console.log(`\n${allOk ? 'ALL GATES PROVEN NON-DECORATIVE (red then green).' : 'FAILURE: one or more gates are decoration or broken — see table above.'}`)
  process.exit(allOk ? 0 : 1)
}

main()
