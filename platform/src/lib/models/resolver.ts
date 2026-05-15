import 'server-only'
import { anthropic } from '@ai-sdk/anthropic'
import { google } from '@ai-sdk/google'
import { deepseek } from '@ai-sdk/deepseek'
import { extractReasoningMiddleware, wrapLanguageModel } from 'ai'
import type { LanguageModel } from 'ai'
import { getModelMeta, getWorkerForModel } from './registry'
import { getOpenAIModel } from './openai'
import { getNvidiaModel } from './nvidia'

// DeepSeek R1 wraps its chain-of-thought in <think>…</think> blocks.
// The middleware separates them into the reasoning stream-part channel so
// they never leak into the displayed answer text. R1 uses the standard
// streamText path (not o-series convention) — only the middleware differs.
const R1_REASONING_MIDDLEWARE = extractReasoningMiddleware({ tagName: 'think' })

/**
 * Resolve a model ID to a `LanguageModel` for `streamText`.
 * Server-only — provider SDKs must never land in the client bundle.
 * Validate the ID with `isValidModelId` (from registry) before calling.
 *
 * All models use the standard AI SDK streamText calling convention:
 * system message + user messages + temperature + tool-use (where capable).
 * The o-series convention (folded system prompt, no temperature, no streaming)
 * has been removed — o1/o3/o4-mini are no longer in the registry.
 *
 * @deprecated New code should use runAdapter / streamAdapter from \@/lib/adapters.
 * Provider resolution is now encapsulated inside the adapter layer.
 * Remaining call sites: legacy_runAdapter.ts, single_model_strategy.ts (streamBuildRaw path).
 */
export function resolveModel(id: string): LanguageModel {
  const meta = getModelMeta(id)
  if (!meta) throw new Error(`Unknown model id: ${id}`)
  switch (meta.provider) {
    case 'anthropic':
      return anthropic(meta.id)
    case 'google':
      return google(meta.id)
    case 'deepseek':
      // R1 (deepseek-reasoner) gets the think-strip middleware; V3 is plain.
      if (meta.id === 'deepseek-reasoner') {
        return wrapLanguageModel({
          model: deepseek(meta.id),
          middleware: R1_REASONING_MIDDLEWARE,
        })
      }
      return deepseek(meta.id)
    case 'openai':
      return getOpenAIModel(meta.id)
    case 'nvidia':
      // NVIDIA NIM — OpenAI-compatible endpoint. Models in this provider are
      // planner-only (role='planner') and are never called from synthesis paths.
      // Requires NVIDIA_NIM_API_KEY env variable.
      return getNvidiaModel(meta.id)
    default: {
      const _exhaustive: never = meta.provider
      throw new Error(`Unhandled provider: ${String(_exhaustive)}`)
    }
  }
}

/**
 * Resolve the worker model for a given synthesis model — same provider family,
 * cheapest/fastest option. Used by the planner and title generator so that
 * internal LLM calls bill the same provider the user already has credentials
 * for (BHISMA ADR-1 / FAMILY_WORKER pattern).
 *
 * @deprecated No active call sites — adapter layer handles model resolution
 * via QueryRequest.callType + stack routing.
 */
export function resolveWorkerModel(synthesisModelId: string): string {
  return getWorkerForModel(synthesisModelId)
}

// ─────────────────────────────────────────────────────────────────────────────
// DeepSeek provider options — thinking mode
// ─────────────────────────────────────────────────────────────────────────────

/**
 * DeepSeek V4 Pro thinking-mode config for streamText `providerOptions`.
 *
 * deepseek-v4-pro is a dual-mode model. For synthesis we want thinking=enabled
 * (chain-of-thought reasoning before the answer). For planner calls we want
 * thinking=disabled to get fast structured JSON without CoT overhead.
 *
 * Returns undefined for non-deepseek-v4-pro model IDs — deepseek-chat and
 * deepseek-reasoner must not receive a thinking providerOption.
 *
 * SDK note: @ai-sdk/deepseek ≥2.0.x exposes thinking via
 * providerOptions.deepseek.thinking.type ('enabled' | 'disabled').
 *
 * @deprecated Adapter layer (adapter_deepseek.ts) handles thinking-mode config
 * internally. Remaining call site: single_model_strategy.ts (streamBuildRaw path).
 */
export function deepseekProviderOptions(
  modelId: string,
  mode: 'synthesis' | 'planner' = 'synthesis',
):
  | { deepseek: { thinking: { type: 'enabled' | 'disabled' } } }
  | undefined {
  const meta = getModelMeta(modelId)
  if (meta?.provider !== 'deepseek') return undefined
  if (modelId !== 'deepseek-v4-pro') return undefined
  return {
    deepseek: {
      thinking: { type: mode === 'synthesis' ? 'enabled' : 'disabled' },
    },
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Google provider options — safety settings + thinking budget
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Google-specific safety + thinking config for streamText `providerOptions`.
 *
 * @deprecated Adapter layer (adapter_gemini.ts) handles safety + thinking config
 * internally. Remaining call site: single_model_strategy.ts (streamBuildRaw path).
 *
 * **Why this is necessary for MARSYS-JIS:**
 *
 * 1. SAFETY FILTER (root cause of "Network error after 5-6 lines"):
 *    Google's default safety thresholds are BLOCK_MEDIUM_AND_ABOVE on all
 *    categories. Jyotish synthesis output regularly contains:
 *      – Health vulnerability windows (maraka dasha analysis)
 *      – Death-timing analysis (marana karaka, 8th-lord periods)
 *      – Predictions about suffering, challenges, adversity
 *    These trigger HARM_CATEGORY_DANGEROUS_CONTENT mid-stream. The Google API
 *    closes the SSE connection without a clean finishReason → the AI SDK
 *    cannot emit a proper finish event → useChat surfaces "Network error."
 *    Setting threshold: 'BLOCK_NONE' on all categories disables the filters
 *    for this consenting-adult, disclosure-gated instrument.
 *
 * 2. EXTENDED THINKING (root cause of "query hangs with no response"):
 *    gemini-2.5-pro has thinking enabled by default. With a 340K-token corpus
 *    the thinking phase can run 30–90 s emitting only reasoning-delta SSE
 *    chunks. useChat does not render reasoning tokens as visible text, so the
 *    user sees a spinner indefinitely. Capping thinkingBudget at 8 192 tokens
 *    (≈ 30 s max) keeps latency acceptable while preserving some CoT benefit.
 *    Set thinkingBudget: 0 to fully disable thinking (fastest path).
 *
 * Returns undefined for non-Google models so callers can spread safely.
 */
export function googleProviderOptions(modelId: string):
  | {
      google: {
        safetySettings: Array<{ category: string; threshold: 'BLOCK_NONE' }>
        thinkingConfig: { thinkingBudget: number }
      }
    }
  | undefined {
  const meta = getModelMeta(modelId)
  if (meta?.provider !== 'google') return undefined
  return {
    google: {
      safetySettings: [
        { category: 'HARM_CATEGORY_HATE_SPEECH',       threshold: 'BLOCK_NONE' },
        { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_NONE' },
        { category: 'HARM_CATEGORY_HARASSMENT',        threshold: 'BLOCK_NONE' },
        { category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold: 'BLOCK_NONE' },
        { category: 'HARM_CATEGORY_CIVIC_INTEGRITY',   threshold: 'BLOCK_NONE' },
      ],
      thinkingConfig: {
        thinkingBudget: 24576,
      },
    },
  }
}
