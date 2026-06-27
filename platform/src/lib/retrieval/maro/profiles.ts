/**
 * MARO — Model-Agnostic Retrieval Orchestration: Per-Family Profiles
 * ===================================================================
 * D-PROFILES wave — RETRIEVAL_MODEL_PROFILES v1.0 implementation.
 *
 * One profile per LLM family. Values tagged [UNMEASURED — D8] are v1 hypotheses
 * drawn from RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md.
 * Each is scheduled for re-measurement against the MARSYS corpus once
 * the D8 eval harness exists. Until then these are production defaults.
 *
 * Profile version format: semver. Bump PROFILE_VERSION on any profile change.
 * This is a LIVING artifact — re-measured + bumped as models evolve.
 *
 * NVIDIA NIM: uses openai profile + cache_strategy:none override.
 * No fifth profile needed — see normalizeForFamily() which applies the override.
 */

import type { FamilyNormalization, ModelFamily } from './types'

/** Semver version for all four profiles in this build. */
export const PROFILE_VERSION = '1.0.0'

/**
 * Profile status flag.
 * 'UNMEASURED' — v1 hypothesis values from provider spec; not yet validated
 *   against the MARSYS corpus by the D8 eval harness.
 * 'MEASURED'   — values confirmed by D8 eval harness on MARSYS corpus.
 */
export type ProfileStatus = 'UNMEASURED' | 'MEASURED'

export const PROFILE_STATUS: ProfileStatus = 'UNMEASURED'

// ── Anthropic profile ─────────────────────────────────────────────────────────
// Models: claude-haiku-4-5 (200K ctx) / claude-sonnet-4-6 (1M) / claude-opus-4-7 (1M)
// Pinned from platform/src/lib/models/registry.ts (FAMILY_WORKER + STACK_ROUTING).
// Deprecations: none currently flagged.

/**
 * Anthropic family normalization profile.
 *
 * Key behaviors:
 * - Tool args: parsed object (no JSON.parse)
 * - Tool results: tool_result blocks; results-first in user message
 * - Caching: MUST mark explicitly; ≤4 breakpoints; never cache timestamped blocks
 * - Structured output: json_schema + strict=true → grammar-constrained (drift=0)
 * - Reasoning: thinking+redacted_thinking blocks MUST be passed back verbatim
 * - MCP: HTTPS only; tools only; no resources/prompts on Anthropic connector
 */
export const ANTHROPIC_PROFILE: FamilyNormalization = {
  family: 'anthropic',
  tool_arg_format: 'object',         // parsed — no JSON.parse needed
  requires_json_parse: false,
  tool_result_wire: 'tool_result_block',  // results-first user msg [UNMEASURED — D8]
  cache_strategy: 'explicit_headers',
  structured_output_format: 'json_schema',
  validate_and_repair: false,        // strict=true grammar-constrained; still validate values
  context_budget: {
    worker:  200_000,                // Haiku 4.5 cap
    mid:   1_000_000,                // Sonnet 4.6
    premium: 1_000_000,             // Opus 4.7
  },
  reasoning_round_trip: 'unmodified',  // thinking+redacted_thinking MUST pass back verbatim
  mcp_transport: 'https_only',
  strip_mcp_constructs: false,
  prompt_structure: '[stable_prefix]→[variable_tail]',
  max_active_tools: 20,              // ≤20 strict; ≤24 optional params; ≤16 union params [UNMEASURED — D8]
}

// ── Gemini profile ────────────────────────────────────────────────────────────
// Models: gemini-2.5-flash-lite (8K out) / gemini-2.5-flash (1M in) / gemini-2.5-pro (2M in)
// Pinned from registry.ts.
// Deprecations: gemini-2.0-flash-lite (HTTP 404 on OpenAI-compat endpoint 2026-05-03).

/**
 * Gemini family normalization profile.
 *
 * Key behaviors:
 * - Tool args: parsed object (no JSON.parse)
 * - Tool results: functionResponse with EXACT id from functionCall (id mismatch = silent failure)
 * - Caching: explicit caches.create → handle preferred; implicit auto-on 2.5+ but not guaranteed
 * - Structured output: gemini_response_schema; does NOT guarantee values semantically correct
 * - Reasoning: thought_signatures required for function calling; send per original Part; never merge
 * - MCP: Streamable HTTP only (no SSE); no `-` in server names; not on Gemini 3 yet
 */
export const GEMINI_PROFILE: FamilyNormalization = {
  family: 'gemini',
  tool_arg_format: 'object',                       // parsed — no JSON.parse needed
  requires_json_parse: false,
  tool_result_wire: 'functionResponse_with_exact_id',  // exact id from functionCall MUST match [UNMEASURED — D8]
  cache_strategy: 'context_caching',
  structured_output_format: 'gemini_response_schema',
  validate_and_repair: true,                       // ALWAYS validate values; ignores unsupported props
  context_budget: {
    worker:      8_192,                            // output cap; Flash Lite
    mid:     1_000_000,                            // Flash 1M input
    premium: 2_000_000,                            // Pro 2M — largest of all stacks
  },
  reasoning_round_trip: 'per_part_unmodified',     // thought_signature per Part; never merge/concat [UNMEASURED — D8]
  mcp_transport: 'streamable_http',                // no SSE; snake_case server names only
  strip_mcp_constructs: false,
  prompt_structure: 'large_common_at_beginning_query_at_end',
  max_active_tools: 20,                            // 10–20 soft guidance; may reject large/nested schemas [UNMEASURED — D8]
}

// ── OpenAI profile ────────────────────────────────────────────────────────────
// Models: gpt-4.1-nano (1M) / gpt-4.1-mini (1M) / gpt-4.1 (1M)
// Pinned from registry.ts.
// Deprecations: gpt-4o / gpt-4o-mini (128K — not suitable for Whole-Chart-Read).
// NVIDIA NIM: inherits this profile with cache_strategy:none override.

/**
 * OpenAI family normalization profile.
 *
 * Key behaviors:
 * - Tool args: JSON STRING — MUST JSON.parse(arguments) (same as DeepSeek)
 * - Tool results: function_call_output{call_id} (Responses) / role:tool (Chat)
 * - Caching: automatic, free, no code change needed; min 1024 tokens
 * - Structured output: json_schema + strict=true → schema guarantee; refusal field
 * - Reasoning: reasoning.encrypted_content or previous_response_id; reserve ≥25K tokens
 * - MCP: Streamable HTTP or SSE; approval default; defer_loading for large servers
 */
export const OPENAI_PROFILE: FamilyNormalization = {
  family: 'openai',
  tool_arg_format: 'json_string',      // MUST JSON.parse(arguments)
  requires_json_parse: true,
  tool_result_wire: 'function_call_output',  // Responses: function_call_output{call_id}; Chat: role:tool [UNMEASURED — D8]
  cache_strategy: 'automatic',
  structured_output_format: 'json_schema',
  validate_and_repair: false,          // strict=true guarantee; still validate values; watch refusal field
  context_budget: {
    worker:   1_000_000,
    mid:      1_000_000,
    premium:  1_000_000,
    billing_threshold: 272_000,        // extended-context billing above this threshold
  },
  reasoning_round_trip: 'encrypted_content_or_prev_id',  // reserve ≥25K for reasoning+output [UNMEASURED — D8]
  mcp_transport: 'streamable_http_or_sse',
  strip_mcp_constructs: false,
  prompt_structure: '[stable_prefix]→[variable_tail]',
  max_active_tools: 20,                // "keep initially available functions small"; <20 [UNMEASURED — D8]
}

// ── DeepSeek profile ──────────────────────────────────────────────────────────
// Models: deepseek-chat (worker/planner — only valid non-thinking API ID)
//         deepseek-v4-pro (premium synthesis, thinking mode)
// Deprecation watchpoint: 2026-07-24 — deepseek-chat → deepseek-v4-flash alias retires
//                                       deepseek-reasoner → deepseek-v4-pro alias retires
// deepseek-v4-flash is NOT a valid DeepSeek API model ID (rejects toolChoice).

/**
 * DeepSeek family normalization profile.
 *
 * Key behaviors:
 * - Tool args: JSON STRING — MUST JSON.parse(arguments) (same as OpenAI)
 * - Tool results: role:tool (OpenAI-compatible)
 * - Caching: automatic on DeepSeek API; 64-token min unit (smallest of all families)
 * - Structured output: json_object ONLY; no content-level strict schema; 5–12% drift rate
 *   → validate-and-repair is MANDATORY; may return empty content
 * - Reasoning: V4 rule: reasoning_content MUST be passed back on tool turns (400 error otherwise)
 *   V4 INVERTS legacy R1 behavior — version-pin is critical
 * - MCP: NONE — DeepSeek does not implement MCP; plain tool-calling backend only
 */
export const DEEPSEEK_PROFILE: FamilyNormalization = {
  family: 'deepseek',
  tool_arg_format: 'json_string',      // MUST JSON.parse(arguments) — OpenAI-compatible
  requires_json_parse: true,
  tool_result_wire: 'role_tool',       // role:tool (OpenAI-compatible)
  cache_strategy: 'none',             // automatic on API; registry sets none for routing
  structured_output_format: 'json_object',  // NO content-level strict schema
  validate_and_repair: true,           // MANDATORY — 5–12% drift; may return empty content [UNMEASURED — D8]
  context_budget: {
    worker:    128_000,                // conservative floor [UNMEASURED — D8] — V4 Flash via deepseek-chat
    premium: 1_000_000,               // V4 Pro confirmed 1M
    working_assumption: '~128k floor until V4 Flash API endpoint confirmed at 1M end-to-end',
  },
  reasoning_round_trip: 'reasoning_content_v4_tool_turns',  // 400 error if omitted on V4 tool turns
  mcp_transport: 'none',               // DeepSeek has NO MCP support
  strip_mcp_constructs: true,          // MUST strip MCP-specific constructs for DeepSeek
  prompt_structure: '[stable_prefix_from_token_0]→[variable_tail]',
  max_active_tools: 10,                // smallest-footprint; fewest tools; avoid nested schemas [UNMEASURED — D8]
}

// ── Universal fallback profile ────────────────────────────────────────────────
// Served when no family is declared by the client.
// Conservative: smallest common denominator of all four families.
// Tool names must be cross-family valid: snake_case, no hyphens, ≤64 chars, [A-Za-z0-9_.]

/**
 * Universal fallback normalization profile.
 * Applied when family is undeclared or unrecognized.
 * Uses the most conservative settings from the conflict matrix:
 *   - json_string (openai/deepseek require JSON.parse; universal must handle it)
 *   - validate_and_repair: true (DeepSeek worst-case)
 *   - context_budget: 128K (DeepSeek conservative floor)
 *   - mcp_transport: streamable_http (Gemini constraint; OpenAI accepts this too)
 *   - no MCP constructs (DeepSeek can't handle them)
 */
export const UNIVERSAL_PROFILE: FamilyNormalization = {
  family: 'universal',
  tool_arg_format: 'json_string',      // conservative: caller must handle JSON.parse
  requires_json_parse: true,
  tool_result_wire: 'universal',
  cache_strategy: 'none',             // no assumptions about caching mechanism
  structured_output_format: 'json_object',  // most conservative format
  validate_and_repair: true,           // always validate on universal
  context_budget: {
    worker:  128_000,                  // conservative DeepSeek floor
    premium: 128_000,
  },
  reasoning_round_trip: 'none',        // no reasoning assumptions on universal
  mcp_transport: 'streamable_http',    // Gemini constraint (no SSE); cross-family safe
  strip_mcp_constructs: false,         // caller must handle per actual family
  prompt_structure: '[stable_prefix]→[variable_tail]',
  max_active_tools: 10,                // smallest of all families
}

// ── Profile registry ──────────────────────────────────────────────────────────

const PROFILES: Record<ModelFamily, FamilyNormalization> = {
  anthropic: ANTHROPIC_PROFILE,
  gemini:    GEMINI_PROFILE,
  openai:    OPENAI_PROFILE,
  deepseek:  DEEPSEEK_PROFILE,
  universal: UNIVERSAL_PROFILE,
}

/**
 * Get the normalization profile for a given LLM family.
 * Falls back to 'universal' if the family is unknown.
 */
export function getProfile(family: ModelFamily): FamilyNormalization {
  return PROFILES[family] ?? UNIVERSAL_PROFILE
}

/**
 * Get context budget tokens for a given profile and tier.
 * Used by MARO to shape bundle size and prompt construction.
 */
export function getContextBudget(
  profile: FamilyNormalization,
  tier: 'worker' | 'mid' | 'premium' = 'premium',
): number {
  const budget = profile.context_budget
  if (tier === 'mid' && budget.mid !== undefined) return budget.mid
  if (tier === 'worker') return budget.worker
  return budget.premium
}

/**
 * Deprecation watchlist for alias retirement.
 * Each entry documents a model ID that will stop working or change behavior
 * on the stated retire_date.
 *
 * DeepSeek legacy aliases retire 2026-07-24 — see profile for V4 behavior notes.
 */
export interface DeprecationWatch {
  model_id: string
  family: ModelFamily
  retire_date?: string
  note: string
}

export const DEPRECATION_WATCHLIST: DeprecationWatch[] = [
  {
    model_id: 'deepseek-chat',
    family: 'deepseek',
    retire_date: '2026-07-24',
    note: 'API alias → deepseek-v4-flash (non-thinking). Use as worker/planner until alias retires.',
  },
  {
    model_id: 'deepseek-reasoner',
    family: 'deepseek',
    retire_date: '2026-07-24',
    note: 'API alias → deepseek-v4-pro (thinking). Deprecated — use deepseek-v4-pro directly.',
  },
  {
    model_id: 'deepseek-v4-flash',
    family: 'deepseek',
    note: 'NOT a valid DeepSeek API model ID — rejects toolChoice. Do not use as API model ID.',
  },
  {
    model_id: 'gemini-2.0-flash-lite',
    family: 'gemini',
    note: 'HTTP 404 on OpenAI-compat endpoint 2026-05-03 — replaced by gemini-2.5-flash-lite.',
  },
  {
    model_id: 'gpt-4o',
    family: 'openai',
    note: '128K context — not suitable for Whole-Chart-Read; legacy backward compat only.',
  },
  {
    model_id: 'gpt-4o-mini',
    family: 'openai',
    note: '128K context — not suitable for Whole-Chart-Read; legacy backward compat only.',
  },
]
