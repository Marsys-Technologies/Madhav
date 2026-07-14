#!/usr/bin/env -S npx tsx
/**
 * run.ts — D-1.5a executable assertion harness (Lane A-0, BRIEF_D1_5A.md).
 *
 * CLI contract (frozen by the brief):
 *   npx tsx platform/scripts/audit/doctrine_harness/run.ts \
 *     --assertions <ids|all> [--wave <w>] [--target <mcp-url>]
 *   → exit 0 all-green / 1 any-red, JSON receipt to stdout
 *     (per-assertion id/green|red/evidence).
 *
 * Every assertion is a live call against the deployed MCP surface
 * (marsys-jis-direct, or the Bearer-token face — CONDUCTOR_PROTOCOL §8.1).
 * This script never reads the database and never fabricates a pass —
 * an assertion that cannot be evaluated reports red with a diagnosis
 * (CLAUDE.md B.10 spirit, applied to the harness itself).
 *
 * Credentials (first match wins):
 *   1. --target already contains `?api_key=...` (the marsys-jis-direct
 *      seat, `~/.claude.json`) — used as-is, no extra header.
 *   2. MARSYS_MCP_API_KEY env — appended to --target/default target as
 *      `?api_key=`.
 *   3. MARSYS_MCP_KEY or MCP_SMOKE_BEARER_TOKEN env — sent as
 *      `Authorization: Bearer <token>` against --target/default target
 *      (protocol §8.1's default reproducible face; `source
 *      scripts/setup_mcp_env.sh` populates MARSYS_MCP_KEY).
 *   Exits with a clear diagnostic (not a silent skip) if none resolve.
 *
 * Exit codes: 0 = all requested assertions green. 1 = at least one red.
 * 2 = usage/config error (bad --assertions id, no credential resolved).
 */
import { McpClient } from './lib/mcp_client'
import { ALL_ASSERTIONS, runAssertion } from './lib/assertions'
import type { AssertionResult, RunContext } from './lib/types'

const ABHISEK_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const DEFAULT_TARGET = 'https://amjis-mcp-qm256lasva-el.a.run.app/mcp'

type Args = {
  assertions: string[] | 'all'
  wave?: string
  target: string
}

function parseArgs(argv: string[]): Args {
  let assertions: string[] | 'all' = 'all'
  let wave: string | undefined
  let target = DEFAULT_TARGET
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]
    if (arg === '--assertions') {
      const val = argv[++i]
      assertions = val === 'all' ? 'all' : val.split(',').map((s) => s.trim())
    } else if (arg === '--wave') {
      wave = argv[++i]
    } else if (arg === '--target') {
      target = argv[++i]
    }
  }
  return { assertions, wave, target }
}

function resolveClient(target: string): McpClient {
  if (target.includes('api_key=')) {
    return new McpClient(target)
  }
  const apiKey = process.env.MARSYS_MCP_API_KEY
  if (apiKey) {
    const sep = target.includes('?') ? '&' : '?'
    return new McpClient(`${target}${sep}api_key=${apiKey}`)
  }
  const bearer = process.env.MARSYS_MCP_KEY || process.env.MCP_SMOKE_BEARER_TOKEN
  if (bearer) {
    return new McpClient(target, bearer)
  }
  console.error(
    JSON.stringify({
      error: 'NO_CREDENTIAL',
      message:
        'No MCP credential resolved. Either pass --target with an embedded ?api_key=..., set MARSYS_MCP_API_KEY, or set MARSYS_MCP_KEY / MCP_SMOKE_BEARER_TOKEN (source scripts/setup_mcp_env.sh).',
    })
  )
  process.exit(2)
}

async function main() {
  const args = parseArgs(process.argv.slice(2))

  let selected = ALL_ASSERTIONS
  if (args.assertions !== 'all') {
    const ids = new Set(args.assertions)
    selected = ALL_ASSERTIONS.filter((a) => ids.has(a.id))
    const unknown = [...ids].filter((id) => !ALL_ASSERTIONS.some((a) => a.id === id))
    if (unknown.length > 0) {
      console.error(JSON.stringify({ error: 'UNKNOWN_ASSERTION_IDS', unknown, known: ALL_ASSERTIONS.map((a) => a.id) }))
      process.exit(2)
    }
  }

  const client = resolveClient(args.target)
  const ctx: RunContext = { client, chartId: ABHISEK_CHART_ID, secondChartId: ABHINANDAN_CHART_ID }

  const results: AssertionResult[] = []
  for (const def of selected) {
    // Sequential execution: keeps evidence deterministic and avoids
    // hammering the deployed connector with a burst of concurrent calls
    // (some assertions already fan out internally, e.g. A5, K.2 §1-5's
    // pagination).
    const result = await runAssertion(def, ctx)
    results.push(result)
  }

  const green = results.filter((r) => r.status === 'green').map((r) => r.id)
  const red = results.filter((r) => r.status === 'red').map((r) => r.id)

  const receipt = {
    harness: 'doctrine_harness',
    wave: args.wave ?? 'D-1.5a',
    target: args.target,
    chart_id: ABHISEK_CHART_ID,
    second_chart_id: ABHINANDAN_CHART_ID,
    run_at: new Date().toISOString(),
    requested: args.assertions === 'all' ? 'all' : args.assertions,
    summary: { total: results.length, green: green.length, red: red.length, green_ids: green, red_ids: red },
    results,
  }

  console.log(JSON.stringify(receipt, null, 2))
  process.exit(red.length > 0 ? 1 : 0)
}

main().catch((err) => {
  console.error('doctrine_harness FATAL:', err)
  process.exit(2)
})
