import 'server-only'
/**
 * Paripraśna real-reading stream capture — SAMĀPTI lane B-PB8-BYTEEQ,
 * deliverable (b) of `FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE.md`.
 *
 * WHAT PROBLEM THIS SOLVES
 * ────────────────────────
 * BRIEF_PB-2 §G-1 required the canonical byte-equality gate run "against one
 * real deployed reading". It never has, because there was no durable, queryable
 * record of a real reading's raw SSE event stream to replay against its own
 * persisted `message_parts` rows.
 *
 * ONE CORRECTION TO THE FOLLOW-UP'S FRAMING (measured, not assumed).
 * `FOLLOWUP_PB-2…md` §1 item 4 and §3 both say the stream is "emitted to the
 * client and discarded, never logged" / "no mechanism persists a real reading's
 * raw event stream at all". That is REFUTED as worded: PB-2/M-5's
 * `./ring_buffer.ts` already appends EVERY event of EVERY turn (Redis list
 * `parp:buf:<turn_id>`), which is how resume works. What is true — and what
 * actually blocks §G-1 — is that the ring buffer is deliberately EPHEMERAL:
 * capped at `RING_BUFFER_MAX_EVENTS` (500), TTL 600 s open / 180 s closed, gone
 * when Redis is unconfigured, and not queryable after the fact. This module is
 * the durable, sampled, opt-in counterpart. It does not replace the ring buffer
 * and does not change resume behaviour in any way.
 *
 * SAFETY PROPERTIES (this sits on the live streaming hot path)
 * ────────────────────────────────────────────────────────────
 *   • OFF BY DEFAULT — `PARIPRASHNA_STREAM_CAPTURE` must be exactly '1'/'true'.
 *     With the flag unset, `captureEvent` returns before touching the DB and
 *     `beginTurnCapture` never marks a turn, so the cost is one boolean read.
 *   • SAMPLED PER TURN, never per event — a turn is captured whole or not at
 *     all, so a captured turn is always replayable end-to-end. The decision is
 *     made once, at `beginTurnCapture`, and cached for the turn.
 *   • NEVER THROWS, NEVER BLOCKS — every DB call is wrapped and awaited only by
 *     the caller's own fire-and-forget `void`. A capture failure degrades to
 *     "this turn wasn't captured", never to a broken reading. Same discipline
 *     as `ring_buffer.appendBufferedEvent`.
 *   • NO USER TEXT. Verified against `./events.ts`: no member of the
 *     `PariprashnaEvent` union carries the native's question. Captured rows are
 *     assistant-side output + grounding metadata only.
 *   • BOUNDED RETENTION — every row is written with an `expires_at`
 *     (`PARIPRASHNA_STREAM_CAPTURE_RETENTION_DAYS`, default 14) and
 *     `purgeExpiredStreamCaptures()` deletes past it.
 */

import { query } from '@/lib/db/client'
import type { PariprashnaEvent } from './events'

/** Default retention window for a captured turn. */
export const DEFAULT_RETENTION_DAYS = 14

function envFlagOn(raw: string | undefined): boolean {
  return raw === '1' || raw?.toLowerCase() === 'true'
}

/** True only when the deployment has explicitly opted in. */
export function isStreamCaptureEnabled(): boolean {
  return envFlagOn(process.env.PARIPRASHNA_STREAM_CAPTURE)
}

/** Sample rate in [0,1]. Unset ⇒ 1 (capture every turn) — meaningful only when
 *  the feature flag above is already on. */
export function streamCaptureSampleRate(): number {
  const raw = process.env.PARIPRASHNA_STREAM_CAPTURE_SAMPLE
  if (raw === undefined || raw === '') return 1
  const n = Number(raw)
  if (!Number.isFinite(n)) return 0
  return Math.max(0, Math.min(1, n))
}

function retentionDays(): number {
  const raw = process.env.PARIPRASHNA_STREAM_CAPTURE_RETENTION_DAYS
  const n = raw === undefined || raw === '' ? DEFAULT_RETENTION_DAYS : Number(raw)
  return Number.isFinite(n) && n > 0 ? n : DEFAULT_RETENTION_DAYS
}

/**
 * Turns currently marked for capture. Bounded by `endTurnCapture` being called
 * on every terminal event; `MAX_TRACKED_TURNS` is a hard backstop so a leaked
 * turn (a process killed mid-stream) can never grow this without limit.
 */
const MAX_TRACKED_TURNS = 256
const captured = new Map<string, { conversationId: string; chartId: string }>()

/**
 * Decide ONCE, at turn open, whether this turn is captured. Deterministic
 * injection point for `sampler` so the decision is testable without stubbing
 * Math.random globally.
 */
export function beginTurnCapture(
  args: { turnId: string; conversationId: string; chartId: string },
  sampler: () => number = Math.random,
): boolean {
  if (!isStreamCaptureEnabled()) return false
  const rate = streamCaptureSampleRate()
  if (rate <= 0) return false
  if (rate < 1 && sampler() >= rate) return false
  if (captured.size >= MAX_TRACKED_TURNS) {
    // Evict the oldest tracked turn rather than growing without bound. Losing
    // the tail of an abandoned turn is strictly better than an unbounded Map.
    const oldest = captured.keys().next()
    if (!oldest.done) captured.delete(oldest.value)
  }
  captured.set(args.turnId, { conversationId: args.conversationId, chartId: args.chartId })
  return true
}

/** Is this turn being captured? (Cheap, synchronous, no I/O.) */
export function isTurnCaptured(turnId: string): boolean {
  return captured.has(turnId)
}

/** Stop tracking a turn. Safe to call for an uncaptured turn. */
export function endTurnCapture(turnId: string): void {
  captured.delete(turnId)
}

/**
 * Persist one event of a captured turn. No-op (returns immediately) for an
 * uncaptured turn. Never throws.
 *
 * `ON CONFLICT (turn_id, seq) DO NOTHING` — the wire seq is the natural key, so
 * a resume-path re-delivery of an already-captured event is idempotent rather
 * than a duplicate-key error (§N.3 delete-then-insert does not apply here: this
 * is an append-only forensic log, not a rebuildable per-chart asset).
 */
export async function captureEvent(turnId: string, event: PariprashnaEvent): Promise<void> {
  const meta = captured.get(turnId)
  if (!meta) return
  try {
    await query(
      `INSERT INTO pariprashna_stream_capture
         (turn_id, seq, event_type, event, conversation_id, chart_id, expires_at)
       VALUES ($1, $2, $3, $4::jsonb, $5, $6, now() + ($7 || ' days')::interval)
       ON CONFLICT (turn_id, seq) DO NOTHING`,
      [turnId, event.seq, event.type, JSON.stringify(event), meta.conversationId, meta.chartId, String(retentionDays())],
    )
  } catch (err) {
    // Degrade honestly: this turn is simply not (fully) captured. Never let a
    // forensic sink break a live reading.
    console.warn('[stream_capture] event capture failed (non-fatal):', err)
  }
}

export interface CapturedTurn {
  turn_id: string
  conversation_id: string | null
  chart_id: string | null
  events: PariprashnaEvent[]
}

/** Read a captured turn's events back, in wire-seq order. */
export async function readCapturedTurn(turnId: string): Promise<CapturedTurn | null> {
  const { rows } = await query<{ turn_id: string; conversation_id: string | null; chart_id: string | null; event: unknown }>(
    `SELECT turn_id, conversation_id, chart_id, event
       FROM pariprashna_stream_capture
      WHERE turn_id = $1
      ORDER BY seq ASC`,
    [turnId],
  )
  if (rows.length === 0) return null
  return {
    turn_id: rows[0].turn_id,
    conversation_id: rows[0].conversation_id,
    chart_id: rows[0].chart_id,
    events: rows.map((r) => r.event as PariprashnaEvent),
  }
}

/** List captured turn ids, most recent first. */
export async function listCapturedTurns(limit = 20): Promise<{ turn_id: string; captured_at: string; events: number }[]> {
  const { rows } = await query<{ turn_id: string; captured_at: string; events: string }>(
    `SELECT turn_id, max(captured_at) AS captured_at, count(*)::text AS events
       FROM pariprashna_stream_capture
      GROUP BY turn_id
      ORDER BY max(captured_at) DESC
      LIMIT $1`,
    [limit],
  )
  return rows.map((r) => ({ turn_id: r.turn_id, captured_at: r.captured_at, events: Number(r.events) }))
}

/** Retention sweep. Returns the number of rows deleted. */
export async function purgeExpiredStreamCaptures(): Promise<number> {
  const { rowCount } = await query(`DELETE FROM pariprashna_stream_capture WHERE expires_at < now()`, [])
  return rowCount ?? 0
}

/** Test helper — clears the in-process capture marks. Never for production. */
export function __resetStreamCaptureForTests(): void {
  captured.clear()
}
