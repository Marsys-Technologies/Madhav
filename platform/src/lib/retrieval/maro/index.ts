/**
 * MARO — Model-Agnostic Retrieval Orchestration
 * ===============================================
 * D-PROFILES wave public API.
 *
 * Single source of model-aware logic — consumed by BOTH channels:
 *   - Chat engine (chat channel): MARO owns the loop; full per-model optimization.
 *   - MCP adapter (BYO-MCP channel): MARO shapes surface/returns/grounding/budget/validation.
 *
 * No per-channel duplication of the per-family normalization logic. If a channel
 * needs model-aware behavior, it imports from here, not from a parallel copy.
 *
 * Usage (chat channel):
 *   import { orchestrate, resolveFamily } from '@/lib/retrieval/maro'
 *   const result = orchestrate(request, capability)
 *   // → result.normalization, result.normalized_args, result.validate_and_repair, …
 *
 * Usage (MCP channel):
 *   import { getMcpSurface } from '@/lib/retrieval/maro'
 *   const surface = getMcpSurface(declaredFamily)
 *   // → surface.max_tools, surface.tool_name_pattern, surface.strip_mcp_constructs, …
 *
 * Chart-agnostic: no literal chart_id, no native identifiers in any artifact.
 * chart_id is required in every RetrievalRequest — never defaulted by MARO.
 */

export { resolveFamily, resolveNormalization, getMcpSurfaceSpec, applyNvidiaOverrides, normalizeToolArgs, serializeToolArgs, validateAndRepair, stripMcpConstructs } from './normalizer'
export { getProfile, getContextBudget, PROFILE_VERSION, PROFILE_STATUS, DEPRECATION_WATCHLIST, ANTHROPIC_PROFILE, GEMINI_PROFILE, OPENAI_PROFILE, DEEPSEEK_PROFILE, UNIVERSAL_PROFILE } from './profiles'
export type { ModelFamily, RetrievalRequest, OrchestrationResult, FamilyNormalization, ToolArgFormat, ToolResultWire, CacheStrategy, StructuredOutputFormat, ReasoningRoundTrip, McpTransport, ContextBudget, UNIVERSAL_SURFACE as UniversalSurfaceSpec } from './types'
export { UNIVERSAL_SURFACE } from './types'
export type { McpSurfaceSpec, ValidationResult } from './normalizer'
export type { DeprecationWatch, ProfileStatus } from './profiles'

// Re-export the primary orchestration function with the canonical name
import { resolveNormalization } from './normalizer'
import type { RetrievalRequest, OrchestrationResult } from './types'
import type { CapabilityDescriptor } from '@/lib/retrieval/registry/types'

/**
 * Primary MARO orchestration entry point.
 *
 * Takes a RetrievalRequest + optional capability descriptor and returns
 * the full normalization spec for the resolved model family.
 *
 * chart_id ALWAYS required — throws if absent. Per D1 contract principle #14:
 * chart_id is never defaulted or inferred by MARO.
 *
 * @param request - The retrieval request (chart_id required)
 * @param capability - Optional capability descriptor for behavioral_overrides
 * @param isNvidiaModel - True if the model is on NVIDIA NIM (applies openai+cache:none override)
 */
export function orchestrate(
  request: RetrievalRequest,
  capability?: CapabilityDescriptor,
  isNvidiaModel?: boolean,
): Omit<OrchestrationResult, 'tool_result'> {
  return resolveNormalization(request, capability, isNvidiaModel)
}

/**
 * Get the MCP channel surface spec for a declared model family.
 * Exported with the canonical name for MCP adapter consumption.
 */
export { getMcpSurfaceSpec as getMcpSurface } from './normalizer'
