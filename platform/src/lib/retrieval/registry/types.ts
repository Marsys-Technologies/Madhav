/**
 * retrieval/registry/types.ts
 *
 * Capability descriptor types for the unified L0-L5 retrieval registry.
 * Covers all three primitive types: Tool, Resource, Prompt.
 *
 * L0FR Stream A — authored 2026-06-07
 * No audience_tier — access is uniform per L0FR architecture.
 */

// ── Primitive types ───────────────────────────────────────────────────────────

export type PrimitiveType = 'tool' | 'resource' | 'prompt'

export type Layer = 'L0' | 'L1' | 'L2' | 'L3' | 'L4' | 'L5'

export type CostClass = 'cheap' | 'medium' | 'expensive'

// ── Adapter hints ─────────────────────────────────────────────────────────────

export interface AgenticHints {
  /** Relative cost for loop budget governor decisions */
  cost_class: CostClass
  /** If true, always run in pre-fetch phase regardless of query */
  always_prefetch?: boolean
  /** Typical latency in ms (used for budget planning) */
  latency_ms_p50?: number
}

export interface BulkContextHints {
  /** 0-100: higher = fetched first in bulk-context pre-fetch pass */
  pre_fetch_priority: number
  /** If true, always include regardless of query intent */
  always_include?: boolean
  /** Typical result size in KB */
  result_size_kb_p50?: number
}

export interface AdapterHints {
  agentic?: AgenticHints
  bulk_context?: BulkContextHints
  /** Max result size in KB; clips before returning to LLM */
  result_max_kb?: number
}

// ── Tool descriptor ───────────────────────────────────────────────────────────

export interface ToolInputSchema {
  type: 'object'
  properties: Record<string, {
    type: string
    description?: string
    enum?: string[]
    default?: unknown
  }>
  required?: string[]
  additionalProperties?: boolean
}

export interface ToolOutputSchema {
  type: 'object'
  properties: Record<string, { type: string; description?: string }>
}

export interface ToolCapability {
  primitive_type: 'tool'
  /** marsys://tool/{layer}/{name} */
  uri: string
  layer: Layer
  name: string
  description: string
  input_schema: ToolInputSchema
  output_schema?: ToolOutputSchema
  llm_hints: AdapterHints
  /** Handler: receives validated args, returns result */
  handler: (args: Record<string, unknown>, ctx: CapabilityContext) => Promise<unknown>
}

// ── Resource descriptor ───────────────────────────────────────────────────────

export interface ResourceCapability {
  primitive_type: 'resource'
  /** marsys://resource/{path} */
  uri: string
  layer: Layer
  name: string
  description: string
  mime_type?: string
  llm_hints: AdapterHints
  /** Loader: returns the resource content */
  loader: (ctx: CapabilityContext) => Promise<unknown>
}

// ── Prompt descriptor ─────────────────────────────────────────────────────────

export interface PromptArgument {
  name: string
  description?: string
  required?: boolean
}

export interface PromptCapability {
  primitive_type: 'prompt'
  /** marsys://prompt/{name} */
  uri: string
  layer: Layer
  name: string
  description: string
  arguments?: PromptArgument[]
  llm_hints: AdapterHints
  /** Renderer: receives args, returns rendered prompt messages */
  renderer: (args: Record<string, string>, ctx: CapabilityContext) => Promise<PromptMessage[]>
}

export interface PromptMessage {
  role: 'user' | 'assistant'
  content: string
}

// ── Union type ────────────────────────────────────────────────────────────────

export type Capability = ToolCapability | ResourceCapability | PromptCapability

// ── Context passed to all handlers/loaders/renderers ─────────────────────────

export interface CapabilityContext {
  /** DB connection or pool getter */
  db?: () => Promise<unknown>
  /** Optional chart_id for per-chart queries */
  chart_id?: string
  /** Request-scoped trace ID */
  trace_id?: string
}
