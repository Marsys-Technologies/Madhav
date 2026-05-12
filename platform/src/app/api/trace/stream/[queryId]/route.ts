/**
 * MARSYS-JIS Query Trace Panel — SSE streaming endpoint
 *
 * GET /api/trace/stream/[queryId]
 *   Live mode:       replays any existing DB steps, then streams live TraceEvents from the emitter.
 *   Historical mode: replays stored steps from query_trace_steps (?mode=historical query param).
 *
 * Auth: super_admin only (same pattern as /api/audit/*).
 * Sends a 'done' sentinel event when the pipeline completes or all stored steps are replayed.
 */

import { requireSuperAdmin } from '@/lib/auth/access-control'
import { NextResponse } from 'next/server'
import { traceEmitter } from '@/lib/trace/emitter'
import { fetchTraceSteps } from '@/lib/trace/writer'
import type { TraceEvent } from '@/lib/trace/types'

export const dynamic = 'force-dynamic'
export const maxDuration = 120

export async function GET(
  request: Request,
  { params }: { params: Promise<{ queryId: string }> }
) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  const { queryId } = await params
  if (!queryId) {
    return new Response('Missing queryId', { status: 400 })
  }

  const encoder = new TextEncoder()
  // `satisfies TraceEvent` ensures any drift in event shape becomes a compile-time
  // error here (added Gate II 2026-05-12 per W7).
  const encode = (event: TraceEvent) =>
    encoder.encode(`data: ${JSON.stringify(event satisfies TraceEvent)}\n\n`)

  const reqUrl = new URL(request.url)
  const isHistorical = reqUrl.searchParams.get('mode') === 'historical'

  if (isHistorical) {
    // Replay stored steps synchronously as a one-shot stream
    let steps: Awaited<ReturnType<typeof fetchTraceSteps>>
    try {
      steps = await fetchTraceSteps(queryId)
    } catch (err) {
      console.error('[api/trace/stream] fetchTraceSteps (historical) failed', err)
      return new Response('Internal Server Error', { status: 500 })
    }

    const stream = new ReadableStream({
      start(controller) {
        for (const step of steps) {
          controller.enqueue(encode({ event: 'step_done', query_id: queryId, step }))
        }
        controller.enqueue(encode({ event: 'done', query_id: queryId }))
        controller.close()
      },
    })
    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache, no-transform',
        Connection: 'keep-alive',
        'X-Accel-Buffering': 'no',   // prevent nginx/LB buffering
      },
    })
  }

  // Live mode: replay any steps already persisted (handles clients that connect after
  // the pipeline finishes), then subscribe to the in-process EventEmitter for future steps.
  let cleanup: ((e: TraceEvent) => void) | null = null
  let cancelled = false

  const stream = new ReadableStream({
    async start(controller) {
      // --- Phase 1: flush existing DB steps ---
      // Covers: (a) late-connecting client, (b) panel opened mid-pipeline.
      let existingSteps: Awaited<ReturnType<typeof fetchTraceSteps>>
      try {
        existingSteps = await fetchTraceSteps(queryId)
      } catch (err) {
        console.error('[api/trace/stream] fetchTraceSteps (live) failed', err)
        controller.close()
        return
      }

      if (cancelled) return

      for (const step of existingSteps) {
        controller.enqueue(encode({ event: 'step_done', query_id: queryId, step }))
      }

      // If the synthesis step is already done, the pipeline is complete — send the
      // done sentinel and close. No need to subscribe to the live emitter.
      const pipelineComplete = existingSteps.some(
        s => s.step_name === 'synthesis' && s.status === 'done'
      )
      if (pipelineComplete) {
        controller.enqueue(encode({ event: 'done', query_id: queryId }))
        controller.close()
        return
      }

      // --- Phase 2: subscribe for live events (pipeline still in progress) ---
      const handler = (event: TraceEvent) => {
        try {
          controller.enqueue(encode(event))
          if (event.event === 'done') {
            traceEmitter.unsubscribe(queryId, handler)
            controller.close()
          }
        } catch {
          // Client disconnected — clean up silently
          traceEmitter.unsubscribe(queryId, handler)
        }
      }
      cleanup = handler
      traceEmitter.subscribe(queryId, handler)
    },
    cancel() {
      cancelled = true
      if (cleanup) {
        traceEmitter.unsubscribe(queryId, cleanup)
        cleanup = null
      }
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
