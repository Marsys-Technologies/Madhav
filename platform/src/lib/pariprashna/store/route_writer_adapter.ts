/**
 * Route persistence-mapping adapter — PB-2 (SMṚTI) lane M-2.
 *
 * Pure, isomorphic mapping functions from the /api/pariprashna route's OWN
 * in-memory turn data onto M-1's canonical `message_parts` kinds. This is the
 * "persistence-mapping logic" lane M-2's task references: the route
 * (`app/api/pariprashna/route.ts`) calls these functions directly at
 * finalize time to build the `MessagePartInput[]` it hands to M-1's
 * `writeTurn`; lane M-2's byte-equality gate
 * (`tests/pariprashna/reducer/canonical_serialization_golden.test.ts`) ALSO
 * calls these exact functions (the real production mapping) and asserts their
 * output agrees, byte-for-byte after `serializeCanonical`, with an
 * independently-coded client-side reducer simulation.
 *
 * SCOPE, as of lane P3-C (SMṚTI completion):
 *   text                 <- a committed 'prose' block (block.commit where the
 *                            originating block.open carried role:'prose')
 *   reasoning             <- a committed 'thinking' block (same block.commit
 *                            machinery, role:'thinking' — see reading_parts.ts)
 *   tool_call             <- a successful evidence-stage retrieval dispatch
 *                            (`evidence_stage.ts`'s `validToolResults`)
 *   tool_result           <- the outcome of that SAME dispatch
 *   citation              <- a citation.define event / detection
 *   prediction_candidate  <- a server-side prediction-candidate detection
 *                            (`detectPredictionCandidates`, PPL γ3)
 *
 * `attachment` is still NOT mapped here — no wire event and no in-memory
 * turn data carries one today (B.10: nothing to map without inventing it).
 *
 * `tool_call`/`tool_result` DISCLOSED NARROWING (still real, not closed by
 * this lane):
 *   - only SUCCESSFUL dispatches are representable — `evidence_stage.ts`
 *     filters a failed dispatch out of `validToolResults` before this module
 *     ever sees it (the failure is only visible in that stage's local
 *     `toolEventLog`, which is not threaded through to persistence yet);
 *   - `tool_result.body.result` (the actual retrieved content) is
 *     intentionally omitted — only call/outcome metadata (status/count/ms)
 *     is persisted. `tool_name`/`args` on `tool_call` MUST already be
 *     resolved to the reader-safe label and leak-scrubbed by the CALLER
 *     (`reading_parts.ts`'s `resolveActivityLabel`/`scrubToolArgs`) — these
 *     two mapping functions stay pure and do not re-derive either, matching
 *     every other function in this file.
 *   - `reasoning`/`tool_call`/`tool_result` are NOT reconstructable from the
 *     wire alone the way `text`/`citation` are (activity.upsert carries only
 *     the resolved label, never raw tool_name/args — gate 11 [integrity]),
 *     so `store/replay_paths.ts`'s wire-replay path covers `reasoning`
 *     (block.open/block.commit DO carry `role` on the wire) but not
 *     `tool_call`/`tool_result` — see that module's own header.
 *   - PASS-1-ONLY: `buildCanonicalParts` (`reading_parts.ts`) is fed
 *     `evidence_stage.ts`'s `validToolResults`, which is retrieval PASS 1
 *     only. The synthesis stage runs its own agentic tool loop
 *     (`synthesis_stage.ts`'s `useAgenticLoop`, true for every provider in
 *     `AGENTIC_PROVIDERS` — which includes `'google'`, the production
 *     default — for up to 8 iterations) that re-enters retrieval; passes
 *     2..N's tool calls are real (observed re-entering `phase retrieve` at
 *     `pass_id= 2`, `pass_id= 3`, …) but are never threaded back into
 *     `validToolResults` and so never reach `tool_call`/`tool_result` parts —
 *     no fixture exercises them. A persisted turn's tool_call/tool_result
 *     rows are a first-pass-only account of the turn's retrieval, not a
 *     complete one; a reader of the canonical store must not assume the
 *     persisted set is exhaustive.
 *   - `ToolResultFromDispatch.status` is typed `'done' | 'error'` but
 *     `reading_parts.ts`'s only caller hardcodes `status: 'done'` — nothing
 *     in this lane ever produces `'error'`, so that variant currently has no
 *     producer and the field can never read false from this path.
 */

import type { MessagePartInput } from './schema'

// ---------------------------------------------------------------------------
// text — from a committed prose block
// ---------------------------------------------------------------------------

export interface CommittedProseBlock {
  block_id: string
  text: string
}

/**
 * Map one committed prose block to a canonical `text` part.
 * `model_visible: true` — this is the reader-visible assistant prose the
 * model itself should see when this turn is replayed into future context.
 */
export function textPartFromBlock(block: CommittedProseBlock, seq: number): MessagePartInput {
  return {
    seq,
    kind: 'text',
    body: { text: block.text, block_id: block.block_id },
    model_visible: true,
  }
}

// ---------------------------------------------------------------------------
// citation — from a citation.define event / detection
// ---------------------------------------------------------------------------

export interface DetectedCitation {
  index: number
  signal_id: string
  layer: string
  snippet: string
  reader_label?: string
  grade?: string
}

/**
 * Map one detected citation to a canonical `citation` part.
 * `model_visible: false` — a citation is metadata ABOUT the prose (the
 * grounding annotation), not verbatim text the model re-reads as its own
 * prior utterance.
 */
export function citationPartFromDetection(c: DetectedCitation, seq: number): MessagePartInput {
  return {
    seq,
    kind: 'citation',
    body: {
      index: c.index,
      signal_id: c.signal_id,
      layer: c.layer,
      snippet: c.snippet,
      ...(c.reader_label !== undefined ? { reader_label: c.reader_label } : {}),
      ...(c.grade !== undefined ? { grade: c.grade } : {}),
    },
    model_visible: false,
  }
}

// ---------------------------------------------------------------------------
// prediction_candidate — from a server-side detection
// ---------------------------------------------------------------------------

export interface DetectedPredictionCandidate {
  text: string
  score: number
  horizon: string | null
}

/**
 * Map one server-side prediction-candidate detection to a canonical
 * `prediction_candidate` part.
 *
 * NOTE (disclosed asymmetry): this is fed from the route's OWN structured
 * detection (`detectPredictionCandidates` output), never from the wire — the
 * real `PariprashnaEvent` union has no dedicated prediction-candidate event;
 * the route surfaces a candidate to the CLIENT only as a formatted `flag`
 * info string (`${text} (score=${score}[, horizon=${horizon}])`). A client
 * reducer can at best regex-parse that string back into approximate parts
 * (lossy, format-coupled); it cannot independently derive a schema-true
 * `prediction_candidate` body the way it can for `text`/`citation`. See the
 * M-2 report for why this kind is a disclosed residual for the
 * reducer<->writer cross-check, not a silent gap.
 *
 * `model_visible: false` — an internal detection annotation, not prose the
 * model re-reads verbatim.
 */
export function predictionCandidatePartFromDetection(
  c: DetectedPredictionCandidate,
  seq: number,
): MessagePartInput {
  return {
    seq,
    kind: 'prediction_candidate',
    body: {
      claim: c.text,
      confidence: Math.max(0, Math.min(1, c.score)),
      ...(c.horizon !== null && c.horizon !== undefined ? { window: c.horizon } : {}),
      source_flag_code: 'prediction_candidate',
    },
    model_visible: false,
  }
}

// ---------------------------------------------------------------------------
// reasoning — from a committed 'thinking' block (lane P3-C)
// ---------------------------------------------------------------------------

export interface CommittedThinkingBlock {
  block_id: string
  text: string
}

/**
 * Map one committed 'thinking' block to a canonical `reasoning` part.
 *
 * `model_visible: false` — mirrors the live route's own discipline for
 * thinking text: `ReadingPartsAssembler.accumulatedText` (reading_parts.ts)
 * deliberately EXCLUDES thinking deltas, so thinking text never re-enters
 * future model context as the assistant's own prior utterance; persisting it
 * as `model_visible: false` keeps that same boundary on the canonical record.
 *
 * `signature`/`provider_opaque` (see schema.ts's `ReasoningBodySchema`) are
 * left unset — this codebase has no provider-native reasoning metadata
 * plumbed to this layer today. Leaving them unset is the honest choice
 * (B.10): a fabricated signature would be worse than an absent one.
 */
export function reasoningPartFromBlock(block: CommittedThinkingBlock, seq: number): MessagePartInput {
  return {
    seq,
    kind: 'reasoning',
    body: { text: block.text, block_id: block.block_id },
    model_visible: false,
  }
}

// ---------------------------------------------------------------------------
// tool_call / tool_result — from a successful evidence-stage dispatch
// (lane P3-C). See this file's header for the disclosed narrowing.
// ---------------------------------------------------------------------------

export interface ToolCallFromDispatch {
  call_id: string
  /** MUST already be the resolved, reader-safe label (gate 11 [integrity]) —
   *  this function does not call `resolveActivityLabel` itself. */
  tool_name: string
  /** MUST already be leak-scrubbed by the caller (`reading_parts.ts`'s
   *  `scrubToolArgs`) — this function does not lint it itself. */
  args: Record<string, unknown>
}

/**
 * Map one successful evidence-stage tool dispatch to a canonical `tool_call`
 * part. `model_visible: false` — an internal audit annotation (what was
 * asked of a tool), not reader prose the model replays verbatim.
 */
export function toolCallPartFromBundle(input: ToolCallFromDispatch, seq: number): MessagePartInput {
  return {
    seq,
    kind: 'tool_call',
    body: { call_id: input.call_id, tool_name: input.tool_name, args: input.args },
    model_visible: false,
  }
}

export interface ToolResultFromDispatch {
  call_id: string
  status: 'done' | 'error'
  count?: number
  ms?: number
}

/**
 * Map one evidence-stage dispatch OUTCOME to a canonical `tool_result` part.
 * `result` (schema.ts's `ToolResultBodySchema.result`) is deliberately left
 * unset — see this file's header "disclosed narrowing" note; only
 * status/count/ms are populated. `model_visible: false`, matching `tool_call`.
 */
export function toolResultPartFromBundle(input: ToolResultFromDispatch, seq: number): MessagePartInput {
  return {
    seq,
    kind: 'tool_result',
    body: {
      call_id: input.call_id,
      status: input.status,
      ...(input.count !== undefined ? { count: input.count } : {}),
      ...(input.ms !== undefined ? { ms: input.ms } : {}),
    },
    model_visible: false,
  }
}
