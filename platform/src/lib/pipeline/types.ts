/**
 * types.ts — PipelinePlan: the single authoritative contract between the
 * pipeline planner and all downstream pipeline stages.
 *
 * Problem solved:
 *   The legacy pipeline maintained two separate LLM-produced schemas:
 *   - PlanSchema  (manifest_planner.ts) — 6-class enum, tool_calls only
 *   - QueryPlan   (router/types.ts)     — 8-class enum, no tool params
 *   These were merged at route.ts runtime via a `plannerParamsMap` graft,
 *   producing a semantically incoherent result (P2/P6/P8 structural problems).
 *
 * Target:
 *   One LLM call (pipeline_planner.ts) produces one PipelinePlan.
 *   route.ts stamps caller-controlled fields post-LLM and passes the plan
 *   unchanged to bundle_hydrator.ts, the retrieval layer, and synthesis.
 *
 * Separation of concerns:
 *   Fields marked [PLANNER OUTPUT] are emitted by the planning LLM.
 *   Fields marked [ROUTE STAMP] are injected by route.ts after the LLM call.
 *   The LLM never sets query_plan_id or manifest_fingerprint.
 *
 * Phase 1 deliverable. Downstream wiring (pipeline_planner.ts rename,
 * bundle_hydrator.ts, route.ts rewrite) follows in Phases 2–3.
 */

import { z } from 'zod'
import type { JSONSchema7 } from 'json-schema'
import { ScopeTupleSchema } from '@/lib/vidhi/scope_classifier'

export { ScopeTupleSchema, type ScopeTuple } from '@/lib/vidhi/scope_classifier'

// ─────────────────────────────────────────────────────────────────────────────
// §1. Query class enum — unified 8-class taxonomy
//
//     Resolves P6/P8:
//       - manifest_planner (legacy PlanSchema) used 6 classes:
//         remedial | interpretive | predictive | holistic | planetary | single_answer
//       - router.ts classify() used 8 classes:
//         factual | interpretive | predictive | cross_domain | discovery |
//         holistic | remedial | cross_native
//     These were incompatible and merged at runtime by route.ts, producing
//     a plan whose query_class label (from classify) and tool selection
//     (from manifest_planner's 6-class reasoning) were out of sync.
//
//     This 8-class enum is the authoritative, single definition going forward.
// ─────────────────────────────────────────────────────────────────────────────

export const QueryClassEnum = z.enum([
  'factual',       // single factual answer ("what is my lagna")
  'interpretive',  // what does X mean in the chart (house, planet, yoga, varga)
  'predictive',    // timing, future periods, dashas, transits
  'cross_domain',  // multi-domain analysis without holistic scope
  'discovery',     // open-ended exploration — what's interesting / what stands out
  'holistic',      // comprehensive overview, all-domain synthesis, chart-wide themes
  'remedial',      // prescriptions: gemstones, mantras, rituals, propitiation
  'cross_native',              // comparative analysis across multiple birth charts
  'classical_grounding',       // classical text source verification + citation (M8)
  'multi_school_triangulation', // inter-school convergence analysis across 7 Jyotish schools (M9)
])

export type QueryClass = z.infer<typeof QueryClassEnum>

// ─────────────────────────────────────────────────────────────────────────────
// §2. Asset bundle item — canonical documents for the synthesis context window
//
//     [PLANNER OUTPUT]
//
//     The planner declares which canonical artifacts (by their canonical_id
//     from CAPABILITY_MANIFEST.json) should be loaded into the synthesis
//     context window. bundle_hydrator.ts resolves each asset_id to its GCS
//     path and fetches the content.
//
//     Known asset IDs the planner may reference:
//       FORENSIC  — FORENSIC_ASTROLOGICAL_DATA: birth chart facts (floor asset)
//       CGM       — CGM: chart constellation map, structural topology (floor asset)
//       UCN       — UCN: unified chart narrative, interpretive synthesis
//       CDLM      — CDLM: cross-domain linkage matrix, domain relationships
//       RM        — RM: resonance matrix, cross-domain signal resonance
//       LEL       — LEL: life event log, temporal/predictive ground-truth
//
//     Floor assets (FORENSIC + CGM) are enforced by bundle_hydrator even if
//     absent from this array. The planner should declare them explicitly for
//     auditability.
//
//     Domain reports (L3 documents) are fetched via vector_search tool_calls;
//     they do not appear in asset_bundle.
// ─────────────────────────────────────────────────────────────────────────────

export const AssetBundleItemSchema = z.object({
  /** Canonical artifact ID as declared in CAPABILITY_MANIFEST.json */
  asset_id: z.string().min(1),
  /** 1 = required for synthesis quality; 2 = supporting context; 3 = optional enrichment */
  priority: z.union([z.literal(1), z.literal(2), z.literal(3)]),
  /** ≤15 words: why this document is needed for this specific query */
  reason: z.string().min(1),
})

export type AssetBundleItem = z.infer<typeof AssetBundleItemSchema>

// ─────────────────────────────────────────────────────────────────────────────
// §3. Tool call item — retrieval tools the pipeline executes
//
//     [PLANNER OUTPUT]
//
//     Structure is identical to the legacy PlanSchema.tool_calls so existing
//     retrieval infrastructure (budget_arbiter.ts, retrieval tools) continues
//     to work without change.
// ─────────────────────────────────────────────────────────────────────────────

export const ToolCallItemSchema = z.object({
  /** One of the tool_names in CAPABILITY_MANIFEST.json */
  tool_name: z.string().min(1),
  /** Parameter object; keys must be drawn from the tool's query_schema.properties */
  params: z.record(z.string(), z.unknown()),
  /** Token budget for this tool's result; range 100–2000 */
  token_budget: z.number().int().min(100).max(2000),
  /** 1 = required; 2 = supporting; 3 = nice-to-have (may be dropped by budget_arbiter) */
  priority: z.union([z.literal(1), z.literal(2), z.literal(3)]),
  /** ≤15 words: why this tool with these params for this specific query */
  reason: z.string().min(1),
})

export type ToolCallItem = z.infer<typeof ToolCallItemSchema>

// ─────────────────────────────────────────────────────────────────────────────
// §4. PipelinePlan — the single authoritative contract
//
//     Fields are labelled by producer:
//       [PLANNER OUTPUT]  — emitted by pipeline_planner.ts (the planning LLM)
//       [ROUTE STAMP]     — injected by route.ts after the LLM call returns
//
//     Downstream consumers (bundle_hydrator, retrieval layer, synthesis,
//     validators, audit) read from this type only — never from PlanSchema
//     or QueryPlan (those are deleted in Phase 4).
// ─────────────────────────────────────────────────────────────────────────────

// ─────────────────────────────────────────────────────────────────────────────
// §4a. Field classification: HARD-REQUIRED vs SOFT-OPTIONAL fields
//
//   HARD-REQUIRED — leave as z.string() / z.enum() WITHOUT .catch(): a null or
//   missing value is a genuine planner failure that must surface as 422 so it
//   gets fixed at the model/prompt level.
//     query_class, query_intent_summary
//     AssetBundleItemSchema: asset_id, reason
//     ToolCallItemSchema:    tool_name, reason
//
//   SOFT-OPTIONAL — fields whose absence is tolerable at parse time; we coerce
//   null → undefined to absorb LLM format jitter (Anthropic and other providers
//   sometimes return null for optional fields instead of omitting them).
//   Coercions are detected at the call site and emitted as a trace_step for
//   audit visibility in query_trace_steps.
//
//   Two implementation patterns (both tested, both handle null):
//
//   (A) String fields (synthesis_guidance, planning_rationale):
//       z.preprocess(v => v === null ? undefined : v, z.string().optional())
//       — preserves the pre-parse null in rawPlannerArgs for coercion logging.
//
//   (B) Enum / boolean / array / object fields (everything else):
//       z.TYPE.optional().catch(undefined)
//       — .catch swallows any parse failure (including null) and returns undefined.
//       Simpler than preprocess for non-string types; same runtime safety.
//
//   IMPORTANT: Both patterns are semantically equivalent for route.ts — the
//   downstream consumers treat undefined and absent identically. The only
//   difference is that pattern (A) enables pre-coercion null detection for
//   audit logging; pattern (B) does not. String fields use (A) because the
//   planner prompt explicitly forbids null there and we want visibility into
//   violations; other optional fields use (B) because they are structurally
//   optional in the prompt schema.
// ─────────────────────────────────────────────────────────────────────────────

export const PipelinePlanSchema = z.object({

  // ── Core classification ────────────────────────────────────────────────────

  /** [PLANNER OUTPUT] Unified 8-class query taxonomy. HARD-REQUIRED. */
  query_class: QueryClassEnum,

  /** [PLANNER OUTPUT] ≤20-word neutral gloss of what the native is asking. HARD-REQUIRED. */
  query_intent_summary: z.string().min(1).max(200),

  // ── Scope tuple ────────────────────────────────────────────────────────────
  //
  // [DETERMINISTIC — NOT LLM OUTPUT] The deterministic scope-tuple classification
  // of the incoming query, produced by `classifyScope()` (@/lib/vidhi/scope_classifier)
  // and attached to the plan by `callPipelinePlanner` AFTER the LLM call. The planner
  // LLM never emits this — it is optional here so the LLM's raw output still parses
  // (the field is stamped on post-parse, exactly like the [ROUTE STAMP] fields below).
  scope_tuple: ScopeTupleSchema.optional(),

  // ── Synthesis corpus ──────────────────────────────────────────────────────

  /**
   * [PLANNER OUTPUT] Canonical artifacts to load into the synthesis context window.
   * Replaces rule_composer.ts + composition_rules.ts (deleted in Phase 4).
   * FORENSIC and CGM are floor assets — bundle_hydrator enforces them even
   * when absent from this array.
   */
  asset_bundle: z.array(AssetBundleItemSchema),

  // ── Retrieval layer ───────────────────────────────────────────────────────

  /**
   * [PLANNER OUTPUT] Retrieval tool calls the pipeline executes.
   * Replaces the plannerParamsMap merge and classify()-derived tools_authorized.
   */
  tool_calls: z.array(ToolCallItemSchema),

  // ── Synthesis guidance ────────────────────────────────────────────────────

  /**
   * [PLANNER OUTPUT] Optional instruction to the synthesis LLM on angle,
   * depth, emphasis, and structural framing. Replaces context_assembler.ts
   * (deleted in Phase 4). The planner produces this in the same LLM call
   * as the plan — no separate 3rd LLM call.
   *
   * If absent, synthesis uses its default system prompt without guidance.
   * Present for non-trivial queries; absent for single_answer (factual).
   *
   * SOFT-OPTIONAL: null is coerced to undefined at parse time. Coercions are
   * logged via the 'planner_field_coerced' trace_step for audit visibility.
   */
  synthesis_guidance: z.preprocess(v => v === null ? undefined : v, z.string().optional()),

  // ── Output shape ──────────────────────────────────────────────────────────

  /**
   * [PLANNER OUTPUT] Response shape the synthesis LLM should produce.
   * Drives token caps and validator selection.
   * SOFT-OPTIONAL: .catch(undefined) absorbs null returns from the LLM (same
   * class of provider jitter as synthesis_guidance; catch is equivalent to
   * preprocess null→undefined for enum/boolean/array/object types).
   */
  expected_output_shape: z.enum([
    'single_answer',
    'three_interpretation',
    'time_indexed_prediction',
    'structured_data',
  ]).optional().catch(undefined),

  /** [PLANNER OUTPUT] Conversation history handling mode. */
  history_mode: z.enum(['synthesized', 'research']).optional().catch(undefined),

  /**
   * [PLANNER OUTPUT] Whether to route through the panel multi-LLM path.
   * SOFT-OPTIONAL: .catch(undefined) handles null from provider.
   */
  panel_mode: z.boolean().optional().catch(undefined),

  // ── Chart-level retrieval hints ───────────────────────────────────────────
  // [PLANNER OUTPUT] Structured extraction from the query. Allows retrieval
  // tools to parameterize calls without re-parsing query text.
  // All fields are SOFT-OPTIONAL: .catch(undefined) absorbs null from LLM output.

  planets: z.array(z.string()).optional().catch(undefined),
  houses: z.array(z.number()).optional().catch(undefined),
  domains: z.array(z.string()).optional().catch(undefined),
  forward_looking: z.boolean().optional().catch(undefined),
  dasha_context_required: z.boolean().optional().catch(undefined),
  graph_seed_hints: z.array(z.string()).optional().catch(undefined),
  edge_type_filter: z.array(z.string()).optional().catch(undefined),
  vector_search_filter: z.object({
    doc_type: z.array(z.string()).optional().catch(undefined),
    layer: z.string().optional().catch(undefined),
  }).optional().catch(undefined),

  // ── Temporal scope ────────────────────────────────────────────────────────

  /**
   * [PLANNER OUTPUT] Absolute time window for temporal retrieval scoping.
   * SOFT-OPTIONAL: .catch(undefined) handles null from provider.
   */
  time_window: z.object({
    start: z.string(),
    end: z.string(),
  }).optional().catch(undefined),

  // ── Plan rationale ────────────────────────────────────────────────────────

  /**
   * [PLANNER OUTPUT] Why this overall plan was chosen. Stored in audit trail.
   * SOFT-OPTIONAL: null coerced to undefined (same pattern as synthesis_guidance).
   */
  planning_rationale: z.preprocess(v => v === null ? undefined : v, z.string().optional()),

  // ── Gate III: prior-turn relevance ───────────────────────────────────────
  //
  // [PLANNER OUTPUT] Smart per-query context selection. The planner decides
  // how many prior turns the synthesis layer should see, and in what mode.
  // The synthesis prompt enforces "context for comprehension only, never for
  // substance". route.ts uses `used` to trim the conversation_history slice;
  // the UI renders mode + reason as a ContextUsageCue chip.
  //
  // Optional for backwards-compat with planner outputs predating Gate III.
  // When absent, route.ts falls back to the legacy 2-pair window.
  // SOFT-OPTIONAL: .catch(undefined) handles null from provider.
  prior_turn_relevance: z.object({
    used: z.union([z.literal(0), z.literal(1), z.literal(2)]),
    reason: z.string().min(1).max(400),
    mode: z.enum(['independent', 'narrative_context', 'continuation']),
  }).optional().catch(undefined),

  // ── Route-stamped metadata ────────────────────────────────────────────────
  // These fields are NEVER part of the LLM output. route.ts stamps them
  // after the plan is validated so downstream consumers see a single object.

  /** [ROUTE STAMP] UUID for this request. Generated by route.ts. */
  query_plan_id: z.string().uuid().optional(),

  /** [ROUTE STAMP] The original query text. */
  query_text: z.string().optional(),

  // audience_tier excised (C-2, tier_excision / DG1 ruling): it never
  // differentiated pipeline behavior. Disclosure is carried separately via the
  // route-local `audienceTier` → audit `disclosure_tier`.

  /** [ROUTE STAMP] Fingerprint of the CAPABILITY_MANIFEST.json at request time. */
  manifest_fingerprint: z.string().optional(),

  /** [ROUTE STAMP] Schema version for forward-compat detection. */
  schema_version: z.literal('2.0').optional(),

  /** [ROUTE STAMP] Model ID that produced this plan. */
  planning_model_id: z.string().optional(),

  /** [ROUTE STAMP] Wall-clock milliseconds for the planning LLM call. */
  planning_latency_ms: z.number().optional(),
})

export type PipelinePlan = z.infer<typeof PipelinePlanSchema>

// ─────────────────────────────────────────────────────────────────────────────
// §5. Hand-crafted JSON Schema for NIM-compatible tool-call mode
//
//     NIM rejects certain Zod-generated JSON Schema constructs:
//       - z.record(z.string(), z.unknown()) → emits `propertyNames` keyword (rejected)
//       - z.union([z.literal(1), z.literal(2), z.literal(3)]) → emits anyOf[{const}] (rejected)
//
//     This hand-crafted schema governs what NIM constrains the model to emit.
//     PipelinePlanSchema is applied post-call as the runtime validator.
//     Only [PLANNER OUTPUT] fields appear here — route-stamped fields are never
//     part of the model's generation.
// ─────────────────────────────────────────────────────────────────────────────

export const PipelinePlanInputJsonSchema: JSONSchema7 = {
  type: 'object',
  properties: {
    query_class: {
      type: 'string',
      enum: [
        'factual',
        'interpretive',
        'predictive',
        'cross_domain',
        'discovery',
        'holistic',
        'remedial',
        'cross_native',
        'classical_grounding',
        'multi_school_triangulation',
      ],
    },
    query_intent_summary: { type: 'string' },
    asset_bundle: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          asset_id: { type: 'string' },
          priority: { type: 'integer', minimum: 1, maximum: 3 },
          reason: { type: 'string' },
        },
        required: ['asset_id', 'priority', 'reason'],
      },
    },
    tool_calls: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          tool_name: { type: 'string' },
          params: { type: 'object' },
          token_budget: { type: 'integer', minimum: 100, maximum: 2000 },
          priority: { type: 'integer', minimum: 1, maximum: 3 },
          reason: { type: 'string' },
        },
        required: ['tool_name', 'params', 'token_budget', 'priority', 'reason'],
      },
    },
    synthesis_guidance: {
      type: 'string',
      description: 'MUST be a non-empty string describing how the synthesis model should compose its answer — angle, depth, emphasis, structural framing. NEVER return null or omit this field for non-factual queries. Empty string is not acceptable.',
    },
    planning_rationale: {
      type: 'string',
      description: 'MUST be a non-empty string explaining why this plan was chosen. NEVER return null.',
    },
    expected_output_shape: {
      type: 'string',
      enum: ['single_answer', 'three_interpretation', 'time_indexed_prediction', 'structured_data'],
    },
    history_mode: {
      type: 'string',
      enum: ['synthesized', 'research'],
    },
    panel_mode: { type: 'boolean' },
    planets: { type: 'array', items: { type: 'string' } },
    houses: { type: 'array', items: { type: 'integer' } },
    domains: { type: 'array', items: { type: 'string' } },
    forward_looking: { type: 'boolean' },
    dasha_context_required: { type: 'boolean' },
    graph_seed_hints: { type: 'array', items: { type: 'string' } },
    edge_type_filter: { type: 'array', items: { type: 'string' } },
    vector_search_filter: {
      type: 'object',
      properties: {
        doc_type: { type: 'array', items: { type: 'string' } },
        layer: { type: 'string' },
      },
    },
    time_window: {
      type: 'object',
      properties: {
        start: { type: 'string' },
        end: { type: 'string' },
      },
      required: ['start', 'end'],
    },
    prior_turn_relevance: {
      type: 'object',
      properties: {
        used: { type: 'integer', minimum: 0, maximum: 2 },
        reason: { type: 'string' },
        mode: { type: 'string', enum: ['independent', 'narrative_context', 'continuation'] },
      },
      required: ['used', 'reason', 'mode'],
    },
  },
  required: ['query_class', 'query_intent_summary', 'asset_bundle', 'tool_calls'],
}

// ─────────────────────────────────────────────────────────────────────────────
// §6. PipelinePlannerError
//
//     Replaces both PlannerError (manifest_planner.ts) and PipelineError
//     (router/errors.ts). In the target pipeline, a planner failure surfaces
//     as HTTP 422 to the client — there is no silent fallback to classify().
//     Callers must handle this explicitly.
// ─────────────────────────────────────────────────────────────────────────────

export class PipelinePlannerError extends Error {
  constructor(
    message: string,
    public readonly cause?: unknown,
  ) {
    super(message)
    this.name = 'PipelinePlannerError'
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// §7. Planner outcome contract — the 3-way discriminated union
// (W4 "One Planner" core step 2).
//
//   The planner call USED to have two effective outcomes: a `PipelinePlan`
//   (success) or a thrown `PipelinePlannerError` (which route.ts turned into a
//   raw, leaky `HTTP 422 {"error":"planner_failed", ...}`). This union replaces
//   that with three EXPLICIT, TYPED outcomes so `callPipelinePlanner` never
//   throws for an expected failure and route.ts branches on a discriminant:
//
//     'plan'                → PlanReceipt          (proceed as before)
//     'clarification_needed' → ClarificationRequest (ask the user a question)
//     'fault'               → PlannerFaultResult    (clean typed error response)
//
//   The intended names come from the design docs, which specify the outcome set
//   as `PlanReceipt | ClarificationRequest | fault`
//   (RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §C-5;
//    PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md §744). `PlanReceipt` was previously
//   docs-only ("absent from code entirely" — RETRIEVAL_SYSTEM_TRUTH_v2_0.md);
//   this is its first code definition.
// ─────────────────────────────────────────────────────────────────────────────

/**
 * The successful outcome: a validated `PipelinePlan` (carrying its deterministic
 * `scope_tuple`) wrapped with the `outcome: 'plan'` discriminant. Wrapping (rather
 * than adding `outcome` to `PipelinePlanSchema` itself) keeps every downstream
 * consumer of `PipelinePlan` — bundle_hydrator, budget_arbiter, the adapter
 * dispatch shim — unchanged; route.ts unwraps `.plan` and proceeds exactly as
 * it did before.
 */
export interface PlanReceipt {
  outcome: 'plan'
  plan: PipelinePlan
}

/**
 * The clarification outcome: the deterministic scope classifier could not
 * confidently classify the query (its `fallback_recommended` signal fired), so
 * rather than silently guessing a plan the planner asks the user a clarifying
 * question. `missing_scope_dims` names the scope dimensions that came back
 * unknown/default; `suggested_options` offers concrete choices the UI can render.
 */
export interface ClarificationRequest {
  outcome: 'clarification_needed'
  question: string
  missing_scope_dims?: string[]
  suggested_options?: string[]
}

/**
 * The fault outcome: a NORMAL, TYPED return value — never a thrown exception.
 * Emitted when the LLM planner produced unparseable/invalid output that survived
 * one structured repair-retry, or when the provider call itself failed after the
 * retry budget was exhausted. `retryable` tells route.ts whether the same request,
 * repeated unchanged, could succeed (true for transient provider faults; false for
 * a model that keeps returning malformed output).
 */
export interface PlannerFaultResult {
  outcome: 'fault'
  reason: string
  retryable: boolean
}

/** The 3-way outcome `callPipelinePlanner` returns. */
export type PlannerOutcome = PlanReceipt | ClarificationRequest | PlannerFaultResult

