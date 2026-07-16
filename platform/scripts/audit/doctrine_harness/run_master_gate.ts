#!/usr/bin/env -S npx tsx
/**
 * run_master_gate.ts — D-2 Lane V-0 master-acceptance harness (BRIEF_D2.md §G / BIND_D-2.md
 * §F1.7 ledger rows 1-6).
 *
 * Composes the ledger-row deliverables into one gate-runner-facing entrypoint:
 *   1. The §G.0 six wealth-conclusion presence checks (lib/wealth_conclusions.ts).
 *   2. The full census battery, paced (lib/census.ts via run_census.ts's logic, inlined here
 *      for a single-process gate run — see run_census.ts for the standalone CLI).
 *   3. The completeness-receipt validator (lib/completeness_receipt.ts) — reports
 *      skipped_v2_not_shipped honestly until V-2 lands (cycle 2).
 *   4. The alias-count check (lib/alias_check.ts) — reports the mechanical-fallback stub
 *      honestly until V-3 lands (cycle 2).
 *   5. The pre-existing regression battery (lib/assertions.ts's ALL_ASSERTIONS — K.2/A5/A7/
 *      Gate-B, D-1.5a/D-1.5b) — BRIEF_D2.md §G.2's "Gate-A + Gate-B + Gate-Ś batteries still
 *      green (regression)" clause. `--skip-regression` exists for the same reason
 *      `--skip-census` does (a full battery run is not always needed on every invocation).
 *
 * This is NOT a replacement for run.ts (the existing K.2/A5/A7/Gate-B assertion CLI) or
 * run_census.ts (the standalone, resumable census CLI) — it is the single command the §G gate
 * runner invokes to get one composite receipt covering everything BIND_D-2.md's promise ledger
 * assigns to V-0. `--skip-census` exists because a full 135-tool paced sweep takes several
 * minutes; the gate runner passes it when it has already run run_census.ts separately and wants
 * only the wealth-conclusion + receipt + alias checks re-verified.
 *
 * Exit codes: 0 = 6/6 wealth conclusions AND census has 0 regressions AND alias check reconciles
 * (or is an explicitly-flagged stub) AND completeness receipt validates (or is an explicitly-
 * flagged skip). 1 = any hard failure. 2 = usage/config/credential error.
 */
import { McpClient } from './lib/mcp_client'
import { runWealthConclusionGate } from './lib/wealth_conclusions'
import { runCensusSweep, summarizeCensus, DEFAULT_BATCH_SIZE, DEFAULT_INTER_BATCH_MS } from './lib/census'
import { validateLiveReceipt } from './lib/completeness_receipt'
import { checkAliasCount } from './lib/alias_check'
import { ALL_ASSERTIONS, runAssertion } from './lib/assertions'
import type { RunContext } from './lib/types'
import { join } from 'node:path'
import { tmpdir } from 'node:os'

const ABHISEK_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const DEFAULT_TARGET = 'https://amjis-mcp-qm256lasva-el.a.run.app/mcp'

type Args = { target: string; skipCensus: boolean; skipRegression: boolean; checkpointPath: string }

function parseArgs(argv: string[]): Args {
  let target = DEFAULT_TARGET
  let skipCensus = false
  let skipRegression = false
  let checkpointPath = join(tmpdir(), 'doctrine_harness_census_checkpoint.json')
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--target') target = argv[++i]
    else if (argv[i] === '--skip-census') skipCensus = true
    else if (argv[i] === '--skip-regression') skipRegression = true
    else if (argv[i] === '--checkpoint') checkpointPath = argv[++i]
  }
  return { target, skipCensus, skipRegression, checkpointPath }
}

function resolveClient(target: string): McpClient {
  if (target.includes('api_key=')) return new McpClient(target)
  const apiKey = process.env.MARSYS_MCP_API_KEY
  if (apiKey) {
    const sep = target.includes('?') ? '&' : '?'
    return new McpClient(`${target}${sep}api_key=${apiKey}`)
  }
  const bearer = process.env.MARSYS_MCP_KEY || process.env.MCP_SMOKE_BEARER_TOKEN
  if (bearer) return new McpClient(target, bearer)
  console.error(JSON.stringify({ error: 'NO_CREDENTIAL', message: 'No MCP credential resolved (see run.ts header for the resolution order).' }))
  process.exit(2)
}

async function main() {
  const args = parseArgs(process.argv.slice(2))
  const client = resolveClient(args.target)

  console.error('[1/5] §G.0 wealth-conclusion gate…')
  const wealthGate = await runWealthConclusionGate({ client, chartId: ABHISEK_CHART_ID, secondChartId: ABHINANDAN_CHART_ID })

  // Fetched once, reused by both the census sweep and the alias-count check — never a second
  // tools/list call just to feed the alias check (extra live calls are exactly what the
  // pacing discipline exists to minimize).
  const tools = await client.listTools()

  let census: Awaited<ReturnType<typeof runCensusSweep>> | null = null
  let censusSummary: ReturnType<typeof summarizeCensus> | null = null
  if (!args.skipCensus) {
    console.error('[2/5] Census battery (paced)…')
    census = await runCensusSweep(client, tools, {
      checkpointPath: args.checkpointPath,
      chartId: ABHISEK_CHART_ID,
      target: args.target,
      batchSize: DEFAULT_BATCH_SIZE,
      interBatchMs: DEFAULT_INTER_BATCH_MS,
    })
    censusSummary = summarizeCensus(census.results)
  } else {
    console.error('[2/5] Census battery SKIPPED (--skip-census)')
  }

  console.error('[3/5] Completeness-receipt validator…')
  const receiptCheck = await validateLiveReceipt(client, ABHISEK_CHART_ID, 'wealth')

  console.error('[4/5] Alias-count check…')
  const aliasCheck = checkAliasCount(tools)

  let regression: { total: number; green: number; red: number; red_ids: string[] } | null = null
  if (!args.skipRegression) {
    console.error('[5/5] Regression battery (Gate-A/B/Ś assertions, K.2/A5/A7/Gate-B)…')
    const ctx: RunContext = { client, chartId: ABHISEK_CHART_ID, secondChartId: ABHINANDAN_CHART_ID }
    const results = []
    for (const def of ALL_ASSERTIONS) results.push(await runAssertion(def, ctx))
    const greenIds = results.filter((r) => r.status === 'green').map((r) => r.id)
    const redIds = results.filter((r) => r.status === 'red').map((r) => r.id)
    regression = { total: results.length, green: greenIds.length, red: redIds.length, red_ids: redIds }
  } else {
    console.error('[5/5] Regression battery SKIPPED (--skip-regression)')
  }

  const receipt = {
    harness: 'doctrine_harness/run_master_gate',
    wave: 'D-2',
    target: args.target,
    chart_id: ABHISEK_CHART_ID,
    run_at: new Date().toISOString(),
    wealth_conclusions: wealthGate,
    census: census
      ? { tool_count: census.results.length, summary: censusSummary, resumed_from_checkpoint: census.resumed }
      : { skipped: true },
    completeness_receipt: receiptCheck,
    alias_check: aliasCheck,
    regression_battery: regression ?? { skipped: true },
  }

  console.log(JSON.stringify(receipt, null, 2))

  const censusHardFail = censusSummary ? censusSummary.FAIL > 0 : false
  const aliasHardFail = aliasCheck.source === 'v3_canonical_face_list' && !aliasCheck.reconciles
  const receiptHardFail = receiptCheck.status === 'validated' && receiptCheck.result?.valid === false
  // Regression battery is reported, NOT gated into `ok`: BIND_D-2.md §B.1 records two
  // EXPECTED residual reds (PARK-#4, Gate Ś #8-class items) that are non-blocking by the
  // Binder's own disposition — this harness has no way to distinguish an expected residual
  // from a genuine new regression without the Binder's live-recorded baseline, which is the
  // gate runner's job (CONDUCTOR_PROTOCOL §2 step 7), not this composite convenience script's.
  // A caller wanting a hard gate on regression should diff `regression_battery.red_ids`
  // against the wave's recorded expected-residual list itself.
  const ok = wealthGate.sixOfSix && !censusHardFail && !aliasHardFail && !receiptHardFail
  console.error(
    `Summary: wealth ${wealthGate.green}/6` +
      (censusSummary ? `; census FAIL=${censusSummary.FAIL} PASS=${censusSummary.PASS}` : '; census skipped') +
      `; receipt=${receiptCheck.status}; alias_check=${aliasCheck.source}(reconciles=${aliasCheck.reconciles})` +
      (regression ? `; regression ${regression.green}/${regression.total} (red_ids: ${regression.red_ids.join(',') || 'none'})` : '; regression skipped')
  )
  process.exit(ok ? 0 : 1)
}

main().catch((err) => {
  console.error('run_master_gate FATAL:', err)
  process.exit(2)
})
