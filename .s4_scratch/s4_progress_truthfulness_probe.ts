/**
 * S4 synergy #5 (Progress truthfulness) — LIVE probe.
 *
 * Calls the REAL platform-side prashna_ask engine route
 * (platform/src/app/api/mcp/prashna_ask/route.ts) DIRECTLY IN-PROCESS
 * (import + invoke POST(request) — no network hop, no separate server needed;
 * this process controls its own env, including MCP_INTERNAL_TOKEN, before any
 * platform module is imported, which is why we don't need to touch the
 * already-running `next dev` process on :3000).
 *
 * We then feed the REAL NDJSON progress/final lines through the EXACT SAME
 * downstream logic register_prashna_ask.ts + job_registry.ts + register_
 * prashna_status.ts use (copied verbatim from those files below), so what we
 * print is exactly what an MCP caller polling prashna_status would see —
 * real DB, real tool dispatch, real LLM synthesis call, real synthetic chart
 * 1c826d5a-41cb-4450-b4dc-59d440e5f75a, real progress events. The only thing
 * skipped is the platform-mcp HTTP relay hop, which per prashna_ask_bridge.ts's
 * own header is "ONLY the HTTP call to that route" — no data transformation.
 */
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

// Minimal .env.local loader (no dotenv dep in this repo) — same file the
// running `next dev` process on :3000 already loads; we just need it in THIS
// fresh node process too, since we import platform route code directly.
function loadEnvLocal(path: string) {
  const text = readFileSync(path, 'utf8')
  for (const rawLine of text.split('\n')) {
    const line = rawLine.trim()
    if (!line || line.startsWith('#')) continue
    const eq = line.indexOf('=')
    if (eq === -1) continue
    const key = line.slice(0, eq).trim()
    let value = line.slice(eq + 1).trim()
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1)
    }
    if (process.env[key] === undefined) process.env[key] = value
  }
}
loadEnvLocal(join(__dirname, '..', 'platform', '.env.local'))

process.env.MCP_INTERNAL_TOKEN = 'probe-internal-token-s4'

const SYNTH_CHART = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const OWNER_UID = 'xl2wYZRPwsVgPSAgtn9XJ80Xkub2' // from s2_latency_probe.ts, confirmed owner of synthetic chart

// ---- verbatim copies of the client-facing formatting logic under test ----
// (register_prashna_ask.ts's estimateProgressPct + progress message format,
// job_registry.ts's JobRegistry, register_prashna_status.ts's elapsed_ms calc)

interface ProgressEvent {
  tools_dispatched_count: number
  cap_ceiling: { maxCalls: number; maxWallClockMs: number }
  elapsed_ms: number
  last_tool: string
}

function estimateProgressPct(progress: ProgressEvent): number {
  const wallClockRatio = progress.elapsed_ms / Math.max(1, progress.cap_ceiling.maxWallClockMs)
  const callCountRatio = progress.tools_dispatched_count / Math.max(1, progress.cap_ceiling.maxCalls)
  const pct = Math.round(Math.max(wallClockRatio, callCountRatio) * 100)
  return Math.min(99, Math.max(0, pct))
}

interface JobProgress { message: string; pct: number }
let jobProgress: JobProgress | undefined
let jobStatus: 'pending' | 'running' | 'complete' | 'failed' = 'pending'
const jobCreatedAt = Date.now()

function updateProgress(p: JobProgress) {
  jobStatus = 'running'
  jobProgress = p
}

async function main() {
  const { POST } = await import('../platform/src/app/api/mcp/prashna_ask/route')

  const body = JSON.stringify({
    chart_id: SYNTH_CHART,
    question:
      'Give me a deep, comprehensive reading of my career prospects, wealth potential, and major life themes across all houses, drawing on dasha timing, yogas, and divisional charts.',
  })

  const req = new Request('http://internal/api/mcp/prashna_ask', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': 'probe-internal-token-s4',
      'X-MCP-User': OWNER_UID,
      'X-MCP-Key-Id': 's4-probe-key',
    },
    body,
  })

  const turnStart = Date.now()
  console.log(`[t=0ms] POST /api/mcp/prashna_ask sent (chart=${SYNTH_CHART})`)

  const res = await POST(req)
  console.log(`[t=${Date.now() - turnStart}ms] response headers received, status=${res.status}`)

  if (!res.body) {
    const text = await res.text()
    console.log('NO STREAM BODY — plain response:', text.slice(0, 2000))
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const processLine = (raw: string) => {
    const line = raw.trim()
    if (!line) return
    const t = Date.now() - turnStart
    let parsed: Record<string, unknown>
    try {
      parsed = JSON.parse(line)
    } catch {
      console.log(`[t=${t}ms] UNPARSEABLE LINE: ${line.slice(0, 200)}`)
      return
    }
    if (parsed['event'] === 'progress') {
      const progress = parsed as unknown as ProgressEvent
      const elapsedSec = (progress.elapsed_ms / 1000).toFixed(1)
      const message =
        `${progress.tools_dispatched_count}/~${progress.cap_ceiling.maxCalls} tool calls made, ` +
        `${elapsedSec}s elapsed`
      const pct = estimateProgressPct(progress)
      updateProgress({ message, pct })
      // What prashna_status would ALSO show at this instant (live top-level elapsed_ms):
      const statusElapsedMs = Date.now() - jobCreatedAt
      console.log(
        `[t=${t}ms] PROGRESS EVENT last_tool=${progress.last_tool} tools=${progress.tools_dispatched_count} ` +
          `raw_elapsed_ms=${progress.elapsed_ms} => job.progress={message:"${message}", pct:${pct}} ` +
          `| prashna_status.elapsed_ms(live)=${statusElapsedMs}`,
      )
    } else if (parsed['event'] === 'final') {
      jobStatus = 'complete'
      console.log(
        `[t=${t}ms] FINAL EVENT reading_len=${typeof parsed['reading'] === 'string' ? (parsed['reading'] as string).length : 'null'} ` +
          `completeness=${JSON.stringify(parsed['completeness'])} judgment_flags=${JSON.stringify(parsed['judgment_flags'])}`,
      )
    } else if (parsed['event'] === 'error') {
      console.log(`[t=${t}ms] ERROR EVENT: ${JSON.stringify(parsed)}`)
    } else {
      console.log(`[t=${t}ms] NON-STREAM (early-return) BODY: ${JSON.stringify(parsed).slice(0, 1000)}`)
    }
  }

  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let idx: number
    while ((idx = buffer.indexOf('\n')) >= 0) {
      processLine(buffer.slice(0, idx))
      buffer = buffer.slice(idx + 1)
    }
  }
  buffer += decoder.decode()
  if (buffer.trim()) processLine(buffer)

  console.log(`[t=${Date.now() - turnStart}ms] STREAM DONE. Final job snapshot: status=${jobStatus} progress=${JSON.stringify(jobProgress)}`)
}

main().catch((err) => {
  console.error('PROBE FAILED:', err)
  process.exit(1)
})
