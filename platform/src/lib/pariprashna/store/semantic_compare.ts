/**
 * Semantic-hash replay↔persistence comparator — P2-D (PPR-10, FD-9).
 *
 * The REPLACEMENT invariant for `replay_compare.ts`'s byte-equality
 * comparator (kept in place for diagnostic use; see its header and
 * `semantic_hash.ts`'s header for the full "why byte equality was rejected"
 * record). Same INPUTS as the byte-equality comparator — a captured turn's
 * raw wire events (the PR-#927 / SAMĀPTI B-PB8-BYTEEQ capture apparatus:
 * `protocol/stream_capture.ts` writes them, `scripts/pariprashna/
 * verify_captured_turn.ts` reads them back) replayed through the SAME
 * production mapping (`replay_paths.ts`'s `replayCanonicalParts`) — but the
 * DECISION is normalized-semantic-hash equality, not raw string equality.
 *
 * This is the "repurposed as the comparator's feed" half of PPR-10: nothing
 * about the capture mechanism changes (still off by default, still sampled,
 * still bounded-retention) — only what gets DONE with what it feeds is new.
 *
 * RED_TEAM_G0 C-F7 disposition (ACCEPTED): "repurposed as the semantic-hash
 * comparator's capture feed; FD-9 closes against the new invariant." This
 * module is that closure.
 */

import type { PariprashnaEvent } from '../protocol/events'
import type { CanonicalMessage, MessagePartInput, PersistedMessagePart } from './schema'
import { predictionCandidatesFromWireFlags, replayCanonicalParts } from './replay_paths'
import {
  computeSemanticHash,
  normalizeForDiagnostics,
  normalizeForSemanticHash,
} from './semantic_hash'

export type SemanticComparisonStatus =
  /** Replayed stream and persisted rows are semantically equivalent — same
   *  hash. Presentation-only differences (if any) are still reported. */
  | 'semantic_match'
  /** A real content divergence — different hash. Itemised in `diffs`. */
  | 'semantic_diverged'
  /** The comparison could not be attempted. NEVER conflated with a pass. */
  | 'not_comparable'

export interface SemanticPartDiff {
  index: number
  kind: string | null
  /** 'identity' = a real content divergence (part of the hash).
   *  'presentation_only' = same fact, differently phrased (NOT part of the
   *  hash) — still surfaced, per B.10, never silently dropped. */
  diff_class: 'identity' | 'presentation_only'
  replayed: string | null
  persisted: string | null
}

export interface SemanticComparison {
  status: SemanticComparisonStatus
  reason?: string
  turn_id: string
  message_id: string | null
  captured_events: number
  replayed_parts: number
  persisted_parts: number
  predictions_below_floor: number
  predictions_unparseable: string[]
  replayed_hash: string | null
  persisted_hash: string | null
  diffs: SemanticPartDiff[]
}

export type ComparatorIdentity = Pick<
  CanonicalMessage,
  'id' | 'conversation_id' | 'role' | 'schema_version' | 'model_id' | 'provider'
>

function partsByIdentity(view: { parts: Array<{ seq: number; kind: string; body: unknown }> }) {
  return view.parts
}

/**
 * Diagnostic diff between the two sides' FULL normalized form (presentation
 * included), tagged by whether the divergence is inside the hash-eligible
 * identity fields or only in presentation. A part present on one side and
 * absent on the other is always `identity` (that IS a real divergence — a
 * missing/extra part is never "just presentation").
 */
function diffParts(
  replayed: MessagePartInput[],
  persisted: PersistedMessagePart[],
  identity: ComparatorIdentity,
): SemanticPartDiff[] {
  const diag = {
    a: partsByIdentity(normalizeForDiagnostics(identity, replayed)),
    b: partsByIdentity(normalizeForDiagnostics(identity, persisted)),
  }
  const hashable = {
    a: partsByIdentity(normalizeForSemanticHash(identity, replayed)),
    b: partsByIdentity(normalizeForSemanticHash(identity, persisted)),
  }
  const out: SemanticPartDiff[] = []
  for (let i = 0; i < Math.max(diag.a.length, diag.b.length); i++) {
    const dj = diag.a[i] ? JSON.stringify(diag.a[i]) : null
    const dk = diag.b[i] ? JSON.stringify(diag.b[i]) : null
    if (dj === dk) continue
    const hj = hashable.a[i] ? JSON.stringify(hashable.a[i]) : null
    const hk = hashable.b[i] ? JSON.stringify(hashable.b[i]) : null
    const isIdentityDiff = hj !== hk || dj === null || dk === null
    out.push({
      index: i,
      kind: diag.a[i]?.kind ?? diag.b[i]?.kind ?? null,
      diff_class: isIdentityDiff ? 'identity' : 'presentation_only',
      replayed: dj,
      persisted: dk,
    })
  }
  return out
}

/** Build a `not_comparable` result. Kept explicit — §N.8: "couldn't check"
 *  must never read as "checked and fine". */
export function notComparableSemantic(turnId: string, reason: string): SemanticComparison {
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
    replayed_hash: null,
    persisted_hash: null,
    diffs: [],
  }
}

/**
 * The comparison. `events` is a captured turn's wire stream in seq order
 * (the PR-#927 capture feed, read via `readCapturedTurn`); `persistedParts`
 * is what `readTurnParts(message.id)` returned. Pure — no I/O; callers own
 * fetching both sides.
 */
export function compareSemanticEquivalence(args: {
  turnId: string
  events: readonly PariprashnaEvent[]
  message: ComparatorIdentity
  persistedParts: PersistedMessagePart[]
}): SemanticComparison {
  const { turnId, events, message, persistedParts } = args
  const predictions = predictionCandidatesFromWireFlags(events)
  const replayedParts = replayCanonicalParts(events, predictions.kept)

  const replayedHash = computeSemanticHash(message, replayedParts)
  const persistedHash = computeSemanticHash(message, persistedParts)
  const match = replayedHash === persistedHash

  return {
    status: match ? 'semantic_match' : 'semantic_diverged',
    turn_id: turnId,
    message_id: message.id,
    captured_events: events.length,
    replayed_parts: replayedParts.length,
    persisted_parts: persistedParts.length,
    predictions_below_floor: predictions.belowFloor,
    predictions_unparseable: predictions.unparseable,
    replayed_hash: replayedHash,
    persisted_hash: persistedHash,
    // Diffs are computed even on a match, in case only presentation-only
    // divergences exist — B.10: never silently drop a real difference just
    // because it did not move the hash.
    diffs: diffParts(replayedParts, persistedParts, message),
  }
}

/** Human-readable report, mirroring `formatReplayComparison`'s shape. */
export function formatSemanticComparison(c: SemanticComparison): string {
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
  lines.push(`replayed hash     ${c.replayed_hash}`)
  lines.push(`persisted hash    ${c.persisted_hash}`)
  const identityDiffs = c.diffs.filter((d) => d.diff_class === 'identity')
  const presentationDiffs = c.diffs.filter((d) => d.diff_class === 'presentation_only')
  if (presentationDiffs.length > 0) {
    lines.push(`note              ${presentationDiffs.length} presentation-only diff(s) — same fact, independently re-derived text (documented asymmetry, does not fail the invariant)`)
  }
  if (c.status === 'semantic_match') {
    lines.push('\nRESULT: SEMANTIC MATCH — replayed stream and persisted message_parts are equivalent.')
    return lines.join('\n')
  }
  lines.push('\nRESULT: SEMANTIC DIVERGENCE.\n')
  for (const d of identityDiffs) {
    lines.push(`part[${d.index}] (${d.kind ?? 'unknown kind'}) [IDENTITY — real content divergence]`)
    lines.push(`  replayed(stream) : ${d.replayed ?? '<absent>'}`)
    lines.push(`  persisted(db)    : ${d.persisted ?? '<absent>'}`)
  }
  return lines.join('\n')
}

/** 0 = semantic match · 1 = diverged · 2 = not comparable. */
export function exitCodeForSemantic(c: SemanticComparison): 0 | 1 | 2 {
  if (c.status === 'semantic_match') return 0
  if (c.status === 'semantic_diverged') return 1
  return 2
}
