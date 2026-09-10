/**
 * Replay a Paripraśna wire event stream into canonical `message_parts` —
 * SAMĀPTI lane B-PB8-BYTEEQ.
 *
 * Isomorphic + pure (no `server-only`, no I/O, no clock). This is PRODUCTION
 * code, not a test helper, and it is deliberately the ONE definition of
 * "wire stream → canonical parts" in the tree:
 *
 *   • `tests/pariprashna/reducer/canonical_serialization_golden.test.ts` and
 *     `…/canonical_serialization_corpus.test.ts` drive it as the WRITER side of
 *     the byte-equality gate (the REDUCER side stays an independently-coded
 *     test-owned simulation — that independence is the whole point of the gate);
 *   • `scripts/pariprashna/verify_captured_turn.ts` drives it to replay a REAL
 *     captured reading against that reading's own persisted rows.
 *
 * ORDERING CONTRACT — mirrors `app/api/pariprashna/route.ts`'s `writeMessages`
 * seam exactly: every committed prose block first (`for (const b of
 * committedBlocks)`), then every citation, then every prediction candidate.
 * NOT wire order. `canonical_serialization_corpus.test.ts` gates both this
 * ordering and route.ts's, so the two cannot drift apart silently.
 *
 * COMMIT CONTRACT — only a COMMITTED prose block becomes a `text` part;
 * route.ts persists `committedBlocks` and nothing else, so an opened-but-never-
 * committed block (stopped / disconnected turn) contributes nothing.
 *
 * WHAT IT CANNOT DO FROM THE WIRE ALONE (disclosed, not silently absent).
 * `prediction_candidate` parts are built from the SERVER's own structured
 * detection, which never rides the wire — the client only ever sees a flattened
 * `flag{code:'prediction_candidate'}` string. Callers must supply the
 * detections; `predictionCandidatesFromWireFlags` reconstructs them
 * best-effort from the flag string for replay contexts where the structured
 * detection is unavailable, and reports what it could not parse.
 *
 * `tool_call`/`tool_result` (lane P3-C, `route_writer_adapter.ts`) are ALSO
 * not replayable from the wire alone — `activity.upsert` deliberately carries
 * only the resolved reader-safe label (gate 11 [integrity]), never the raw
 * `tool_name`/`invocation_params` a `tool_call` body requires — so this
 * function does not attempt them; a caller comparing a wire-replayed turn
 * against its persisted canonical parts must expect the persisted side to
 * carry MORE than the replayed side for these two kinds. This is the same
 * class of disclosed asymmetry as `prediction_candidate` above, not a new one.
 *
 * `reasoning` (lane P3-C) IS wire-derivable and IS covered here: a
 * `block.open` event carries `role`, so a 'thinking' block's later
 * `block.commit` can be told apart from a 'prose' one exactly the way this
 * function already tracks `blockRoleById` for the existing prose case.
 */

import type { PariprashnaEvent } from '../protocol/events'
import type { MessagePartInput } from './schema'
import {
  textPartFromBlock,
  citationPartFromDetection,
  predictionCandidatePartFromDetection,
  reasoningPartFromBlock,
  type DetectedCitation,
  type DetectedPredictionCandidate,
} from './route_writer_adapter'

/** route.ts's own persistence filter — see its `predictionCandidatesFound`. */
export const PREDICTION_SCORE_FLOOR = 0.5

/**
 * Replay a wire event stream into canonical parts using the REAL production
 * mapping functions, in route.ts's kind-grouped order.
 */
export function replayCanonicalParts(
  events: readonly PariprashnaEvent[],
  predictionCandidates: readonly DetectedPredictionCandidate[] = [],
): MessagePartInput[] {
  const blockRoleById = new Map<string, 'prose' | 'thinking'>()
  /** Committed blocks (prose AND thinking, lane P3-C), in commit order —
   *  route.ts's `committedBlocks`. */
  const committedBlocks: { block_id: string; text: string; role: 'prose' | 'thinking' }[] = []
  const citations: DetectedCitation[] = []

  for (const event of events) {
    if (event.type === 'block.open') {
      blockRoleById.set(event.block_id, event.role)
    } else if (event.type === 'block.commit') {
      const role = blockRoleById.get(event.block_id)
      if (role === 'prose' || role === 'thinking') {
        committedBlocks.push({ block_id: event.block_id, text: event.text, role })
      }
    } else if (event.type === 'citation.define') {
      citations.push({
        index: event.index,
        signal_id: event.signal_id,
        layer: event.layer,
        snippet: event.snippet,
        ...(event.reader_label !== undefined ? { reader_label: event.reader_label } : {}),
        ...(event.grade !== undefined ? { grade: event.grade } : {}),
      })
    }
  }

  const parts: MessagePartInput[] = []
  let seq = 0
  for (const b of committedBlocks) {
    if (b.role === 'prose') parts.push(textPartFromBlock(b, seq++))
    else parts.push(reasoningPartFromBlock(b, seq++))
  }
  for (const c of citations) parts.push(citationPartFromDetection(c, seq++))
  for (const c of predictionCandidates) parts.push(predictionCandidatePartFromDetection(c, seq++))
  return parts
}

/**
 * Regex-reconstruction of route.ts's
 * `${text} (score=${score}[, horizon=${horizon}])` flag-detail format.
 * Returns null when the string does not parse — the format-coupling fragility
 * the M-2 golden test demonstrates directly. Exported because both the gate and
 * the real-reading comparator need the SAME parse, not two of them.
 */
export function parsePredictionFlagDetail(
  detail: string,
): { claim: string; score: number; horizon: string | null } | null {
  const m = /^(.*) \(score=([\d.]+)(?:, horizon=(.+))?\)$/.exec(detail)
  if (!m) return null
  return { claim: m[1], score: Number(m[2]), horizon: m[3] ?? null }
}

export interface WirePredictionReconstruction {
  /** Detections that parsed AND cleared route.ts's persistence floor. */
  kept: DetectedPredictionCandidate[]
  /** Parsed but below `PREDICTION_SCORE_FLOOR` — route.ts would not persist these. */
  belowFloor: number
  /** Flag details that could not be parsed at all. */
  unparseable: string[]
}

/**
 * Best-effort reconstruction of the writer's prediction-candidate input from
 * the wire's flattened flags, applying route.ts's own `score >= 0.5` filter so
 * a comparison isolates real divergence rather than re-reporting a documented,
 * intentional filter. Lossy by construction — see the module header.
 */
export function predictionCandidatesFromWireFlags(
  events: readonly PariprashnaEvent[],
): WirePredictionReconstruction {
  const kept: DetectedPredictionCandidate[] = []
  const unparseable: string[] = []
  let belowFloor = 0
  for (const e of events) {
    if (e.type !== 'flag' || e.code !== 'prediction_candidate' || !e.detail) continue
    const parsed = parsePredictionFlagDetail(e.detail)
    if (!parsed) {
      unparseable.push(e.detail)
      continue
    }
    if (parsed.score < PREDICTION_SCORE_FLOOR) {
      belowFloor += 1
      continue
    }
    kept.push({ text: parsed.claim, score: parsed.score, horizon: parsed.horizon })
  }
  return { kept, belowFloor, unparseable }
}
