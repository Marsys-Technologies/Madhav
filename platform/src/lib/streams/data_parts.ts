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

export const CitationGatePartSchema = z.object({
  type: z.literal('citation_gate'),
  status: z.enum(['pass', 'warn', 'fail']),
  issues: z.array(z.string()).optional(),
})

export type CitationGatePart = z.infer<typeof CitationGatePartSchema>

// ── Citation part (β4) ────────────────────────────────────────────────────

export const CitationPartSchema = z.object({
  type: z.literal('citation'),
  index: z.number().int().positive(),
  signal_id: z.string(),
  layer: z.enum(['L1', 'L2.5']).default('L2.5'),
  snippet: z.string().default(''),
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

// ── Panel meta part (γ1) ─────────────────────────────────────────────────
// Single part carrying overall panel metadata for the confidence ribbon.

export const PanelMetaPartSchema = z.object({
  type: z.literal('panel_meta'),
  member_count: z.number().int().positive(),
  has_divergence: z.boolean(),
  adjudicator_model_id: z.string().optional(),
})

export type PanelMetaPart = z.infer<typeof PanelMetaPartSchema>

// ── Union ─────────────────────────────────────────────────────────────────

export const DataPartSchema = z.discriminatedUnion('type', [
  StagePartSchema,
  ToolPartSchema,
  CostPartSchema,
  ObservabilityPartSchema,
  CitationGatePartSchema,
  CitationPartSchema,
  PersistencePartSchema,
  PanelMemberPartSchema,
  PanelMetaPartSchema,
])

export type DataPart = z.infer<typeof DataPartSchema>

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

export const panelMemberPart = (args: Omit<PanelMemberPart, 'type'>): PanelMemberPart => ({
  type: 'panel_member',
  ...args,
})

export const panelMetaPart = (args: Omit<PanelMetaPart, 'type'>): PanelMetaPart => ({
  type: 'panel_meta',
  ...args,
})
