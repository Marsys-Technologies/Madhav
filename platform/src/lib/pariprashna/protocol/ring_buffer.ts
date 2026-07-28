/**
 * Paripraśna per-turn ring buffer — lane PB-2/M-5 ("resume: Last-Event-ID
 * over a ring buffer"), wave SMṚTI.
 *
 * WHY THIS EXISTS
 * ───────────────
 * The route's `PariprashnaEmitter` writes each SSE event straight to the
 * open HTTP response and forgets it. A client whose connection drops mid-turn
 * (network blip, backgrounded tab the OS reclaimed, a deliberate reconnect)
 * has no way to ask "what did I miss?" — the bytes are gone the instant they
 * leave the process. This module gives every in-flight turn a bounded,
 * ordered log of its own events (a ring buffer, keyed by `turn_id`) that a
 * reconnecting client can replay from via `Last-Event-ID` (see
 * `/api/pariprashna/resume/route.ts`).
 *
 * SHARED-STORE SCOPING (read this before changing the backend)
 * ──────────────────────────────────────────────────────────────
 * `amjis-web` (this Next.js app) deploys to Cloud Run with `--min-instances=1`
 * and NO `--max-instances` cap (`.github/workflows/deploy.yml` A-S8 step) —
 * i.e. the floor is 1 warm instance, but the service WILL scale out under
 * concurrent load using Cloud Run's default ceiling. A client that reconnects
 * after a network blip has no guarantee it lands back on the same instance
 * that was streaming its turn. An in-process-only buffer would therefore
 * silently break resume for exactly the class of user this lane exists for
 * (the one whose connection just dropped and is retrying). So: Redis
 * (Memorystore, already provisioned — `redis_client.ts`, Stream C wave 4) is
 * the PRIMARY backend whenever `REDIS_HOST` is configured (i.e. every real
 * deploy). An in-process `Map` is the fallback used only when Redis is
 * unconfigured (local dev, unit tests) — in that mode there is exactly one
 * process anyway, so process-locality is a non-issue, not a silent gap.
 *
 * DEGRADED-REDIS HANDLING
 * ───────────────────────
 * Every Redis call here follows the same "never throws, degrade honestly"
 * discipline as `shared_cache.ts`: on a Redis error, `getBufferedEventsSince`
 * reports `evicted: true` — exactly the same signal used for a genuinely
 * trimmed-out seq. This is deliberate, not a shortcut: the caller already has
 * a correct, safe response to "history unavailable" (the snapshot fallback in
 * `resume/route.ts`), so routing a transient Redis hiccup through that same
 * path is strictly safer than trying to distinguish the two cases — it can
 * never silently lose data (worst case: a snapshot instead of an incremental
 * replay) and never duplicates a block.
 *
 * WHAT THIS MODULE DOES NOT DO
 * ─────────────────────────────
 * It never calls the conversation-message persistence writer or the
 * regex-based prediction-candidate detector (the two symbols the shared
 * onFinish write-through helper — `lib/pipelines/shared/onfinish_writethrough`
 * — invokes on the main route's own finalize step) — by construction, not by
 * a runtime guard. That is the provable half of "an interrupted turn must
 * never seed prediction-candidate detection" (see `finalizeInterruptedIfStale`
 * below + its test's source check, which greps for both symbol names).
 */

import 'server-only'
import { getRedis } from '@/lib/cache/redis_client'
import type { PariprashnaEvent } from './events'

// ---------------------------------------------------------------------------
// Tunables
// ---------------------------------------------------------------------------

/** Max events retained per turn — beyond this, oldest events are trimmed. */
export const RING_BUFFER_MAX_EVENTS = 500

/**
 * No wire activity for this long while `status === 'open'` ⇒ the turn is
 * treated as server-died-mid-turn on the NEXT resume attempt (detection is
 * lazy/on-demand, not a proactive sweep — see module docstring in
 * `resume/route.ts` for the honest limitation this implies).
 */
export const GRACE_WINDOW_MS = 60_000

/** TTL while a turn is still open (sliding — refreshed on every append). */
const TURN_TTL_OPEN_SECONDS = 600
/** TTL once a turn is closed/interrupted — long enough for a late reconnect. */
const TURN_TTL_CLOSED_SECONDS = 180

function bufKey(turnId: string): string {
  return `parp:buf:${turnId}`
}
function metaKey(turnId: string): string {
  return `parp:meta:${turnId}`
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface StoredCitation {
  index: number
  signal_id: string
  layer: string
  snippet: string
}

export type TurnBufferStatus = 'open' | 'closed' | 'interrupted'

export interface TurnBufferMeta {
  turnId: string
  chartId: string
  conversationId: string
  status: TurnBufferStatus
  createdAtMs: number
  lastActivityAtMs: number
  closedAtMs: number | null
  /** Lowest seq still retained in the ring (events before this were evicted). */
  minSeqRetained: number
  /** Highest seq ever appended (used to mint fresh seqs for synthetic events). */
  maxSeqSeen: number
  /** Concatenation of every `block.commit` text seen so far — snapshot basis. */
  committedText: string
  /** The currently-open (uncommitted) block, if any. */
  openTail: { blockId: string; text: string } | null
  citations: StoredCitation[]
}

// ---------------------------------------------------------------------------
// In-memory fallback (Redis unconfigured — local dev / tests)
// ---------------------------------------------------------------------------

const memBuffers = new Map<string, string[]>()
const memMeta = new Map<string, { json: string; expiresAtMs: number }>()

function memMetaGet(turnId: string, nowMs: number): string | null {
  const entry = memMeta.get(metaKey(turnId))
  if (!entry) return null
  if (entry.expiresAtMs < nowMs) {
    memMeta.delete(metaKey(turnId))
    memBuffers.delete(bufKey(turnId))
    return null
  }
  return entry.json
}
function memMetaSet(turnId: string, json: string, ttlSeconds: number, nowMs: number): void {
  memMeta.set(metaKey(turnId), { json, expiresAtMs: nowMs + ttlSeconds * 1000 })
}

// ---------------------------------------------------------------------------
// Meta read/write (Redis primary, memory fallback)
// ---------------------------------------------------------------------------

async function readMeta(turnId: string, nowMs: number): Promise<TurnBufferMeta | null> {
  const r = getRedis()
  if (r) {
    try {
      const raw = await r.get(metaKey(turnId))
      if (raw == null) return null
      return JSON.parse(raw) as TurnBufferMeta
    } catch (err) {
      console.warn('[ring_buffer] meta read failed, treating as unavailable:', err)
      return null
    }
  }
  const raw = memMetaGet(turnId, nowMs)
  return raw ? (JSON.parse(raw) as TurnBufferMeta) : null
}

async function writeMeta(meta: TurnBufferMeta, nowMs: number): Promise<void> {
  const ttlSeconds = meta.status === 'open' ? TURN_TTL_OPEN_SECONDS : TURN_TTL_CLOSED_SECONDS
  const json = JSON.stringify(meta)
  const r = getRedis()
  if (r) {
    try {
      await r.set(metaKey(meta.turnId), json, 'EX', ttlSeconds)
      return
    } catch (err) {
      console.warn('[ring_buffer] meta write failed (degraded — resume for this turn may fall back to snapshot):', err)
      // Fall through to memory as a best-effort local mirror; a DIFFERENT
      // instance still won't see it, which is the honest, already-documented
      // degraded mode (see module docstring).
    }
  }
  memMetaSet(meta.turnId, json, ttlSeconds, nowMs)
}

// ---------------------------------------------------------------------------
// Buffer (event list) read/write
// ---------------------------------------------------------------------------

async function pushEvent(turnId: string, event: PariprashnaEvent): Promise<void> {
  const json = JSON.stringify(event)
  const r = getRedis()
  if (r) {
    try {
      const key = bufKey(turnId)
      await r.rpush(key, json)
      await r.ltrim(key, -RING_BUFFER_MAX_EVENTS, -1)
      await r.expire(key, TURN_TTL_OPEN_SECONDS)
      return
    } catch (err) {
      console.warn('[ring_buffer] event append failed (degraded):', err)
      // fall through to memory mirror (best-effort; see docstring)
    }
  }
  const key = bufKey(turnId)
  const list = memBuffers.get(key) ?? []
  list.push(json)
  if (list.length > RING_BUFFER_MAX_EVENTS) list.splice(0, list.length - RING_BUFFER_MAX_EVENTS)
  memBuffers.set(key, list)
}

/** Returns `null` if Redis errored / buffer unreadable (treated as evicted by the caller). */
async function readAllEvents(turnId: string): Promise<PariprashnaEvent[] | null> {
  const r = getRedis()
  if (r) {
    try {
      const raw = await r.lrange(bufKey(turnId), 0, -1)
      return raw.map((s) => JSON.parse(s) as PariprashnaEvent)
    } catch (err) {
      console.warn('[ring_buffer] event read failed, treating as evicted:', err)
      return null
    }
  }
  const raw = memBuffers.get(bufKey(turnId))
  if (!raw) return []
  return raw.map((s) => JSON.parse(s) as PariprashnaEvent)
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export async function openTurnBuffer(args: {
  turnId: string
  chartId: string
  conversationId: string
  nowMs?: number
}): Promise<void> {
  const nowMs = args.nowMs ?? Date.now()
  const meta: TurnBufferMeta = {
    turnId: args.turnId,
    chartId: args.chartId,
    conversationId: args.conversationId,
    status: 'open',
    createdAtMs: nowMs,
    lastActivityAtMs: nowMs,
    closedAtMs: null,
    minSeqRetained: 0,
    maxSeqSeen: -1,
    committedText: '',
    openTail: null,
    citations: [],
  }
  await writeMeta(meta, nowMs)
}

/** Fold one event into the derived committed-state fields on `meta` (mutates + returns it). */
function applyEventToMeta(meta: TurnBufferMeta, event: PariprashnaEvent, nowMs: number): TurnBufferMeta {
  meta.lastActivityAtMs = nowMs
  meta.maxSeqSeen = Math.max(meta.maxSeqSeen, event.seq)

  switch (event.type) {
    case 'block.open':
      meta.openTail = { blockId: event.block_id, text: '' }
      break
    case 'block.delta':
      if (meta.openTail && meta.openTail.blockId === event.block_id) {
        meta.openTail = { ...meta.openTail, text: meta.openTail.text + event.delta }
      }
      break
    case 'block.commit': {
      const text = event.text ?? (meta.openTail && meta.openTail.blockId === event.block_id ? meta.openTail.text : '')
      meta.committedText = meta.committedText ? `${meta.committedText}\n\n${text}` : text
      if (meta.openTail && meta.openTail.blockId === event.block_id) meta.openTail = null
      break
    }
    case 'citation.define':
      meta.citations = [
        ...meta.citations,
        { index: event.index, signal_id: event.signal_id, layer: event.layer, snippet: event.snippet },
      ]
      break
    case 'turn.close':
      meta.status = 'closed'
      meta.closedAtMs = nowMs
      break
    default:
      break
  }
  return meta
}

/**
 * Append one event to a turn's buffer + fold it into the derived meta.
 * Fire-and-forget from the caller's perspective (never throws).
 */
export async function appendBufferedEvent(turnId: string, event: PariprashnaEvent, nowMs = Date.now()): Promise<void> {
  try {
    await pushEvent(turnId, event)
    const meta = await readMeta(turnId, nowMs)
    if (!meta) return // turn buffer was never opened (or has expired) — nothing to fold into
    applyEventToMeta(meta, event, nowMs)
    // A trim may have advanced minSeqRetained — recompute it from what's
    // actually left in the buffer so getBufferedEventsSince's eviction check
    // stays accurate even under the Redis-degraded memory-mirror path.
    const remaining = await readAllEvents(turnId)
    if (remaining && remaining.length > 0) meta.minSeqRetained = remaining[0].seq
    await writeMeta(meta, nowMs)
  } catch (err) {
    console.error('[ring_buffer] appendBufferedEvent error (non-fatal):', err)
  }
}

export async function getTurnMeta(turnId: string, nowMs = Date.now()): Promise<TurnBufferMeta | null> {
  return readMeta(turnId, nowMs)
}

export interface BufferedRange {
  events: PariprashnaEvent[]
  /** True when `sinceSeq` is older than what the ring still retains (or the store errored). */
  evicted: boolean
}

/**
 * Events with `seq > sinceSeq`. Returns `null` only when the turn is
 * entirely unknown (never opened, or its meta has fully expired) — the
 * caller should treat that as `UNKNOWN_TURN`, distinct from `evicted`.
 */
export async function getBufferedEventsSince(turnId: string, sinceSeq: number, nowMs = Date.now()): Promise<BufferedRange | null> {
  const meta = await readMeta(turnId, nowMs)
  if (!meta) return null
  const all = await readAllEvents(turnId)
  if (all === null) return { events: [], evicted: true } // Redis error mid-read — degrade to snapshot, never fabricate history
  if (sinceSeq < meta.minSeqRetained - 1 && meta.maxSeqSeen >= 0) {
    // The client's last-seen seq is older than the oldest event we still have
    // (and at least one event has actually been recorded) — a real gap.
    return { events: [], evicted: true }
  }
  return { events: all.filter((e) => e.seq > sinceSeq), evicted: false }
}

/**
 * Lazily detect + finalize a server-died-mid-turn condition: if the turn is
 * still `open` in the buffer but has seen no wire activity for
 * `GRACE_WINDOW_MS`, mark it `interrupted`, commit whatever open tail exists
 * as a final synthetic `block.commit`, and append a synthetic `turn.close`
 * (status `'aborted'` — reuses PB-1's real enum, no schema change) so a
 * replaying/tailing client sees a clean terminal state instead of hanging.
 *
 * Deliberately does NOT touch persistence or prediction-candidate detection
 * — those only ever run inside the original POST request's own onFinish
 * write-through call (see `app/api/pariprashna/route.ts`'s finalize step,
 * where the shared write-through helper is invoked), which by definition
 * never reached that step (that absence is WHY this function exists). This
 * module has no import of either downstream symbol; that is the provable
 * half of the exclusion guarantee (see `ring_buffer.test.ts`'s source-grep
 * assertion, which names both symbols explicitly).
 */
export async function finalizeInterruptedIfStale(turnId: string, nowMs = Date.now()): Promise<TurnBufferMeta | null> {
  const meta = await readMeta(turnId, nowMs)
  if (!meta) return null
  if (meta.status !== 'open') return meta
  if (nowMs - meta.lastActivityAtMs < GRACE_WINDOW_MS) return meta

  const closeSeq = meta.maxSeqSeen + 1
  if (meta.openTail && meta.openTail.text) {
    const commitEvent: PariprashnaEvent = {
      type: 'block.commit',
      seq: closeSeq,
      t: nowMs,
      block_id: meta.openTail.blockId,
      text: meta.openTail.text,
    }
    await pushEvent(turnId, commitEvent)
    meta.committedText = meta.committedText ? `${meta.committedText}\n\n${meta.openTail.text}` : meta.openTail.text
    meta.openTail = null
    meta.maxSeqSeen = closeSeq
  }
  const closeEventSeq = meta.maxSeqSeen + 1
  const closeEvent: PariprashnaEvent = {
    type: 'turn.close',
    seq: closeEventSeq,
    t: nowMs,
    turn_id: turnId,
    status: 'aborted',
    ms: nowMs - meta.createdAtMs,
  }
  await pushEvent(turnId, closeEvent)
  meta.maxSeqSeen = closeEventSeq
  meta.status = 'interrupted'
  meta.closedAtMs = nowMs
  meta.lastActivityAtMs = nowMs
  // Mirror appendBufferedEvent's post-trim recompute so minSeqRetained stays
  // accurate even if these synthetic pushes happened to trigger a trim.
  const remaining = await readAllEvents(turnId)
  if (remaining && remaining.length > 0) meta.minSeqRetained = remaining[0].seq
  await writeMeta(meta, nowMs)
  return meta
}

/** Build the single-blob snapshot text a `snapshot.apply` event carries. */
export function buildSnapshotText(meta: TurnBufferMeta): string {
  return [meta.committedText, meta.openTail?.text].filter((s): s is string => !!s).join('\n\n')
}

/** Test/ops helper — never for production request paths. */
export async function __resetRingBufferForTests(): Promise<void> {
  memBuffers.clear()
  memMeta.clear()
}
