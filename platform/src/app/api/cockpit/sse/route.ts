import { NextRequest } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

async function isSuperAdmin(uid: string): Promise<boolean> {
  const { rows } = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [uid])
  return rows[0]?.role === 'super_admin'
}

export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  const user = await getServerUser()
  if (!user) return new Response('Forbidden', { status: 403 })
  if (!(await isSuperAdmin(user.uid))) return new Response('Forbidden', { status: 403 })

  const chartId = req.nextUrl.searchParams.get('chart_id')
  if (!chartId) return new Response('chart_id required', { status: 400 })

  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    start(controller) {
      const send = (event: string, data: unknown) => {
        try {
          controller.enqueue(encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`))
        } catch {
          // stream closed
        }
      }

      // Initial hello
      send('hello', { chart_id: chartId, ts: new Date().toISOString() })

      // Heartbeat every 30s
      const heartbeat = setInterval(() => {
        try {
          controller.enqueue(encoder.encode(`: heartbeat\n\n`))
        } catch {
          clearInterval(heartbeat)
        }
      }, 30_000)

      // Cleanup on close
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
