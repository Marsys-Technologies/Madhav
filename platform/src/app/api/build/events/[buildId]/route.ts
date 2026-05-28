/**
 * GET /api/build/events/[buildId]
 *
 * SSE rail the cockpit subscribes to. Replays all existing build_events
 * rows then long-polls for new ones every 1s. The Python pipeline writes
 * directly to the table; we tail it.
 *
 * Auth: chart-page access (owner / super_admin / view-grantee can all
 * see progress; only owner/super_admin trigger via /api/build/start).
 */

import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import { listBuildEvents, type BuildEventRow } from '@/lib/build/events'

export const dynamic = 'force-dynamic'
export const maxDuration = 300

type Params = Promise<{ buildId: string }>

export async function GET(request: Request, ctx: { params: Params }): Promise<Response> {
  const { buildId } = await ctx.params
  if (!buildId) return new Response('Missing buildId', { status: 400 })

  const user = await getServerUser()
  if (!user) return new Response('Unauthorized', { status: 401 })

  // Find chart_id for this build to authz against it.
  const rowRes = await query<{ chart_id: string }>(
    'SELECT chart_id FROM build_events WHERE build_id=$1 LIMIT 1',
    [buildId],
  )
  const chartId = rowRes.rows[0]?.chart_id
  if (!chartId) return new Response('Build not found', { status: 404 })

  const profile = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id=$1',
    [user.uid],
  )
  const role: 'super_admin' | 'guest' =
    (profile.rows[0]?.role ?? '') === 'super_admin' ? 'super_admin' : 'guest'

  const permission = await authorizeChartAccess({
    principal: { uid: user.uid, role },
    chartId,
    db: { query },
  })
  if (permission === 'deny') return new Response('Forbidden', { status: 404 })

  const encoder = new TextEncoder()
  const encode = (row: BuildEventRow): Uint8Array =>
    encoder.encode(`data: ${JSON.stringify(row)}\n\n`)
  const encodeDone = (): Uint8Array => encoder.encode(`event: done\ndata: {}\n\n`)

  const stream = new ReadableStream({
    async start(controller) {
      let lastSeq = -1
      let closed = false
      const safeClose = (): void => {
        if (closed) return
        closed = true
        try { controller.close() } catch { /* already closed */ }
      }
      const tick = async (): Promise<void> => {
        try {
          const rows = await listBuildEvents(buildId)
          for (const row of rows) {
            if (row.stage_seq <= lastSeq) continue
            controller.enqueue(encode(row))
            lastSeq = row.stage_seq
            if (
              (row.asset === 'orchestrator' && row.stage === 'finalize' && row.status === 'complete') ||
              row.status === 'failed' ||
              row.status === 'rolled_back'
            ) {
              controller.enqueue(encodeDone())
              safeClose()
              return
            }
          }
        } catch (err) {
          console.error('[api/build/events] poll error', err)
          safeClose()
        }
      }

      await tick()
      const handle = setInterval(() => {
        if (closed) {
          clearInterval(handle)
          return
        }
        void tick()
      }, 1000)

      request.signal.addEventListener('abort', () => {
        clearInterval(handle)
        safeClose()
      })
    },
  })

  return new NextResponse(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
    },
  })
}
