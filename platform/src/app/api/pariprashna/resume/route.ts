/**
 * /api/pariprashna/resume — Paripraśna reconnect route (lane PB-2/M-5,
 * wave SMṚTI: "resume: Last-Event-ID over a ring buffer").
 *
 * A client whose SSE connection to `/api/pariprashna` (the main route) drops
 * mid-turn — network blip, a backgrounded tab the OS reclaimed, or a
 * deliberate client-side reconnect (`visibilitychange`) — GETs here with the
 * server `turn_id` it received on `turn.open` and the highest `seq` it
 * actually applied, via the standard SSE `Last-Event-ID` header (query-param
 * fallback `?last_event_id=` for callers that can't set custom headers on a
 * GET). This route NEVER special-cases *why* the client reconnected — the
 * same path serves a genuine network drop, a backgrounded-tab return, and a
 * manual retry identically, because all three are "a client asking to catch
 * up from a seq," full stop.
 *
 * Three outcomes, in order of preference:
 *   1. REPLAY — `last_event_id` is still within the turn's ring buffer
 *      (`ring_buffer.ts`, `RING_BUFFER_MAX_EVENTS`-deep): every buffered event
 *      with `seq > last_event_id` is re-emitted VERBATIM (original seq/t
 *      preserved via `writeRawEvent` — never re-stamped), so the client's
 *      existing seen-set dedup (`components/pariprashna/state/reducer.ts`)
 *      makes this idempotent even on an overlapping replay window.
 *   2. SNAPSHOT — the requested seq has already been evicted (buffer too
 *      small / too much time passed) or the shared store degraded mid-read.
 *      Rather than silently lose the gap OR silently duplicate a block, the
 *      server emits a `flag{code:'resumed_via_snapshot'}` + ONE
 *      `snapshot.apply` event carrying the CURRENT COMMITTED STATE as a
 *      single blob — the client applies it in one write, no replay
 *      animation (see `ring_buffer.ts`'s module docstring for the full
 *      reasoning).
 *   3. INTERRUPTED — the turn has been `open` with zero wire activity for
 *      `GRACE_WINDOW_MS` (`ring_buffer.finalizeInterruptedIfStale`), which
 *      this route treats as "the process that was streaming it died."  The
 *      accumulated tail is committed as a final block, a synthetic
 *      `turn.close{status:'aborted'}` is appended, and — CRITICALLY — this
 *      route contains NO import of the shared onFinish write-through helper,
 *      the persistence writer, or the prediction-candidate detector (see
 *      `ring_buffer.test.ts`'s source-grep assertion, which names all three
 *      symbols explicitly and fails the moment any of them appears here). A
 *      truncated claim can therefore never reach persistence or
 *      prediction-candidate detection through this path, by construction —
 *      those only ever run inside the ORIGINAL POST request's own finalize
 *      step, which by definition never completes for an interrupted turn.
 *
 * After replay/snapshot, if the turn is still `open`, this route TAILS the
 * shared buffer by polling every `POLL_INTERVAL_MS` until `turn.close`
 * appears or `MAX_TAIL_MS` elapses — a deliberately simple mechanism (no
 * Redis Pub/Sub or Streams `XREAD BLOCK`) chosen for this wave's scope; see
 * the wave report for the honest cost/latency tradeoff this implies.
 */

import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'
import { configService } from '@/lib/config/index'
import { PariprashnaEmitter, writeRawEvent } from '@/lib/pariprashna/protocol/emitter'
import {
  getTurnMeta,
  getBufferedEventsSince,
  finalizeInterruptedIfStale,
  appendBufferedEvent,
  buildSnapshotText,
} from '@/lib/pariprashna/protocol/ring_buffer'

export const maxDuration = 120

/** How often to poll the shared buffer for new events while tailing a still-open turn. */
const POLL_INTERVAL_MS = 400
/** Safety cap on how long one resume connection will tail before handing back to the client to reconnect again. */
const MAX_TAIL_MS = 100_000

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function GET(request: Request): Promise<Response> {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  if (!configService.getFlag('PARIPRASHNA_ENABLED')) {
    return res.notFound('Paripraśna is not enabled.')
  }

  const url = new URL(request.url)
  const turnId = url.searchParams.get('turn_id')
  if (!turnId) return res.badRequest('turn_id is required')

  const lastEventIdRaw = request.headers.get('last-event-id') ?? url.searchParams.get('last_event_id')
  const parsedLastSeq = lastEventIdRaw !== null && Number.isFinite(Number(lastEventIdRaw)) ? Number(lastEventIdRaw) : -1

  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const encoder = new TextEncoder()
      let em: PariprashnaEmitter | null = null

      const fail = (code: string, message: string, retryable: boolean): void => {
        // Pre-emitter faults (unknown turn, forbidden) still ride the same
        // typed `error` event shape — write it directly since `em` may not
        // exist yet (we don't know the turn's real seq to seed it at).
        writeRawEvent(controller, { type: 'error', seq: 0, t: Date.now(), code, message, retryable }, encoder)
        try {
          controller.close()
        } catch {
          /* already closed */
        }
      }

      try {
        let meta = await getTurnMeta(turnId)
        if (!meta) {
          fail('UNKNOWN_TURN', 'No such turn (never started, or its record has expired).', false)
          return
        }

        // Same per-chart authorization the main route applies — a resume
        // request is a read of this turn's content and must pass the same gate.
        const profileResult = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [user.uid])
        const isSuperAdmin = profileResult.rows[0]?.role === 'super_admin'
        const { authorizeChartAccess } = await import('@/lib/auth/authorizeChartAccess')
        type DbLike = import('@/lib/auth/authorizeChartAccess').DbLike
        const permission = await authorizeChartAccess({
          principal: { uid: user.uid, role: isSuperAdmin ? 'super_admin' : 'guest' },
          chartId: meta.chartId,
          db: { query: (sql: string, params?: unknown[]) => query(sql, params).then((r) => ({ rows: r.rows })) } as DbLike,
        })
        if (permission === 'deny') {
          fail('FORBIDDEN', 'Not authorized for this chart.', false)
          return
        }

        // Lazy interrupted-turn detection — see module docstring + ring_buffer.ts.
        meta = (await finalizeInterruptedIfStale(turnId)) ?? meta

        // Seed the emitter's seq counter past everything already recorded, so
        // any NEW (synthetic) event this route mints — the snapshot flag/apply
        // pair — continues the turn's monotonic sequence instead of colliding
        // with replayed history.
        em = new PariprashnaEmitter(controller, (event) => void appendBufferedEvent(turnId, event), meta.maxSeqSeen + 1)

        const range = await getBufferedEventsSince(turnId, parsedLastSeq)
        if (!range) {
          em.error({ code: 'UNKNOWN_TURN', message: 'Turn record disappeared mid-resume.', retryable: false })
          em.close()
          return
        }

        let lastWrittenSeq = parsedLastSeq
        if (range.evicted) {
          em.flag({
            code: 'resumed_via_snapshot',
            level: 'info',
            detail: `requested seq ${parsedLastSeq} is no longer in the ring buffer — serving current state as a snapshot`,
          })
          em.snapshotApply({
            turn_id: turnId,
            text: buildSnapshotText(meta),
            citations: meta.citations,
            turn_status: meta.status,
          })
          lastWrittenSeq = meta.maxSeqSeen
        } else {
          for (const bufferedEvent of range.events) {
            if (!writeRawEvent(controller, bufferedEvent, encoder)) return
            lastWrittenSeq = bufferedEvent.seq
          }
        }

        if (meta.status !== 'open') {
          em.close()
          return
        }

        // ── Live-tail: poll the shared buffer until turn.close or timeout. ──
        const tailStartedAt = Date.now()
        while (Date.now() - tailStartedAt < MAX_TAIL_MS) {
          await sleep(POLL_INTERVAL_MS)
          if (request.signal.aborted) return

          await finalizeInterruptedIfStale(turnId)
          const fresh = await getBufferedEventsSince(turnId, lastWrittenSeq)
          if (!fresh) break

          if (fresh.evicted) {
            // Only reachable if the buffer raced far ahead of our last write
            // (or the store degraded mid-tail) — defensively re-snapshot
            // rather than guess at what was missed.
            const latest = await getTurnMeta(turnId)
            if (latest) {
              em.flag({
                code: 'resumed_via_snapshot',
                level: 'info',
                detail: 'tail buffer advanced past the last replayed window',
              })
              em.snapshotApply({
                turn_id: turnId,
                text: buildSnapshotText(latest),
                citations: latest.citations,
                turn_status: latest.status,
              })
              lastWrittenSeq = latest.maxSeqSeen
              if (latest.status !== 'open') break
            }
          } else {
            for (const ev of fresh.events) {
              if (!writeRawEvent(controller, ev, encoder)) return
              lastWrittenSeq = ev.seq
            }
          }

          const latestMeta = await getTurnMeta(turnId)
          if (!latestMeta || latestMeta.status !== 'open') break
        }

        em.close()
      } catch (fatal) {
        console.error('[pariprashna/resume] fatal in-stream error:', fatal)
        if (em) {
          em.error({ code: 'INTERNAL', message: fatal instanceof Error ? fatal.message : String(fatal), retryable: true })
          em.close()
        } else {
          fail('INTERNAL', fatal instanceof Error ? fatal.message : String(fatal), true)
        }
      }
    },
  })

  return new Response(stream, {
    headers: {
      'content-type': 'text/event-stream; charset=utf-8',
      'cache-control': 'no-cache, no-transform',
      connection: 'keep-alive',
      'x-accel-buffering': 'no',
    },
  })
}
