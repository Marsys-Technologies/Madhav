import { createHash } from 'node:crypto'
import { NextRequest } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { requireChartPermission } from '@/lib/auth/requireChartPermission'

export const dynamic = 'force-dynamic'

const GOOGLE_CLOUD_PROJECT = process.env.GOOGLE_CLOUD_PROJECT ?? 'madhav-astrology'
const PUBSUB_TOPIC = process.env.PUBSUB_TOPIC ?? 'cockpit-events'
// Finish below Firebase Hosting's documented 60s ceiling, even when a proxy
// does not propagate client disconnect. This bounds the application session,
// not remote resource existence after an ambiguous provider RPC outcome.
const SESSION_BUDGET_MS = 35_000
const CLOCK_SKEW_MS = 5_000
const RPC_TIMEOUT_MS = 5_000
// 20s nominal forwarding + 5s skew + at most 10s cleanup waiting = 35s.
const SESSION_DURATION_MS = SESSION_BUDGET_MS - CLOCK_SKEW_MS - 2 * RPC_TIMEOUT_MS
const RPC_OPTIONS = { timeout: RPC_TIMEOUT_MS, retry: null, maxRetries: 0 }
type Session = { deadline: number; subscriptionName: string }

/** Whether Pub/Sub is available (topic env set and not explicitly disabled). */
function pubsubEnabled(): boolean {
  return !process.env.PUBSUB_DISABLED && !!process.env.GOOGLE_CLOUD_PROJECT
}

function sseResponse(body: ReadableStream<Uint8Array> | null): Response {
  return new Response(body, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
  })
}

export async function GET(req: NextRequest) {
  const user = await getServerUser()
  if (!user) return new Response('Forbidden', { status: 403 })

  const chartId = req.nextUrl.searchParams.get('chart_id')
  if (!chartId) return new Response('chart_id required', { status: 400 })

  // V3-E-011: chart-level authz gate before opening any stream — the route
  // used to check only "is anyone logged in", letting any authenticated user
  // open a live SSE stream on an arbitrary chart_id and receive real-time
  // run.state_change / asset.progress events (including rows_written)
  // indefinitely. Placed before the pubsub/polling branch so neither stream
  // implementation can open without it.
  const denied = await requireChartPermission({ uid: user.uid, chartId, access: 'read' })
  if (denied) return denied
  if (req.signal.aborted) return sseResponse(null)

  const sessionId = req.nextUrl.searchParams.get('session_id')
  const started = Number(req.nextUrl.searchParams.get('session_started_at'))
  const now = Date.now()
  if (!sessionId || !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(sessionId)
      || !Number.isSafeInteger(started) || started <= 0 || started > now + CLOCK_SKEW_MS) {
    return new Response('A current stream session_id and session_started_at are required', { status: 400 })
  }
  // 204 tells native EventSource to stop retrying this expired URL. A live
  // consumer explicitly creates a new session; a proxy retry cannot allocate.
  if (now >= started + SESSION_DURATION_MS) return new Response(null, { status: 204 })
  const session: Session = {
    deadline: started + SESSION_DURATION_MS,
    subscriptionName: `cockpit-sse-${createHash('sha256').update(JSON.stringify([user.uid, chartId, sessionId])).digest('hex')}`,
  }
  const encoder = new TextEncoder()

  if (pubsubEnabled()) {
    return pubsubStream(req, chartId, encoder, session)
  }
  return pollingStream(req, chartId, encoder, session)
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
  session: Session,
): Promise<Response> {
  // Dynamic import keeps the bundle clean when pubsub is disabled.
  const { PubSub } = await import('@google-cloud/pubsub')
  if (req.signal.aborted || Date.now() >= session.deadline) return sseResponse(null)
  const client = new PubSub({ projectId: GOOGLE_CLOUD_PROJECT })

  const subName = session.subscriptionName

  let sub: ReturnType<typeof client.subscription> | undefined
  let controller: ReadableStreamDefaultController<Uint8Array> | undefined
  let heartbeat: ReturnType<typeof setInterval> | undefined
  let creating = true
  let closed = false
  let cleanupPromise: Promise<void> | undefined
  let expire!: () => void
  const expired = new Promise<undefined>(resolve => { expire = () => resolve(undefined) })
  const deadline = setTimeout(() => {
    closed = true
    expire()
    if (!creating) void cleanup(false)
  }, Math.max(0, session.deadline - Date.now()))

  async function boundedCleanup(action: () => Promise<unknown>, label: string): Promise<void> {
    let timer: ReturnType<typeof setTimeout> | undefined
    try {
      await Promise.race([
        action(),
        new Promise<never>((_, reject) => {
          timer = setTimeout(() => reject(new Error('cleanup deadline; remote outcome unverified')), RPC_TIMEOUT_MS)
        }),
      ])
    } catch (err) {
      if (label !== 'subscription delete' || (err as { code?: number }).code !== 5) {
        console.error(`[sse] ${label} failed:`, subName, (err as Error).message)
      }
    } finally {
      if (timer !== undefined) clearTimeout(timer)
    }
  }

  const cleanup = (finishBodyImmediately = true): Promise<void> => {
    closed = true
    if (heartbeat) clearInterval(heartbeat)
    clearTimeout(deadline)
    req.signal.removeEventListener('abort', onAbort)
    // An observed disconnect closes immediately. On NORMAL expiry keep the
    // response alive through bounded cleanup, so request-billed CPU remains
    // available for deletion. A disconnected/throttled instance still needs
    // independent operator verification; a JS timer is not a provider TTL.
    if (finishBodyImmediately) {
      try { controller?.close() } catch { /* already canceled/closed */ }
    }
    cleanupPromise ??= (async () => {
      if (sub) {
        try { sub.removeAllListeners() } catch (err) {
          console.error('[sse] subscription listener cleanup failed:', subName, (err as Error).message)
        }
        // Start both operations independently: subscriber shutdown cannot hold
        // deletion hostage. JS deadlines bound waiting, not remote RPC outcomes.
        await Promise.all([
          (async () => {
            // Keep the atomic name reserved until this URL expires. Deleting
            // earlier would let an intermediary replay allocate it again on
            // another instance. Body/subscriber close immediately; deletion is
            // deliberately deferred only to this fixed session deadline.
            const remaining = session.deadline - Date.now()
            if (remaining > 0) await new Promise<void>(resolve => setTimeout(resolve, remaining))
            await boundedCleanup(() => sub!.delete(RPC_OPTIONS), 'subscription delete')
          })(),
          boundedCleanup(() => sub!.close(), 'subscription close'),
        ])
      }
      await boundedCleanup(() => client.close(), 'client close')
      try { controller?.close() } catch { /* already canceled/closed */ }
    })()
    return cleanupPromise
  }

  function onAbort() {
    closed = true
    // A pending create may still succeed. Its settlement owns cleanup, so a
    // late subscription cannot escape an earlier, already-finished cleanup.
    if (!creating) void cleanup()
  }
  req.signal.addEventListener('abort', onAbort, { once: true })

  // Create subscription before opening the stream so an active failure falls back cleanly.
  try {
    if (req.signal.aborted) {
      creating = false
      await cleanup()
      return sseResponse(null)
    }
    const topic = client.topic(PUBSUB_TOPIC)
    const creation = topic.createSubscription(subName, {
      expirationPolicy: { ttl: { seconds: 86400 } },
      filter: `attributes.chart_id = "${chartId}"`,
      messageRetentionDuration: { seconds: 600 },
      gaxOpts: RPC_OPTIONS,
    }).then(([created]) => {
      sub = created
      creating = false
      if (closed || req.signal.aborted) void cleanup()
      return created
    }).catch(async err => {
      creating = false
      if (closed || req.signal.aborted) await cleanup()
      throw err
    })
    const created = await Promise.race([creation, expired])
    if (!created) return sseResponse(null)
    creating = false
  } catch (err) {
    creating = false
    await cleanup()
    if (req.signal.aborted || Date.now() >= session.deadline) return sseResponse(null)
    // An existing deterministic name belongs to the first request. Never attach
    // another subscriber, delete that request's resource, or start polling for it.
    if ((err as { code?: number }).code === 6) return new Response(null, { status: 204 })
    console.error('[sse] create outcome requires exact-resource verification:', subName)
    console.error(
      '[sse/PUBSUB_FALLBACK] Pub/Sub subscription creation failed — falling back to 2s pollingStream.' +
      ' Check GOOGLE_CLOUD_PROJECT + PUBSUB_TOPIC env. Error:', (err as Error).message
    )
    return pollingStream(req, chartId, encoder, session)
  }

  if (closed || req.signal.aborted) {
    await cleanup()
    return sseResponse(null)
  }
  const subscription = sub
  if (!subscription) {
    await cleanup()
    return new Response('Stream setup failed', { status: 503 })
  }
  const stream = new ReadableStream<Uint8Array>({
    start(streamController) {
      controller = streamController
      if (closed || req.signal.aborted) { void cleanup(); return }
      const enqueue = (data: string) => {
        if (closed) return false
        try { streamController.enqueue(encoder.encode(data)); return true } catch {
          void cleanup()
          return false
        }
      }

      // Named hello event so the client addEventListener('hello') handler fires
      enqueue(`event: hello\ndata: ${JSON.stringify({ connected: true, chart_id: chartId })}\n\n`)

      heartbeat = setInterval(() => enqueue(`event: heartbeat\ndata: {}\n\n`), 10_000)

      subscription.on('message', (message) => {
        if (closed) return
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
          if (enqueue(`event: ${eventType}\ndata: ${raw}\n\n`)) message.ack()
          else message.nack()
        } catch {
          message.nack()
        }
      })

      subscription.on('error', (err) => {
        if (!closed) console.error('[sse] pubsub error:', err.message)
      })
    },
    cancel: () => cleanup(),
  })

  return sseResponse(stream)
}

const TERMINAL_STATES = new Set(['completed', 'failed', 'stopped'])
const ACTIVE_STATES = new Set(['planned', 'running', 'paused'])

/**
 * Fallback: heartbeat + run-state poll used when Pub/Sub is disabled.
 * Polls build_runs every 2s
 * and emits a synthetic run.state_change frame when the run reaches a
 * terminal state — so DataAssetsView's completion-triggered refetchStats()
 * fires within ~2s even without Pub/Sub (C1-Step1).
 */
function pollingStream(
  req: NextRequest,
  chartId: string,
  encoder: TextEncoder,
  session: Session,
): Response {
  let closed = false
  let controller: ReadableStreamDefaultController<Uint8Array> | undefined
  let heartbeat: ReturnType<typeof setInterval> | undefined
  let poll: ReturnType<typeof setInterval> | undefined
  let deadline: ReturnType<typeof setTimeout> | undefined
  const cleanup = () => {
    if (closed) return
    closed = true
    if (heartbeat) clearInterval(heartbeat)
    if (poll) clearInterval(poll)
    if (deadline) clearTimeout(deadline)
    req.signal.removeEventListener('abort', cleanup)
    try { controller?.close() } catch { /* already canceled/closed */ }
  }
  const stream = new ReadableStream<Uint8Array>({
    start(streamController) {
      controller = streamController
      deadline = setTimeout(cleanup, Math.max(0, session.deadline - Date.now()))
      req.signal.addEventListener('abort', cleanup, { once: true })
      if (req.signal.aborted) { cleanup(); return }
      const enqueue = (data: string) => {
        if (closed) return
        try { streamController.enqueue(encoder.encode(data)) } catch { cleanup() }
      }

      // Named hello event so the client addEventListener('hello') handler fires
      enqueue(`event: hello\ndata: ${JSON.stringify({ connected: true, chart_id: chartId })}\n\n`)

      let lastRunId: string | null = null
      let lastState: string | null = null
      // Track per-asset rows_written so we only emit asset.progress when the count changes
      const lastRowsWritten = new Map<string, number>()

      const pollRun = async () => {
        if (closed) return
        try {
          const { rows } = await query<{ id: string; state: string }>(
            // Index: build_runs_chart_state_planned_idx covers planned/running/paused
            // See migration NNN_fix_build_runs_active_index.sql
            `SELECT id, state FROM build_runs
              WHERE chart_id=$1
              ORDER BY created_at DESC LIMIT 1`,
            [chartId]
          )
          if (closed) return
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
              if (closed) return
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

      heartbeat = setInterval(() => enqueue(`event: heartbeat\ndata: {}\n\n`), 10_000)
      poll = setInterval(pollRun, 2_000)
      // Prime on first connect so we know the current run id
      pollRun()

    },
    cancel: cleanup,
  })

  return sseResponse(stream)
}
