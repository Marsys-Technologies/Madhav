import { NextRequest } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

async function isSuperAdmin(uid: string): Promise<boolean> {
  const { rows } = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [uid])
  return rows[0]?.role === 'super_admin'
}

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
  if (!(await isSuperAdmin(user.uid))) return new Response('Forbidden', { status: 403 })

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

  let subRef: ReturnType<typeof client.subscription> | null = null

  const stream = new ReadableStream({
    async start(controller) {
      const enqueue = (data: string) => {
        try { controller.enqueue(encoder.encode(data)) } catch { /* closed */ }
      }

      enqueue(`: hello ${chartId}\n\n`)

      const heartbeat = setInterval(() => enqueue(`: hb\n\n`), 30_000)

      try {
        const topic = client.topic(PUBSUB_TOPIC)
        const [sub] = await topic.createSubscription(subName, {
          expirationPolicy: { ttl: { seconds: 86400 } },
          filter: `attributes.chart_id = "${chartId}"`,
          messageRetentionDuration: { seconds: 600 },
        })
        subRef = sub

        sub.on('message', (message) => {
          try {
            enqueue(`data: ${message.data.toString()}\n\n`)
            message.ack()
          } catch {
            message.nack()
          }
        })

        sub.on('error', (err) => {
          console.error('[sse] pubsub error:', err.message)
        })
      } catch (err) {
        console.error(
          '[sse/PUBSUB_FALLBACK] Pub/Sub subscription failed — degrading to heartbeat-only mode.' +
          ' Build events will NOT stream in real-time; run-completion detection falls back to the' +
          ' 5s active-run poll in pollingStream. Check GOOGLE_CLOUD_PROJECT + PUBSUB_TOPIC env.' +
          ' Error:', (err as Error).message
        )
        // pollingStream handles completion detection without Pub/Sub (C1-Step1)
      }

      req.signal.addEventListener('abort', async () => {
        clearInterval(heartbeat)
        if (subRef) {
          subRef.removeAllListeners()
          await subRef.delete().catch(() => {})
        }
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

      enqueue(`data: ${JSON.stringify({ type: 'hello', chart_id: chartId })}\n\n`)

      let lastRunId: string | null = null
      let lastState: string | null = null

      const pollRun = async () => {
        try {
          const { rows } = await query<{ id: string; state: string }>(
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
            return
          }

          // Emit run.state_change when an active run reaches a terminal state
          if (lastState && ACTIVE_STATES.has(lastState) && state && TERMINAL_STATES.has(state)) {
            enqueue(`data: ${JSON.stringify({ type: 'run.state_change', run_id: runId, state, chart_id: chartId })}\n\n`)
          }
          lastState = state
        } catch {
          // db error — skip this tick
        }
      }

      const heartbeat = setInterval(() => enqueue(`: hb\n\n`), 30_000)
      const poll = setInterval(pollRun, 5_000)
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
