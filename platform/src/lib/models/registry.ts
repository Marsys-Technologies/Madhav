/**
 * Model registry — data only. Safe to import from both client and server.
 * The provider SDKs (`@ai-sdk/anthropic`, `@ai-sdk/google`, `@ai-sdk/deepseek`,
 * `@ai-sdk/openai`) live in a separate `resolver.ts` so they are never bundled
 * into the client.
 *
 * ── Design objective ───────────────────────────────────────────────────────
 * Every query response must be capable of Whole-Chart-Read: the synthesis
 * model receives ALL L2.5 artifacts (MSR 499 signals + UCN + CDLM + CGM + RM)
 * plus L1 FORENSIC data in a single unbroken context, without relevance-based
 * filtering at planning time. Relevance filtering at the planner stage creates
 * the risk of "missing the secret source" — a signal dismissed as irrelevant
 * that turns out to be the operative one. The 1M-context synthesis models
 * (DeepSeek-V4-Pro, Gemini-2.5-Pro) eliminate this risk: feed everything,
 * let the model decide what matters.
 *
 * Estimated full-corpus token load:
 *   MSR 499 signals    ~150K tokens
 *   UCN               ~ 50K tokens
 *   CDLM              ~ 30K tokens
 *   CGM               ~ 50K tokens
 *   RM                ~ 20K tokens
 *   L1 FORENSIC       ~ 30K tokens
 *   History + query   ~ 10K tokens
 *   ─────────────────────────────
 *   Total             ~340K tokens  ← fits comfortably in 1M context
 *
 * ── Three-tier family structure ────────────────────────────────────────────
 *   premium — flagship/deepest model; user-selectable for synthesis.
 *   mid     — balanced model; user-selectable for synthesis.
 *   worker  — cheapest model in the family; used for planner + title generation.
 *             Also user-selectable (fast/cheap chat), but labelled accordingly in UI.
 *
 * Every provider family must have exactly one model with tier='worker'; that model
 * is the canonical FAMILY_WORKER entry. All models use the standard AI SDK calling
 * convention (streamText with system message). No o-series / reasoning convention.
 *
 * ── Call-type routing ──────────────────────────────────────────────────────
 * CALL_TYPE_ROUTING maps each pipeline call type to { primary, fallback }.
 * Primary is tried first; fallback is used on rate-limit / timeout / error.
 * See CallType for the full taxonomy.
 */

import type { ProviderQuirks } from '@/lib/adapters/types'
export type { ProviderQuirks }

export type Provider = 'anthropic' | 'google' | 'deepseek' | 'openai' | 'nvidia'
export type Capability = 'tool-use' | 'prompt-caching'
export type SpeedTier = 'fast' | 'balanced' | 'deep'
export type ModelTier = 'premium' | 'mid' | 'worker'

/**
 * How this model surfaces its chain-of-thought reasoning to the UI.
 *
 *  'markers' — model emits ‹reasoning›…‹/reasoning› inline text markers that
 *              parseMarkers extracts from the visible stream (DeepSeek V4 Pro / R1).
 *              REASONING_NARRATION_GATE stays in the synthesis prompt.
 *
 *  'native'  — reasoning arrives via SDK-level `type:'reasoning'` UIMessage
 *              parts (Gemini 2.5 with thinkingBudget). No inline markers needed;
 *              REASONING_NARRATION_GATE is stripped from the synthesis prompt.
 *              The chat consumer extracts these parts for the reasoning UI surface (ReasoningSlot).
 *
 *  'none'    — no reasoning UI surface (GPT, Anthropic, NVIDIA, etc.).
 *              REASONING_NARRATION_GATE is stripped from the synthesis prompt,
 *              reducing token waste and prompt confusion.
 */
export type ReasoningMode = 'markers' | 'native' | 'none'

/**
 * ADR-1: each model declares whether it can serve as a worker
 * (planning/routing/title generation), synthesis (final answer), or both.
 * Workers are the cheapest model in their family; synthesis models are the
 * full set exposed to the user for final-answer generation.
 */
/**
 * planner — NVIDIA NIM models used exclusively as internal planners; never
 * exposed to users for synthesis. Excluded from synthesisPicker() automatically
 * since that helper only includes 'synthesis' | 'both'.
 */
export type ModelRole = 'worker' | 'synthesis' | 'both' | 'planner'

export interface ModelMeta {
  id: string
  label: string
  hint: string
  provider: Provider
  /** Family tier — used by the UI picker and by FAMILY_WORKER assignment. */
  tier: ModelTier
  speedTier: SpeedTier
  /**
   * Maximum number of INPUT tokens the model accepts (context window).
   * Omit for models where the limit is not a design constraint (<200K).
   * Explicitly set for 1M-context models to enable Whole-Chart-Read routing.
   */
  maxInputTokens?: number
  maxOutputTokens: number
  capabilities: Capability[]
  role: ModelRole
  /** USD cost per 1M input tokens — used by trace cost panel + telemetry. */
  costPer1MInput: number
  /** USD cost per 1M output tokens. */
  costPer1MOutput: number
  /**
   * How this model's chain-of-thought reasoning surfaces in the UI.
   * Controls whether REASONING_NARRATION_GATE is included in the synthesis
   * prompt and how the chat consumer routes reasoning content to the UI.
   */
  reasoningMode: ReasoningMode
  /** Provider-specific behavior metadata. Drives the Adapter Layer (AD.1+). */
  quirks: ProviderQuirks
}

/**
 * Single source of truth for every model the app exposes to users. Add a new
 * model here and it appears in the picker, the command palette, validation,
 * and capability gating simultaneously.
 */
export const MODELS: ModelMeta[] = [
  // ── Anthropic — Claude ──────────────────────────────────────────────────────
  // Worker: haiku-4-5  |  Mid: sonnet-4-6  |  Premium: opus-4-7
  {
    id: 'claude-haiku-4-5',
    provider: 'anthropic',
    tier: 'worker',
    label: 'Haiku 4.5',
    hint: 'Fast & cost-effective — planner + quick answers',
    speedTier: 'fast',
    maxOutputTokens: 64_000,
    capabilities: ['tool-use', 'prompt-caching'],
    role: 'both',
    costPer1MInput: 1.00,
    costPer1MOutput: 5.00,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: false,
      tool_use_format: 'anthropic',
      structured_output_format: 'json_schema',
      cache_strategy: 'explicit_headers',
      system_prompt_shape: 'system_block_array',
    },
  },
  {
    id: 'claude-sonnet-4-6',
    provider: 'anthropic',
    tier: 'mid',
    label: 'Sonnet 4.6',
    hint: 'Balanced depth and speed',
    speedTier: 'balanced',
    maxOutputTokens: 64_000,
    capabilities: ['tool-use', 'prompt-caching'],
    role: 'synthesis',
    costPer1MInput: 3.00,
    costPer1MOutput: 15.00,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: false,
      tool_use_format: 'anthropic',
      structured_output_format: 'json_schema',
      cache_strategy: 'explicit_headers',
      system_prompt_shape: 'system_block_array',
    },
  },
  {
    id: 'claude-opus-4-7',
    provider: 'anthropic',
    tier: 'premium',
    label: 'Opus 4.7',
    hint: 'Deepest Jyotish analysis',
    speedTier: 'deep',
    maxOutputTokens: 64_000,
    capabilities: ['tool-use', 'prompt-caching'],
    role: 'synthesis',
    costPer1MInput: 15.00,
    costPer1MOutput: 75.00,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: false,
      tool_use_format: 'anthropic',
      structured_output_format: 'json_schema',
      cache_strategy: 'explicit_headers',
      system_prompt_shape: 'system_block_array',
    },
  },

  // ── Google — Gemini ─────────────────────────────────────────────────────────
  // Worker: gemini-2.5-flash-lite  |  Mid: gemini-2.5-flash  |  Premium: gemini-2.5-pro
  //
  // gemini-2.5-flash-lite is the dedicated planner/worker: confirmed live on
  // Google OpenAI-compat endpoint (HTTP 200, smoke test 2026-05-03).
  // Replaces gemini-2.0-flash-lite which was dropped from the OpenAI-compat
  // endpoint (HTTP 404 confirmed 2026-05-03 — all variant IDs tested).
  {
    id: 'gemini-2.5-flash-lite',
    provider: 'google',
    tier: 'worker',
    label: 'Gemini 2.5 Flash Lite',
    hint: 'Lightest Google model — planner + quick answers',
    speedTier: 'fast',
    maxOutputTokens: 8_192,
    capabilities: ['tool-use'],
    role: 'both',
    costPer1MInput: 0.015,
    costPer1MOutput: 0.06,
    reasoningMode: 'native',  // Gemini thinking arrives via SDK type:'reasoning' parts
    quirks: {
      reasoning_via: 'native',
      streaming_required: false,
      tool_use_format: 'gemini',
      structured_output_format: 'gemini_response_schema',
      cache_strategy: 'context_caching',
      system_prompt_shape: 'system_message',
      request_transforms: { safety_filter: 'block_none', thinking_budget: 24576 },
    },
  },
  {
    id: 'gemini-2.5-flash',
    provider: 'google',
    tier: 'mid',
    label: 'Gemini 2.5 Flash',
    hint: 'Gemini Stack planner + context assembly — 1M context, $0.075 input',
    speedTier: 'balanced',
    maxInputTokens: 1_000_000,
    maxOutputTokens: 65_536,
    capabilities: ['tool-use'],
    role: 'both',
    costPer1MInput: 0.075,
    costPer1MOutput: 0.30,
    reasoningMode: 'native',  // Gemini thinking arrives via SDK type:'reasoning' parts
    quirks: {
      reasoning_via: 'native',
      streaming_required: false,
      tool_use_format: 'gemini',
      structured_output_format: 'gemini_response_schema',
      cache_strategy: 'context_caching',
      system_prompt_shape: 'system_message',
      request_transforms: { safety_filter: 'block_none', thinking_budget: 24576 },
    },
  },
  {
    id: 'gemini-2.5-pro',
    provider: 'google',
    tier: 'premium',
    label: 'Gemini 2.5 Pro',
    hint: 'Gemini Stack synthesis — 2M context, largest window of all stacks',
    speedTier: 'deep',
    maxInputTokens: 2_000_000,  // Largest context of any stack — full corpus + headroom
    maxOutputTokens: 65_536,
    capabilities: ['tool-use'],
    role: 'synthesis',
    costPer1MInput: 1.25,       // $1.25 up to 200K input; $2.50 above 200K
    costPer1MOutput: 10.00,
    reasoningMode: 'native',  // Gemini thinking arrives via SDK type:'reasoning' parts
    quirks: {
      reasoning_via: 'native',
      streaming_required: false,
      tool_use_format: 'gemini',
      structured_output_format: 'gemini_response_schema',
      cache_strategy: 'context_caching',
      system_prompt_shape: 'system_message',
      request_transforms: { safety_filter: 'block_none', thinking_budget: 24576 },
    },
  },


  // ── Gemini 3.x — CATALOG ONLY, NOT ACTIVE (PARIPRASHNA-P3-PREFLIGHT-2026-08-21) ──
  // Registered per the native's ruling item 1 (model ids verified) + item 2
  // (do not move any model yet — registration only). Neither model is
  // referenced by any live STACK_ROUTING entry; see STAGED_TIER_UPGRADE_ROUTING
  // below for the pinned activation plan. Model ids + specs verified live
  // against https://ai.google.dev/gemini-api/docs/models and
  // .../gemini-api/docs/pricing on 2026-08-21 — neither model has a published
  // deprecation date as of that check (see DD register for the standing
  // re-check rule). KNOWN GAP: both use Gemini 3.x's `thinking_level`
  // (low/medium/high) parameter, not the `thinking_budget` numeric token
  // count `adapter_gemini.ts` currently sends (`thinkingConfig.thinkingBudget`,
  // line ~20) — the adapter needs a `thinking_level` code path before either
  // model can actually serve traffic, not just be selected here.
  {
    id: 'gemini-3.1-pro-preview',
    provider: 'google',
    tier: 'premium',
    label: 'Gemini 3.1 Pro (preview)',
    hint: 'PREVIEW — no GA successor named. 1M ctx, $2/$12 (<=200K in), $4/$18 (>200K in). Not wired to any CallType; see STAGED_TIER_UPGRADE_ROUTING.',
    speedTier: 'deep',
    maxInputTokens: 1_048_576,
    maxOutputTokens: 65_536,
    capabilities: ['tool-use'],
    role: 'synthesis',
    costPer1MInput: 2.00,        // $2.00 up to 200K input; $4.00 above 200K
    costPer1MOutput: 12.00,      // $12.00 up to 200K input; $18.00 above 200K
    reasoningMode: 'native',
    quirks: {
      reasoning_via: 'native',
      streaming_required: false,
      tool_use_format: 'gemini',
      structured_output_format: 'gemini_response_schema',
      cache_strategy: 'context_caching',
      system_prompt_shape: 'system_message',
      // thinking_level (not thinking_budget) — adapter does not read this key
      // yet; recorded here as the intended config, not a functioning one.
      request_transforms: { safety_filter: 'block_none', thinking_level: 'high' },
    },
  },
  {
    id: 'gemini-3.7-flash',
    provider: 'google',
    tier: 'mid',
    label: 'Gemini 3.7 Flash',
    hint: 'GA (stable). 1M ctx, $0.75/$3.75 through 2026-12-31, rising to $1.50/$7.50 on 2027-01-01. Not wired to any CallType; see STAGED_TIER_UPGRADE_ROUTING.',
    speedTier: 'balanced',
    maxInputTokens: 1_000_000,
    maxOutputTokens: 65_536,
    capabilities: ['tool-use'],
    role: 'both',
    costPer1MInput: 0.75,        // rises to $1.50 on 2027-01-01 — re-check before then
    costPer1MOutput: 3.75,       // rises to $7.50 on 2027-01-01 — re-check before then
    reasoningMode: 'native',
    quirks: {
      reasoning_via: 'native',
      streaming_required: false,
      tool_use_format: 'gemini',
      structured_output_format: 'gemini_response_schema',
      cache_strategy: 'context_caching',
      system_prompt_shape: 'system_message',
      // thinking_level: 'high' per the native's own ruling item 1/2b — same
      // adapter caveat as gemini-3.1-pro-preview above.
      request_transforms: { safety_filter: 'block_none', thinking_level: 'high' },
    },
  },


  // ── DeepSeek ────────────────────────────────────────────────────────────────
  // Current:   deepseek-v4-pro (synthesis, thinking)  |  deepseek-v4-flash (worker)
  // Deprecated: deepseek-chat (→ V4 Flash alias, retires 2026-07-24)
  //             deepseek-reasoner (→ V4 Pro thinking alias, retires 2026-07-24)
  //
  // V4 Pro: 1.6T/49B active MoE, dual mode (thinking / non-thinking), 1M context.
  // V4 Flash: 1M context, non-thinking only, $0.14/$0.28 — used as planner+worker.
  // R1-style <think> middleware is NO LONGER NEEDED for V4 Pro — the model exposes
  // thinking natively via the 'thinking' parameter on the API call.
  {
    // DeepSeek Stack synthesis model. 1.6T/49B, 1M context, dual mode.
    // Use thinking=true for deep synthesis; thinking=false for planner calls
    // to get fast structured JSON without CoT overhead.
    id: 'deepseek-v4-pro',
    provider: 'deepseek',
    tier: 'premium',
    label: 'DeepSeek V4 Pro',
    hint: 'DeepSeek Stack synthesis — 1.6T params, 1M context, thinking mode',
    speedTier: 'deep',
    maxInputTokens: 1_000_000,
    maxOutputTokens: 32_768,
    capabilities: ['tool-use'],
    role: 'synthesis',
    costPer1MInput: 1.74,   // post-promo (promo at $0.44 until 2026-05-31)
    costPer1MOutput: 3.48,
    reasoningMode: 'none',  // reasoning via native <think>…</think> blocks (extractReasoningTrace); marker GATE not needed
    quirks: {
      reasoning_via: 'none',
      streaming_required: false,
      tool_use_format: 'openai',
      structured_output_format: 'json_object',
      cache_strategy: 'none',
      system_prompt_shape: 'system_message',
      request_transforms: { thinking_mode: 'toggle' },
    },
  },
  {
    // DeepSeek Stack worker + planner + context_assembly model.
    // Non-thinking only; 1M context at $0.14/$0.28 — cheapest 1M-ctx model available.
    id: 'deepseek-v4-flash',
    provider: 'deepseek',
    tier: 'mid',
    label: 'DeepSeek V4 Flash [internal label only]',
    hint: 'DeepSeek V4 Flash — canonical model ID for standard (CoT-off) calls (confirmed valid 2026-06-28). Replaces deprecated deepseek-chat alias (retires 2026-07-24). Supports tool_choice, JSON, 1M context.',
    speedTier: 'fast',
    maxInputTokens: 1_000_000,
    maxOutputTokens: 8_192,
    capabilities: ['tool-use'],
    role: 'both',
    costPer1MInput: 0.14,
    costPer1MOutput: 0.28,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: false,
      tool_use_format: 'openai',
      structured_output_format: 'json_object',
      cache_strategy: 'none',
      system_prompt_shape: 'system_message',
    },
  },
  // ── DeepSeek legacy aliases (DEPRECATED — retire 2026-07-24) ─────────────
  // deepseek-chat now routes to deepseek-v4-flash (non-thinking) on DeepSeek's API.
  // deepseek-reasoner now routes to deepseek-v4-pro (thinking) on DeepSeek's API.
  // Kept here for backward compatibility with existing conversations that
  // persisted these model IDs in localStorage. Remove after 2026-07-24.
  {
    id: 'deepseek-chat',
    provider: 'deepseek',
    tier: 'mid',
    label: 'DeepSeek Chat (V4 Flash)',
    hint: 'DeepSeek planner + worker — non-thinking, supports tool_choice. API alias for V4 Flash non-thinking.',
    speedTier: 'fast',
    maxOutputTokens: 8_192,
    capabilities: ['tool-use'],
    role: 'both',
    costPer1MInput: 0.14,   // now routes to V4 Flash pricing
    costPer1MOutput: 0.28,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: false,
      tool_use_format: 'openai',
      structured_output_format: 'json_object',
      cache_strategy: 'none',
      system_prompt_shape: 'system_message',
    },
  },
  {
    id: 'deepseek-reasoner',
    provider: 'deepseek',
    tier: 'premium',
    label: 'DeepSeek R1 (deprecated)',
    hint: '⚠ Deprecated alias → V4 Pro thinking. Will stop working 2026-07-24.',
    speedTier: 'deep',
    maxOutputTokens: 8_192,
    capabilities: [],
    role: 'synthesis',
    costPer1MInput: 1.74,   // now routes to V4 Pro pricing
    costPer1MOutput: 3.48,
    reasoningMode: 'none',  // deprecated alias for V4 Pro; reasoning via native <think> blocks, not markers
    quirks: {
      reasoning_via: 'none',
      streaming_required: false,
      tool_use_format: 'none',  // rejects tool_choice — confirmed behavior
      structured_output_format: 'none',
      cache_strategy: 'none',
      system_prompt_shape: 'system_message',
    },
  },

  // ── OpenAI — GPT ────────────────────────────────────────────────────────────
  // GPT Stack: gpt-4.1 (synthesis)  |  gpt-4.1-mini (planner)  |  gpt-4.1-nano (worker)
  // All three GPT-4.1 family models support 1M context window.
  //
  // Legacy: gpt-4o, gpt-4o-mini retained for backward compat (128K context, not
  // suitable for Whole-Chart-Read synthesis). Not part of the GPT stack routing.
  //
  // Prompt-caching on OpenAI is automatic (no explicit headers); cache reads
  // billed at 25% of standard input price.
  {
    // GPT Stack synthesis model. 1M context, best instruction following in the family.
    id: 'gpt-4.1',
    provider: 'openai',
    tier: 'premium',
    label: 'GPT-4.1',
    hint: 'GPT Stack synthesis — 1M context, best instruction following',
    speedTier: 'deep',
    maxInputTokens: 1_000_000,
    maxOutputTokens: 16_384,
    capabilities: ['tool-use'],
    role: 'synthesis',
    costPer1MInput: 2.00,
    costPer1MOutput: 8.00,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: false,
      tool_use_format: 'openai',
      structured_output_format: 'json_schema',
      cache_strategy: 'automatic',
      system_prompt_shape: 'system_message',
    },
  },
  {
    // GPT Stack planner_deep + planner_fast + context_assembly model.
    // 1M context at $0.40/$1.60 — strong reasoning at mid cost.
    id: 'gpt-4.1-mini',
    provider: 'openai',
    tier: 'mid',
    label: 'GPT-4.1 mini',
    hint: 'GPT Stack planner + context assembly — 1M context, $0.40 input',
    speedTier: 'balanced',
    maxInputTokens: 1_000_000,
    maxOutputTokens: 16_384,
    capabilities: ['tool-use'],
    role: 'both',
    costPer1MInput: 0.40,
    costPer1MOutput: 1.60,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: false,
      tool_use_format: 'openai',
      structured_output_format: 'json_schema',
      cache_strategy: 'automatic',
      system_prompt_shape: 'system_message',
    },
  },
  {
    // GPT Stack worker model. 1M context at $0.05/$0.20 — cheapest OpenAI model.
    id: 'gpt-4.1-nano',
    provider: 'openai',
    tier: 'worker',
    label: 'GPT-4.1 nano',
    hint: 'GPT Stack worker — 1M context, $0.05 input (title gen + summarization)',
    speedTier: 'fast',
    maxInputTokens: 1_000_000,
    maxOutputTokens: 16_384,
    capabilities: ['tool-use'],
    role: 'both',
    costPer1MInput: 0.05,
    costPer1MOutput: 0.20,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: false,
      tool_use_format: 'openai',
      structured_output_format: 'json_schema',
      cache_strategy: 'automatic',
      system_prompt_shape: 'system_message',
    },
  },
  // ── OpenAI legacy models (pre-GPT-4.1 era, 128K context) ───────────────────
  // Not part of the GPT stack routing; retained for backward compat with
  // existing conversations that persisted these model IDs in localStorage.
  {
    id: 'gpt-4o-mini',
    provider: 'openai',
    tier: 'worker',
    label: 'GPT-4o mini (legacy)',
    hint: 'Legacy OpenAI worker — 128K context. Prefer gpt-4.1-nano.',
    speedTier: 'fast',
    maxOutputTokens: 16_384,
    capabilities: ['tool-use'],
    role: 'both',
    costPer1MInput: 0.15,
    costPer1MOutput: 0.60,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: false,
      tool_use_format: 'openai',
      structured_output_format: 'json_schema',
      cache_strategy: 'automatic',
      system_prompt_shape: 'system_message',
    },
  },
  {
    id: 'gpt-4o',
    provider: 'openai',
    tier: 'mid',
    label: 'GPT-4o (legacy)',
    hint: 'Legacy OpenAI model — 128K context. Prefer gpt-4.1.',
    speedTier: 'balanced',
    maxOutputTokens: 16_384,
    capabilities: ['tool-use'],
    role: 'synthesis',
    costPer1MInput: 2.50,
    costPer1MOutput: 10.00,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: false,
      tool_use_format: 'openai',
      structured_output_format: 'json_schema',
      cache_strategy: 'automatic',
      system_prompt_shape: 'system_message',
    },
  },

  // ── NVIDIA NIM — full model stack ────────────────────────────────────────────
  // All models served via NVIDIA's free endpoint (https://integrate.api.nvidia.com/v1).
  // Cost fields reflect the free tier ($0.00) — update if billing is activated.
  //
  // ── Comprehensive scan 2026-05-03 (nim_synthesis_candidates.mjs) ────────────
  // Active (✅):
  //   mistralai/mistral-large-3-675b-instruct-2512   ✅  554ms  675B — ctx TBD (likely 128K)
  //   openai/gpt-oss-120b                            ✅  425ms  120B — ctx TBD; replied "?"
  //   openai/gpt-oss-20b                             ✅  364ms   20B — ctx TBD; replied "?"
  //   nvidia/nemotron-3-super-120b-a12b              ✅ 4662ms  120B — 1M ctx CONFIRMED ✓ synthesis primary
  //   nvidia/llama-3.3-nemotron-super-49b-v1         ✅ 6776ms   49B — ctx ~128K (Llama 3.3 base)
  //
  // Timing out at 30s (do not route synthesis traffic here):
  //   deepseek-ai/deepseek-v4-flash    ⏱ — was ✅ 13.6s on 2026-05-02; NIM free tier pulled?
  //   deepseek-ai/deepseek-v4-pro      ⏱ — was ⏱ on 2026-05-02 as well (never served)
  //   deepseek-ai/deepseek-v3.2        ⏱ — new in catalog, too slow for free tier
  //   deepseek-ai/deepseek-v3.1-terminus ⏱
  //   moonshotai/kimi-k2.6             ⏱ — newer variant of kimi-k2-instruct, not serving
  //   moonshotai/kimi-k2-thinking      ⏱
  //   qwen/qwen3.5-397b-a17b           ⏱
  //   meta/llama-3.1-405b-instruct     ⏱
  //   meta/llama-3.1-8b-instruct       ⏱ — was ✅ 2026-05-02; now removed/degraded
  //
  // Dead (HTTP 404/410):
  //   nvidia/llama-3.1-nemotron-ultra-253b-v1  ❌ 404 — not on free tier
  //   qwen/qwen3-235b-a22b                     ⚠️ 410 EOL
  //
  // 1M context verdict (2026-05-03):
  //   ONLY nvidia/nemotron-3-super-120b-a12b has CONFIRMED 1M context + is actively serving.
  //   All DeepSeek models (the natural 1M candidates) are currently unavailable on NIM free tier.
  //   Mistral Large 3 675B is active and promising but context window UNVERIFIED
  //   (run nim_1m_context_scan.mjs to confirm — if ≥1M it becomes the preferred synthesis model).
  //   moonshotai/kimi-k2-instruct: active but 256K only → does NOT meet Whole-Chart-Read minimum.
  //
  // Synthesis routing update 2026-05-03:
  //   nemotron-3-super-120b-a12b promoted to synthesis primary (only confirmed 1M ctx).
  //   kimi-k2-instruct retained in registry (256K) but removed from synthesis routing.
  //
  // Planner routing (via getNvidiaPlanner / getNvidiaContextAssembler):
  //   multi_domain | remedial | holistic → nemotron-super-49b-v1   (deep CoT, 6.8s cold-start)
  //   planetary | dasha | transit        → nemotron-3-super-120b   (fast JSON, 356ms, 1M ctx)
  //   context_assembly                   → nemotron-3-super-120b   (1M ctx, RULER-1M 91.64)
  //   summarization / fallback / worker  → nemotron-3-super-120b

  // — User-selectable synthesis models —
  {
    // TIMEOUT 2026-05-02 + 2026-05-03 — both smoke tests: no HTTP headers in 15s.
    // Not available on NIM free tier. deepseek-ai/deepseek-v4-flash also times out.
    // Retained for when/if NVIDIA activates DeepSeek V4 on the free endpoint.
    // Do not route synthesis traffic here until re-tested and confirmed ✅.
    id: 'deepseek-ai/deepseek-v4-pro',
    provider: 'nvidia',
    tier: 'premium',
    label: 'DeepSeek V4 Pro (NIM) [unavailable]',
    hint: 'UNAVAILABLE on NIM free tier — timeout on smoke tests 2026-05-02 + 2026-05-03',
    speedTier: 'deep',
    maxInputTokens: 1_000_000,  // Whole-Chart-Read: full L2.5 corpus in one pass
    maxOutputTokens: 32_768,
    capabilities: ['tool-use'],
    role: 'synthesis',
    costPer1MInput: 0.00,
    costPer1MOutput: 0.00,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: true,
      tool_use_format: 'openai',
      structured_output_format: 'json_object',
      cache_strategy: 'none',
      system_prompt_shape: 'system_message',
      request_transforms: { thinking_mode: 'toggle' },
    },
  },
  {
    // DEPRECATED 2026-05-02 — smoke test: ❌ HTTP 404 (not found on NIM free tier).
    // Model may require a paid NIM subscription. Removed from STACK_ROUTING.
    id: 'nvidia/llama-3.1-nemotron-ultra-253b-v1',
    provider: 'nvidia',
    tier: 'premium',
    label: 'Nemotron Ultra 253B [unavailable]',
    hint: 'UNAVAILABLE on NIM free tier — HTTP 404 on smoke test 2026-05-02',
    speedTier: 'deep',
    maxOutputTokens: 32_768,
    capabilities: ['tool-use'],
    role: 'both',
    costPer1MInput: 0.00,
    costPer1MOutput: 0.00,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: true,
      tool_use_format: 'openai',
      structured_output_format: 'json_object',
      cache_strategy: 'none',
      system_prompt_shape: 'system_message',
    },
  },
  {
    // Dual-use: user-selectable synthesis AND parallel orchestration (Wave 2).
    // 1T total / 32B active MoE, 256K context. Agent swarm: 100 parallel agents,
    // 1,500 simultaneous tool calls — maps directly to UQE parallel tool fetch.
    id: 'moonshotai/kimi-k2-instruct',
    provider: 'nvidia',
    tier: 'mid',
    label: 'Kimi K2 Instruct',
    hint: 'Moonshot AI — 1T MoE, 256K context, agent swarm orchestration',
    speedTier: 'balanced',
    maxOutputTokens: 32_768,
    capabilities: ['tool-use'],
    role: 'both',
    costPer1MInput: 0.00,
    costPer1MOutput: 0.00,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: true,
      tool_use_format: 'openai',
      structured_output_format: 'json_object',
      cache_strategy: 'none',
      system_prompt_shape: 'system_message',
    },
  },

  {
    // NIM SYNTHESIS FALLBACK (2026-05-03) — nim_1m_context_scan.mjs: ✅ 374ms, 1M ctx confirmed.
    // 30B reasoning model (Nemotron nano omni variant). Ranked #2 of 2 confirmed-1M NIM models.
    // Serves as synthesis fallback behind nemotron-3-super-120b-a12b (#1, 120B).
    // Both are free on NIM; both have confirmed 1M context for Whole-Chart-Read.
    id: 'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning',
    provider: 'nvidia',
    tier: 'worker',
    label: 'Nemotron 3 Nano 30B Reasoning',
    hint: 'NIM synthesis fallback — 1M context confirmed, 374ms. Reasoning model.',
    speedTier: 'fast',
    maxInputTokens: 1_000_000,  // confirmed by nim_1m_context_scan.mjs 2026-05-03
    maxOutputTokens: 32_768,
    capabilities: [],
    role: 'both',
    costPer1MInput: 0.00,
    costPer1MOutput: 0.00,
    reasoningMode: 'none',  // NIM reasoning format unverified; no marker gate until tested
    quirks: {
      reasoning_via: 'none',
      streaming_required: true,
      tool_use_format: 'openai',
      structured_output_format: 'json_object',
      cache_strategy: 'none',
      system_prompt_shape: 'system_message',
    },
  },

  {
    // NEW 2026-05-03 — nim_synthesis_candidates.mjs: ✅ HTTP 200 in 554ms.
    // 675B total params (likely MoE). Context window UNVERIFIED — run nim_1m_context_scan.mjs.
    // If context_length ≥ 1M this becomes the preferred NIM synthesis model (largest active params).
    // Excluded from Whole-Chart-Read synthesis routing until context is confirmed ≥ 1M.
    // maxInputTokens omitted until confirmed; supportsWholeChartRead() will return false.
    id: 'mistralai/mistral-large-3-675b-instruct-2512',
    provider: 'nvidia',
    tier: 'premium',
    label: 'Mistral Large 3 675B (NIM)',
    hint: 'NIM: 675B confirmed active 554ms. ⚠ Context window unverified — not yet routed for synthesis.',
    speedTier: 'deep',
    // maxInputTokens: 1_000_000,  // uncomment + confirm via nim_1m_context_scan.mjs
    maxOutputTokens: 32_768,
    capabilities: [],  // tool-use capability unverified
    role: 'synthesis',  // pending context confirmation before routing
    costPer1MInput: 0.00,
    costPer1MOutput: 0.00,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: true,
      tool_use_format: 'none',  // tool-use capability unverified per registry comment
      structured_output_format: 'none',
      cache_strategy: 'none',
      system_prompt_shape: 'system_message',
    },
  },

  // — Internal planner-only models —
  {
    // DEEP PLANNER MODEL — confirmed live on NIM free tier (catalog check 2026-05-02).
    // Successor to nvidia/llama-3.1-nemotron-ultra-253b-v1 (HTTP 404 on free tier).
    // 49B params, Llama-3.3 base, NVIDIA RLHF-tuned for reasoning and instruction following.
    // Used for multi_domain / remedial / holistic query planning where CoT depth matters.
    id: 'nvidia/llama-3.3-nemotron-super-49b-v1',
    provider: 'nvidia',
    tier: 'mid',
    label: 'Nemotron Super 49B',
    hint: 'Deep planner — 49B successor to Nemotron Ultra, confirmed live on NIM free tier (internal only)',
    speedTier: 'balanced',
    maxInputTokens: 131_072,
    maxOutputTokens: 32_768,
    capabilities: ['tool-use'],
    role: 'planner',
    costPer1MInput: 0.00,
    costPer1MOutput: 0.00,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: true,
      tool_use_format: 'openai',
      structured_output_format: 'json_object',
      cache_strategy: 'none',
      system_prompt_shape: 'system_message',
    },
  },
  {
    // NIM SYNTHESIS PRIMARY (2026-05-03) + CONTEXT ASSEMBLY MODEL.
    // 120B total / 12B active hybrid Mamba-Transformer.
    // 1M-token context window — PRACTICAL (linear-time Mamba layers, not quadratic
    // attention). RULER-1M score: 91.64 — highest long-context recall on NIM.
    // Promoted to synthesis primary 2026-05-03: only confirmed 1M ctx model actively
    // serving on NIM free tier after DeepSeek and Qwen models went offline.
    // Also handles context_assembly, planner_fast, and worker pipeline steps.
    id: 'nvidia/nemotron-3-super-120b-a12b',
    provider: 'nvidia',
    tier: 'mid',
    label: 'Nemotron 3 Super 120B',
    hint: 'NIM synthesis primary — 1M context confirmed, RULER-1M 91.64. Also context assembly + planner.',
    speedTier: 'balanced',
    maxInputTokens: 1_000_000,  // linear-time Mamba — 1M is practical, not theoretical
    maxOutputTokens: 65_536,
    capabilities: [],
    role: 'both',  // promoted from 'planner' — synthesis primary as of 2026-05-03
    costPer1MInput: 0.00,
    costPer1MOutput: 0.00,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: true,
      tool_use_format: 'openai',
      structured_output_format: 'json_object',
      cache_strategy: 'none',
      system_prompt_shape: 'system_message',
    },
  },
  {
    // DEPRECATED 2026-05-02 — smoke test: ⚠️ HTTP 410 Gone.
    // NIM API response: "The model 'qwen/qwen3-235b-a22b' has reached its end of life."
    // Removed from STACK_ROUTING. Retained as historical record only.
    id: 'qwen/qwen3-235b-a22b',
    provider: 'nvidia',
    tier: 'mid',
    label: 'Qwen3 235B-A22B [EOL]',
    hint: 'END OF LIFE on NIM — HTTP 410 on smoke test 2026-05-02',
    speedTier: 'balanced',
    maxOutputTokens: 32_768,
    capabilities: ['tool-use'],
    role: 'planner',
    costPer1MInput: 0.00,
    costPer1MOutput: 0.00,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: true,
      tool_use_format: 'openai',
      structured_output_format: 'json_object',
      cache_strategy: 'none',
      system_prompt_shape: 'system_message',
    },
  },
  {
    // DEGRADED 2026-05-03 — smoke test: ⏱ TIMEOUT (was ✅ HTTP 200 on 2026-05-02).
    // Likely removed or overloaded on NIM free tier. NIM worker role has been
    // transferred to nvidia/nemotron-3-super-120b-a12b (confirmed live, 356ms).
    // Retained as historical record; STACK_ROUTING no longer routes here.
    id: 'meta/llama-3.1-8b-instruct',
    provider: 'nvidia',
    tier: 'worker',
    label: 'Llama 3.1 8B [degraded]',
    hint: 'TIMEOUT on NIM free tier 2026-05-03 — do not use. Was worker; replaced by nemotron-3-super-120b.',
    speedTier: 'fast',
    maxOutputTokens: 8_192,
    capabilities: [],
    role: 'planner',
    costPer1MInput: 0.00,
    costPer1MOutput: 0.00,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: true,
      tool_use_format: 'none',
      structured_output_format: 'none',
      cache_strategy: 'none',
      system_prompt_shape: 'system_message',
    },
  },
]

// Default stack and synthesis model. Switched from NIM → Gemini on 2026-05-10:
// NIM Nemotron endpoint is degraded (axum Bearer auth 500s); Anthropic credits
// exhausted. Gemini 2.5 Pro is the active default going forward.
// A user's previously-persisted stack choice in localStorage overrides this.
// DEFAULT_MODEL_ID is derived from the default stack — kept for backward compat.
export const DEFAULT_STACK_ID = 'gemini' as const
export const DEFAULT_MODEL_ID = 'gemini-2.5-pro' // Gemini stack synthesis primary

/**
 * Title generator always uses the worker of the same family as the user's
 * chosen synthesis model. Pinned to haiku-4-5 as the ultimate fallback.
 * Use getWorkerForModel(synthesisModelId) at the call site — this constant
 * is the fallback only.
 */
export const TITLE_MODEL_ID = 'claude-haiku-4-5'

const MODEL_INDEX: Record<string, ModelMeta> = Object.fromEntries(
  MODELS.map(m => [m.id, m])
)

export function getModelMeta(id: string): ModelMeta | undefined {
  return MODEL_INDEX[id]
}

export function isValidModelId(id: string): boolean {
  return id in MODEL_INDEX
}

export function supports(id: string, cap: Capability): boolean {
  return MODEL_INDEX[id]?.capabilities.includes(cap) ?? false
}

/** Group models by provider for UI rendering (preserves registry order). */
export function modelsByProvider(): Array<{ provider: Provider; models: ModelMeta[] }> {
  const groups = new Map<Provider, ModelMeta[]>()
  for (const m of MODELS) {
    if (!groups.has(m.provider)) groups.set(m.provider, [])
    groups.get(m.provider)!.push(m)
  }
  return Array.from(groups.entries()).map(([provider, models]) => ({ provider, models }))
}

/**
 * @deprecated Since stack-based routing replaced individual model selection.
 * Use stackPicker() instead. Retained for any legacy UI components that still
 * render a per-model dropdown; remove once all UI is migrated to stackPicker().
 */
export function synthesisPicker(): Array<{ provider: Provider; models: ModelMeta[] }> {
  const TIER_ORDER: Record<ModelTier, number> = { premium: 0, mid: 1, worker: 2 }
  return modelsByProvider().map(({ provider, models }) => ({
    provider,
    models: models
      .filter(m => m.role === 'synthesis' || m.role === 'both')
      .sort((a, b) => TIER_ORDER[a.tier] - TIER_ORDER[b.tier]),
  }))
}

export const PROVIDER_LABEL: Record<Provider, string> = {
  anthropic: 'Anthropic',
  google: 'Google',
  deepseek: 'DeepSeek',
  openai: 'OpenAI',
  nvidia: 'NVIDIA NIM',
}

// ─────────────────────────────────────────────────────────────────────────────
// BHISMA-B1 §3.1 — Family-aware worker assignment
// ─────────────────────────────────────────────────────────────────────────────

/**
 * The worker model for each provider family, used for planning, title
 * generation, and any internal LLM call that does not require synthesis depth.
 *
 * Rule: FAMILY_WORKER[provider] must always point to the model in that family
 * with tier='worker'. When updating the registry, keep this map in sync.
 *
 * Note on DeepSeek: V3 (deepseek-chat) is tier='mid' in the registry because
 * there is no cheaper dedicated sub-V3 model in the DeepSeek public API.
 * It still serves as the DeepSeek worker — the tier field on the registry
 * entry reflects user-facing positioning; this map governs internal routing.
 */
export const FAMILY_WORKER: Record<Provider, string> = {
  anthropic: 'claude-haiku-4-5',                // tier=worker  $1.00/$5.00
  google:    'gemini-2.5-flash-lite',            // tier=worker  $0.015/$0.06  (was gemini-2.0-flash-lite, dropped from OpenAI-compat 2026-05-03)
  openai:    'gpt-4.1-nano',                     // tier=worker  $0.05/$0.20  (was gpt-4o-mini)
  deepseek:  'deepseek-v4-flash',                  // non-thinking, supports tool_choice; canonical API ID (retires deepseek-chat alias 2026-07-24)
  nvidia:    'nvidia/nemotron-3-super-120b-a12b', // tier=worker  $0.00 (llama-3.1-8b timed out 2026-05-03; nemotron-3 confirmed ✅ 356ms)
}

const ULTIMATE_WORKER_FALLBACK = 'claude-haiku-4-5'

/**
 * Resolve the worker model that should pair with a given synthesis model.
 * Falls back to claude-haiku-4-5 if the synthesis model is unknown — the
 * caller is expected to validate the synthesis ID first via isValidModelId.
 */
export function getWorkerForModel(synthesisModelId: string): string {
  const meta = MODEL_INDEX[synthesisModelId]
  if (!meta) return ULTIMATE_WORKER_FALLBACK
  return FAMILY_WORKER[meta.provider] ?? ULTIMATE_WORKER_FALLBACK
}

// ─────────────────────────────────────────────────────────────────────────────
// NVIDIA NIM — query-class-based planner routing
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Query classes that benefit from Nemotron Ultra's deep chain-of-thought.
 * Multi-domain, remedial, and holistic queries involve cross-layer reasoning
 * and mathematical signal weighting — the 253B CoT model excels here.
 */
export const NVIDIA_DEEP_PLANNER_QUERY_CLASSES = [
  'multi_domain',
  'remedial',
  'holistic',
] as const

/**
 * Query classes that benefit from Qwen3-235B's fast MoE inference.
 * Single-domain planetary/dasha/transit queries need tight structured JSON
 * output; Qwen3's 22B active params deliver high-quality JSON at low latency.
 */
export const NVIDIA_FAST_PLANNER_QUERY_CLASSES = [
  'planetary',
  'dasha',
  'transit',
] as const

/**
 * Return the NVIDIA NIM model ID most appropriate for the given query class.
 *
 * Called by the UQE planner when NVIDIA_PLANNER_ENABLED is true. The caller
 * is responsible for checking the feature flag — this function always returns
 * a valid model ID regardless.
 *
 * Routing table (updated 2026-05-02 — catalog check confirmed dead models):
 *   multi_domain | remedial | holistic  → llama-3.3-nemotron-super-49b-v1  (successor; ✅ HTTP 200 744ms)
 *                                          replaces: nemotron-ultra-253b-v1 (❌ HTTP 404 on free tier)
 *   planetary | dasha | transit         → nemotron-3-super-120b-a12b       (✅ HTTP 200 598ms)
 *                                          replaces: qwen3-235b-a22b        (⚠️ HTTP 410 EOL)
 *   everything else                     → nemotron-3-super-120b-a12b       (worker; llama-3.1-8b timed out 2026-05-03)
 */
export function getNvidiaPlanner(queryClass: string): string {
  if ((NVIDIA_DEEP_PLANNER_QUERY_CLASSES as readonly string[]).includes(queryClass)) {
    // Nemotron Ultra 253B is HTTP 404 on NIM free tier (catalog check 2026-05-02).
    // Replaced with confirmed-live successor: llama-3.3-nemotron-super-49b-v1 (✅ 744ms).
    return 'nvidia/llama-3.3-nemotron-super-49b-v1'
  }
  if ((NVIDIA_FAST_PLANNER_QUERY_CLASSES as readonly string[]).includes(queryClass)) {
    // Qwen3-235B-A22B reached end of life on NIM (HTTP 410, catalog check 2026-05-02).
    // Replaced with nemotron-3-super-120b-a12b (✅ 598ms, 1M ctx, RULER-1M 91.64).
    return 'nvidia/nemotron-3-super-120b-a12b'
  }
  // llama-3.1-8b timed out on 2026-05-03 smoke test; nemotron-3-super is confirmed live
  return 'nvidia/nemotron-3-super-120b-a12b'
}

/**
 * Return the NVIDIA NIM model to use for the context_assembly pipeline step.
 *
 * Nemotron 3 Super 120B is selected because:
 * - 1M-token context window (linear-time Mamba layers make this practical)
 * - RULER-1M score of 91.64 — highest long-context recall on NIM
 * - Hybrid Mamba-Transformer handles the full L1+L2.5 corpus in a single pass
 *   without chunking, preserving cross-document signal relationships
 *
 * Called by the context_assembly step when NVIDIA_PLANNER_ENABLED is true.
 */
export function getNvidiaContextAssembler(): string {
  return 'nvidia/nemotron-3-super-120b-a12b'
}

/**
 * Return the preferred NVIDIA NIM synthesis model.
 *
 * Kimi K2 Instruct is selected because (as of 2026-05-02 catalog check):
 * - Only confirmed-live 1M+ context synthesis model on NIM free tier
 * - 1T total / 32B active MoE — largest active-param synthesis model available
 * - 256K context — sufficient for full MARSYS corpus (~340K tokens with compression)
 * - Agent-swarm capable: 100 parallel agents, 1,500 simultaneous tool calls
 *
 * Previous choice (deepseek-ai/deepseek-v4-pro) timed out on NIM free tier;
 * all DeepSeek and Qwen alternatives confirmed dead (EOL or 404) in catalog check.
 * This function returns kimi-k2-instruct until a 1M-context NIM model becomes
 * available on the free tier again.
 */
export function getNvidiaSynthesisModel(): string {
  // Updated 2026-05-03: kimi-k2-instruct removed — 256K context fails 340K Whole-Chart-Read minimum.
  // All DeepSeek models timing out on NIM free tier (v4-flash was ✅ on 2026-05-02, now ⏱).
  // nemotron-3-super-120b-a12b is the ONLY confirmed 1M ctx model actively serving on free tier.
  // When DeepSeek V4 Flash comes back online on NIM, reassign to 'deepseek-ai/deepseek-v4-flash'.
  // When mistral-large-3-675b context is confirmed ≥ 1M, reassign to that (675B > 120B).
  return 'nvidia/nemotron-3-super-120b-a12b'
}

// ─────────────────────────────────────────────────────────────────────────────
// Stack-based routing — replaces the individual model picker
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Every LLM call in the MARSYS pipeline belongs to exactly one CallType.
 *
 *  synthesis         — final answer generation; must support Whole-Chart-Read
 *                      (~340K token corpus); deepest reasoning required.
 *  planner_deep      — per-tool query planning for multi-domain / remedial /
 *                      holistic queries; mathematical precision matters.
 *  planner_fast      — per-tool query planning for single-domain planetary /
 *                      dasha / transit queries; structured JSON, low latency.
 *  context_assembly  — intermediate step that receives all tool outputs and
 *                      compresses/reorders them before synthesis; 1M context
 *                      required to hold the full retrieval result set.
 *  worker            — title generation, history summarization, any call where
 *                      minimal latency and minimal cost dominate.
 */
export type CallType =
  | 'synthesis'
  | 'planner_deep'
  | 'planner_fast'
  | 'context_assembly'
  | 'worker'
  // interpretation_sets — 3-way distinct candidate reading + falsifier
  // synthesis per significant judgment (pariprashna/interpretation/worker.ts,
  // DD-17/DD-20). Folded into the shared registry 2026-08-21
  // (PARIPRASHNA-P3-PREFLIGHT-2026-08-21, model-tier ruling item 2a) —
  // previously a local bypass constant on that one call site only; see
  // DD-17's entry in PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md for why
  // the bypass existed and why it was closed.
  | 'interpretation_sets'
  // AIOps CP.1 — Quality & Verification call types (cross-stack; pick from full catalog)
  | 'eval_judge'       // grades outputs in answer:eval / planner:eval scripts
  | 'eval_generator'   // generates eval prompts dynamically
  | 'smoke_synth'      // stack smoke-test synthesis probe
  | 'checkpoint_4_5'   // Phase 6 planner mid-flight verification
  | 'checkpoint_5_5'   // Phase 6 context-assembly mid-flight verification
  | 'checkpoint_8_5'   // Phase 6 synthesis post-hoc verification

// ── ModelStack ────────────────────────────────────────────────────────────────

/**
 * A stack is a named, pre-configured bundle of models covering every pipeline
 * call type. The user selects a stack (not individual models) from the UI.
 * Switching stacks changes all call types simultaneously.
 *
 * Default stack: 'nim' — all calls free via NVIDIA NIM.
 */
export type ModelStack = 'nim' | 'anthropic' | 'gemini' | 'gpt' | 'deepseek' | 'marsys'

export const STACK_LABEL: Record<ModelStack, string> = {
  nim:       'NIM Stack',
  anthropic: 'Anthropic Stack',
  gemini:    'Gemini Stack',
  gpt:       'GPT Stack',
  deepseek:  'DeepSeek Stack',
  marsys:    'MARSYS Stack',
}

/** The provider whose models serve as primaries in each stack.
 *  MARSYS is excluded — it is cross-provider; its routing lives in llm_stack_routing_override. */
export const STACK_PRIMARY_PROVIDER: Record<Exclude<ModelStack, 'marsys'>, Provider> = {
  nim:       'nvidia',
  anthropic: 'anthropic',
  gemini:    'google',
  gpt:       'openai',
  deepseek:  'deepseek',
}

/**
 * Per-stack, per-call-type routing with primary and fallback model IDs.
 *
 * Fallback policy: the call site tries primary first; on rate-limit (429),
 * timeout, or provider error it retries immediately with fallback.
 * Both models in every pair satisfy the same functional floor:
 * — synthesis entries: both have ≥1M context (Whole-Chart-Read capable)
 * — context_assembly entries: both have ≥1M context
 * — planner / worker entries: both support tool-use where required
 *
 * ─── Stack synthesis context windows ────────────────────────────────────────
 *   NIM       nvidia/nemotron-3-super-120b-a12b  1M   free  (DeepSeek V4 unavail 2026-05-03)
 *   Anthropic claude-opus-4-7                    1M   $5/$25 per 1M
 *   Gemini    gemini-2.5-pro                     2M   $1.25–$2.50/$10–$15 per 1M
 *   GPT       gpt-4.1                            1M   $2/$8 per 1M
 *   DeepSeek  deepseek-v4-pro                    1M   $1.74/$3.48 per 1M (post-promo)
 */
export const STACK_ROUTING: Record<ModelStack, Record<CallType, { primary: string; fallback: string }>> = {

  // ── NIM Stack (all free via https://integrate.api.nvidia.com/v1) ─────────
  //
  // SMOKE TEST RESULTS 2026-05-02 (nim_model_test.mjs):
  //   deepseek-ai/deepseek-v4-pro            ⏱ TIMEOUT  — no HTTP headers in 15s
  //   nvidia/llama-3.1-nemotron-ultra-253b-v1 ❌ HTTP 404 — not on NIM free tier
  //   qwen/qwen3-235b-a22b                   ⚠️ HTTP 410 — EOL
  //   moonshotai/kimi-k2-instruct            ✅ HTTP 200  — 5497ms
  //   nvidia/nemotron-3-super-120b-a12b      ✅ HTTP 200  — 598ms
  //   meta/llama-3.1-8b-instruct             ✅ HTTP 200  — 13638ms
  //
  // CATALOG CHECK RESULTS 2026-05-02 (nim_catalog_check.mjs):
  //   deepseek-ai/deepseek-r1                ⚠️ HTTP 410 — EOL
  //   deepseek-ai/deepseek-v3-0324           ❌ HTTP 404
  //   deepseek-ai/deepseek-r1-0528           ⚠️ HTTP 410 — EOL
  //   nvidia/llama-3.3-nemotron-super-49b-v1 ✅ HTTP 200  — 744ms  ← Nemotron Ultra successor
  //   nvidia/llama-3.1-nemotron-70b-instruct ❌ HTTP 404
  //   nvidia/nemotron-4-340b-instruct        ❌ HTTP 404
  //   qwen/qwq-32b                           ⚠️ HTTP 410 — EOL
  //   qwen/qwen2.5-72b-instruct              ❌ HTTP 404
  //   qwen/qwen3-30b-a3b                     ❌ HTTP 404
  //
  // Conclusion: NIM free tier has removed all DeepSeek and Qwen models.
  // Only confirmed-live NIM models: kimi-k2-instruct, nemotron-3-super-120b-a12b,
  //   llama-3.3-nemotron-super-49b-v1 (new), meta/llama-3.1-8b-instruct.
  nim: {
    synthesis: {
      // Updated 2026-05-03: nemotron-3-super-120b promoted from planner to synthesis primary.
      // Only confirmed-1M-context model actively serving on NIM free tier.
      // kimi-k2-instruct removed (256K only — fails Whole-Chart-Read 340K minimum).
      // DeepSeek V4 Flash (was ✅ 13.6s on 2026-05-02) is now timing out — NIM free tier pulled.
      primary:  'nvidia/nemotron-3-super-120b-a12b',                  // ✅ 120B, 1M ctx, 653ms
      fallback: 'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning',    // ✅  30B, 1M ctx, 374ms — both free NIM
    },
    planner_deep: {
      primary:  'nvidia/llama-3.3-nemotron-super-49b-v1',   // ✅ 49B, 6.8s cold-start, deep CoT
      fallback: 'nvidia/nemotron-3-super-120b-a12b',        // ✅ 1M ctx fallback (kimi removed: 256K)
    },
    planner_fast: {
      primary:  'nvidia/nemotron-3-super-120b-a12b',        // ✅ 356ms, fast structured output
      fallback: 'nvidia/llama-3.3-nemotron-super-49b-v1',   // ✅ 49B fallback (llama-3.1-8b timed out 2026-05-03)
    },
    context_assembly: {
      primary:  'nvidia/nemotron-3-super-120b-a12b',        // ✅ 1M ctx, RULER-1M 91.64
      fallback: 'nvidia/llama-3.3-nemotron-super-49b-v1',   // ✅ 49B fallback (kimi removed: 256K)
    },
    worker: {
      primary:  'nvidia/nemotron-3-super-120b-a12b',        // ✅ 356ms, confirmed live 2026-05-03
      fallback: 'claude-haiku-4-5',                         // prompt-caching, reliable paid fallback
    },
    interpretation_sets: {
      // Same pick as context_assembly — nearest existing role by capability
      // demand (quality-sensitive, not latency-sensitive). Never exercised on
      // this stack in production yet (worker.ts's bypass only ever resolved
      // to a gemini id); added for STACK_ROUTING completeness (2026-08-21).
      primary:  'nvidia/nemotron-3-super-120b-a12b',
      fallback: 'nvidia/llama-3.3-nemotron-super-49b-v1',
    },
    // AIOps CP.1 Quality & Verification (R13 seeds — same as synthesis/planner_deep/worker)
    eval_judge:      { primary: 'nvidia/nemotron-3-super-120b-a12b',             fallback: 'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning' },
    eval_generator:  { primary: 'nvidia/llama-3.3-nemotron-super-49b-v1',        fallback: 'nvidia/nemotron-3-super-120b-a12b' },
    smoke_synth:     { primary: 'nvidia/nemotron-3-super-120b-a12b',             fallback: 'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning' },
    checkpoint_4_5:  { primary: 'nvidia/nemotron-3-super-120b-a12b',             fallback: 'claude-haiku-4-5' },
    checkpoint_5_5:  { primary: 'nvidia/nemotron-3-super-120b-a12b',             fallback: 'claude-haiku-4-5' },
    checkpoint_8_5:  { primary: 'nvidia/nemotron-3-super-120b-a12b',             fallback: 'claude-haiku-4-5' },
  },

  // ── Anthropic Stack ───────────────────────────────────────────────────────
  // context_assembly MUST use Sonnet 4.6 or Opus 4.7 — Haiku 4.5 caps at 200K.
  anthropic: {
    synthesis: {
      primary:  'claude-opus-4-7',                          // 1M ctx, $5/$25, deepest
      fallback: 'claude-sonnet-4-6',                        // 1M ctx, $3/$15
    },
    planner_deep: {
      primary:  'claude-sonnet-4-6',                        // 1M ctx, tool-use, $3/$15
      fallback: 'claude-opus-4-7',                          // 1M ctx, overkill but reliable
    },
    planner_fast: {
      primary:  'claude-haiku-4-5',                         // 200K ctx, $1/$5, fast
      fallback: 'claude-sonnet-4-6',                        // 1M ctx fallback
    },
    context_assembly: {
      primary:  'claude-sonnet-4-6',                        // 1M ctx required
      fallback: 'claude-opus-4-7',                          // 1M ctx fallback
    },
    worker: {
      primary:  'claude-haiku-4-5',                         // $1/$5, prompt-caching
      fallback: 'claude-sonnet-4-6',                        // fallback if Haiku fails
    },
    interpretation_sets: {
      // Same pick as context_assembly — see NIM stack's comment above.
      primary:  'claude-sonnet-4-6',
      fallback: 'claude-opus-4-7',
    },
    eval_judge:      { primary: 'claude-opus-4-7',   fallback: 'claude-sonnet-4-6' },
    eval_generator:  { primary: 'claude-sonnet-4-6', fallback: 'claude-opus-4-7' },
    smoke_synth:     { primary: 'claude-opus-4-7',   fallback: 'claude-sonnet-4-6' },
    checkpoint_4_5:  { primary: 'claude-haiku-4-5',  fallback: 'claude-sonnet-4-6' },
    checkpoint_5_5:  { primary: 'claude-haiku-4-5',  fallback: 'claude-sonnet-4-6' },
    checkpoint_8_5:  { primary: 'claude-haiku-4-5',  fallback: 'claude-sonnet-4-6' },
  },

  // ── Gemini Stack ──────────────────────────────────────────────────────────
  // Gemini 2.5 Pro has the largest context of any stack: 2M tokens.
  // Context caching available — 90% discount on repeated prompts.
  gemini: {
    synthesis: {
      primary:  'gemini-2.5-pro',                           // 2M ctx, $1.25–$2.50/$10–$15
      fallback: 'gemini-2.5-flash',                         // 1M ctx, $0.075/$0.30
    },
    planner_deep: {
      primary:  'gemini-2.5-flash',                         // 1M ctx, $0.075/$0.30
      fallback: 'gemini-2.5-pro',                           // 2M ctx, higher cost
    },
    planner_fast: {
      primary:  'gemini-2.5-flash',                         // 1M ctx, fast + cheap
      fallback: 'gemini-2.5-flash-lite',                    // $0.015, ultra-cheap
    },
    context_assembly: {
      primary:  'gemini-2.5-flash',                         // 1M ctx, cost-efficient
      fallback: 'gemini-2.5-pro',                           // 2M ctx fallback
    },
    worker: {
      primary:  'gemini-2.5-flash-lite',                    // $0.015/$0.06, tool-use (replaced gemini-2.0-flash-lite, HTTP 404 2026-05-03)
      fallback: 'gemini-2.5-flash',                         // 1M ctx fallback
    },
    interpretation_sets: {
      // DD-17's ruling, unchanged by folding it into the registry
      // (PARIPRASHNA-P3-PREFLIGHT-2026-08-21 item 2a) — 'gemini-2.5-flash'
      // is the SAME model `INTERPRETATION_SETS_MODEL_ID` resolved to before
      // this entry existed; this is a plumbing change, not a model change.
      // Fallback newly defined here (the bypass constant had none) —
      // escalates to the flagship on failure, same shape as context_assembly.
      primary:  'gemini-2.5-flash',
      fallback: 'gemini-2.5-pro',
    },
    eval_judge:      { primary: 'gemini-2.5-pro',       fallback: 'gemini-2.5-flash' },
    eval_generator:  { primary: 'gemini-2.5-flash',     fallback: 'gemini-2.5-pro' },
    smoke_synth:     { primary: 'gemini-2.5-pro',       fallback: 'gemini-2.5-flash' },
    checkpoint_4_5:  { primary: 'gemini-2.5-flash-lite', fallback: 'gemini-2.5-flash' },
    checkpoint_5_5:  { primary: 'gemini-2.5-flash-lite', fallback: 'gemini-2.5-flash' },
    checkpoint_8_5:  { primary: 'gemini-2.5-flash-lite', fallback: 'gemini-2.5-flash' },
  },

  // ── GPT Stack ─────────────────────────────────────────────────────────────
  // Entire GPT-4.1 family supports 1M context. Automatic prompt caching
  // (no headers needed) at 75% discount on cached reads.
  gpt: {
    synthesis: {
      primary:  'gpt-4.1',                                  // 1M ctx, $2/$8
      fallback: 'gpt-4.1-mini',                             // 1M ctx, $0.40/$1.60
    },
    planner_deep: {
      primary:  'gpt-4.1-mini',                             // 1M ctx, $0.40/$1.60
      fallback: 'gpt-4.1',                                  // 1M ctx fallback
    },
    planner_fast: {
      primary:  'gpt-4.1-mini',                             // 1M ctx, balanced cost
      fallback: 'gpt-4.1-nano',                             // 1M ctx, $0.05/$0.20
    },
    context_assembly: {
      primary:  'gpt-4.1-mini',                             // 1M ctx, $0.40/$1.60
      fallback: 'gpt-4.1',                                  // 1M ctx fallback
    },
    worker: {
      primary:  'gpt-4.1-nano',                             // 1M ctx, $0.05/$0.20
      fallback: 'gpt-4.1-mini',                             // 1M ctx fallback
    },
    interpretation_sets: {
      // Same pick as context_assembly — see NIM stack's comment above.
      primary:  'gpt-4.1-mini',
      fallback: 'gpt-4.1',
    },
    eval_judge:      { primary: 'gpt-4.1',      fallback: 'gpt-4.1-mini' },
    eval_generator:  { primary: 'gpt-4.1-mini', fallback: 'gpt-4.1' },
    smoke_synth:     { primary: 'gpt-4.1',      fallback: 'gpt-4.1-mini' },
    checkpoint_4_5:  { primary: 'gpt-4.1-nano', fallback: 'gpt-4.1-mini' },
    checkpoint_5_5:  { primary: 'gpt-4.1-nano', fallback: 'gpt-4.1-mini' },
    checkpoint_8_5:  { primary: 'gpt-4.1-nano', fallback: 'gpt-4.1-mini' },
  },

  // ── DeepSeek Stack (via api.deepseek.com) ────────────────────────────────
  // V4 Pro: thinking mode (CoT) for synthesis + deep planning.
  // V4 Flash: non-thinking, $0.14/$0.28, used for planner_fast / worker.
  // Both models have 1M context.
  deepseek: {
    synthesis: {
      primary:  'deepseek-v4-pro',                          // 1M ctx, thinking, $1.74/$3.48
      fallback: 'deepseek-v4-flash',                        // non-thinking, canonical API ID (was: deepseek-chat alias, retired 2026-07-24)
    },
    planner_deep: {
      primary:  'deepseek-v4-pro',                          // thinking=false for JSON speed
      fallback: 'deepseek-v4-flash',                        // non-thinking, canonical API ID (was: deepseek-chat alias, retired 2026-07-24)
    },
    planner_fast: {
      primary:  'deepseek-v4-flash',                        // non-thinking, supports toolChoice; canonical API ID (was: deepseek-chat alias, retired 2026-07-24)
      fallback: 'deepseek-v4-pro',                          // fallback with thinking=false
    },
    context_assembly: {
      primary:  'deepseek-v4-flash',                        // non-thinking, canonical API ID (was: deepseek-chat alias, retired 2026-07-24)
      fallback: 'deepseek-v4-pro',                          // 1M ctx, thinking=false
    },
    worker: {
      primary:  'deepseek-v4-flash',                        // non-thinking, canonical API ID (was: deepseek-chat alias, retired 2026-07-24)
      fallback: 'deepseek-v4-pro',                          // fallback
    },
    interpretation_sets: {
      // Same pick as context_assembly — see NIM stack's comment above.
      primary:  'deepseek-v4-flash',
      fallback: 'deepseek-v4-pro',
    },
    eval_judge:      { primary: 'deepseek-v4-pro',  fallback: 'deepseek-v4-flash' },
    eval_generator:  { primary: 'deepseek-v4-pro',  fallback: 'deepseek-v4-flash' },
    smoke_synth:     { primary: 'deepseek-v4-pro',  fallback: 'deepseek-v4-flash' },
    checkpoint_4_5:  { primary: 'deepseek-v4-flash', fallback: 'deepseek-v4-pro' },
    checkpoint_5_5:  { primary: 'deepseek-v4-flash', fallback: 'deepseek-v4-pro' },
    checkpoint_8_5:  { primary: 'deepseek-v4-flash', fallback: 'deepseek-v4-pro' },
  },

  // ── MARSYS Stack (AIOps CP.1) ─────────────────────────────────────────────
  // Cross-provider custom mix. No single-provider constraint. These seeds are
  // the starting state; the super-admin overrides via the Control Panel UI.
  // The resolver falls through to llm_stack_routing_override for MARSYS;
  // STACK_ROUTING['marsys'] serves as the last-resort registry default only.
  marsys: {
    synthesis:        { primary: 'gemini-2.5-pro',       fallback: 'deepseek-v4-pro' },
    planner_deep:     { primary: 'gemini-2.5-flash',     fallback: 'deepseek-v4-pro' },
    planner_fast:     { primary: 'gemini-2.5-flash-lite', fallback: 'gemini-2.5-flash' },
    context_assembly: { primary: 'gemini-2.5-flash',     fallback: 'gemini-2.5-pro' },
    worker:           { primary: 'gemini-2.5-flash-lite', fallback: 'gpt-4.1-nano' },
    interpretation_sets: { primary: 'gemini-2.5-flash',   fallback: 'gemini-2.5-pro' },
    eval_judge:       { primary: 'gemini-2.5-pro',       fallback: 'deepseek-v4-pro' },
    eval_generator:   { primary: 'gemini-2.5-flash',     fallback: 'deepseek-v4-pro' },
    smoke_synth:      { primary: 'gemini-2.5-pro',       fallback: 'deepseek-v4-pro' },
    checkpoint_4_5:   { primary: 'gemini-2.5-flash-lite', fallback: 'gpt-4.1-nano' },
    checkpoint_5_5:   { primary: 'gemini-2.5-flash-lite', fallback: 'gpt-4.1-nano' },
    checkpoint_8_5:   { primary: 'gemini-2.5-flash-lite', fallback: 'gpt-4.1-nano' },
  },
}

/**
 * STAGED (NOT ACTIVE) — the model-tier-policy activation plan for
 * gemini-3.1-pro-preview / gemini-3.7-flash, pinned per the native's ruling
 * (PARIPRASHNA-P3-PREFLIGHT-2026-08-21, item 2b). NOTHING reads this object —
 * it is not wired into `getEffectiveModel`, `STACK_ROUTING`, or
 * `CALL_TYPE_ROUTING`. Its only purpose is to record the intended
 * primary/fallback pair for each CallType BEFORE activation, so switching a
 * CallType over later is a one-line `STACK_ROUTING.gemini[callType] =
 * STAGED_TIER_UPGRADE_ROUTING[callType]`-shaped change instead of a fresh
 * design decision made under deploy pressure.
 *
 * Preconditions still open before ANY of these may be copied into
 * STACK_ROUTING (native ruling, item 2 + item 6):
 *   (a) DONE 2026-08-21 — interpretation_sets folded into the shared registry.
 *   (b) DONE 2026-08-21 — this table itself (fallbacks pinned).
 *   (c) DONE 2026-08-21 — Google deprecation page checked (see DD register);
 *       standing re-check rule added, must re-run before any deploy that
 *       touches model config, including the eventual activation deploy.
 *   (d) OPEN — adapter_gemini.ts needs a `thinking_level` code path; it
 *       currently only sends `thinkingConfig.thinkingBudget` (numeric,
 *       Gemini 2.x-era), not `thinkingLevel` (low/medium/high, Gemini
 *       3.x-era) — see MODELS[] entries above.
 *   (e) OPEN — a fresh `dd20_e2e_verify.ts` waiver-rate run, current as of
 *       the activation decision, not the 2026-08-21 close-day proof.
 *
 * Fallback rationale (gemini-3.1-pro-preview → gemini-2.5-pro, not another
 * preview): checked live 2026-08-21 against
 * https://ai.google.dev/gemini-api/docs/deprecations — preview models get
 * as little as ~2 weeks' shutdown notice and are typically replaced by the
 * NEXT preview, not a GA model (gemini-3-pro-preview → gemini-3.1-pro-preview
 * is the exact precedent). Pinning another preview as the fallback would
 * just relocate the fragility. gemini-2.5-pro is GA, is the model
 * gemini-3.1-pro-preview would be upgrading FROM, and is already the live
 * synthesis primary — zero new integration risk as a fallback.
 */
export const STAGED_TIER_UPGRADE_ROUTING: Partial<Record<CallType, { primary: string; fallback: string }>> = {
  synthesis:           { primary: 'gemini-3.1-pro-preview', fallback: 'gemini-2.5-pro' },
  interpretation_sets: { primary: 'gemini-3.1-pro-preview', fallback: 'gemini-2.5-pro' },
  planner_fast:        { primary: 'gemini-3.7-flash',       fallback: 'gemini-2.5-flash' },
  worker:              { primary: 'gemini-3.7-flash',       fallback: 'gemini-2.5-flash-lite' },
}

/**
 * The canonical CALL_TYPE_ROUTING alias — resolves to the DEFAULT_STACK_ID (gemini).
 *
 * D8 GOVERNANCE FIX (2026-06-28): Previously pointed at STACK_ROUTING['nim'], which
 * contradicted DEFAULT_STACK_ID='gemini'. The ruling per D8 governance §3.1:
 *   - Policy: Gemini-primary, DeepSeek-fallback. NIM is NOT the default.
 *   - DEFAULT_STACK_ID='gemini' is the single source of truth.
 *   - CALL_TYPE_ROUTING now derives from DEFAULT_STACK_ID so both agree.
 *   - NIM was the old default (pre-2026-05-10) before NIM axum auth started
 *     returning 500s; the comment was stale. Resolved here.
 *
 * Call sites that are not yet stack-aware can use this directly;
 * stack-aware call sites should use STACK_ROUTING[selectedStack][callType].
 */
export const CALL_TYPE_ROUTING = STACK_ROUTING[DEFAULT_STACK_ID]

/**
 * Return the primary and fallback model IDs for a given stack + call type.
 */
export function getStackModel(
  stack: ModelStack,
  callType: CallType,
): { primary: string; fallback: string } {
  return STACK_ROUTING[stack][callType]
}

/**
 * Convenience helper: return the primary model for a call type on a given stack.
 */
export function getPrimaryModel(stack: ModelStack, callType: CallType): string {
  return STACK_ROUTING[stack][callType].primary
}

/**
 * Convenience helper: return the fallback model for a call type on a given stack.
 */
export function getFallbackModel(stack: ModelStack, callType: CallType): string {
  return STACK_ROUTING[stack][callType].fallback
}

/**
 * Return all stacks as an array for the UI stack picker.
 * Each entry includes the stack ID, display label, synthesis model metadata,
 * and the synthesis context window — enough for a rich selector component.
 */
export function stackPicker(): Array<{
  stack: ModelStack
  label: string
  synthesisModelId: string
  synthesisContextWindow: number | undefined
  isDefault: boolean
}> {
  return (Object.keys(STACK_ROUTING) as ModelStack[]).map(stack => {
    const synthId = STACK_ROUTING[stack].synthesis.primary
    const meta = MODEL_INDEX[synthId]
    return {
      stack,
      label: STACK_LABEL[stack],
      synthesisModelId: synthId,
      synthesisContextWindow: meta?.maxInputTokens,
      isDefault: stack === DEFAULT_STACK_ID,
    }
  })
}

/**
 * Return true if this model has a 1M-token context window, making it eligible
 * for Whole-Chart-Read (feeding all L2.5 artifacts without chunking).
 */
export function supportsWholeChartRead(modelId: string): boolean {
  const meta = MODEL_INDEX[modelId]
  return (meta?.maxInputTokens ?? 0) >= 1_000_000
}

/**
 * Return the reasoning mode for a model ID.
 * Defaults to 'none' for unknown IDs so callers can branch safely.
 */
export function getReasoningMode(modelId: string): ReasoningMode {
  return MODEL_INDEX[modelId]?.reasoningMode ?? 'none'
}
