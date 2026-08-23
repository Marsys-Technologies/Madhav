#!/usr/bin/env npx tsx
/**
 * dd1_feel_proxy_battery — the DD-1 automated feel-proxy battery.
 *
 * ══════════════════════════════════════════════════════════════════════════
 *  MACHINE PROXY — NOT AC-15.  (full label: metrics.ts PROXY_LABEL)
 * ══════════════════════════════════════════════════════════════════════════
 *
 * ONE COMMAND:
 *
 *   # 1. bank the §N.8 red proof (REQUIRED — no PASS can be minted without it)
 *   npm run pariprashna:dd1-battery -- --red-proof
 *
 *   # 2. run the battery against the live default surface
 *   npm run pariprashna:dd1-battery -- --base-url https://<target>
 *
 * FLAGS
 *   --base-url <url>     target (default: the live prod service URL)
 *   --chart-id <uuid>    synthetic chart only; the native's chart is refused
 *   --red-proof          run the red-then-green proof and write the receipt
 *   --no-browser         skip the live-surface browser lane
 *   --no-fixture         skip the edge-state fixture suite
 *   --no-live            skip the live probe turns (prose lane) — diagnostics only
 *   --headed             run the browser lane headed
 *   --probes <n>         how many of the probe set to run (default: all)
 *   --turn-timeout <ms>  per-turn settle timeout in the browser lane
 *   --out <dir>          artifact directory
 *
 * EXIT CODES (the CONDUCTOR reads these)
 *   0  every DD-1-enumerated metric reported PASS               → gate OPEN
 *   1  at least one metric reported FAIL                        → battery RED, retirement PARKS
 *   2  no FAIL, but a DD-1-enumerated metric is NOT_IMPLEMENTED → battery INCOMPLETE,
 *      the surrogate rules on whether the covered subset is enough to open the gate
 *   3  the battery could not run at all (target unreachable, auth failed)
 */
import { mkdirSync, writeFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'
import { METRICS, PROXY_LABEL, type MetricSpec, type MetricStatus } from './metrics'
import { PROSE_CHECKS, type ReadingRecord, type CheckOutcome } from './prose_checks'
import { driveTurn, mintSessionCookie, SYNTHETIC_TEST_CHART_ID, REAL_NATIVE_CANONICAL_CHART_ID } from './live_turn'
import { runBrowserLane, runBrowserRedProof } from './browser_lane'
import {
  applyRedProofGate, detectorHash, loadReceipt, runProseRedProof, saveReceipt,
  type RedProofEntry, type RedProofReceipt,
} from './red_proof'

const __dirname = dirname(fileURLToPath(import.meta.url))
const REPO_PLATFORM = join(__dirname, '..', '..', '..')
const DEFAULT_BASE_URL = 'https://amjis-web-qm256lasva-el.a.run.app'
const DEFAULT_OUT = join(__dirname, 'out')

/**
 * The probe set — real questions, spanning the reading shapes the register
 * rules are actually about (§4 journeys J1/J3/J7 + a remedial turn, which is
 * the one the voice lint's imperative detector exists for).
 */
const PROBE_SET: Array<{ label: string; question: string }> = [
  { label: 'J1-career', question: 'What does this period ask of my work?' },
  { label: 'J3-health-in-fear', question: 'I am frightened about my health this year. What does the chart actually say?' },
  { label: 'J7-honest-gap', question: 'Which city should I move to?' },
  { label: 'remedy', question: 'What remedy should I do for my weak Moon?' },
  { label: 'timing', question: 'When does the next favourable window for a change of role open?' },
]

export interface Args {
  baseUrl: string
  chartId: string
  redProof: boolean
  browser: boolean
  fixture: boolean
  live: boolean
  headed: boolean
  probes: number
  turnTimeoutMs: number
  outDir: string
}

/**
 * THE ONE PLACE the native's-real-chart refusal lives (fix for the REFUTED
 * PR #1501 finding: the guard used to live ONLY inside `driveTurn()`
 * (live_turn.ts), which `--no-live` skips entirely — `browser_lane.ts` built
 * its target URL from the raw `--chart-id` argument with no guard at all, so
 * `--no-live --chart-id <native>` drove a real authenticated turn on the
 * native's real chart against the live surface. Binding the refusal here, in
 * argument parsing itself, means it fires before ANY lane (prose, browser, or
 * fixture) sees the chart id, for every flag combination — there is no flag
 * that reaches past this check. See COMMON_BRIEF hard-never + charter §9.
 */
function refuseRealNativeChart(chartId: string): void {
  if (chartId !== REAL_NATIVE_CANONICAL_CHART_ID) return
  console.error(
    `dd1_battery refuses to run against the real native's canonical chart ` +
      `(${REAL_NATIVE_CANONICAL_CHART_ID}). The battery probes the synthetic chart only ` +
      `(${SYNTHETIC_TEST_CHART_ID}) — COMMON_BRIEF hard-never; charter §9. This refusal is ` +
      'enforced in parseArgs() and binds every lane (prose/browser/fixture) and every flag ' +
      'combination, including --no-live — there is no escape hatch.',
  )
  process.exit(1)
}

export function parseArgs(argv: string[]): Args {
  const a: Args = {
    baseUrl: DEFAULT_BASE_URL,
    chartId: SYNTHETIC_TEST_CHART_ID,
    redProof: false,
    browser: true,
    fixture: true,
    live: true,
    headed: false,
    probes: PROBE_SET.length,
    turnTimeoutMs: 180_000,
    outDir: DEFAULT_OUT,
  }
  for (let i = 0; i < argv.length; i++) {
    const t = argv[i]
    if (t === '--base-url') a.baseUrl = argv[++i]
    else if (t === '--chart-id') a.chartId = argv[++i]
    else if (t === '--red-proof') a.redProof = true
    else if (t === '--no-browser') a.browser = false
    else if (t === '--no-fixture') a.fixture = false
    else if (t === '--no-live') a.live = false
    else if (t === '--headed') a.headed = true
    else if (t === '--probes') a.probes = Number(argv[++i])
    else if (t === '--turn-timeout') a.turnTimeoutMs = Number(argv[++i])
    else if (t === '--out') a.outDir = argv[++i]
    else if (t === '--help' || t === '-h') { printHelp(); process.exit(0) }
  }
  refuseRealNativeChart(a.chartId)
  return a
}

function printHelp(): void {
  console.log(PROXY_LABEL)
  console.log('\nUsage: npm run pariprashna:dd1-battery -- [--red-proof] [--base-url <url>] [flags]')
  console.log('See the header of scripts/pariprashna/dd1_battery/index.ts for the full flag list.')
}

const lines: string[] = []
function log(s = ''): void {
  console.log(s)
  lines.push(s)
}

// ── the fixture (edge-state) lane ──────────────────────────────────────────
function runNpm(script: string, extra: string[] = []): { code: number; tail: string } {
  const r = spawnSync('npm', ['run', script, ...extra], { cwd: REPO_PLATFORM, encoding: 'utf8' })
  const out = `${r.stdout ?? ''}\n${r.stderr ?? ''}`
  return { code: r.status ?? 1, tail: out.trim().split('\n').slice(-25).join('\n') }
}

function runFixtureLane(): CheckOutcome {
  log('[edge] running the edge-state fixture suite (npm run pariprashna:gates) …')
  const desktop = runNpm('pariprashna:gates')
  log(`[edge] desktop project exit=${desktop.code}`)
  const mobile = runNpm('pariprashna:gates:mobile')
  log(`[edge] mobile-390x844 project exit=${mobile.code}`)
  const findings: string[] = []
  if (desktop.code !== 0) findings.push(`EDGE desktop gate suite failed (exit ${desktop.code}):\n${desktop.tail}`)
  if (mobile.code !== 0) findings.push(`EDGE mobile-390x844 gate suite failed (exit ${mobile.code}):\n${mobile.tail}`)
  return {
    ok: findings.length === 0,
    findings,
    detail: {
      desktop_exit: desktop.code,
      mobile_exit: mobile.code,
      honesty_note:
        'This suite runs against the standalone replay harness page ' +
        '(tests/pariprashna/harness/public/index.html), NOT the production React surface. ' +
        'It is a FIXTURE lane by construction and does not substitute for the live-surface ' +
        'browser lane.',
    },
  }
}

function runFixtureRedProof(): RedProofEntry {
  log('[edge] running the repo\'s own automated red-then-green gate selftest (npm run pariprashna:selftest) …')
  const r = runNpm('pariprashna:selftest')
  log(`[edge] selftest exit=${r.code}`)
  return {
    check: 'EDGE',
    red_fired: r.code === 0, // selftest exits non-zero if ANY gate is decoration
    red_findings: r.code === 0
      ? ['pariprashna:selftest exit 0 — every edge-state gate was run against its own seeded violation and observed to FAIL, then re-run clean and observed to PASS']
      : [`pariprashna:selftest exit ${r.code} — at least one gate is decoration or broken:\n${r.tail}`],
    green_clean: r.code === 0,
    green_findings: [],
    note: 'the red-then-green demonstration is the repo\'s own scripts/replay/selftest.ts, not a re-implementation',
  }
}

// ── the prose lane ─────────────────────────────────────────────────────────
async function collectCorpus(args: Args): Promise<{ corpus: ReadingRecord[]; transcripts: unknown[]; fatal: string | null }> {
  log(`[live] minting a session cookie against ${args.baseUrl} …`)
  let cookie: string
  try {
    cookie = await mintSessionCookie(args.baseUrl)
  } catch (err) {
    return { corpus: [], transcripts: [], fatal: `auth failed: ${String(err)}` }
  }
  const corpus: ReadingRecord[] = []
  const transcripts: unknown[] = []
  for (const probe of PROBE_SET.slice(0, args.probes)) {
    log(`[live] probe "${probe.label}": ${probe.question}`)
    const turn = await driveTurn({ serviceUrl: args.baseUrl, cookie, chartId: args.chartId, question: probe.question })
    log(`[live]   → status=${turn.terminalStatus} blocks=${turn.blocks.length} ttft=${turn.firstProseDeltaMs}ms total=${turn.totalMs}ms chars=${turn.prose.length}`)
    transcripts.push(turn)
    if (turn.prose.length === 0) {
      log(`[live]   ! probe "${probe.label}" produced NO reader prose (${turn.terminalStatus}${turn.error ? `: ${turn.error}` : ''}) — excluded from the corpus`)
      continue
    }
    corpus.push({
      label: probe.label,
      question: probe.question,
      prose: turn.prose,
      events: turn.events,
      blocks: turn.blocks,
      firstProseDeltaMs: turn.firstProseDeltaMs,
    })
  }
  return { corpus, transcripts, fatal: null }
}

// ── report ─────────────────────────────────────────────────────────────────
interface MetricResult {
  spec: MetricSpec
  status: MetricStatus
  rawStatus: MetricStatus
  gateNote: string | null
  findings: string[]
  detail: Record<string, unknown>
  reason: string | null
}

function statusIcon(s: MetricStatus): string {
  return s === 'PASS' ? 'PASS' : s === 'FAIL' ? 'FAIL' : 'NOT-IMPL'
}

function renderMarkdown(results: MetricResult[], args: Args, receipt: RedProofReceipt | null): string {
  const out: string[] = []
  out.push('# DD-1 feel-proxy battery — result')
  out.push('')
  out.push('```')
  out.push(PROXY_LABEL)
  out.push('```')
  out.push('')
  out.push(`- target: \`${args.baseUrl}\``)
  out.push(`- chart: \`${args.chartId}\` (synthetic — Abhinandan Mohanty)`)
  out.push(`- run at: ${new Date().toISOString()}`)
  out.push(`- detector hash: \`${detectorHash().slice(0, 16)}…\``)
  out.push(`- red-proof receipt: ${receipt ? `banked ${receipt.generated_at} (${Object.keys(receipt.proofs).length} proofs)` : '**ABSENT — no PASS can be minted**'}`)
  out.push('')
  out.push('## Per-metric result')
  out.push('')
  out.push('| Metric | DD-1? | Lane | Status | Threshold | What would have to fail for this to read false (§N.8) |')
  out.push('|---|---|---|---|---|---|')
  for (const r of results) {
    const falsifier = r.spec.falsifier.replace(/\s+/g, ' ').replace(/\|/g, '\\|')
    out.push(
      `| **${r.spec.id}** ${r.spec.title} | ${r.spec.inDd1Enumeration ? 'yes' : 'no'} | ${r.spec.lane} | **${statusIcon(r.status)}** | ${r.spec.threshold.replace(/\|/g, '\\|')} | ${falsifier} |`,
    )
  }
  out.push('')
  out.push('## Findings')
  out.push('')
  for (const r of results) {
    if (r.status === 'PASS' && !r.gateNote) continue
    out.push(`### ${r.spec.id} — ${statusIcon(r.status)}`)
    if (r.gateNote) out.push(`- red-proof gate: ${r.gateNote}`)
    if (r.reason) out.push(`- ${r.reason}`)
    for (const f of r.findings) out.push(`- ${f}`)
    out.push('')
  }
  out.push('## Metric definitions (verbatim, with provenance)')
  out.push('')
  for (const r of results) {
    out.push(`- **${r.spec.id}** — "${r.spec.definition}" · target "${r.spec.threshold}" · source: ${r.spec.sourceRef}`)
  }
  return out.join('\n')
}

// ── main ───────────────────────────────────────────────────────────────────
async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2))
  mkdirSync(args.outDir, { recursive: true })

  log(PROXY_LABEL)
  log('')
  log(`target      : ${args.baseUrl}`)
  log(`chart       : ${args.chartId}`)
  log(`detector    : ${detectorHash()}`)
  log('')

  // ── --red-proof ─────────────────────────────────────────────────────────
  if (args.redProof) {
    log('RUNNING THE §N.8 RED PROOF — every detector is fed a deliberately broken input')
    log('and must be OBSERVED TO FAIL it, then observed to pass its clean counterpart.')
    log('No PASS this battery ever emits counts until this receipt exists.')

    const proofs: Record<string, RedProofEntry> = { ...runProseRedProof(METRICS, log) }

    if (args.browser) {
      log('')
      log('── browser-lane red proofs (synthetic DOM carrying the PRODUCTION selectors) ──')
      Object.assign(proofs, await runBrowserRedProof({ headless: !args.headed, log }))
    }
    if (args.fixture) {
      log('')
      proofs.edge_fixture_suite = runFixtureRedProof()
    }

    const receipt: RedProofReceipt = {
      generated_at: new Date().toISOString(),
      detector_hash: detectorHash(),
      target: null,
      proofs,
    }
    const p = saveReceipt(args.outDir, receipt)
    log('')
    log(`red-proof receipt written: ${p}`)

    const unproven = Object.entries(proofs).filter(([, e]) => !e.red_fired || !e.green_clean)
    log('')
    log('SUMMARY')
    for (const [k, e] of Object.entries(proofs)) {
      log(`  ${e.red_fired && e.green_clean ? 'PROVEN    ' : 'UNPROVEN  '} ${k} (check ${e.check}) red_fired=${e.red_fired} green_clean=${e.green_clean}`)
    }
    writeFileSync(join(args.outDir, 'dd1_red_proof_transcript.txt'), lines.join('\n'))
    process.exit(unproven.length === 0 ? 0 : 1)
  }

  // ── full run ────────────────────────────────────────────────────────────
  const receipt = loadReceipt(args.outDir)
  if (!receipt) {
    log('WARNING: no red-proof receipt banked. Every would-be PASS will be downgraded to')
    log('NOT-IMPLEMENTED, because a green from this battery does not count until the red exists.')
    log('Run `--red-proof` first.')
    log('')
  }

  const results: MetricResult[] = []
  const record = (spec: MetricSpec, raw: MetricStatus, outc: CheckOutcome | null, reason: string | null) => {
    const gated = applyRedProofGate(raw, spec, receipt)
    results.push({
      spec, status: gated.status, rawStatus: raw, gateNote: gated.gateNote,
      findings: outc?.findings ?? [], detail: outc?.detail ?? {}, reason,
    })
  }

  // prose lane
  let corpus: ReadingRecord[] = []
  let transcripts: unknown[] = []
  let proseFatal: string | null = null
  if (args.live) {
    const collected = await collectCorpus(args)
    corpus = collected.corpus
    transcripts = collected.transcripts
    proseFatal = collected.fatal
    writeFileSync(join(args.outDir, 'dd1_probe_transcripts.json'), JSON.stringify(transcripts, null, 2))
  } else {
    proseFatal = '--no-live: the prose lane was skipped'
  }

  for (const spec of METRICS.filter((m) => m.lane === 'prose')) {
    const check = PROSE_CHECKS[spec.id]
    if (!check) { record(spec, 'NOT_IMPLEMENTED', null, 'no detector registered'); continue }
    if (proseFatal) { record(spec, 'NOT_IMPLEMENTED', null, proseFatal); continue }
    if (corpus.length === 0) {
      record(spec, 'NOT_IMPLEMENTED', null, 'no probe turn produced reader prose — nothing to measure')
      continue
    }
    const outc = check(corpus)
    record(spec, outc.ok ? 'PASS' : 'FAIL', outc, null)
  }

  // browser lane
  const browserSpecs = METRICS.filter((m) => m.lane === 'browser')
  if (!args.browser) {
    for (const spec of browserSpecs) record(spec, 'NOT_IMPLEMENTED', null, '--no-browser: the live-surface lane was skipped')
  } else {
    log('')
    log('[browser] opening the live default surface under 390x844 device emulation …')
    let cookie: string | null = null
    try {
      cookie = await mintSessionCookie(args.baseUrl)
    } catch (err) {
      for (const spec of browserSpecs) record(spec, 'NOT_IMPLEMENTED', null, `auth failed: ${String(err)}`)
    }
    if (cookie) {
      const bl = await runBrowserLane({
        baseUrl: args.baseUrl, chartId: args.chartId, cookie,
        question: PROBE_SET[0].question, headless: !args.headed,
        turnTimeoutMs: args.turnTimeoutMs, log,
      })
      writeFileSync(join(args.outDir, 'dd1_browser_lane.json'), JSON.stringify(bl, null, 2))
      for (const spec of browserSpecs) {
        if (spec.redProofKey === null) {
          record(spec, 'NOT_IMPLEMENTED', null, 'not implemented as defined — see the falsifier column')
          continue
        }
        if (!bl.available) { record(spec, 'NOT_IMPLEMENTED', null, bl.unavailableReason); continue }
        const outc = bl.checks[spec.id]
        if (!outc) { record(spec, 'NOT_IMPLEMENTED', null, 'no result produced by the browser lane'); continue }
        if (outc.detail.not_measured) { record(spec, 'NOT_IMPLEMENTED', outc, String(outc.detail.gate_reason ?? 'not measured')); continue }
        record(spec, outc.ok ? 'PASS' : 'FAIL', outc, null)
      }
    }
  }

  // fixture lane
  for (const spec of METRICS.filter((m) => m.lane === 'fixture')) {
    if (!args.fixture) { record(spec, 'NOT_IMPLEMENTED', null, '--no-fixture: the edge-state suite was skipped'); continue }
    const outc = runFixtureLane()
    record(spec, outc.ok ? 'PASS' : 'FAIL', outc, null)
  }

  // ── report ──────────────────────────────────────────────────────────────
  results.sort((a, b) => METRICS.indexOf(a.spec) - METRICS.indexOf(b.spec))
  log('')
  log('══════════════════════════════════════════════════════════════════════')
  log(' DD-1 FEEL-PROXY BATTERY — PER-METRIC RESULT  (MACHINE PROXY, NOT AC-15)')
  log('══════════════════════════════════════════════════════════════════════')
  for (const r of results) {
    log(`  ${statusIcon(r.status).padEnd(9)} ${r.spec.id.padEnd(9)} ${r.spec.lane.padEnd(8)} ${r.spec.inDd1Enumeration ? '[DD-1]' : '[extra]'} ${r.spec.title}`)
    if (r.gateNote) log(`             ↳ red-proof gate: ${r.gateNote}`)
    if (r.reason) log(`             ↳ ${r.reason}`)
    for (const f of r.findings.slice(0, 8)) log(`             · ${f}`)
    if (r.findings.length > 8) log(`             · … and ${r.findings.length - 8} more`)
  }

  const dd1 = results.filter((r) => r.spec.inDd1Enumeration)
  const fails = results.filter((r) => r.status === 'FAIL')
  const dd1NotImpl = dd1.filter((r) => r.status === 'NOT_IMPLEMENTED')

  log('')
  log(`DD-1-enumerated metrics: ${dd1.filter((r) => r.status === 'PASS').length} PASS · ${dd1.filter((r) => r.status === 'FAIL').length} FAIL · ${dd1NotImpl.length} NOT-IMPLEMENTED (of ${dd1.length})`)
  log('')
  log('This result is a MACHINE PROXY. It is not AC-15 and no AC-15 PASS is recorded by it.')

  const md = renderMarkdown(results, args, receipt)
  writeFileSync(join(args.outDir, 'DD1_BATTERY_RESULT.md'), md)
  writeFileSync(join(args.outDir, 'dd1_battery_result.json'), JSON.stringify({
    proxy_label: PROXY_LABEL,
    is_ac15: false,
    target: args.baseUrl,
    chart_id: args.chartId,
    generated_at: new Date().toISOString(),
    detector_hash: detectorHash(),
    red_proof_receipt_present: receipt !== null,
    results: results.map((r) => ({
      id: r.spec.id, title: r.spec.title, lane: r.spec.lane, in_dd1_enumeration: r.spec.inDd1Enumeration,
      definition: r.spec.definition, threshold: r.spec.threshold, source_ref: r.spec.sourceRef,
      falsifier: r.spec.falsifier, status: r.status, raw_status: r.rawStatus,
      red_proof_gate_note: r.gateNote, reason: r.reason, findings: r.findings, detail: r.detail,
    })),
  }, null, 2))
  writeFileSync(join(args.outDir, 'dd1_battery_transcript.txt'), lines.join('\n'))
  log('')
  log(`artifacts: ${args.outDir}`)

  if (fails.length > 0) process.exit(1)
  if (dd1NotImpl.length > 0) process.exit(2)
  process.exit(0)
}

// Only auto-run when this file is the entry script (`npx tsx index.ts`), not
// when imported — the `--no-live` refusal test imports `parseArgs` directly
// and must not trigger a real `main()` run as a side effect of that import.
const isDirectRun = (() => {
  try {
    return import.meta.url === `file://${process.argv[1]}`
  } catch {
    return false
  }
})()

if (isDirectRun) {
  main().catch((err) => {
    console.error('[dd1-battery] fatal:', err)
    process.exit(3)
  })
}
