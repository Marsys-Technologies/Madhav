/**
 * MARO — Model-Agnostic Retrieval Orchestration: Types
 * =====================================================
 * D-PROFILES wave — D-GROUNDTRUTH implementation.
 *
 * The four supported LLM families (from RETRIEVAL_MODEL_PROFILES_v1_0.md):
 *   anthropic — Claude family (claude-haiku-4-5 / claude-sonnet-4-6 / claude-opus-4-7)
 *   gemini    — Google Gemini family (gemini-2.5-flash-lite / gemini-2.5-flash / gemini-2.5-pro)
 *   openai    — OpenAI GPT family (gpt-4.1-nano / gpt-4.1-mini / gpt-4.1)
 *   deepseek  — DeepSeek family (deepseek-chat / deepseek-v4-pro)
 *
 * NVIDIA NIM models use the openai profile (OpenAI-compatible tool_use_format)
 * with cache_strategy:none override — no fifth profile.
 *
 * 'universal' is the undeclared fallback: MARO serves the cross-model surface
 * when no family is declared by the client.
 *
 * Chart-agnostic: no literal chart_id, no native identifiers in any MARO artifact.
 */

// ── Family discriminator ──────────────────────────────────────────────────────

/**
 * The four LLM families that MARO profiles, plus the 'universal' fallback.
 * Undeclared family → 'universal' → consolidated cross-model surface.
 */
export type ModelFamily =
  | 'anthropic'
  | 'gemini'
  | 'openai'
  | 'deepseek'
  | 'universal'

// ── Per-family normalization output (MARO produces this per call) ─────────────

/**
 * How tool arguments arrive from the model on this family.
 * 'object'      — parsed object; consume directly (anthropic, gemini).
 * 'json_string' — raw JSON string in `arguments`; must JSON.parse (openai, deepseek).
 */
export type ToolArgFormat = 'object' | 'json_string'

/**
 * Wire format for tool results sent back to the model.
 */
export type ToolResultWire =
  | 'tool_result_block'              // Anthropic: results-first user message, tool_result blocks
  | 'functionResponse_with_exact_id' // Gemini: functionResponse with exact functionCall.id
  | 'function_call_output'           // OpenAI: function_call_output{call_id} or role:tool
  | 'role_tool'                      // DeepSeek: role:tool (OpenAI-compatible)
  | 'universal'                      // Universal fallback: plain text role:tool

/**
 * Cache strategy for prompt construction.
 */
export type CacheStrategy =
  | 'explicit_headers'   // Anthropic: mark up to 4 cache_control breakpoints
  | 'context_caching'    // Gemini: explicit caches.create handle preferred
  | 'automatic'          // OpenAI: no code change; automatic on gpt-4o+
  | 'none'               // DeepSeek + NVIDIA NIM: automatic but registry set to none

/**
 * Structured output format the family supports.
 */
export type StructuredOutputFormat =
  | 'json_schema'           // Anthropic (strict=true, grammar-constrained) / OpenAI (strict=true)
  | 'gemini_response_schema' // Gemini: gemini_response_schema (values may err; validate)
  | 'json_object'           // DeepSeek: json_object only; no content-level strict schema

/**
 * Reasoning artifact round-trip mode.
 */
export type ReasoningRoundTrip =
  | 'unmodified'                         // Anthropic: thinking+redacted_thinking MUST pass back verbatim
  | 'per_part_unmodified'                // Gemini: thought_signature inside original Part, never merge
  | 'encrypted_content_or_prev_id'       // OpenAI: reasoning.encrypted_content or previous_response_id
  | 'reasoning_content_v4_tool_turns'    // DeepSeek V4: reasoning_content MUST pass back on tool turns
  | 'none'                               // No reasoning round-trip (families without extended thinking)

/**
 * MCP transport the family supports.
 */
export type McpTransport =
  | 'https_only'              // Anthropic connector: HTTPS, tools only
  | 'streamable_http'         // Gemini: Streamable HTTP; no SSE; snake_case server names
  | 'streamable_http_or_sse'  // OpenAI: Streamable HTTP or SSE
  | 'none'                    // DeepSeek: no MCP support; plain tool backend only

// ── Context budget by tier ────────────────────────────────────────────────────

/**
 * Context budget in tokens per model tier for this family.
 * Used by MARO to shape bundle size and prompt construction.
 */
export interface ContextBudget {
  worker: number
  mid?: number
  premium: number
  /** Extended-context billing threshold (OpenAI) */
  billing_threshold?: number
  /** Working assumption note for uncertain values */
  working_assumption?: string
}

// ── Full per-family normalization spec ────────────────────────────────────────

/**
 * The full normalization specification for a single LLM family.
 * MARO produces a NormalizedRequest from a RetrievalRequest + this spec.
 * Values tagged [UNMEASURED — D8] in the profile artifact are v1 hypotheses
 * awaiting D8 eval-harness measurement.
 */
export interface FamilyNormalization {
  /** Which family this normalization covers */
  family: ModelFamily

  /** Tool argument decode format */
  tool_arg_format: ToolArgFormat

  /** Tool result wire format */
  tool_result_wire: ToolResultWire

  /** Cache strategy */
  cache_strategy: CacheStrategy

  /** Structured output format */
  structured_output_format: StructuredOutputFormat

  /** Whether validate-and-repair is required on structured output */
  validate_and_repair: boolean

  /** Context budget by tier */
  context_budget: ContextBudget

  /** Reasoning round-trip mode */
  reasoning_round_trip: ReasoningRoundTrip

  /** MCP transport (or none) */
  mcp_transport: McpTransport

  /** Prompt structure hint for the caller */
  prompt_structure: string

  /** Maximum active tool count (soft guidance) */
  max_active_tools: number

  /** Whether JSON.parse is required on tool arguments */
  requires_json_parse: boolean

  /** Whether DeepSeek MCP stripping is required */
  strip_mcp_constructs: boolean

  /**
   * Per-capability behavioral overrides applied on top of family defaults.
   * Set from capability.behavioral_overrides[family]. Most capabilities leave this empty.
   */
  capability_overrides?: Record<string, unknown>
}

// ── MARO request / result ─────────────────────────────────────────────────────

/**
 * Input to MARO orchestration.
 *
 * chart_id is ALWAYS required and NEVER defaulted — per D1 contract principle #14.
 * MARO does not inject a chart_id; the caller must always supply one.
 */
export interface RetrievalRequest {
  /**
   * Chart UUID for chart-scoped capabilities.
   * REQUIRED — MARO will reject requests without a chart_id.
   * The chart_id is never defaulted or inferred by MARO.
   */
  chart_id: string

  /** The query to route */
  query: string

  /**
   * Declared model family from the client.
   * Undeclared → 'universal' → consolidated cross-model surface.
   * Declaration mechanisms (per §0.2 of the brief):
   *   1. Config declaration (operator-set)
   *   2. OAuth scope
   *   3. Per-key binding
   *   4. Client hint (header or initial parameter)
   */
  model_family?: ModelFamily

  /** Target URI of the capability to invoke */
  capability_uri: string

  /** Request arguments (tool args or resource params) */
  args?: Record<string, unknown>

  /** Whether LEL signals are enabled */
  lel_enabled?: boolean

  /** Budget ceiling in USD */
  budget_usd?: number

  /** Model tier hint (affects context budget selection) */
  model_tier?: 'worker' | 'mid' | 'premium'
}

/**
 * MARO orchestration output — normalized for the resolved model family.
 */
export interface OrchestrationResult {
  /** Resolved family (may differ from request if undeclared → 'universal') */
  resolved_family: ModelFamily

  /** Full normalization spec used for this request */
  normalization: FamilyNormalization

  /**
   * Tool arguments after normalization.
   * If tool_arg_format='json_string', args have been JSON.stringified.
   * If tool_arg_format='object', args are passed as-is.
   */
  normalized_args: Record<string, unknown> | string

  /**
   * Prompt structure guidance for the caller.
   * The caller should arrange prompts per this hint to optimize caching.
   */
  prompt_structure: string

  /**
   * Whether this family requires validate-and-repair on structured output.
   */
  validate_and_repair: boolean

  /**
   * Whether MCP constructs must be stripped (DeepSeek only).
   */
  strip_mcp_constructs: boolean

  /**
   * Context budget for the resolved tier.
   */
  context_budget_tokens: number

  /**
   * Raw tool result (may be undefined if the capability was not invoked).
   */
  tool_result?: unknown
}

// ── Universal surface spec ────────────────────────────────────────────────────

/**
 * Universal (undeclared family) surface spec.
 * When no family is declared, MARO serves the consolidated cross-model surface:
 *   - 10–15 consolidated workflow tools (not the full 70-asset mirror)
 *   - Tool names valid for ALL families: snake_case, no hyphens, ≤64 chars, [A-Za-z0-9_.]
 *   - response_format/verbosity enum so client self-selects
 *   - structuredContent + serialized JSON text block per MCP spec
 */
export interface UniversalSurfaceSpec {
  max_tools: 15
  tool_name_pattern: '^[A-Za-z0-9_.]{1,64}$'
  dual_output: true  // structuredContent + text JSON block
  verbosity_enum: ['minimal', 'standard', 'detailed']
}

export const UNIVERSAL_SURFACE: UniversalSurfaceSpec = {
  max_tools: 15,
  tool_name_pattern: '^[A-Za-z0-9_.]{1,64}$',
  dual_output: true,
  verbosity_enum: ['minimal', 'standard', 'detailed'],
}
