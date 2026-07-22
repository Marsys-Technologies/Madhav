#!/usr/bin/env tsx
/**
 * harness.ts — Task 12: the load-generation harness for the master brief's §9.7
 * four-point load test (W-28 cache, W-29 concurrency capacity, W-30 QoS/backpressure,
 * W-31 quality-under-load proof — see `RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md`'s §9
 * tracking register; there is no section literally titled "§9.7" with prose, it is a
 * grouping label over those four line items).
 *
 * ────────────────────────────────────────────────────────────────────────────────
 * SCOPE BOUNDARY — read before running this against anything real.
 *
 * This session has NO valid bearer credential for the deployed `amjis-mcp`/
 * `amjis-web` services. Building and dry-run-verifying this harness IS this task's
 * job; running it for real against the live connector is a NAMED RESIDUAL carried to
 * a separate task (Task 13) for a human operator with an authenticated session. Do
 * not attempt to obtain or use a production credential to close that residual from
 * here — `--target=<url>` below exists so a future authorized run can point this same
 * harness at the real target, not so this session can.
 * ────────────────────────────────────────────────────────────────────────────────
 *
 * Every threshold this harness gates on is an explicit, labeled, OVERRIDABLE
 * placeholder — see `types.ts` `DEFAULT_THRESHOLDS`'s doc comment. No source doctrine
 * document was found (confirmed by search) that names a concrete target RPS, p95
 * latency budget, or cache hit-rate percentage for §9.7; the doctrine describes
 * categories, not numbers.
 *
 * Usage:
 *   npx tsx tests/eval/w6_load_battery/harness.ts [--dry-run] [--target=local|<url>]
 *     [--mode=cache|concurrency|qos|slo|all] [--concurrency=N] [--out=path.json]
 *     [--config=thresholds.json]
 *
 *   --dry-run / --target=local   Spin up the in-process mock server (mock_server.ts)
 *                                 and run against it. This is the ONLY mode exercised
 *                                 by this task — see scope boundary above.
 *   --target=<url>                Point at a real deployed target (Task 13's job).
 *                                 Bearer token, if needed, comes from the
 *                                 LOAD_TEST_BEARER_TOKEN env var — never hardcoded,
 *                                 never requested by this script.
 *   --mode=<name>                 Run one mode only; default `all` (all four).
 *   --concurrency=N                Max concurrency level for the concurrency-capacity
 *                                 ramp's top rung (default ramp tops out at 32).
 *   --out=path.json                Write the JSON report there instead of stdout.
 *   --config=thresholds.json       Override any subset of `DEFAULT_THRESHOLDS`.
 *
 * Exit code: 0 if every requested mode's `pass` is true against the (placeholder)
 * thresholds; 1 otherwise. Exit code is diagnostic information for a human/CI reading
 * the report — given the placeholder nature of the thresholds, a non-zero exit here
 * means "worth a human look", not "confirmed regression against ratified doctrine".
 */
import { readFileSync, writeFileSync } from 'node:fs'
import { defaultTarget } from './http_client'
import { measureCacheHitRate, measureConcurrencyCapacity, measureQosBackpressure, measureSloPerQueryClass } from './modes'
import { startMockServer, type MockServerHandle } from './mock_server'
import { DEFAULT_THRESHOLDS } from './types'
import type { LoadHarnessReport, LoadTarget, LoadThresholds } from './types'

/** Mutable build-up shape for the report this CLI assembles incrementally, one mode
 *  at a time. `LoadHarnessReport` itself is all-readonly (the shape callers should
 *  treat the finished report as); this local type drops that for construction only. */
type MutableReport = { -readonly [K in keyof LoadHarnessReport]?: LoadHarnessReport[K] } & {
  gate: { pass: boolean; per_mode: Record<string, boolean> }
}

type Mode = 'cache' | 'concurrency' | 'qos' | 'slo'
const ALL_MODES: readonly Mode[] = ['cache', 'concurrency', 'qos', 'slo']

interface Args {
  dryRun: boolean
  target: string
  modes: readonly Mode[]
  concurrency: number
  out?: string
  configPath?: string
}

export function parseArgs(argv: readonly string[]): Args {
  let dryRun = false
  let target = 'local'
  let modes: readonly Mode[] = ALL_MODES
  let concurrency = 32
  let out: string | undefined
  let configPath: string | undefined

  for (const arg of argv) {
    if (arg === '--dry-run') dryRun = true
    const t = arg.match(/^--target=(.+)$/)
    if (t) target = t[1]
    const m = arg.match(/^--mode=(.+)$/)
    if (m) {
      const requested = m[1]
      modes = requested === 'all' ? ALL_MODES : ([requested] as Mode[])
    }
    const c = arg.match(/^--concurrency=(\d+)$/)
    if (c) concurrency = Number(c[1])
    const o = arg.match(/^--out=(.+)$/)
    if (o) out = o[1]
    const cfg = arg.match(/^--config=(.+)$/)
    if (cfg) configPath = cfg[1]
  }
  if (target === 'local') dryRun = true
  return { dryRun, target, modes, concurrency, out, configPath }
}

function loadThresholds(configPath?: string): LoadThresholds {
  if (!configPath) return DEFAULT_THRESHOLDS
  const raw = JSON.parse(readFileSync(configPath, 'utf-8')) as Partial<LoadThresholds>
  return { ...DEFAULT_THRESHOLDS, ...raw }
}

function buildTarget(targetArg: string, mockUrl: string | undefined): LoadTarget {
  const baseUrl = targetArg === 'local' ? mockUrl! : targetArg
  const headers: Record<string, string> = { 'content-type': 'application/json' }
  const token = process.env.LOAD_TEST_BEARER_TOKEN
  if (token && targetArg !== 'local') headers.authorization = `Bearer ${token}`
  return defaultTarget(baseUrl, { headers })
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2))
  const thresholds = loadThresholds(args.configPath)

  let mock: MockServerHandle | undefined
  if (args.dryRun) {
    mock = await startMockServer()
    console.error(`[mock] local target listening at ${mock.url}`)
  } else {
    console.error(
      `[live] targeting ${args.target} — this path is Task 13's job (authorized human ` +
        `operator only); this session does not hold a credential for it.`,
    )
  }

  const target = buildTarget(args.target, mock?.url)

  const report: MutableReport = {
    captured_at: new Date().toISOString(),
    target_kind: args.dryRun ? 'local_mock' : 'remote',
    thresholds,
    thresholds_note:
      'Every threshold above is an explicit, overridable placeholder — no source-documented ' +
      'numeric target was found for §9.7 in the master brief / elevation plan. See types.ts.',
    modes_run: args.modes,
    gate: { pass: true, per_mode: {} },
  }

  try {
    if (args.modes.includes('cache')) {
      console.error('[1/4] W-28 cache hit-rate…')
      const r = await measureCacheHitRate(target, thresholds)
      report.cache = r
      report.gate.per_mode.cache = r.pass
    }
    if (args.modes.includes('concurrency')) {
      console.error('[2/4] W-29 concurrency capacity…')
      const levels = [1, 2, 4, 8, 16, args.concurrency].filter((v, i, arr) => arr.indexOf(v) === i && v <= args.concurrency)
      const r = await measureConcurrencyCapacity(target, thresholds, { levels })
      report.concurrency = r
      report.gate.per_mode.concurrency = r.pass
    }
    if (args.modes.includes('qos')) {
      console.error('[3/4] W-30 QoS / backpressure…')
      const r = await measureQosBackpressure(target, thresholds)
      report.qos = r
      report.gate.per_mode.qos = r.pass
    }
    if (args.modes.includes('slo')) {
      console.error('[4/4] W-31 SLO per query-class…')
      const r = await measureSloPerQueryClass(target, thresholds)
      report.slo = r
      report.gate.per_mode.slo = r.overallPass
    }
  } finally {
    if (mock) await mock.close()
  }

  report.gate.pass = Object.values(report.gate.per_mode).every(Boolean)

  const json = JSON.stringify(report, null, 2)
  if (args.out) {
    writeFileSync(args.out, json, 'utf-8')
    console.error(`Report written to ${args.out}`)
  } else {
    console.log(json)
  }

  console.error('\n── Summary ──')
  for (const [mode, pass] of Object.entries(report.gate.per_mode)) {
    console.error(`  ${mode.padEnd(12)} ${pass ? 'PASS' : 'FAIL'} (vs. placeholder threshold — see thresholds_note)`)
  }
  console.error(`GATE: ${report.gate.pass ? 'PASS' : 'FAIL'}`)

  if (!report.gate.pass) process.exitCode = 1
}

main().catch((err) => {
  console.error('harness.ts fatal error:', err)
  process.exitCode = 2
})
