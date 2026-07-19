/**
 * L0FR Stream A — Retrieval Registry Types
 * ==========================================
 * Full Capability descriptor per master plan §6.
 * Zero audience_tier — capabilities are universally accessible.
 *
 * FREEZE DECLARATION (D1 contract, 2026-06-28):
 * Core shape (CapabilityDescriptor + chart-agnostic gate fields) is FROZEN.
 * New optional fields may only be added via a versioned amendment that bumps
 * the amendment_version below and documents the change.
 * amendment_version: 1 (initial freeze)
 *
 * AMENDMENT PROCEDURE:
 * 1. Add the new OPTIONAL field to CapabilityDescriptor (never remove or rename required fields).
 * 2. Bump amendment_version above.
 * 3. Add an entry to the D1_AMENDMENTS array at the bottom of this file.
 * 4. Update all existing capabilities to set the new field (or document why it is left optional).
 * 5. Re-run: npm run registry:chart-agnostic-gate
 */

// ── Primitive types ─────────────────────────────────────────────────────────

/** The three primitive capability types. */
export type CapabilityType = 'tool' | 'resource' | 'prompt'

/** URI format: marsys://tool/L0/name or marsys://resource/path or marsys://prompt/name */
export type CapabilityUri = string

/** Layer identifiers */
export type Layer = 'L0' | 'L1' | 'L2' | 'L3' | 'L4' | 'L5'

// ── D1 contract: topology types ──────────────────────────────────────────────

/**
 * The 8 retrieval archetypes from RETRIEVAL_GROUNDTRUTH_TOOL_TOPOLOGY §2.
 * Determines the tool shape (single leaf, umbrella, hybrid-retrieval, etc.).
 */
export type RetrievalArchetype =
  | 'flat_fact'           // exact keyed lookup (L1 positions, dignity, strength, etc.)
  | 'prose_citation'      // hybrid BM25+dense retrieval over verse/rule corpora (L0 texts)
  | 'rich_relational'     // multi-vantage reconciled surface (L2 signals, domain framing)
  | 'graph_traversal'     // CGM/CDLM graph traversal (bo_bimba, bo_karanajala)
  | 'cross_domain'        // contradiction/convergence across domains (bo_sangati, CDLM)
  | 'temporal'            // time-keyed (dashas, transits, L3 kala)
  | 'orientation_digest'  // whole-chart gestalt entry (bo_samvada UCD, asset catalogs)
  | 'calibration'         // quality/trust metadata (bo_pramana_mapa, L5 mimamsa)

/**
 * Traversal levels from the Vedic reading hierarchy (D-GROUNDTRUTH traversal model).
 * Determines whether this capability is an umbrella entry or a drill leaf.
 */
export type TraversalLevel =
  | 'L-ORIENT'    // Whole-chart orientation — first call of nearly every reading
  | 'L-OVERVIEW'  // Layer or domain overview (asset catalog, list operations)
  | 'L-DOMAIN'    // Life-domain framing (career, health, relationship, etc.)
  | 'L-SIGNAL'    // Individual signal / factor drill (specific graha, yoga, dosha)
  | 'L-SOURCE'    // Classical citation / classical grounding (verse, rule, sutra)
  | 'L-SYNTH'     // Cross-layer synthesis — D6 synergy tools spanning multiple layers

/**
 * Tool role in the topology (drives MARO routing decisions).
 */
export type ToolRole =
  | 'umbrella'          // broad entry tool returning surface + drill pointers
  | 'drill'             // intermediate drill (narrows domain; returns finer pointers)
  | 'leaf'              // terminal fact lookup (returns data, not pointers)
  | 'graph'             // graph traversal (neighbors / paths / clusters)
  | 'hybrid_retrieval'  // BM25+dense+rerank prose retrieval
  | 'temporal'          // time-keyed tool family
  | 'quality'           // calibration/trust surface
  | 'synthesizer'       // cross-layer synthesis tool (D6 synergy layer)

// ── Scope discriminator: per_chart vs global ─────────────────────────────────

/**
 * 'per_chart' — operates on a specific chart; chart_id is REQUIRED from request context.
 * 'global'    — chart-agnostic (reference data, ephemeris catalog, entity resolution).
 *
 * CONTRACT RULE (principle #14 / D0 §D.2): if scope === 'per_chart', the descriptor
 * MUST list 'chart_id' in required_inputs and the handler MUST error if chart_id is absent.
 * The chart-agnostic CI gate (chart_agnostic_gate.ts) enforces this at build time.
 */
export type Scope = 'per_chart' | 'global'

// ── Base fields shared by both scopes ────────────────────────────────────────

interface CapabilityDescriptorBase {
  /** Unique URI: marsys://tool|resource|prompt/layer/name */
  uri: CapabilityUri

  /** Primitive type */
  type: CapabilityType

  /** Layer this capability belongs to */
  layer: Layer

  /** Short human-readable name */
  name: string

  /**
   * Full description for LLM consumption.
   * MUST NOT contain any literal chart_id (e.g. '482012f1-…') or native
   * identifiers ('Abhisek Mohanty', '1984-02-05', 'Bhubaneswar').
   * Use the placeholder '<chart_uuid>' when referencing chart identity.
   */
  description: string

  /** Input schema (required for tools and parameterized prompts; omit for resources) */
  input_schema?: InputSchema

  /** Which parameters are required */
  required_inputs?: string[]

  /** Adapter hints — guides routing decisions without changing functional behavior */
  llm_hints?: LLMHints

  /**
   * Handler function — the actual implementation.
   * For MCP: called when the MCP client invokes the tool.
   * For Consume Chat: called by the retrieval pipeline.
   */
  handler: CapabilityHandler

  /**
   * MCP-specific metadata:
   * - annotations: per MCP spec (readOnly, destructive, etc.)
   */
  mcp_annotations?: {
    readOnly?: boolean
    destructive?: boolean
  }

  // ── D1 topology fields (FROZEN 2026-06-28) ───────────────────────────────

  /**
   * Retrieval archetype (from RETRIEVAL_GROUNDTRUTH_TOOL_TOPOLOGY §2).
   * Drives tool shape selection in MARO.
   */
  archetype: RetrievalArchetype

  /**
   * Traversal level in the reading hierarchy.
   * Determines umbrella vs drill vs leaf placement.
   */
  traversal_level: TraversalLevel

  /**
   * Tool role in the topology.
   */
  tool_role: ToolRole

  /**
   * Child capabilities this umbrella or drill tool fans into.
   * Set on umbrella/drill tools; omit on leaf/graph/hybrid.
   */
  drill_children?: CapabilityUri[]

  /**
   * Whether this tool returns signal_id / fact_id references rather than restated facts.
   * Enforces F1 (reference-don't-repeat) — drill/leaf tools must set this true.
   */
  emits_references: boolean

  /**
   * F3 (layer-resolution-DOWN): which reference layers this tool's output resolves to.
   * A tool that returns signals with constituent_facts_array resolves to L1 fact_ids.
   * A tool that returns L1 facts with citation_id resolves to L0 citation_ids.
   */
  grounds_to?: {
    l1_fact_ids?: boolean
    l0_citation_ids?: boolean
  }

  /**
   * Whether this capability can surface lel_origin=true calibration signals.
   * If true, the handler MUST respect the lel_enabled flag (default false),
   * excluding lel_origin rows unless lel_enabled is explicitly true.
   * Most tools set this false (no LEL data touches them).
   */
  lel_capable: boolean

  /**
   * Output schema for structured output across providers (MCP structuredContent).
   * Promotes from the narrowed ToolCapability to the main descriptor.
   */
  output_schema?: Record<string, unknown>

  /**
   * Per-family MARO behavioral override hooks (optional).
   * MARO reads these to shape bundle size, context budget, output format per model family.
   * Leave unset for most capabilities — only set when a family needs explicit override.
   */
  behavioral_overrides?: {
    anthropic?: Record<string, unknown>
    gemini?: Record<string, unknown>
    openai?: Record<string, unknown>
    deepseek?: Record<string, unknown>
  }

  /**
   * Lane 5 (§N.6 (iv) density contract — Doctrine Campaign D-1 Night-1). Declares this
   * capability's serving-density discipline so a future census/CI harness (per the brief,
   * NOT built tonight — see DEPLOYED_TOOL_CENSUS_2026-07-13.md for the census shape) can
   * assert byte caps and facet/empty-reason coverage per tool without re-deriving it from
   * source. Additive/optional — absent on capabilities this campaign did not touch.
   */
  density_contract?: {
    max_verdict_bytes?: number
    max_digest_bytes?: number
    paginated: boolean
    facets: string[]
    empty_reason: boolean
  }
}

// ── Discriminated union: per_chart enforces chart_id in required_inputs ──────

/**
 * A capability that operates on a specific chart.
 * CONTRACT: required_inputs MUST include 'chart_id'.
 * Enforced at the type level via the discriminated union, and at runtime by the CI gate.
 */
export interface PerChartCapabilityDescriptor extends CapabilityDescriptorBase {
  scope: 'per_chart'
  /**
   * required_inputs MUST include 'chart_id'.
   * TypeScript enforces this via the ReadonlyArray constraint below.
   * The CI gate (chart_agnostic_gate.ts) enforces it at build time.
   */
  required_inputs: [string, ...string[]] & { 0: 'chart_id' } | (string[] & { includes(s: 'chart_id'): true })
}

/**
 * A chart-agnostic capability (reference data, ephemeris, entity resolution).
 * MUST NOT accept a chart_id as a meaningful routing key.
 */
export interface GlobalCapabilityDescriptor extends CapabilityDescriptorBase {
  scope: 'global'
}

/**
 * Full Capability descriptor — discriminated union.
 * Use scope field to narrow:
 *   if (cap.scope === 'per_chart') { /* chart_id is required *\/ }
 *
 * No audience_tier, no per-tier filtering — universally accessible.
 */
export type CapabilityDescriptor = PerChartCapabilityDescriptor | GlobalCapabilityDescriptor

// ── Adapter hints ────────────────────────────────────────────────────────────

/** Hints for the Agentic Loop adapter */
export interface AgenticHints {
  /** Cost class determines tool-call batching and parallelism decisions */
  cost_class: 'cheap' | 'medium' | 'expensive'
  /** Whether this tool benefits from chain-of-thought before invocation */
  requires_cot?: boolean
  /** Whether this tool returns data that the loop should cache */
  cacheable?: boolean
  /** Maximum retries on tool error */
  max_retries?: number
}

/** Hints for the Bulk Context adapter */
export interface BulkContextHints {
  /** 0-100: higher means pre-fetch earlier */
  pre_fetch_priority: number
  /** Estimated token cost of the result */
  result_size_estimate_tokens?: number
  /** Whether to include in system context by default */
  always_include?: boolean
}

/** Hints for OpenAI function-calling adapter */
export interface OpenAIFunctionHints {
  /** Whether this supports parallel tool calls */
  parallel_safe?: boolean
  /** Whether to use structured outputs for this tool */
  use_structured_output?: boolean
}

/** Adapter-specific hints bundle */
export interface LLMHints {
  agentic?: AgenticHints
  bulk_context?: BulkContextHints
  openai_function?: OpenAIFunctionHints
}

// ── Input/Output schema ──────────────────────────────────────────────────────

/** JSON Schema-compatible parameter definition */
export interface ParameterSchema {
  type: 'string' | 'number' | 'boolean' | 'object' | 'array'
  description?: string
  required?: boolean
  default?: unknown
  enum?: unknown[]
  items?: ParameterSchema
  properties?: Record<string, ParameterSchema>
}

/** Schema for a capability's input arguments */
export type InputSchema = Record<string, ParameterSchema>

// ── Registry interfaces ───────────────────────────────────────────────────────

/** Parity check result */
export interface ParityCheckResult {
  passed: boolean
  mcp_count: number
  consume_count: number
  missing_in_mcp: CapabilityUri[]
  missing_in_consume: CapabilityUri[]
  extra_in_mcp: CapabilityUri[]
  /**
   * Non-null when the MCP capability bridge failed to import/execute (GT-36).
   * A non-null bridge_error ALWAYS forces `passed: false`, even in the
   * degenerate case where both URI sets end up empty — a failed bridge means
   * the check could not run at all and must never be reported as a pass.
   */
  bridge_error: string | null
}

/** Capability filter for listing */
export interface CapabilityFilter {
  type?: CapabilityType
  layer?: Layer
  name_prefix?: string
  scope?: Scope
  archetype?: RetrievalArchetype
  traversal_level?: TraversalLevel
  tool_role?: ToolRole
}

// ── L0FR Stream B: narrowed capability descriptor types ──────────────────────

interface L0FRLLMHints {
  agentic?: {
    cost_class?: 'cheap' | 'medium' | 'expensive'
    always_prefetch?: boolean
    latency_ms_p50?: number
  }
  bulk_context?: {
    pre_fetch_priority?: number
    always_include?: boolean
    result_size_kb_p50?: number
  }
  result_max_kb?: number
}

/** Result type for tool calls */
export interface ToolResult {
  content: string | object
  is_error?: boolean
  metadata?: Record<string, unknown>
}

/** Handler function signature */
export type CapabilityHandler = (
  args: Record<string, unknown>,
  context?: CapabilityContext
) => Promise<ToolResult>

/** Context passed to handlers */
export interface CapabilityContext {
  /** Optional chart context for chart-specific capabilities */
  chart_id?: string
  /** Request metadata */
  request_id?: string
}

/**
 * D1 contract fields mixin for the narrowed Stream B types.
 * These types (ToolCapability, ResourceCapability) predate D1 and use different
 * field names (primitive_type, loader). The D1 fields are added as optional here
 * so existing narrowed capabilities can carry the contract fields without breaking
 * the interface. The main CapabilityDescriptor (above) is the authoritative shape.
 */
interface D1Fields {
  scope?: Scope
  archetype?: RetrievalArchetype
  traversal_level?: TraversalLevel
  tool_role?: ToolRole
  drill_children?: CapabilityUri[]
  emits_references?: boolean
  grounds_to?: { l1_fact_ids?: boolean; l0_citation_ids?: boolean }
  lel_capable?: boolean
  behavioral_overrides?: {
    anthropic?: Record<string, unknown>
    gemini?: Record<string, unknown>
    openai?: Record<string, unknown>
    deepseek?: Record<string, unknown>
  }
  required_inputs?: string[]
}

/** Narrowed descriptor for capabilities with primitive_type = 'tool' */
export interface ToolCapability extends D1Fields {
  uri: CapabilityUri
  primitive_type: 'tool'
  layer: Layer
  name: string
  description: string
  input_schema?: Record<string, unknown>
  output_schema?: Record<string, unknown>
  llm_hints?: L0FRLLMHints
  handler: (args: Record<string, unknown>, ctx?: CapabilityContext) => Promise<unknown>
}

/** Narrowed descriptor for capabilities with primitive_type = 'resource' */
export interface ResourceCapability extends D1Fields {
  uri: CapabilityUri
  primitive_type: 'resource'
  layer: Layer
  name: string
  description: string
  mime_type?: string
  llm_hints?: L0FRLLMHints
  loader: (ctx?: CapabilityContext) => Promise<unknown>
}

// ── D1 amendment log ─────────────────────────────────────────────────────────

/**
 * Amendment log for the frozen D1 contract.
 * Any future optional field additions are recorded here.
 */
export const D1_AMENDMENTS: Array<{
  version: number
  date: string
  field: string
  description: string
}> = [
  // No amendments yet — initial freeze only.
]
