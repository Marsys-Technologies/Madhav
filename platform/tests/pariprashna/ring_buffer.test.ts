/**
 * PB-2/M-5 — per-turn ring buffer (`src/lib/pariprashna/protocol/ring_buffer.ts`).
 *
 * Covers the three acceptance scenarios named in the wave brief:
 *   1. a normal reconnect resuming from a valid seq (idempotent range, no
 *      duplicate/missing events);
 *   2. a buffer-evicted case correctly falling back to snapshot (never
 *      silent loss, never duplicate);
 *   3. an interrupted-turn case correctly excluded from prediction detection
 *      — both behaviorally (the finalize path never scores anything) and
 *      structurally (the module itself never imports the detector).
 *
 * REDIS_HOST is unset in the test environment, so `getRedis()` returns
 * `null` and every call below exercises the in-memory fallback
 * deterministically (no live Redis needed).
 */
import { describe, it, expect, beforeEach } from 'vitest'
import fs from 'fs/promises'
import path from 'path'
import {
  openTurnBuffer,
  appendBufferedEvent,
  getTurnMeta,
  getBufferedEventsSince,
  finalizeInterruptedIfStale,
  buildSnapshotText,
  __resetRingBufferForTests,
  RING_BUFFER_MAX_EVENTS,
  GRACE_WINDOW_MS,
} from '@/lib/pariprashna/protocol/ring_buffer'
import type { PariprashnaEvent } from '@/lib/pariprashna/protocol/events'

function blockOpen(seq: number): PariprashnaEvent {
  return { type: 'block.open', seq, t: seq, block_id: 'b1', pass_id: 1, role: 'prose' }
}
function blockDelta(seq: number, delta: string): PariprashnaEvent {
  return { type: 'block.delta', seq, t: seq, block_id: 'b1', delta }
}
function blockCommit(seq: number, text: string): PariprashnaEvent {
  return { type: 'block.commit', seq, t: seq, block_id: 'b1', text }
}

describe('ring_buffer — normal reconnect (no eviction)', () => {
  beforeEach(async () => {
    await __resetRingBufferForTests()
  })

  it('replays events strictly after the requested seq — no duplicates, nothing missing', async () => {
    const turnId = 'turn-replay'
    await openTurnBuffer({ turnId, chartId: 'chart-1', conversationId: 'conv-1' })
    await appendBufferedEvent(turnId, blockOpen(0))
    await appendBufferedEvent(turnId, blockDelta(1, 'Hello '))
    await appendBufferedEvent(turnId, blockDelta(2, 'World'))
    await appendBufferedEvent(turnId, blockCommit(3, 'Hello World'))

    const range = await getBufferedEventsSince(turnId, 1)
    expect(range).not.toBeNull()
    expect(range!.evicted).toBe(false)
    expect(range!.events.map((e) => e.seq)).toEqual([2, 3])
  })

  it('replaying from the very last seq the client saw yields an empty (but non-evicted) range — safe to call repeatedly', async () => {
    const turnId = 'turn-replay-empty'
    await openTurnBuffer({ turnId, chartId: 'chart-1', conversationId: 'conv-1' })
    await appendBufferedEvent(turnId, blockOpen(0))
    const range = await getBufferedEventsSince(turnId, 0)
    expect(range).toEqual({ events: [], evicted: false })
  })

  it('reports UNKNOWN_TURN (null) distinctly from an evicted-but-known turn', async () => {
    const range = await getBufferedEventsSince('never-existed', 0)
    expect(range).toBeNull()
  })
})

describe('ring_buffer — buffer eviction falls back to snapshot, never silently loses or duplicates', () => {
  beforeEach(async () => {
    await __resetRingBufferForTests()
  })

  it('flags eviction once the requested seq falls outside the retained window', async () => {
    const turnId = 'turn-evict'
    await openTurnBuffer({ turnId, chartId: 'chart-1', conversationId: 'conv-1' })
    for (let i = 0; i < RING_BUFFER_MAX_EVENTS + 10; i++) {
      await appendBufferedEvent(turnId, blockCommit(i, `chunk-${i}`))
    }
    // seq 0 was trimmed out of the ring long ago.
    const range = await getBufferedEventsSince(turnId, 0)
    expect(range).not.toBeNull()
    expect(range!.evicted).toBe(true)
    expect(range!.events).toEqual([]) // evicted range never hands back a partial/misleading list
  })

  it('the snapshot built from meta reflects the CURRENT committed state, not the trimmed history', async () => {
    const turnId = 'turn-evict-snapshot'
    await openTurnBuffer({ turnId, chartId: 'chart-1', conversationId: 'conv-1' })
    for (let i = 0; i < RING_BUFFER_MAX_EVENTS + 10; i++) {
      await appendBufferedEvent(turnId, blockCommit(i, `chunk-${i}`))
    }
    const meta = await getTurnMeta(turnId)
    expect(meta).not.toBeNull()
    const snapshotText = buildSnapshotText(meta!)
    // The most recent commit must be present — the derived meta survives eviction
    // even though the raw events themselves were trimmed out of the ring.
    expect(snapshotText).toContain(`chunk-${RING_BUFFER_MAX_EVENTS + 9}`)
    // And an early, now-evicted chunk is NOT independently retrievable as a raw
    // event any more (proving eviction actually happened, not just claimed).
    const range = await getBufferedEventsSince(turnId, 0)
    expect(range!.evicted).toBe(true)
  })

  it('does NOT report eviction for a seq still inside the retained window', async () => {
    const turnId = 'turn-still-fresh'
    await openTurnBuffer({ turnId, chartId: 'chart-1', conversationId: 'conv-1' })
    for (let i = 0; i < 10; i++) {
      await appendBufferedEvent(turnId, blockCommit(i, `chunk-${i}`))
    }
    const range = await getBufferedEventsSince(turnId, 3)
    expect(range!.evicted).toBe(false)
    expect(range!.events).toHaveLength(6)
  })
})

describe('ring_buffer — interrupted-turn detection is provably excluded from prediction-candidate detection', () => {
  beforeEach(async () => {
    await __resetRingBufferForTests()
  })

  it('marks a stale open turn interrupted, commits the tail (never drops it), and appends a synthetic aborted turn.close', async () => {
    const turnId = 'turn-interrupted'
    // A realistic epoch-ms base (NOT a small synthetic number) — meta TTLs are
    // computed as `nowMs + ttlSeconds*1000`, and any downstream call in this
    // test that omits an explicit `nowMs` falls back to the REAL `Date.now()`.
    // A tiny synthetic base would look already-expired against that real clock.
    const t0 = Date.now()
    await openTurnBuffer({ turnId, chartId: 'chart-1', conversationId: 'conv-1', nowMs: t0 })
    await appendBufferedEvent(turnId, blockOpen(0), t0 + 10)
    // Deliberately prediction-shaped text — to prove it is never scored by this path.
    await appendBufferedEvent(
      turnId,
      blockDelta(1, 'Saturn transits your 10th house by 2027, and you will see a major career shift.'),
      t0 + 20,
    )
    // No further activity — simulates the server dying right here.
    const staleNow = t0 + 20 + GRACE_WINDOW_MS + 1
    const meta = await finalizeInterruptedIfStale(turnId, staleNow)

    expect(meta).not.toBeNull()
    expect(meta!.status).toBe('interrupted')
    expect(meta!.openTail).toBeNull() // tail was committed, not silently dropped
    expect(meta!.committedText).toContain('Saturn transits your 10th house')

    const range = await getBufferedEventsSince(turnId, 1)
    expect(range!.evicted).toBe(false)
    expect(range!.events.some((e) => e.type === 'block.commit')).toBe(true)
    const closeEvent = range!.events.find((e) => e.type === 'turn.close')
    expect(closeEvent).toBeDefined()
    expect((closeEvent as Extract<PariprashnaEvent, { type: 'turn.close' }>).status).toBe('aborted')

    // Idempotent — calling it again on an already-interrupted turn is a no-op read.
    const again = await finalizeInterruptedIfStale(turnId, staleNow + 5_000)
    expect(again!.status).toBe('interrupted')
    expect(again!.closedAtMs).toBe(meta!.closedAtMs)
  })

  it('does NOT finalize an actively-updating turn, even if it contains prediction-shaped text', async () => {
    const turnId = 'turn-active'
    const t0 = Date.now()
    await openTurnBuffer({ turnId, chartId: 'chart-1', conversationId: 'conv-1', nowMs: t0 })
    await appendBufferedEvent(turnId, blockDelta(0, 'You will succeed by 2028.'), t0 + 5)
    const stillFresh = t0 + 5 + GRACE_WINDOW_MS - 1_000 // just inside the grace window
    const meta = await finalizeInterruptedIfStale(turnId, stillFresh)
    expect(meta!.status).toBe('open')
  })

  it('a turn that closes normally is never touched by the grace-window path', async () => {
    const turnId = 'turn-closed-normally'
    const t0 = Date.now()
    await openTurnBuffer({ turnId, chartId: 'chart-1', conversationId: 'conv-1', nowMs: t0 })
    await appendBufferedEvent(turnId, blockCommit(0, 'A complete answer.'), t0 + 5)
    await appendBufferedEvent(
      turnId,
      { type: 'turn.close', seq: 1, t: t0 + 6, turn_id: turnId, status: 'ok', ms: 6 },
      t0 + 6,
    )
    // Well past the grace window, but still inside the closed-turn TTL (so the
    // meta read below reflects "not reclassified", not "record expired").
    const longAfter = t0 + 6 + GRACE_WINDOW_MS + 1_000
    const meta = await finalizeInterruptedIfStale(turnId, longAfter)
    expect(meta!.status).toBe('closed') // NOT reclassified to 'interrupted' — it ended cleanly
  })

  it('structural exclusion: the ring buffer module never imports persistence or the prediction-candidate detector', async () => {
    const src = await fs.readFile(
      path.resolve(__dirname, '../../src/lib/pariprashna/protocol/ring_buffer.ts'),
      'utf8',
    )
    expect(src).not.toMatch(/detectPredictionCandidates/)
    expect(src).not.toMatch(/runOnFinishWriteThrough/)
    expect(src).not.toMatch(/writeConversationMessages/)
  })

  it('structural exclusion: the resume route never imports persistence or the prediction-candidate detector', async () => {
    const src = await fs.readFile(
      path.resolve(__dirname, '../../src/app/api/pariprashna/resume/route.ts'),
      'utf8',
    )
    expect(src).not.toMatch(/detectPredictionCandidates/)
    expect(src).not.toMatch(/runOnFinishWriteThrough/)
    expect(src).not.toMatch(/writeConversationMessages/)
  })
})
