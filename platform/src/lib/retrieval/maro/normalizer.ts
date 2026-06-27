/**
 * MARO — Model-Agnostic Retrieval Orchestration: Normalizer
 * ==========================================================
 * D-PROFILES wave — the per-family normalization layer.
 *
 * Applies the four per-axis normalizations mandated by the provider spec:
 *   1. Tool-arg decode: object vs JSON.parse(arguments)
 *   2. Caching control: explicit headers / context_caching / automatic / none
 *   3. Structured output validate-and-repair (mandatory for deepseek, always for gemini)
 *   4. Prompt structure hint for the caller
 *   5. Reasoning round-trip mode
 *
 * Also applies behavioral_overrides from the capability descriptor
 * (D1 contract field: capability.behavioral_overrides[family]).
 *
 * Chart-agnostic: no literal chart_id, no native identifiers in any output.
 * chart_id is always required in the RetrievalRequest — MARO never defaults it.
 */

import type { ModelFamily, RetrievalRequest, OrchestrationResult, FamilyNormalization } from './types'
import { getProfile, getContextBudget } from './profiles'
import type { CapabilityDescriptor } from '@/lib/retrieval/registry/types'

// ── Family resolution ─────────────────────────────────────────────────────────

/**
 * Resolve the effective model family.
 * Undeclared or unrecognized → 'universal' (conservative cross-model fallback).
 *
 * Declaration mechanisms supported (in priority order per §0.2 of the brief):
 *   1. Direct model_family in the request (client hint / config)
 *   2. Undeclared → 'universal'
 *
 * Operator-set config (env), OAuth scope, and per-key binding are resolved
 * BEFORE calling MARO and surfaced as model_family in the request.
 */
export function resolveFamily(request: RetrievalRequest): ModelFamily {
  const declared = request.model_family
  if (!declared) return 'universal'

  const VALID: ModelFamily[] = ['anthropic', 'gemini', 'openai', 'deepseek', 'universal']
  if (!VALID.includes(declared)) {
    // Unknown family → universal fallback
    return 'universal'
  }
  return declared
}

// ── Behavioral override application ──────────────────────────────────────────

/**
 * Apply capability.behavioral_overrides[family] on top of the family default profile.
 * Most capabilities leave behavioral_overrides unset; this is a no-op for them.
 * Only called when a capability needs explicit per-family shaping beyond the profile default.
 *
 * Per D1 contract (platform/src/lib/retrieval/registry/types.ts):
 *   behavioral_overrides?: {
 *     anthropic?: Record<string, unknown>
 *     gemini?: Record<string, unknown>
 *     openai?: Record<string, unknown>
 *     deepseek?: Record<string, unknown>
 *   }
 */
function applyBehavioralOverrides(
  profile: FamilyNormalization,
  capability: CapabilityDescriptor | undefined,
  family: ModelFamily,
): FamilyNormalization {
  if (!capability?.behavioral_overrides) return profile
  if (family === 'universal') return profile

  const overrides = capability.behavioral_overrides[family as keyof typeof capability.behavioral_overrides]
  if (!overrides || Object.keys(overrides).length === 0) return profile

  // Merge overrides into profile; type-safe via spread + capability_overrides field
  return {
    ...profile,
    capability_overrides: overrides,
  }
}

// ── NVIDIA NIM override ───────────────────────────────────────────────────────

/**
 * Apply NVIDIA NIM overrides onto the OpenAI profile.
 * NVIDIA inherits the openai profile with:
 *   - cache_strategy: 'none' (no caching on NIM free tier)
 *   - streaming_required: true (all NIM models)
 *   - validate_and_repair: true (json_object only; treat like DeepSeek)
 *
 * This is NOT a separate profile — it is the openai profile + these overrides.
 * Callers detect NVIDIA by checking provider='nvidia' from the model registry
 * and then calling applyNvidiaOverrides.
 */
export function applyNvidiaOverrides(profile: FamilyNormalization): FamilyNormalization {
  return {
    ...profile,
    cache_strategy: 'none',
    validate_and_repair: true,       // NIM uses json_object; treat as DeepSeek for validation
    capability_overrides: {
      ...profile.capability_overrides,
      streaming_required: true,
      provider_note: 'NVIDIA NIM inherits openai profile; cache_strategy=none; streaming_required=true',
    },
  }
}

// ── Tool argument normalization ───────────────────────────────────────────────

/**
 * Normalize tool arguments for the resolved family.
 *
 * OpenAI + DeepSeek: tool arguments arrive as a JSON string in `arguments`.
 * MARO normalizes this to an object for internal processing, but also
 * returns the format flag so the caller knows how to re-serialize.
 *
 * Anthropic + Gemini: arguments are already parsed objects.
 */
export function normalizeToolArgs(
  args: Record<string, unknown> | string | undefined,
  profile: FamilyNormalization,
): Record<string, unknown> {
  if (!args) return {}

  if (typeof args === 'string') {
    // Came in as JSON string (OpenAI/DeepSeek format)
    try {
      const parsed = JSON.parse(args)
      return typeof parsed === 'object' && parsed !== null ? parsed as Record<string, unknown> : {}
    } catch {
      // Malformed JSON — return empty args; caller should handle as tool error
      return { _parse_error: 'Failed to JSON.parse tool arguments', _raw: args }
    }
  }

  // Already an object (Anthropic/Gemini) — pass through
  return args
}

/**
 * Serialize tool arguments for dispatch to the model.
 * Inverse of normalizeToolArgs: produces the wire format the family expects.
 */
export function serializeToolArgs(
  args: Record<string, unknown>,
  profile: FamilyNormalization,
): Record<string, unknown> | string {
  if (profile.tool_arg_format === 'json_string') {
    return JSON.stringify(args)
  }
  return args
}

// ── Structured output validation ──────────────────────────────────────────────

/**
 * Validate and repair structured output for families that require it.
 *
 * DeepSeek: json_object only; 5–12% drift; may return empty content.
 *   Validate-and-repair is MANDATORY.
 *
 * Gemini: schema honored syntactically but values may be semantically incorrect.
 *   Always validate values; ignores unsupported schema properties.
 *
 * Anthropic + OpenAI (strict mode): grammar-constrained; drift=0 in strict mode.
 *   Still validate values; watch for refusal / truncation.
 *
 * Universal: treat as json_object; always validate.
 */
export interface ValidationResult {
  valid: boolean
  repaired: boolean
  value: unknown
  error?: string
}

export function validateAndRepair(
  output: unknown,
  profile: FamilyNormalization,
  expectedShape?: Record<string, unknown>,
): ValidationResult {
  if (!profile.validate_and_repair) {
    // Strict-mode families: still check for null/undefined
    if (output === null || output === undefined) {
      return { valid: false, repaired: false, value: output, error: 'Output is null/undefined' }
    }
    return { valid: true, repaired: false, value: output }
  }

  // Families requiring validate-and-repair (deepseek, gemini, universal)

  // Handle empty content (DeepSeek may return empty)
  if (output === null || output === undefined || output === '') {
    return {
      valid: false,
      repaired: false,
      value: output,
      error: 'Empty output — retry required (DeepSeek may return empty content)',
    }
  }

  // Parse JSON string if needed
  let parsed = output
  if (typeof output === 'string') {
    try {
      parsed = JSON.parse(output)
    } catch {
      return {
        valid: false,
        repaired: false,
        value: output,
        error: 'Failed to parse JSON output — validate+retry required',
      }
    }
  }

  // Basic shape check if expected shape provided
  if (expectedShape && typeof parsed === 'object' && parsed !== null) {
    const missing = Object.keys(expectedShape).filter(k => !(k in (parsed as Record<string, unknown>)))
    if (missing.length > 0) {
      // Attempt repair: fill missing keys with null
      const repaired = { ...(parsed as Record<string, unknown>) }
      for (const k of missing) {
        repaired[k] = null
      }
      return { valid: true, repaired: true, value: repaired }
    }
  }

  return { valid: true, repaired: false, value: parsed }
}

// ── MCP construct stripping ───────────────────────────────────────────────────

/**
 * Strip MCP-specific constructs from a result for DeepSeek.
 *
 * DeepSeek does NOT implement MCP. If DeepSeek is the declared family on the
 * MCP channel, MARO must strip:
 *   - MCP content blocks (type:'resource', type:'embedded_resource')
 *   - resources, prompts, structuredContent fields
 *   - Any Gemini-specific thought_signature fields
 *
 * Returns only plain text and tool-call-compatible content.
 */
export function stripMcpConstructs(result: unknown): unknown {
  if (typeof result !== 'object' || result === null) return result

  const r = result as Record<string, unknown>
  const stripped: Record<string, unknown> = {}

  for (const [key, value] of Object.entries(r)) {
    // Drop MCP-specific keys
    if (['structuredContent', 'resources', 'prompts', 'embedded_resource', 'thought_signature'].includes(key)) {
      continue
    }
    // For content arrays, filter out non-text blocks
    if (key === 'content' && Array.isArray(value)) {
      const textOnly = value.filter((item: unknown) => {
        if (typeof item !== 'object' || item === null) return true
        const block = item as Record<string, unknown>
        return block['type'] === 'text' || block['type'] === 'tool_result'
      })
      stripped[key] = textOnly
      continue
    }
    stripped[key] = value
  }

  return stripped
}

// ── Main MARO orchestration entry point ───────────────────────────────────────

/**
 * Resolve the normalization parameters for a RetrievalRequest.
 *
 * This is the primary MARO entry point. Both channels consume this:
 *   - Chat channel: MARO owns the loop → full per-model optimization
 *   - BYO-MCP channel: MARO shapes surface/returns/grounding/budget/validation
 *
 * chart_id ALWAYS required — MARO will throw if absent.
 * Per D1 contract principle #14: chart_id is never defaulted or inferred.
 */
export function resolveNormalization(
  request: RetrievalRequest,
  capability?: CapabilityDescriptor,
  isNvidiaModel?: boolean,
): Omit<OrchestrationResult, 'tool_result'> {
  // chart_id guard — never defaulted, always required
  if (!request.chart_id || typeof request.chart_id !== 'string') {
    throw new Error('[MARO] chart_id is required and must be a non-empty string. MARO never defaults chart_id.')
  }

  // Resolve family
  const family = resolveFamily(request)

  // Get base profile
  let profile = getProfile(family)

  // Apply NVIDIA overrides if applicable
  if (isNvidiaModel) {
    profile = applyNvidiaOverrides(profile)
  }

  // Apply capability behavioral overrides
  profile = applyBehavioralOverrides(profile, capability, family)

  // Resolve context budget for the requested tier
  const tier = request.model_tier ?? 'premium'
  const contextBudgetTokens = getContextBudget(profile, tier)

  // Normalize args
  const normalizedArgs = serializeToolArgs(
    normalizeToolArgs(request.args, profile),
    profile,
  )

  return {
    resolved_family: family,
    normalization: profile,
    normalized_args: normalizedArgs,
    prompt_structure: profile.prompt_structure,
    validate_and_repair: profile.validate_and_repair,
    strip_mcp_constructs: profile.strip_mcp_constructs,
    context_budget_tokens: contextBudgetTokens,
  }
}

// ── Channel-specific helpers ──────────────────────────────────────────────────

/**
 * Get the tool surface spec for the BYO-MCP channel.
 *
 * Declared family → serve that family's profiled surface.
 * Undeclared → serve universal-best surface (10–15 consolidated tools;
 * tool names cross-family valid; dual output).
 *
 * DeepSeek on MCP: serve as plain tool-calling backend only; strip MCP constructs.
 */
export interface McpSurfaceSpec {
  family: ModelFamily
  max_tools: number
  tool_name_pattern: string
  requires_dual_output: boolean  // structuredContent + text JSON block per MCP spec
  strip_mcp_constructs: boolean
  transport: string
}

export function getMcpSurfaceSpec(family: ModelFamily): McpSurfaceSpec {
  if (family === 'universal') {
    return {
      family,
      max_tools: 15,
      tool_name_pattern: '^[A-Za-z0-9_.]{1,64}$',  // cross-family valid: no hyphens
      requires_dual_output: true,
      strip_mcp_constructs: false,
      transport: 'streamable_http',
    }
  }

  const profile = getProfile(family)

  return {
    family,
    max_tools: profile.max_active_tools,
    // Cross-family safe tool name pattern: satisfy both Anthropic (allows hyphens)
    // and Gemini (no hyphens) simultaneously by avoiding hyphens.
    tool_name_pattern: '^[A-Za-z0-9_.]{1,64}$',
    requires_dual_output: true,    // always return structuredContent + text block per MCP spec
    strip_mcp_constructs: profile.strip_mcp_constructs,
    transport: profile.mcp_transport,
  }
}
