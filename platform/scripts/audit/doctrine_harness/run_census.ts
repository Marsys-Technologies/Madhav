#!/usr/bin/env -S npx tsx
/**
 * run_census.ts — D-2 Lane V-0 census battery CLI (BIND_D-2.md §F1.7 ledger row 2/5).
 *
 * Sweeps every tool the deployed connector's `tools/list` reports (135 at BIND_D-2.md §B.5,
 * superseding the ~126 planning figure) recording PASS/DEGRADED/EMPTY/FAIL/SKIPPED/
 * TRANSPORT_ERROR + byte size per tool, paced per lib/census.ts's proactive-pacing rules
 * (<=17-call batches, inter-batch throttle, per-batch checkpointing so an interrupted sweep
 * resumes rather than restarts).
 *
 * Usage:
 *   npx tsx platform/scripts/audit/doctrine_harness/run_census.ts \
 *     [--target <mcp-url>] [--checkpoint <path>] [--batch-size 17] [--inter-batch-ms 3000] \
 *     [--baseline <path-to-prior-receipt.json>]
 *
 * Credential resolution identical to run.ts (see its header comment): --target embedded
 * ?api_key=, else MARSYS_MCP_API_KEY, else MARSYS_MCP_KEY/MCP_SMOKE_BEARER_TOKEN as Bearer.
 *
 * Exit codes: 0 = sweep completed with 0 FAIL and 0 unexplained-empty rows beyond baseline;
 * 1 = regressions found (FAIL count increased vs --baseline, or any new FAIL with no baseline);
 * 2 = usage/config/credential error.
 */
import { McpClient } from './lib/mcp_client'
import { runCensusSweep, summarizeCensus, DEFAULT_BATCH_SIZE, DEFAULT_INTER_BATCH_MS, type CensusToolResult } from './lib/census'
import { readFileSync, existsSync } from 'node:fs'
import { join } from 'node:path'
import { tmpdir } from 'node:os'

const ABHISEK_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const DEFAULT_TARGET = 'https://amjis-mcp-qm256lasva-el.a.run.app/mcp'
// Default checkpoint lives OUTSIDE the repo (os.tmpdir()) — a census checkpoint is a run-scoped
// resumption artifact, never a committed file; --checkpoint overrides for CI/gate-runner use
// where a stable, explicitly-managed path is wanted.
const DEFAULT_CHECKPOINT = join(tmpdir(), 'doctrine_harness_census_checkpoint.json')

type Args = {
  target: string
  checkpointPath: string
  batchSize: number
  interBatchMs: number
  baselinePath?: string
}

function parseArgs(argv: string[]): Args {
  let target = DEFAULT_TARGET
  let checkpointPath = DEFAULT_CHECKPOINT
  let batchSize = DEFAULT_BATCH_SIZE
  let interBatchMs = DEFAULT_INTER_BATCH_MS
  let baselinePath: string | undefined
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]
    if (arg === '--target') target = argv[++i]
    else if (arg === '--checkpoint') checkpointPath = argv[++i]
    else if (arg === '--batch-size') batchSize = Number(argv[++i])
    else if (arg === '--inter-batch-ms') interBatchMs = Number(argv[++i])
    else if (arg === '--baseline') baselinePath = argv[++i]
  }
  return { target, checkpointPath, batchSize, interBatchMs, baselinePath }
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
  console.error(
    JSON.stringify({
      error: 'NO_CREDENTIAL',
      message:
        'No MCP credential resolved. Either pass --target with an embedded ?api_key=..., set MARSYS_MCP_API_KEY, or set MARSYS_MCP_KEY / MCP_SMOKE_BEARER_TOKEN (source scripts/setup_mcp_env.sh).',
    })
  )
  process.exit(2)
}

type Baseline = { summary: Record<string, number>; results: CensusToolResult[] }

function loadBaseline(path: string | undefined): Baseline | null {
  if (!path || !existsSync(path)) return null
  try {
    return JSON.parse(readFileSync(path, 'utf8')) as Baseline
  } catch {
    return null
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2))
  const client = resolveClient(args.target)

  const tools = await client.listTools()
  const { results, resumed } = await runCensusSweep(client, tools, {
    checkpointPath: args.checkpointPath,
    chartId: ABHISEK_CHART_ID,
    target: args.target,
    batchSize: args.batchSize,
    interBatchMs: args.interBatchMs,
  })

  const summary = summarizeCensus(results)
  const baseline = loadBaseline(args.baselinePath)

  const failNames = results.filter((r) => r.status === 'FAIL').map((r) => r.tool)
  const baselineFailNames = new Set((baseline?.results ?? []).filter((r) => r.status === 'FAIL').map((r) => r.tool))
  const newFails = failNames.filter((n) => !baselineFailNames.has(n))

  const receipt = {
    harness: 'doctrine_harness/census',
    wave: 'D-2',
    target: args.target,
    chart_id: ABHISEK_CHART_ID,
    run_at: new Date().toISOString(),
    resumed_from_checkpoint: resumed,
    tool_count: tools.length,
    summary,
    new_fails_vs_baseline: newFails,
    results,
  }

  console.log(JSON.stringify(receipt, null, 2))
  console.error(`Census: ${tools.length} tools; PASS=${summary.PASS} DEGRADED=${summary.DEGRADED} EMPTY=${summary.EMPTY} FAIL=${summary.FAIL} SKIPPED=${summary.SKIPPED} TRANSPORT_ERROR=${summary.TRANSPORT_ERROR}`)

  if (newFails.length > 0) {
    console.error(`REGRESSION: ${newFails.length} new FAIL(s) vs baseline: ${newFails.join(', ')}`)
    process.exit(1)
  }
  process.exit(0)
}

main().catch((err) => {
  console.error('census FATAL:', err)
  process.exit(2)
})
