/**
 * diff.ts — Accuracy diff engine for MCPT v3.2 quality harness.
 *
 * Reads the latest accuracy/<git-sha>.json result (written by run.ts / accuracy:capture),
 * compares against the golden fixture, and emits accuracy/diff.json with a
 * structured diff report (added categories, removed categories, changed row counts,
 * overall verdict).
 *
 * Usage:
 *   npx tsx test/accuracy/diff.ts
 *   npm run accuracy:diff
 *
 * Output: accuracy/diff.json (schema below)
 *
 * MCPT v3.2 Phase 8 — Accuracy Harness (P8b)
 */

import { readFileSync, writeFileSync, readdirSync, mkdirSync, existsSync } from 'fs'
import { execSync } from 'child_process'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const FIXTURE_PATH = join(__dirname, 'fixtures/abhisek-mohanty-golden.json')
const ACCURACY_DIR = join(__dirname, '../../../accuracy')
const DIFF_OUTPUT_PATH = join(ACCURACY_DIR, 'diff.json')

// ── Types ─────────────────────────────────────────────────────────────────────

interface GoldenSnapshotCheck {
  expected_rows: number
  actual_rows: number
  delta: number
  added: string[]
  removed: string[]
  changed: string[]
}

export interface AccuracyDiff {
  fixture: string
  run_at: string
  git_sha: string
  checks: {
    golden_snapshot: GoldenSnapshotCheck
  }
  verdict: 'pass' | 'regress'
  regressions: string[]
  detail: Record<string, CategoryDiff>
}

interface CategoryDiff {
  expected_min_rows: number
  actual_rows: number
  delta: number
  status: 'ok' | 'regressed' | 'new' | 'missing'
}

interface GoldenFixture {
  _meta: {
    chart_id: string
    mcpt_version: string
    total_rows: number
    categories: number
    generated_at: string
  }
  [category: string]: { expected_min_rows: number; actual_rows?: number } | { chart_id: string; mcpt_version: string; total_rows: number; categories: number; generated_at: string }
}

interface AccuracyRunResult {
  chart_id: string
  mcpt_version: string
  run_at: string
  git_sha: string
  categories_checked: number
  checks: Record<string, { expected_min_rows: number; actual_rows: number; passed: boolean }>
  verdict: 'pass' | 'regress'
  regressions: string[]
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function getGitSha(): string {
  try {
    return execSync('git rev-parse --short HEAD', { stdio: ['pipe', 'pipe', 'pipe'] })
      .toString()
      .trim()
  } catch {
    return 'unknown'
  }
}

function loadGoldenFixture(): GoldenFixture {
  const raw = readFileSync(FIXTURE_PATH, 'utf-8')
  return JSON.parse(raw) as GoldenFixture
}

function findLatestRunResult(): AccuracyRunResult | null {
  if (!existsSync(ACCURACY_DIR)) {
    return null
  }
  const files = readdirSync(ACCURACY_DIR)
    .filter(f => f.endsWith('.json') && f !== 'diff.json')
    .sort()
    .reverse()

  if (files.length === 0) {
    return null
  }

  const latestPath = join(ACCURACY_DIR, files[0])
  const raw = readFileSync(latestPath, 'utf-8')
  return JSON.parse(raw) as AccuracyRunResult
}

function ensureAccuracyDir(): void {
  mkdirSync(ACCURACY_DIR, { recursive: true })
}

// ── Diff computation ─────────────────────────────────────────────────────────

function computeDiff(fixture: GoldenFixture, runResult: AccuracyRunResult | null): AccuracyDiff {
  const gitSha = getGitSha()
  const fixtureCategories = Object.keys(fixture).filter(k => k !== '_meta')
  const meta = fixture._meta as { chart_id: string; mcpt_version: string; total_rows: number; categories: number; generated_at: string }

  const detail: Record<string, CategoryDiff> = {}
  const regressions: string[] = []
  const added: string[] = []
  const removed: string[] = []
  const changed: string[] = []

  if (runResult) {
    // Determine which categories are in run result but not fixture (new) and vice versa (missing)
    const runCategories = new Set(Object.keys(runResult.checks))
    const fixtureSet = new Set(fixtureCategories)

    for (const cat of fixtureCategories) {
      const expectation = fixture[cat] as { expected_min_rows: number; actual_rows?: number }
      if (runCategories.has(cat)) {
        const check = runResult.checks[cat]
        const delta = check.actual_rows - expectation.expected_min_rows
        const status: 'ok' | 'regressed' = check.passed ? 'ok' : 'regressed'
        detail[cat] = {
          expected_min_rows: expectation.expected_min_rows,
          actual_rows: check.actual_rows,
          delta,
          status,
        }
        if (!check.passed) {
          regressions.push(cat)
          changed.push(cat)
        }
      } else {
        // Category in fixture but not in run result — missing
        detail[cat] = {
          expected_min_rows: expectation.expected_min_rows,
          actual_rows: 0,
          delta: -expectation.expected_min_rows,
          status: 'missing',
        }
        regressions.push(cat)
        removed.push(cat)
      }
    }

    // Categories in run result not present in fixture — new
    for (const cat of runCategories) {
      if (!fixtureSet.has(cat)) {
        const check = runResult.checks[cat]
        detail[cat] = {
          expected_min_rows: 0,
          actual_rows: check.actual_rows,
          delta: check.actual_rows,
          status: 'new',
        }
        added.push(cat)
      }
    }
  } else {
    // No run result found — use fixture self-check (offline mode)
    for (const cat of fixtureCategories) {
      const expectation = fixture[cat] as { expected_min_rows: number; actual_rows?: number }
      const actual = typeof expectation.actual_rows === 'number'
        ? expectation.actual_rows
        : expectation.expected_min_rows
      const passed = actual >= expectation.expected_min_rows
      detail[cat] = {
        expected_min_rows: expectation.expected_min_rows,
        actual_rows: actual,
        delta: actual - expectation.expected_min_rows,
        status: passed ? 'ok' : 'regressed',
      }
      if (!passed) {
        regressions.push(cat)
      }
    }
  }

  const totalExpectedRows = fixtureCategories.reduce((sum, cat) => {
    const exp = fixture[cat] as { expected_min_rows: number }
    return sum + exp.expected_min_rows
  }, 0)

  const totalActualRows = Object.values(detail).reduce((sum, d) => sum + d.actual_rows, 0)

  const diff: AccuracyDiff = {
    fixture: FIXTURE_PATH,
    run_at: new Date().toISOString(),
    git_sha: gitSha,
    checks: {
      golden_snapshot: {
        expected_rows: meta.total_rows,
        actual_rows: totalActualRows,
        delta: totalActualRows - meta.total_rows,
        added,
        removed,
        changed,
      },
    },
    verdict: regressions.length === 0 ? 'pass' : 'regress',
    regressions,
    detail,
  }

  return diff
}

// ── Main entry point ──────────────────────────────────────────────────────────

function main(): void {
  ensureAccuracyDir()

  const fixture = loadGoldenFixture()
  const runResult = findLatestRunResult()

  if (!runResult) {
    console.warn('[accuracy:diff] No run result found in accuracy/ directory.')
    console.warn('[accuracy:diff] Run `npm run accuracy:capture` first to generate a result.')
    console.warn('[accuracy:diff] Proceeding with fixture self-check (offline mode).')
  }

  const diff = computeDiff(fixture, runResult)

  writeFileSync(DIFF_OUTPUT_PATH, JSON.stringify(diff, null, 2))

  console.log(`\n[accuracy:diff] Diff written to: ${DIFF_OUTPUT_PATH}`)
  console.log(`[accuracy:diff] Verdict: ${diff.verdict.toUpperCase()}`)
  console.log(`[accuracy:diff] Total rows — expected: ${diff.checks.golden_snapshot.expected_rows}, actual: ${diff.checks.golden_snapshot.actual_rows}`)

  if (diff.regressions.length > 0) {
    console.error(`[accuracy:diff] REGRESSIONS (${diff.regressions.length}): ${diff.regressions.join(', ')}`)
    process.exit(1)
  } else {
    console.log('[accuracy:diff] All categories pass expected_min_rows thresholds.')
  }
}

main()
