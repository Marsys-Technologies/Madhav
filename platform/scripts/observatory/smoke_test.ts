/**
 * Observatory MVP smoke test (USTAD_S1_13).
 *
 * MANUAL VERIFICATION TOOL — not part of the CI test suite. Run by hand after
 * deploying the Observatory MVP to verify the end-to-end loop:
 *
 *     observe()  →  llm_usage_events INSERT  →  /api/admin/observatory/summary
 *
 * --------------------------------------------------------------------------
 * Modes
 * --------------------------------------------------------------------------
 *
 *   --dry-run    Print the synthetic ObservedLLMRequest payload that would be
 *                handed to observe(), then exit 0. No DB writes, no HTTP fetch.
 *                Use this to prove the script wiring + tsx compile work
 *                without a running server or DATABASE_URL.
 *
 *   (default)    Full end-to-end run. Required environment:
 *                  DATABASE_URL                    — pg connection string
 *                  MARSYS_FLAG_OBSERVATORY_ENABLED — must be "true"
 *                  SMOKE_BASE_URL                  — e.g. http://localhost:3000
 *                  SMOKE_SESSION_COOKIE            — super-admin Cookie header value
 *                Optional:
 *                  SMOKE_CONVERSATION_ID           — defaults to a fresh uuid
 *                  SMOKE_USER_ID                   — defaults to a fresh uuid
 *
 *                Steps:
 *                  1. Call observe() with a synthetic Anthropic call
 *                     (input_tokens=100, output_tokens=50, claude-opus-4-6).
 *                  2. Wait 200ms.
 *                  3. GET /api/admin/observatory/summary?from=&to= (last 1h).
 *                  4. Assert total_requests >= 1 and total_cost_usd > 0.
 *                  5. Print SMOKE PASS or SMOKE FAIL with detail and exit 0/1.
 *
 * --------------------------------------------------------------------------
 * Run
 * --------------------------------------------------------------------------
 *
 *     # from platform/
 *     npm run observatory:smoke -- --dry-run
 *     npm run observatory:smoke
 */

import { randomUUID } from 'node:crypto'
import { Pool } from 'pg'
import { observe } from '../../src/lib/llm/observability/observe'
import type {
  ObservatoryDb,
  ObservedLLMRequest,
  TokenUsage,
} from '../../src/lib/llm/observability/types'
import { isDirectEntrypoint } from '../lib/entrypoint'

const DRY_RUN = process.argv.includes('--dry-run')

function buildSyntheticRequest(): ObservedLLMRequest {
  return {
    provider: 'anthropic',
    model: 'claude-opus-4-6',
    prompt_text: '[smoke-test] hello world',
    system_prompt: '[smoke-test] system',
    parameters: { max_tokens: 256, temperature: 0.7 },
    conversation_id:
      process.env.SMOKE_CONVERSATION_ID ?? randomUUID(),
    conversation_name: 'smoke-test-001',
    prompt_id: randomUUID(),
    user_id: process.env.SMOKE_USER_ID ?? randomUUID(),
    pipeline_stage: 'classify',
  }
}

const SYNTHETIC_USAGE: TokenUsage = {
  input_tokens: 100,
  output_tokens: 50,
  cache_read_tokens: 0,
  cache_write_tokens: 0,
  reasoning_tokens: 0,
}

async function dryRun(): Promise<void> {
  const req = buildSyntheticRequest()
  const payload = {
    request: req,
    usage_that_would_be_recorded: SYNTHETIC_USAGE,
    note: 'DRY RUN — no DB write, no HTTP call. Use without --dry-run for full smoke.',
  }
  console.log(JSON.stringify(payload, null, 2))
  console.log('SMOKE DRY-RUN OK')
}

interface SummaryShape {
  total_cost_usd: number
  total_requests: number
}

async function fullRun(): Promise<void> {
  const baseUrl = requireEnv('SMOKE_BASE_URL')
  const cookie = requireEnv('SMOKE_SESSION_COOKIE')
  if (process.env.MARSYS_FLAG_OBSERVATORY_ENABLED !== 'true') {
    fail('MARSYS_FLAG_OBSERVATORY_ENABLED must be "true"')
  }
  requireEnv('DATABASE_URL')

  const pool = new Pool({ connectionString: process.env.DATABASE_URL })
  const db: ObservatoryDb = {
    query: async (sql, params) => pool.query(sql, params),
  }

  const req = buildSyntheticRequest()
  const startWindow = new Date(Date.now() - 60 * 60 * 1000).toISOString()

  let observedOk = false
  try {
    const result = await observe(
      req,
      async () => ({
        response: { id: 'smoke', text: 'ok' },
        rawUsage: SYNTHETIC_USAGE,
        providerRequestId: 'smoke-req-' + Date.now(),
      }),
      db,
    )
    observedOk = result.observation !== null
  } catch (err) {
    fail(`observe() threw: ${(err as Error).message}`)
  } finally {
    await pool.end()
  }

  if (!observedOk) {
    fail('observe() returned observation=null — persistObservation likely failed; check server logs')
  }

  await sleep(200)

  const endWindow = new Date(Date.now() + 60 * 1000).toISOString()
  const url = `${baseUrl.replace(/\/$/, '')}/api/admin/observatory/summary?from=${encodeURIComponent(startWindow)}&to=${encodeURIComponent(endWindow)}`

  let res: Response
  try {
    res = await fetch(url, {
      method: 'GET',
      headers: { Accept: 'application/json', Cookie: cookie },
    })
  } catch (err) {
    fail(`fetch ${url} threw: ${(err as Error).message}`)
  }
  if (!res!.ok) {
    fail(`fetch ${url} returned ${res!.status} ${res!.statusText}`)
  }
  const summary = (await res!.json()) as SummaryShape

  if (!(summary.total_requests >= 1)) {
    fail(`expected total_requests >= 1, got ${summary.total_requests}`)
  }
  if (!(summary.total_cost_usd > 0)) {
    fail(`expected total_cost_usd > 0, got ${summary.total_cost_usd}`)
  }

  console.log(
    'SMOKE PASS — total_requests=%d total_cost_usd=%s',
    summary.total_requests,
    summary.total_cost_usd,
  )
}

function requireEnv(key: string): string {
  const v = process.env[key]
  if (!v || v.length === 0) fail(`required env ${key} is not set`)
  return v as string
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms))
}

function fail(msg: string): never {
  console.error(`SMOKE FAIL — ${msg}`)
  process.exit(1)
}

async function main(): Promise<void> {
  if (DRY_RUN) {
    await dryRun()
    return
  }
  await fullRun()
}

if (isDirectEntrypoint(import.meta.url, process.argv[1])) {
  void main().catch((err) => {
    fail(`unhandled error: ${(err as Error).message ?? String(err)}`)
  })
}
