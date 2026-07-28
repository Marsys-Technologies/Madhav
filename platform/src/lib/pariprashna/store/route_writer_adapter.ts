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
 * SCOPE (three kinds only — a disclosed, deliberate narrowing):
 *   text                 <- a committed prose block (block.commit where the
 *                            originating block.open carried role:'prose')
 *   citation              <- a citation.define event / detection
 *   prediction_candidate  <- a server-side prediction-candidate detection
 *                            (`detectPredictionCandidates`, PPL γ3)
 *
 * `tool_call` / `tool_result` / `reasoning` / `attachment` are NOT mapped
 * here. The real wire (`@/lib/pariprashna/protocol/events`) does not carry
 * enough client-visible data to reconstruct them without either (a)
 * violating gate 11 [integrity]'s no-leakage discipline (activity.upsert
 * deliberately carries a resolved reader-safe `label_key`, never the raw
 * `tool_name`/args a `tool_call` body requires) or (b) inventing data not
 * actually available (B.10). This is a disclosed residual for a future lane,
 * not an oversight — see the M-2 report.
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
