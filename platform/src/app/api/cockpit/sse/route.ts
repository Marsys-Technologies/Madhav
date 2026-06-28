import { NextRequest } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

const GOOGLE_CLOUD_PROJECT = process.env.GOOGLE_CLOUD_PROJECT ?? 'madhav-astrology'
const PUBSUB_TOPIC = process.env.PUBSUB_TOPIC ?? 'cockpit-events'

/** Whether Pub/Sub is available (topic env set and not explicitly disabled). */
function pubsubEnabled(): boolean {
  return !process.env.PUBSUB_DISABLED && !!process.env.GOOGLE_CLOUD_PROJECT
}

export async function GET(req: NextRequest) {
  const user = await getServerUser()
  if (!user) return new Response('Forbidden', { status: 403 })

  const chartId = req.nextUrl.searchParams.get('chart_id')
  if (!chartId) return new Response('chart_id required', { status: 400 })

  const encoder = new TextEncoder()

  if (pubsubEnabled()) {
    return pubsubStream(req, chartId, encoder)
  }
  return pollingStream(req, chartId, encoder)
}

/**
 * Pub/Sub-backed SSE — creates an ephemeral subscription filtered to chart_id,
 * forwards messages as SSE data frames, cleans up on disconnect.
 *
 * Subscription creation is attempted BEFORE the stream opens so that a failure
 * can fall back to pollingStream immediately (no dead heartbeat-only state).
 */
async function pubsubStream(
  req: NextRequest,
  chartId: string,
  encoder: TextEncoder,
): Promise<Response> {
  // Dynamic import keeps the bundle clean when pubsub is disabled.
  const { PubSub } = await import('@google-cloud/pubsub')
  const client = new PubSub({ projectId: GOOGLE_CLOUD_PROJECT })

  // Unique ephemeral subscription per request (hostname + timestamp + random suffix)
  const hostname = process.env.HOSTNAME ?? 'local'
  const suffix = Math.random().toString(36).slice(2, 8)
  const subName = `cockpit-sse-${hostname}-${Date.now()}-${suffix}`

  // Create subscription before opening the stream so a failure falls back cleanly.
  let sub: ReturnType<typeof client.subscription>
  try {
    const topic = client.topic(PUBSUB_TOPIC)
    const [created] = await topic.createSubscription(subName, {
      expirationPolicy: { ttl: { seconds: 86400 } },
      filter: `attributes.chart_id = "${chartId}"`,
      messageRetentionDuration: { seconds: 600 },
    })
    sub = created
  } catch (err) {
    console.error(
      '[sse/PUBSUB_FALLBACK] Pub/Sub subscription creation failed — falling back to 5s pollingStream.' +
      ' Check GOOGLE_CLOUD_PROJECT + PUBSUB_TOPIC env. Error:', (err as Error).message
    )
    return pollingStream(req, chartId, encoder)
  }

  const stream = new ReadableStream({
    start(controller) {
      const enqueue = (data: string) => {
        try { controller.enqueue(encoder.encode(data)) } catch { /* closed */ }
      }

      // Named hello event so the client addEventListener('hello') handler fires
      enqueue(`event: hello\ndata: ${JSON.stringify({ connected: true, chart_id: chartId })}\n\n`)

      const heartbeat = setInterval(() => enqueue(`: hb\n\n`), 30_000)

      sub.on('message', (message) => {
        try {
          const raw = message.data.toString()
          // Pub/Sub messages are expected to carry a `type` field matching the
          // SSE event name (e.g. "asset.state_change", "run.state_change").
          // Parse the payload to extract the type so we can set the event: line.
          let eventType = 'message'
          try {
            const parsed = JSON.parse(raw) as { type?: string }
            if (parsed?.type) eventType = parsed.type
          } catch { /* not JSON — fall through with generic 'message' */ }
          enqueue(`event: ${eventType}\ndata: ${raw}\n\n`)
          message.ack()
        } catch {
          message.nack()
        }
      })

      sub.on('error', (err) => {
        console.error('[sse] pubsub error:', err.message)
      })

      req.signal.addEventListener('abort', async () => {
        clearInterval(heartbeat)
        sub.removeAllListeners()
        await sub.delete().catch(() => {})
        try { controller.close() } catch { /* already closed */ }
      })
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
  })
}

const TERMINAL_STATES = new Set(['completed', 'failed', 'stopped'])
const ACTIVE_STATES = new Set(['planned', 'running', 'paused'])

/**
 * Fallback: heartbeat + run-state poll used when Pub/Sub is disabled.
 * Polls build_runs every 5s (matching the active-build client poll cadence)
 * and emits a synthetic run.state_change frame when the run reaches a
 * terminal state — so DataAssetsView's completion-triggered refetchStats()
 * fires within ~5s even without Pub/Sub (C1-Step1).
 */
function pollingStream(
  req: NextRequest,
  chartId: string,
  encoder: TextEncoder,
): Response {
  const stream = new ReadableStream({
    start(controller) {
      const enqueue = (data: string) => {
        try { controller.enqueue(encoder.encode(data)) } catch { /* closed */ }
      }

      // Named hello event so the client addEventListener('hello') handler fires
      enqueue(`event: hello\ndata: ${JSON.stringify({ connected: true, chart_id: chartId })}\n\n`)

      let lastRunId: string | null = null
      let lastState: string | null = null
      // Track per-asset rows_written so we only emit asset.progress when the count changes
      const lastRowsWritten = new Map<string, number>()

      const pollRun = async () => {
        try {
          const { rows } = await query<{ id: string; state: string }>(
            // Index: build_runs_chart_state_planned_idx covers planned/running/paused
            // See migration NNN_fix_build_runs_active_index.sql
            `SELECT id, state FROM build_runs
              WHERE chart_id=$1
              ORDER BY created_at DESC LIMIT 1`,
            [chartId]
          )
          const row = rows[0] ?? null
          const runId = row?.id ?? null
          const state = row?.state ?? null

          // Track same run across polls so a new run doesn't look like completion
          if (runId !== lastRunId) {
            lastRunId = runId
            lastState = state
            lastRowsWritten.clear()
            return
          }

          // Emit run.state_change when an active run reaches a terminal state
          if (lastState && ACTIVE_STATES.has(lastState) && state && TERMINAL_STATES.has(state)) {
            enqueue(`event: run.state_change\ndata: ${JSON.stringify({ type: 'run.state_change', run_id: runId, state, chart_id: chartId })}\n\n`)
            lastRowsWritten.clear()
          }
          lastState = state

          // Emit synthetic asset.progress events for all building assets so the
          // progress bar animates continuously without Pub/Sub. Only fires when the
          // chart has an active run to avoid unnecessary DB reads at idle.
          if (state && ACTIVE_STATES.has(state)) {
            try {
              const { rows: buildingRows } = await query<{ asset_id: string; rows_written: number | null }>(
                `SELECT asset_id, rows_written
                   FROM asset_throughput
                  WHERE chart_id=$1 AND state='building'
                  ORDER BY asset_id`,
                [chartId]
              )
              for (const r of buildingRows) {
                if (r.rows_written == null) continue
                const prev = lastRowsWritten.get(r.asset_id)
                if (prev !== r.rows_written) {
                  lastRowsWritten.set(r.asset_id, r.rows_written)
                  enqueue(`event: asset.progress\ndata: ${JSON.stringify({ type: 'asset.progress', asset_id: r.asset_id, rows_written: r.rows_written, chart_id: chartId })}\n\n`)
                }
              }
            } catch { /* skip progress tick on db error */ }
          }
        } catch {
          // db error — skip this tick
        }
      }

      const heartbeat = setInterval(() => enqueue(`: hb\n\n`), 30_000)
      const poll = setInterval(pollRun, 2_000)
      // Prime on first connect so we know the current run id
      pollRun()

      req.signal.addEventListener('abort', () => {
        clearInterval(heartbeat)
        clearInterval(poll)
        try { controller.close() } catch { /* already closed */ }
      })
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
  })
}
