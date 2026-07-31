/**
 * Real-reading byte-equality comparator core — SAMĀPTI lane B-PB8-BYTEEQ,
 * deliverable (b) of `FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE.md`.
 *
 * Pure + isomorphic. Given a REAL reading's captured wire stream and that same
 * reading's persisted canonical message + parts, decide whether replaying the
 * stream through the production mapping reproduces the persisted rows
 * BYTE-FOR-BYTE — the comparison `store/serialize.ts`'s own header describes
 * ("(a) replay the event stream … vs (b) read the persisted message_parts rows
 * back from the DB") and which BRIEF_PB-2 §G-1 demanded but never got.
 *
 * All I/O lives in `scripts/pariprashna/verify_captured_turn.ts`; this file is
 * pure so it is directly testable without a database.
 *
 * KNOWN PRE-EXISTING ASYMMETRIES this comparator is expected to surface. They
 * are properties of `app/api/pariprashna/route.ts` today, NOT of this tool:
 *   • citation — the WIRE's `citation.define` comes from the write-through's
 *     `data-citation` parts; the WRITER independently re-derives citations with
 *     `extractCitations(accumulatedText)` + `fetchMsrSnippets`. Two derivations
 *     of the same fact. Disagreement IS the finding.
 *   • prediction_candidate — the wire carries a flattened flag string for every
 *     detection; the writer persists only `score >= 0.5`. The reconstruction in
 *     `replay_paths.ts` applies the same floor, so only genuine divergence is
 *     reported.
 *   • text — both sides use committed prose blocks. No asymmetry.
 */

import type { PariprashnaEvent } from '../protocol/events'
import type { CanonicalMessage, MessagePartInput, PersistedMessagePart } from './schema'
import { serializeCanonical, serializeCanonicalObject } from './serialize'
import { predictionCandidatesFromWireFlags, replayCanonicalParts } from './replay_paths'

export type ReplayComparisonStatus =
  /** Replayed stream and persisted rows serialize identically. */
  | 'byte_identical'
  /** They differ — a real finding, itemised in `diffs`. */
  | 'diverged'
  /** The comparison could not be attempted. NEVER conflate with a pass. */
  | 'not_comparable'

export interface ReplayPartDiff {
  index: number
  kind: string | null
  replayed: string | null
  persisted: string | null
}

export interface ReplayComparison {
  status: ReplayComparisonStatus
  /** Populated only when status is `not_comparable`. */
  reason?: string
  turn_id: string
  message_id: string | null
  captured_events: number
  replayed_parts: number
  persisted_parts: number
  /** Wire prediction flags parsed but below route.ts's persistence floor. */
  predictions_below_floor: number
  /** Wire prediction flag details that could not be parsed at all. */
  predictions_unparseable: string[]
  diffs: ReplayPartDiff[]
  replayed_serialized: string | null
  persisted_serialized: string | null
}

export type ComparatorIdentity = Pick<
  CanonicalMessage,
  'id' | 'conversation_id' | 'role' | 'schema_version' | 'model_id' | 'provider'
>

function diffParts(replayed: MessagePartInput[], persisted: PersistedMessagePart[], identity: ComparatorIdentity): ReplayPartDiff[] {
  const a = serializeCanonicalObject(identity, replayed).parts
  const b = serializeCanonicalObject(identity, persisted).parts
  const out: ReplayPartDiff[] = []
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    const lj = a[i] ? JSON.stringify(a[i]) : null
    const rj = b[i] ? JSON.stringify(b[i]) : null
    if (lj === rj) continue
    out.push({ index: i, kind: a[i]?.kind ?? b[i]?.kind ?? null, replayed: lj, persisted: rj })
  }
  return out
}

/** Build a `not_comparable` result. Kept explicit so no caller can accidentally
 *  report "couldn't check" as "checked and fine". */
export function notComparable(turnId: string, reason: string): ReplayComparison {
  return {
    status: 'not_comparable',
    reason,
    turn_id: turnId,
    message_id: null,
    captured_events: 0,
    replayed_parts: 0,
    persisted_parts: 0,
    predictions_below_floor: 0,
    predictions_unparseable: [],
    diffs: [],
    replayed_serialized: null,
    persisted_serialized: null,
  }
}

/**
 * The comparison itself. `events` is the captured wire stream in seq order;
 * `persistedParts` is what `readTurnParts(message.id)` returned.
 */
export function compareReplayAgainstPersisted(args: {
  turnId: string
  events: readonly PariprashnaEvent[]
  message: ComparatorIdentity
  persistedParts: PersistedMessagePart[]
}): ReplayComparison {
  const { turnId, events, message, persistedParts } = args
  const predictions = predictionCandidatesFromWireFlags(events)
  const replayedParts = replayCanonicalParts(events, predictions.kept)

  const replayed = serializeCanonical(message, replayedParts)
  const persisted = serializeCanonical(message, persistedParts)

  return {
    status: replayed === persisted ? 'byte_identical' : 'diverged',
    turn_id: turnId,
    message_id: message.id,
    captured_events: events.length,
    replayed_parts: replayedParts.length,
    persisted_parts: persistedParts.length,
    predictions_below_floor: predictions.belowFloor,
    predictions_unparseable: predictions.unparseable,
    diffs: replayed === persisted ? [] : diffParts(replayedParts, persistedParts, message),
    replayed_serialized: replayed,
    persisted_serialized: persisted,
  }
}

/** Human-readable report for the CLI. */
export function formatReplayComparison(c: ReplayComparison): string {
  const lines: string[] = []
  lines.push(`turn_id           ${c.turn_id}`)
  lines.push(`message_id        ${c.message_id ?? '<none>'}`)
  if (c.status === 'not_comparable') {
    lines.push(`\nRESULT: NOT COMPARABLE — ${c.reason}`)
    lines.push('(This is exit code 2, deliberately not 0: "we could not check" must never read as "it passed".)')
    return lines.join('\n')
  }
  lines.push(`captured events   ${c.captured_events}`)
  lines.push(`replayed parts    ${c.replayed_parts}`)
  lines.push(`persisted parts   ${c.persisted_parts}`)
  if (c.predictions_below_floor > 0) {
    lines.push(`note              ${c.predictions_below_floor} wire prediction flag(s) below route.ts's 0.5 persistence floor (excluded on both sides, by design)`)
  }
  for (const d of c.predictions_unparseable) {
    lines.push(`note              UNPARSEABLE prediction flag detail (format-coupling, see the M-2 golden test): ${JSON.stringify(d)}`)
  }
  if (c.status === 'byte_identical') {
    lines.push('\nRESULT: BYTE-IDENTICAL — replayed stream === persisted message_parts.')
    return lines.join('\n')
  }
  lines.push('\nRESULT: DIVERGED.\n')
  for (const d of c.diffs) {
    lines.push(`part[${d.index}] (${d.kind ?? 'unknown kind'})`)
    lines.push(`  replayed(stream) : ${d.replayed ?? '<absent>'}`)
    lines.push(`  persisted(db)    : ${d.persisted ?? '<absent>'}`)
  }
  return lines.join('\n')
}

/** 0 = byte-identical · 1 = diverged · 2 = not comparable. */
export function exitCodeFor(c: ReplayComparison): 0 | 1 | 2 {
  if (c.status === 'byte_identical') return 0
  if (c.status === 'diverged') return 1
  return 2
}
