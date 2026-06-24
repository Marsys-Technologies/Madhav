/**
 * L0FR Stream A — Retrieval Registry Types
 * ==========================================
 * Full Capability descriptor per master plan §6.
 * Zero audience_tier — capabilities are universally accessible.
 */

// ── Primitive types ─────────────────────────────────────────────────────────

/** The three primitive capability types. */
export type CapabilityType = 'tool' | 'resource' | 'prompt'

/** URI format: marsys://tool/L0/name or marsys://resource/path or marsys://prompt/name */
export type CapabilityUri = string

/** Layer identifiers */
export type Layer = 'L0' | 'L1' | 'L2' | 'L3' | 'L4' | 'L5'

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

// ── Capability descriptor ─────────────────────────────────────────────────────

/**
 * Full Capability descriptor — the single definition that both MCP and Consume Chat consume.
 * No audience_tier, no per-tier filtering — universally accessible.
 */
export interface CapabilityDescriptor {
  /** Unique URI: marsys://tool|resource|prompt/layer/name */
  uri: CapabilityUri

  /** Primitive type */
  type: CapabilityType

  /** Layer this capability belongs to */
  layer: Layer

  /** Short human-readable name */
  name: string

  /** Full description for LLM consumption */
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

// ── Registry interfaces ───────────────────────────────────────────────────────

/** Parity check result */
export interface ParityCheckResult {
  passed: boolean
  mcp_count: number
  consume_count: number
  missing_in_mcp: CapabilityUri[]
  missing_in_consume: CapabilityUri[]
  extra_in_mcp: CapabilityUri[]
}

/** Capability filter for listing */
export interface CapabilityFilter {
  type?: CapabilityType
  layer?: Layer
  name_prefix?: string
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

/** Narrowed descriptor for capabilities with primitive_type = 'tool' */
export interface ToolCapability {
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
export interface ResourceCapability {
  uri: CapabilityUri
  primitive_type: 'resource'
  layer: Layer
  name: string
  description: string
  mime_type?: string
  llm_hints?: L0FRLLMHints
  loader: (ctx?: CapabilityContext) => Promise<unknown>
}
