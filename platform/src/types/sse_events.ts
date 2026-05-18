/**
 * sse_events.ts — Gate III event-schema contract.
 *
 * Despite the file name, these are not raw SSE events. The consume route
 * delivers data through the Vercel AI UI message stream protocol, which
 * already serializes start/finish/text parts. Gate III layers additional
 * payloads on top via:
 *
 *   (a) inline ‹marker› tokens in the streamed prose (parsed client-side),
 *   (b) the messageMetadata({part}) hook on `start` and `finish` parts.
 *
 * This module is the canonical type surface for what each payload looks
 * like, regardless of transport. Consumers (ConsumeChat) reference
 * these types; the marker-parser (lib/consume/
 * marker_parser) produces them.
 */

import type { QueryClass } from '@/lib/jyotish/domain_labels'

// ─── Event-type discriminator ────────────────────────────────────────────────

export type SSEEventType =
  | 'reasoning_step'
  | 'answer_chunk'
  | 'context_usage'
  | 'correction'
  | 'out_of_domain'
  | 'sanskrit_terms'
  | 'provenance'
  | 'conversation_title'
  | 'done'
  | 'error'

// ─── Reasoning narration ─────────────────────────────────────────────────────

export interface ReasoningStepEvent {
  type: 'reasoning_step'
  /** 'pipeline' = pre-synthesis trace step; 'synthesis' = ‹reasoning› marker. */
  phase: 'pipeline' | 'synthesis'
  text: string
  timestamp: number
}

// ─── Answer streaming (default UI message stream) ────────────────────────────

export interface AnswerChunkEvent {
  type: 'answer_chunk'
  delta: string
}

// ─── Per-turn metadata (delivered via messageMetadata) ───────────────────────

export type ContextUsageMode = 'independent' | 'narrative_context' | 'continuation'

export interface ContextUsageEvent {
  type: 'context_usage'
  prior_turns_used: number
  reason: string
  mode: ContextUsageMode
}

export interface CorrectionEvent {
  type: 'correction'
  original_claim: string
  corrected_claim: string
  classical_source?: string
}

export interface OutOfDomainEvent {
  type: 'out_of_domain'
  reason: string
}

export interface SanskritTerm {
  term: string
  definition: string
  transliteration?: string
}

export interface SanskritTermsEvent {
  type: 'sanskrit_terms'
  terms: SanskritTerm[]
}

// ─── Provenance ──────────────────────────────────────────────────────────────

export interface ProvenanceModel {
  /** Pipeline stage: classifier, planner, retrieval, synthesizer, validator… */
  stage: string
  /** User-facing role label (e.g., "Question reader", "Synthesizer"). */
  role: string
  /** Raw model id — visible only inside the technical drawer tab. */
  model_id: string
  latency_ms?: number
  tokens?: number
}

export interface ProvenanceSourceItem {
  id: string
  label: string
}

export interface ProvenanceAstrologicalSource {
  /** Internal asset id (e.g., MSR). NEVER displayed verbatim outside the technical tab. */
  asset: string
  /** User-facing translation via ASSET_LABELS. */
  label: string
  items: ProvenanceSourceItem[]
}

export interface ProvenanceTechnicalTag {
  kind: string
  label: string
  value: string
}

export interface ProvenanceEvent {
  type: 'provenance'
  models: ProvenanceModel[]
  sources: {
    astrological: ProvenanceAstrologicalSource[]
    technical: ProvenanceTechnicalTag[]
  }
}

// ─── Conversation lifecycle ─────────────────────────────────────────────────

export interface ConversationTitleEvent {
  type: 'conversation_title'
  title: string
}

export interface DoneEvent {
  type: 'done'
}

export interface ErrorEvent {
  type: 'error'
  message: string
}

// ─── Discriminated union ─────────────────────────────────────────────────────

export type SSEEvent =
  | ReasoningStepEvent
  | AnswerChunkEvent
  | ContextUsageEvent
  | CorrectionEvent
  | OutOfDomainEvent
  | SanskritTermsEvent
  | ProvenanceEvent
  | ConversationTitleEvent
  | DoneEvent
  | ErrorEvent

// ─── Per-turn metadata bundle (delivered through messageMetadata) ────────────

/**
 * Payload attached to the UI message `start` part. Carries everything we
 * know up front: routing decisions, generated title, context-usage cue.
 */
export interface ConsumeStartMetadata {
  conversationId?: string
  queryId?: string
  query_class?: QueryClass
  context_usage?: ContextUsageEvent
  conversation_title?: string
  // Existing fields preserved (model, stack, style, disclosure_tier, ...) —
  // see app/api/chat/consume/route.ts messageMetadata callback.
}

/**
 * Payload attached to the UI message `finish` part. Carries post-stream
 * artifacts that can be computed only at end (provenance + already-existing
 * methodology block).
 */
export interface ConsumeFinishMetadata {
  methodology_block?: string | null
  provenance?: ProvenanceEvent
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

/**
 * Compact SSE serialization for the trace stream subset. Used only by
 * pipeline_event_translator.ts in client-side tests.
 */
export function serializeSSE<T extends SSEEvent>(event: T): string {
  return `event: ${event.type}\ndata: ${JSON.stringify(event)}\n\n`
}

export function parseSSE(line: string): SSEEvent | null {
  const match = line.match(/^event: (\S+)\ndata: (.+)$/m)
  if (!match) return null
  try {
    return JSON.parse(match[2]) as SSEEvent
  } catch {
    return null
  }
}
