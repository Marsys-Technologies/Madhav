/**
 * MARSYS-JIS Stream D — Synthesis Orchestrator shared types
 * schema_version: 1.1 (Phase 6 — adds checkpoint payload fields to audit event)
 */

import type { QueryPlan } from '@/lib/router/types'
import type { Bundle } from '@/lib/bundle/types'
// D7 migration Step 3: ToolBundle sourced from lib/retrieve/types (canonical until Step 4 deletion).
// When lib/retrieve is retired, update to ToolResult from @/lib/retrieval/registry/types.
import type { ToolBundle } from '@/lib/retrieval/shared_types'
import type { RequestScopedToolCache } from '@/lib/cache/index'
import type { AudienceTier, StyleSuffix } from '@/lib/prompts/types'
import type { ValidationResult } from '@/lib/validators/types'
import type { StreamTextResult, ToolSet, ModelMessage } from 'ai'
import type {
  Checkpoint45Result,
  Checkpoint55Result,
  Checkpoint85Result,
  StructuredPrediction,
} from '@/lib/checkpoints/types'

export type { AudienceTier, StyleSuffix }

export interface ChartContext {
  name: string
  birth_date: string  // ISO YYYY-MM-DD
  birth_time: string  // HH:MM (24h)
  birth_place: string // e.g. "Bhubaneswar, Odisha, India"
}

/**
 * Legacy wrapping bundle from the prior intermediate compression step.
 * Retired in Pipeline-Transform-S1; the type is kept for any downstream
 * audit/historical readers that still reference its shape.
 */
export interface ContextBundle {
  tool_bundles: ToolBundle[]
  context_assembly_compressed: true
  context_assembly_model_id: string
  context_assembly_latency_ms: number
  l1_tokens: number
  l2_5_tokens: number
  l4_tokens: number
  vector_tokens: number
  cgm_tokens: number
  total_tokens: number
}

export interface SynthesisRequest {
  query: string
  query_plan: QueryPlan
  bundle: Bundle
  tool_results: ToolBundle[]
  conversation_history: ModelMessage[]
  selected_model_id: string
  style: StyleSuffix
  audience_tier: AudienceTier
  cache: RequestScopedToolCache
  /** Phase 12 (FUB-1): canonical birth particulars for the native. Optional — callers that
   *  don't provide it fall back to placeholder strings rather than crashing. */
  chart_context?: ChartContext
  /** Trace: conversation scope for query_trace_steps DB writes. Optional — absent means
   *  trace steps are written without conversation_id (still queryable by query_id). */
  conversation_id?: string
  /** Phase 4: optional consumer callback. When AUDIT_ENABLED, route.ts wires this. */
  onAuditEvent?: (event: SynthesisAuditEvent) => void
  /** Phase 7: per-query opt-in for panel synthesis. Only active when PANEL_MODE_ENABLED=true. */
  panel_opt_in?: boolean
  /** UQE-9 (W2-BUGS B2W-7): pre-allocated step_seq for the context_assembly trace
   *  step. When present the orchestrator uses it; otherwise falls back to the
   *  legacy `3 + nToolSteps` arithmetic. */
  context_assembly_seq?: number
  /** UQE-9 (W2-BUGS B2W-7): pre-allocated step_seq for the synthesis trace step
   *  (start + done share this value). Falls back to `3 + nToolSteps + 1` when absent. */
  synthesis_seq?: number
  /** BUG-2: callback fired from single_model_strategy onFinish with the
   *  synthesis-stage ValidationResult[]. Called before onAuditEvent so the
   *  audit consumer's validator_results array is populated in time. */
  onValidatorResults?: (results: ValidationResult[]) => void
  /** Phase 3: planner-emitted synthesis guidance (replaces context_assembler).
   *  When present, single_model_strategy appends it to the system prompt as a
   *  separator + guidance block. Absent for trivial factual queries. */
  synthesis_guidance?: string
  /** PIV HIGH.QG6.2: forwarded from the incoming HTTP request so that a client
   *  SSE disconnect cancels the upstream LLM call, stopping token billing. */
  abortSignal?: AbortSignal
  /** β5: extra content parts (images, PDF text) appended to the user query message.
   *  When present, the user turn content becomes an array instead of a plain string. */
  attachment_parts?: Array<
    | { type: 'image'; image: string; mimeType: string }
    | { type: 'text'; text: string }
  >
  /** γ7: called on each text-delta from the synthesis stream for stream-resume
   *  accumulation (pending_streams table). Non-blocking — failures are swallowed
   *  inside createPendingStreamWriter. */
  onTextDelta?: (delta: string) => void
  /** R9-S1: Project identifier for the conversation, if it belongs to a project.
   *  Written into the query_trace for observability. Only populated when
   *  MARSYS_FLAG_R9_PROJECTS=true. */
  project_id?: string
  /** R9-S1: Project-scoped system prompt addition. When MARSYS_FLAG_R9_PROJECTS=true
   *  and the conversation belongs to a project with a non-empty system_prompt_addition,
   *  this is prepended to the synthesis prompt as a [PROJECT CONTEXT] block. */
  project_system_prompt_addition?: string
  /** R9-S3: Active persona identifier. Written into query_trace under persona_injection. */
  persona_id?: string
  /** R9-S3: Active persona system prompt. Prepended first (before project addition)
   *  when MARSYS_FLAG_R9_PERSONAS=true. Order: persona → project → main prompt. */
  persona_system_prompt?: string
}

export interface SynthesisMetadata {
  synthesis_prompt_version: string
  synthesizer_model_id: string
  bundle_hash: string
  started_at: string
}

/**
 * Phase 6 checkpoint payloads nested under audit event.
 * Stored as opaque JSONB by Phase 4's v1 consumer — no schema bump required.
 */
export interface CheckpointPayloads {
  c4_5?: Checkpoint45Result
  c5_5?: Checkpoint55Result
  c8_5?: Checkpoint85Result
}

export interface SynthesisAuditEvent {
  event_type: 'synthesis_complete'
  query_plan_id: string
  bundle_id: string
  synthesis_prompt_version: string
  synthesizer_model_id: string
  finish_reason: string
  validator_votes: Record<string, string>
  started_at: string
  finished_at: string
  // Phase 4 additions — additive, no breaking changes to existing consumers:
  input_tokens: number
  output_tokens: number
  final_output: string
  // Phase 6 additions — optional nested fields stored as JSONB by Phase 4 consumer:
  checkpoints?: CheckpointPayloads
  prediction?: StructuredPrediction
  // Phase 7 additions — panel payload; Phase 4 consumer stores as JSONB without schema bump:
  panel?: PanelAuditPayload
}

/** Phase 7 — Panel audit payload attached to SynthesisAuditEvent when panel mode ran. */
export interface PanelAuditPayload {
  panel_slate: string[]
  adjudicator_model_id: string
  member_statuses: Array<'success' | 'failed'>
  divergence_classification: import('./panel/divergence_detector').DivergenceClassification
  degrade_notice?: string
}

/**
 * Return value from synthesize(). The caller (Stream E) calls
 * result.toUIMessageStreamResponse(...) on the streamText result.
 *
 * methodologyBlockHolder is a mutable container populated synchronously in
 * streamText's onFinish (before the 'finish' SSE part fires), allowing the
 * route to include methodology_block in the finish-part messageMetadata.
 */
export interface SynthesisUsage {
  inputTokens?: number
  outputTokens?: number
  cacheReadInputTokens?: number
  cacheCreationInputTokens?: number
}

export interface SynthesisResult {
  result: StreamTextResult<ToolSet, never>
  metadata: SynthesisMetadata
  /** Optional — only populated by SingleModelOrchestrator. Panel path leaves this absent → null. */
  methodologyBlockHolder?: { value: string | null }
  /** Mutable container populated synchronously in streamText.onFinish — allows the outer
   *  onFinish in the route to read synthesis token counts for observatory telemetry. */
  usageHolder?: { value: SynthesisUsage | null }
  /** β9 — Panel mode: pre-computed stage/tool data parts to emit before merging the
   *  adjudicator stream. The route's execute block replays these via writer.write() so
   *  the UI sees panel:member:N running/done events before the adjudicator stream begins. */
  panelStageEvents?: Array<{ type: string; data: unknown }>
}

export interface SynthesisOrchestrator {
  synthesize(request: SynthesisRequest): Promise<SynthesisResult>
}
