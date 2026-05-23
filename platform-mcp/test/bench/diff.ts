/**
 * diff.ts — MCPT v3.2 Phase 8a Bench Harness: Diff Engine
 *
 * Compares head bench/<git-sha>.json vs bench/baseline.json (or
 * bench/mcpt-v32-baseline.json if baseline.json doesn't exist).
 * Emits bench/diff.json and bench/diff.md.
 *
 * Regression threshold: any metric worsening by >10%.
 * Metrics that decrease are regressions for response_bytes and wall_time_ms
 * (larger = worse). round_trips regressions are flagged when they increase.
 *
 * Usage: tsx test/bench/diff.ts
 *        npm run bench:diff
 *
 * MCPT v3.2 Phase 8a
 */

import * as fs from 'node:fs'
import * as path from 'node:path'
import { fileURLToPath } from 'node:url'
import { execSync } from 'node:child_process'

// ── Directory constants ───────────────────────────────────────────────────────

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
// __dirname = platform-mcp/test/bench → repo root is 3 levels up
const REPO_ROOT = path.resolve(__dirname, '..', '..', '..')
const BENCH_DIR = path.join(REPO_ROOT, 'bench')

// ── Types ─────────────────────────────────────────────────────────────────────

interface ScenarioMetrics {
  round_trips: number
  response_bytes: number
  wall_time_ms: number
}

interface ScenarioResult {
  scenario: string
  description: string
  metrics: ScenarioMetrics
  steps_executed: number
  ok: boolean
  error?: string
}

interface BenchCapture {
  git_sha: string
  captured_at: string
  platform_mcp_dir: string
  scenarios: Record<string, ScenarioResult>
}

export interface ScenarioDiff {
  baseline: ScenarioMetrics
  head: ScenarioMetrics
  delta_pct: Record<string, number>
}

export interface BenchDiff {
  head_sha: string
  baseline_sha: string
  diffed_at: string
  scenarios: Record<string, ScenarioDiff>
  verdict: 'pass' | 'regress'
  regressions: string[]
}

// ── Git SHA helper ────────────────────────────────────────────────────────────

function getGitSha(): string {
  const candidates = [REPO_ROOT, process.cwd()]
  for (const cwd of candidates) {
    try {
      return execSync('git rev-parse --short HEAD', {
        cwd,
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe'],
      }).trim()
    } catch {
      // try next
    }
  }
  return 'unknown'
}

// ── Diff computation ──────────────────────────────────────────────────────────

/** Compute percentage change: (head - baseline) / baseline * 100. */
function deltaPct(baseline: number, head: number): number {
  if (baseline === 0) return head === 0 ? 0 : 100
  return ((head - baseline) / baseline) * 100
}

/**
 * Metrics where a positive delta (head > baseline) is a regression.
 * round_trips: more round-trips = worse
 * response_bytes: larger responses = worse
 * wall_time_ms: slower = worse
 */
const REGRESSION_METRICS: Array<keyof ScenarioMetrics> = [
  'round_trips',
  'response_bytes',
  'wall_time_ms',
]

const REGRESSION_THRESHOLD_PCT = 10

function computeDiff(baseline: BenchCapture, head: BenchCapture): BenchDiff {
  const regressions: string[] = []
  const scenarios: Record<string, ScenarioDiff> = {}

  const allScenarioNames = new Set([
    ...Object.keys(baseline.scenarios),
    ...Object.keys(head.scenarios),
  ])

  for (const name of allScenarioNames) {
    const baseResult = baseline.scenarios[name]
    const headResult = head.scenarios[name]

    if (!baseResult || !headResult) {
      // New or removed scenario — skip diff but note it
      continue
    }

    if (!baseResult.ok || !headResult.ok) {
      // One or both failed — note as regression if head failed
      if (!headResult.ok && baseResult.ok) {
        regressions.push(`${name}: scenario failed in head (was ok in baseline)`)
      }
      continue
    }

    const baseM = baseResult.metrics
    const headM = headResult.metrics

    const delta_pct: Record<string, number> = {}
    for (const metric of REGRESSION_METRICS) {
      const base = baseM[metric] ?? 0
      const headVal = headM[metric] ?? 0
      const pct = deltaPct(base, headVal)
      delta_pct[metric] = Math.round(pct * 10) / 10

      if (pct > REGRESSION_THRESHOLD_PCT) {
        regressions.push(
          `${name}.${metric}: +${pct.toFixed(1)}% (baseline=${base}, head=${headVal})`
        )
      }
    }

    scenarios[name] = {
      baseline: baseM,
      head: headM,
      delta_pct,
    }
  }

  return {
    head_sha: head.git_sha,
    baseline_sha: baseline.git_sha,
    diffed_at: new Date().toISOString(),
    scenarios,
    verdict: regressions.length > 0 ? 'regress' : 'pass',
    regressions,
  }
}

// ── Markdown report generator ─────────────────────────────────────────────────

function renderMarkdown(diff: BenchDiff): string {
  const verdictEmoji = diff.verdict === 'pass' ? '✅' : '⚠️'
  const lines: string[] = []

  lines.push(`## MCP Bench Diff — ${verdictEmoji} ${diff.verdict.toUpperCase()}`)
  lines.push('')
  lines.push(`**Head SHA:** \`${diff.head_sha}\`  `)
  lines.push(`**Baseline SHA:** \`${diff.baseline_sha}\`  `)
  lines.push(`**Diffed at:** ${diff.diffed_at}`)
  lines.push('')

  if (diff.regressions.length > 0) {
    lines.push('### Regressions (>10% worsening)')
    for (const r of diff.regressions) {
      lines.push(`- ${r}`)
    }
    lines.push('')
  }

  lines.push('### Scenario Metrics')
  lines.push('')
  lines.push('| Scenario | Metric | Baseline | Head | Δ% |')
  lines.push('|---|---|---|---|---|')

  for (const [name, s] of Object.entries(diff.scenarios)) {
    for (const metric of REGRESSION_METRICS) {
      const base = s.baseline[metric]
      const head = s.head[metric]
      const pct = s.delta_pct[metric] ?? 0
      const pctStr = pct > 0 ? `+${pct}%` : pct < 0 ? `${pct}%` : `0%`
      const flag = pct > REGRESSION_THRESHOLD_PCT ? ' ⚠️' : ''
      lines.push(`| ${name} | ${metric} | ${base} | ${head} | ${pctStr}${flag} |`)
    }
  }

  lines.push('')

  if (diff.verdict === 'pass') {
    lines.push('_No regressions detected. All metrics within threshold._')
  }

  return lines.join('\n')
}

// ── Main ──────────────────────────────────────────────────────────────────────

function main(): void {
  const gitSha = getGitSha()

  // Find head capture
  const headPath = path.join(BENCH_DIR, `${gitSha}.json`)
  if (!fs.existsSync(headPath)) {
    // Try to find the most recent capture by mtime
    const jsonFiles = fs.readdirSync(BENCH_DIR)
      .filter(f => f.endsWith('.json') && f !== 'diff.json' && !f.includes('baseline'))
      .map(f => ({ name: f, mtime: fs.statSync(path.join(BENCH_DIR, f)).mtimeMs }))
      .sort((a, b) => b.mtime - a.mtime)

    if (jsonFiles.length === 0) {
      console.error('[bench:diff] No head capture found. Run bench:capture first.')
      process.exit(1)
    }
    console.warn(`[bench:diff] No capture for SHA ${gitSha}, using most recent: ${jsonFiles[0]?.name ?? 'unknown'}`)
  }

  const actualHeadPath = fs.existsSync(headPath)
    ? headPath
    : (() => {
        const jsonFiles = fs.readdirSync(BENCH_DIR)
          .filter(f => f.endsWith('.json') && f !== 'diff.json' && !f.includes('baseline'))
          .map(f => ({ name: f, mtime: fs.statSync(path.join(BENCH_DIR, f)).mtimeMs }))
          .sort((a, b) => b.mtime - a.mtime)
        return path.join(BENCH_DIR, jsonFiles[0]?.name ?? '')
      })()

  // Find baseline capture (prefer baseline.json, fall back to mcpt-v32-baseline.json)
  const baselineCandidates = [
    path.join(BENCH_DIR, 'baseline.json'),
    path.join(BENCH_DIR, 'mcpt-v32-baseline.json'),
  ]
  const baselinePath = baselineCandidates.find(p => fs.existsSync(p))

  if (!baselinePath) {
    // No baseline yet — use head as its own baseline (diff will be all zeros)
    console.warn('[bench:diff] No baseline found. Using head as its own baseline (all deltas = 0).')
    const head = JSON.parse(fs.readFileSync(actualHeadPath, 'utf8')) as BenchCapture
    const diff = computeDiff(head, head)
    const diffPath = path.join(BENCH_DIR, 'diff.json')
    fs.writeFileSync(diffPath, JSON.stringify(diff, null, 2))
    const mdPath = path.join(BENCH_DIR, 'diff.md')
    fs.writeFileSync(mdPath, renderMarkdown(diff))
    console.log(`[bench:diff] Written ${diffPath} and ${mdPath} (self-diff — all zeros)`)
    return
  }

  const baseline = JSON.parse(fs.readFileSync(baselinePath, 'utf8')) as BenchCapture
  const head = JSON.parse(fs.readFileSync(actualHeadPath, 'utf8')) as BenchCapture

  const diff = computeDiff(baseline, head)

  const diffPath = path.join(BENCH_DIR, 'diff.json')
  fs.writeFileSync(diffPath, JSON.stringify(diff, null, 2))

  const mdPath = path.join(BENCH_DIR, 'diff.md')
  fs.writeFileSync(mdPath, renderMarkdown(diff))

  console.log(`[bench:diff] Verdict: ${diff.verdict.toUpperCase()}`)
  if (diff.regressions.length > 0) {
    console.log('[bench:diff] Regressions:')
    for (const r of diff.regressions) {
      console.log(`  - ${r}`)
    }
  } else {
    console.log('[bench:diff] No regressions detected.')
  }
  console.log(`[bench:diff] Written ${diffPath} and ${mdPath}`)
}

main()
