/**
 * MARSYS Chat V2 — UIMessage stream data part schemas and helpers.
 *
 * These types are emitted via `writer.write({ type: 'data-<name>', data: ... })`
 * inside `createUIMessageStream` in the consume route. The UI reads them from
 * the `message.data` array to render live pipeline progress.
 *
 * Part types mirror the CLAUDECODE_BRIEF §A.α3 spec:
 *   stage / tool / cost / observability / citation_gate / persistence
 */

import { z } from 'zod'

// ── Stage part ─────────────────────────────────────────────────────────────

export const StageNameSchema = z.enum([
  'classify',
  'compose_bundle',
  'plan_per_tool',
  'tool_fetch',
  // W5 L9 — verdict-first streaming: the request-start → first-verdict-byte
  // stage-timing metric (see TIME_TO_FIRST_VERDICT_SLO_MS below). Emitted
  // unconditionally (degraded or not) the instant the data-orientation SSE
  // event is written — i.e. BEFORE the `synthesis` stage's text starts
  // streaming, not after it completes.
  'first_verdict',
  'synthesis',
  'audit',
  'panel:member:1',
  'panel:member:2',
  'panel:member:3',
  'panel:adjudicator',
])

export type StageName = z.infer<typeof StageNameSchema>

export const StagePartSchema = z.object({
  type: z.literal('stage'),
  stage: StageNameSchema,
  status: z.enum(['running', 'done', 'error']),
  ms: z.number().nonnegative().optional(),
})

export type StagePart = z.infer<typeof StagePartSchema>

// ── Tool part ─────────────────────────────────────────────────────────────

export const ToolPartSchema = z.object({
  type: z.literal('tool'),
  name: z.string().min(1),
  status: z.enum(['pending', 'running', 'done', 'error']),
  ms: z.number().nonnegative().optional(),
  ok_count: z.number().nonnegative().optional(),
  err_count: z.number().nonnegative().optional(),
})

export type ToolPart = z.infer<typeof ToolPartSchema>

// ── Cost part ─────────────────────────────────────────────────────────────

export const CostPartSchema = z.object({
  type: z.literal('cost'),
  model: z.string().min(1),
  input_tokens: z.number().nonnegative().int(),
  output_tokens: z.number().nonnegative().int(),
  reasoning_tokens: z.number().nonnegative().int().optional(),
  dollars: z.number().nonnegative(),
  ms: z.number().nonnegative(),
})

export type CostPart = z.infer<typeof CostPartSchema>

// ── Observability part ────────────────────────────────────────────────────

export const ObservabilityPartSchema = z.object({
  type: z.literal('observability'),
  query_id: z.string().uuid(),
  trace_url: z.string().url(),
})

export type ObservabilityPart = z.infer<typeof ObservabilityPartSchema>

// ── Citation gate part ────────────────────────────────────────────────────

export const GateVerdictSchema = z.object({
  name: z.string(),
  verdict: z.enum(['PASS', 'FAIL', 'WARN']),
  reason: z.string(),
})

export type GateVerdict = z.infer<typeof GateVerdictSchema>

export const CitationGatePartSchema = z.object({
  type: z.literal('citation_gate'),
  status: z.enum(['pass', 'warn', 'fail']),
  issues: z.array(z.string()).optional(),
  gates: z.array(GateVerdictSchema).optional(),
})

export type CitationGatePart = z.infer<typeof CitationGatePartSchema>

// ── Citation part (β4) ────────────────────────────────────────────────────

export const CitationPartSchema = z.object({
  type: z.literal('citation'),
  index: z.number().int().positive(),
  signal_id: z.string(),
  layer: z.enum(['L1', 'L2.5']).default('L2.5'),
  snippet: z.string().default(''),
  confidence: z.number().min(0).max(1).optional(),
})

export type CitationPart = z.infer<typeof CitationPartSchema>

// ── Persistence part ──────────────────────────────────────────────────────

export const PersistencePartSchema = z.object({
  type: z.literal('persistence'),
  conversation_id: z.string().uuid(),
  message_id: z.string().min(1),
  status: z.enum(['ok', 'error']),
})

export type PersistencePart = z.infer<typeof PersistencePartSchema>

// ── Panel member part (γ1) ────────────────────────────────────────────────
// One part per panel member, emitted after runPanelMembers completes (before
// adjudicator stream). Carries the member's full answer for the dissent drawer.

export const PanelMemberPartSchema = z.object({
  type: z.literal('panel_member'),
  member_index: z.number().int().nonnegative(),
  model_id: z.string(),
  provider_family: z.string(),
  status: z.enum(['success', 'failed']),
  answer: z.string().optional(),
  latency_ms: z.number().nonnegative(),
})

export type PanelMemberPart = z.infer<typeof PanelMemberPartSchema>

// ── Prediction candidate part (γ3) ───────────────────────────────────────
// Emitted in route's onFinish after regex detection runs. NOT inline with stream.
// One part per candidate. Client renders "Log as prediction" affordance.

export const PredictionCandidatePartSchema = z.object({
  type: z.literal('prediction_candidate'),
  text: z.string().min(1),
  offset: z.number().int().nonnegative(),
  score: z.number().min(0).max(1),
  horizon: z.string().nullable(),
})

export type PredictionCandidatePart = z.infer<typeof PredictionCandidatePartSchema>

// ── Panel meta part (γ1) ─────────────────────────────────────────────────
// Single part carrying overall panel metadata for the confidence ribbon.

export const PanelMetaPartSchema = z.object({
  type: z.literal('panel_meta'),
  member_count: z.number().int().positive(),
  has_divergence: z.boolean(),
  adjudicator_model_id: z.string().optional(),
})

export type PanelMetaPart = z.infer<typeof PanelMetaPartSchema>

// ── Title part (E.1) ─────────────────────────────────────────────────────
// Emitted on the first turn in onFinish after the conversation is persisted.
// Client uses it as a reload-sidebar signal (the title is already in the DB).

export const TitlePartSchema = z.object({
  type: z.literal('title'),
  conversation_id: z.string().uuid(),
})

export type TitlePart = z.infer<typeof TitlePartSchema>

// ── Correction part (D.3) ─────────────────────────────────────────────────
// Emitted in onFinish when parseMarkers finds a ‹correction› marker in the
// synthesis output. Drives CorrectionNotice in V2Message.

export const CorrectionPartSchema = z.object({
  type: z.literal('correction'),
  original_claim: z.string(),
  corrected_claim: z.string(),
  classical_source: z.string().optional(),
})

export type CorrectionPart = z.infer<typeof CorrectionPartSchema>

// ── Out-of-domain part (D.3) ──────────────────────────────────────────────
// Emitted in onFinish when parseMarkers finds a ‹out_of_domain› marker.
// Drives OutOfDomainBanner in V2Message.

export const OutOfDomainPartSchema = z.object({
  type: z.literal('out_of_domain'),
  reason: z.string(),
})

export type OutOfDomainPart = z.infer<typeof OutOfDomainPartSchema>

// ── Truncated part (R7-S5) ────────────────────────────────────────────────

export const TruncatedPartSchema = z.object({
  type: z.literal('truncated'),
  reason: z.string(),
})

export type TruncatedPart = z.infer<typeof TruncatedPartSchema>

// ── Context-usage part (R7-S5 heuristic fallback) ─────────────────────────

export const ContextUsagePartSchema = z.object({
  type: z.literal('context_usage'),
  tokens_used: z.number().nonnegative().int(),
  tokens_limit: z.number().positive().int(),
})

export type ContextUsagePart = z.infer<typeof ContextUsagePartSchema>

// ── Capability path part (A-S9) ───────────────────────────────────────────
// Emitted by route.ts after each dispatcher.dispatch() call within a turn.
// Carries per-capability telemetry to the client for downstream Observatory
// aggregation. Gated by MARSYS_FLAG_R11V2_CAPABILITY_TELEMETRY (server-side).

export const CapabilityPathPartSchema = z.object({
  type: z.literal('data-capability-path'),
  stackId: z.string().min(1),
  capability: z.string().min(1),
  manifestSupport: z.union([z.string(), z.boolean(), z.number(), z.null()]),
  success: z.boolean(),
  durationMs: z.number().nonnegative(),
  errorClass: z.string().optional(),
})

export type CapabilityPathPart = z.infer<typeof CapabilityPathPartSchema>

// ── Clarification part (W4 "One Planner" — ClarificationRequest outcome) ────
// Emitted by route.ts when the deterministic scope classifier could not
// confidently classify the query, so the planner asks the user a clarifying
// question instead of guessing a plan. The UI renders `question` (and optional
// `suggested_options`) as a prompt for the user to refine their request.

export const ClarificationPartSchema = z.object({
  type: z.literal('clarification'),
  question: z.string().min(1),
  missing_scope_dims: z.array(z.string()).optional(),
  suggested_options: z.array(z.string()).optional(),
})

export type ClarificationPart = z.infer<typeof ClarificationPartSchema>

// ── Completeness part (W4 "One Planner" — completeness receipt on web channel) ──
// Emitted by route.ts / run_adapter_dispatch near the END of the stream, after the
// floor tools have executed. Carries the served/empty/dark completeness receipt for
// the compiled B.11 floor (per floor_item_id), plus a channel_note that honestly
// states how many floor items had NO web-executable retrieval tool (the MCP↔web
// namespace gap). The UI can render coverage + surface the dark/empty items.

export const CompletenessServedItemSchema = z.object({
  floor_item_id: z.string(),
  source: z.string(),
})
export const CompletenessEmptyItemSchema = z.object({
  floor_item_id: z.string(),
  empty_reason: z.string(),
})
export const CompletenessDarkItemSchema = z.object({
  floor_item_id: z.string(),
  cr_row: z.string(),
  note: z.string().optional(),
})

export const CompletenessPartSchema = z.object({
  type: z.literal('completeness'),
  channel: z.literal('web'),
  served: z.array(CompletenessServedItemSchema),
  empty: z.array(CompletenessEmptyItemSchema),
  dark: z.array(CompletenessDarkItemSchema),
  coverage: z.object({
    floor_item_total: z.number().int().nonnegative(),
    served: z.number().int().nonnegative(),
    empty: z.number().int().nonnegative(),
    dark: z.number().int().nonnegative(),
  }),
  channel_note: z.string(),
})

export type CompletenessPart = z.infer<typeof CompletenessPartSchema>

// ── Orientation part (W4 "One Planner" — S-1 orientation front-door on web channel) ──
// Emitted ONCE near the START of the stream. Carries the ≤2000-token orientation block
// (chart frame + structural facts + notable findings + dasha context + category/drill map).
// Kept intentionally loose (passthrough of the ChartOrientation shape) — the block is
// budget-enforced upstream (buildChartOrientation) and delivery metadata for the client.

export const OrientationPartSchema = z.object({
  type: z.literal('orientation'),
  chart_id: z.string(),
  ayanamsha_id: z.string(),
  degraded: z.boolean(),
  budget: z.object({
    limit_tokens: z.number().int().positive(),
    estimated_tokens: z.number().int().nonnegative(),
    enforced: z.boolean(),
    trims: z.array(z.string()),
  }),
  // The full orientation payload (header/structural_facts/notable_findings/…). Passed
  // through as-is; not re-validated field-by-field here (built + bounded upstream).
  orientation: z.record(z.string(), z.unknown()),
})

export type OrientationPart = z.infer<typeof OrientationPartSchema>

// ── Union ─────────────────────────────────────────────────────────────────

export const DataPartSchema = z.discriminatedUnion('type', [
  CompletenessPartSchema,
  OrientationPartSchema,
  ClarificationPartSchema,
  StagePartSchema,
  ToolPartSchema,
  CostPartSchema,
  ObservabilityPartSchema,
  CitationGatePartSchema,
  CitationPartSchema,
  PersistencePartSchema,
  PanelMemberPartSchema,
  PanelMetaPartSchema,
  PredictionCandidatePartSchema,
  CorrectionPartSchema,
  OutOfDomainPartSchema,
  TitlePartSchema,
  TruncatedPartSchema,
  ContextUsagePartSchema,
  CapabilityPathPartSchema,
])

export type DataPart = z.infer<typeof DataPartSchema>

// ── Time-to-first-verdict SLO (W5 L9 — verdict-first streaming) ────────────
//
// Defined as a stage-timing metric fit to the single-request web architecture
// (the plan's original "≤3 calls to first verdict" framing does not map onto
// one HTTP request/response stream — see STATE.md W5 OPEN amendment 3).
//
// Metric: wall-clock ms from route-handler entry (`setupStart` in
// consult/route.ts) to the moment the `data-orientation` SSE event — the
// verdict/orientation layer — is written into the response stream. Captured
// server-side as the `first_verdict` `data-stage` event's `ms` field,
// unconditionally (even when orientation degrades to header+inventory-only,
// or fails outright) so the SLO has 100% query-class coverage, not just the
// classes with a fully-populated orientation block.
//
// Target derived from the W4-close measured baseline (chart `1c826d5a`,
// career-assessment probe, ~51s total wall-clock):
//   classify 4.6s + compose_bundle 0.05s + tool_fetch 6.1s ≈ 10.75s
// — all of which run BEFORE the adapter stream even opens (route.ts awaits
// planner + tool-fetch + orientation synchronously before calling
// runAdapterDispatch). The first_verdict write happens at the very start of
// that stream's `execute()`, before any synthesis text-delta — so
// time-to-first-verdict ≈ the pre-synthesis stage sum plus the (unmeasured
// today) auth/chart-resolution + bundle-compile overhead ahead of `classify`.
// p50 target sits just above the measured 10.75s pre-synthesis sum with
// headroom for that unmeasured prefix; p95 gives room for planner/tool-fetch
// tail latency without letting the SLO drift toward the 38.7s synthesis
// stage it exists to front-run.
export const TIME_TO_FIRST_VERDICT_SLO_MS = {
  /** p50 target — just above the measured 10.75s pre-synthesis stage sum. */
  p50: 12_000,
  /** p95 target — tail-latency headroom, still well under the 38.7s synthesis stage alone. */
  p95: 20_000,
} as const

// ── Helper constructors ───────────────────────────────────────────────────

export const stagePart = (
  stage: StageName,
  status: StagePart['status'],
  ms?: number,
): StagePart => ({ type: 'stage', stage, status, ...(ms !== undefined ? { ms } : {}) })

export const toolPart = (
  name: string,
  status: ToolPart['status'],
  ms?: number,
): ToolPart => ({ type: 'tool', name, status, ...(ms !== undefined ? { ms } : {}) })

export const costPart = (args: Omit<CostPart, 'type'>): CostPart => ({
  type: 'cost',
  ...args,
})

export const observabilityPart = (args: Omit<ObservabilityPart, 'type'>): ObservabilityPart => ({
  type: 'observability',
  ...args,
})

export const citationGatePart = (args: Omit<CitationGatePart, 'type'>): CitationGatePart => ({
  type: 'citation_gate',
  ...args,
})

export const citationPart = (args: Omit<CitationPart, 'type'>): CitationPart => ({
  type: 'citation',
  ...args,
})

export const persistencePart = (args: Omit<PersistencePart, 'type'>): PersistencePart => ({
  type: 'persistence',
  ...args,
})

export const predictionCandidatePart = (args: Omit<PredictionCandidatePart, 'type'>): PredictionCandidatePart => ({
  type: 'prediction_candidate',
  ...args,
})

export const panelMemberPart = (args: Omit<PanelMemberPart, 'type'>): PanelMemberPart => ({
  type: 'panel_member',
  ...args,
})

export const panelMetaPart = (args: Omit<PanelMetaPart, 'type'>): PanelMetaPart => ({
  type: 'panel_meta',
  ...args,
})

export const correctionPart = (args: Omit<CorrectionPart, 'type'>): CorrectionPart => ({
  type: 'correction',
  ...args,
})

export const outOfDomainPart = (args: Omit<OutOfDomainPart, 'type'>): OutOfDomainPart => ({
  type: 'out_of_domain',
  ...args,
})

export const titlePart = (args: Omit<TitlePart, 'type'>): TitlePart => ({
  type: 'title',
  ...args,
})

export const truncatedPart = (reason: string): TruncatedPart => ({
  type: 'truncated',
  reason,
})

export const contextUsagePart = (args: Omit<ContextUsagePart, 'type'>): ContextUsagePart => ({
  type: 'context_usage',
  ...args,
})

export const clarificationPart = (args: Omit<ClarificationPart, 'type'>): ClarificationPart => ({
  type: 'clarification',
  ...args,
})

export const completenessPart = (args: Omit<CompletenessPart, 'type'>): CompletenessPart => ({
  type: 'completeness',
  ...args,
})

export const orientationPart = (args: Omit<OrientationPart, 'type'>): OrientationPart => ({
  type: 'orientation',
  ...args,
})
