import { NextRequest } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

async function isSuperAdmin(uid: string): Promise<boolean> {
  const { rows } = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [uid])
  return rows[0]?.role === 'super_admin'
}

export const dynamic = 'force-dynamic'

const GCP_PROJECT = process.env.GCP_PROJECT ?? 'madhav-astrology'
const PUBSUB_TOPIC = process.env.PUBSUB_TOPIC ?? 'cockpit-events'

/** Whether Pub/Sub is available (topic env set and not explicitly disabled). */
function pubsubEnabled(): boolean {
  return !process.env.PUBSUB_DISABLED && !!process.env.GCP_PROJECT
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
  const client = new PubSub({ projectId: GCP_PROJECT })

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
        console.error('[sse] subscription create failed:', (err as Error).message)
        // Fall back to heartbeat-only; orchestrator events won't stream but client won't hang
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

/**
 * Fallback: in-memory heartbeat-only stream used in local dev when
 * PUBSUB_DISABLED is set or GCP_PROJECT is absent.
 * The cockpit polls /api/cockpit/runs/active for state updates in this mode.
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

      const heartbeat = setInterval(() => enqueue(`: hb\n\n`), 30_000)

      req.signal.addEventListener('abort', () => {
        clearInterval(heartbeat)
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
