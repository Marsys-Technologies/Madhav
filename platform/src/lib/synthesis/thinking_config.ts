import 'server-only'

/**
 * thinking_config.ts — C-S4 R11.C
 *
 * Central helper for resolving adaptive thinking configuration via the
 * provider dispatcher. Called by the synthesis layer (route.ts) before
 * initiating a chat turn when thinking is requested.
 *
 * Usage:
 *   const config = resolveThinkingConfig('anthropic', { effort: 'medium' })
 *   // → { mode: 'native_effort', effort: 'medium', budgetTokens: 8192, providerPayload: {...} }
 *
 * Per-provider shapes (C-S4 decision log):
 *   - Anthropic: { type: 'enabled', effort: 'low'|'medium'|'high' } (Opus/Sonnet 4.6+)
 *     Budget fallback: { type: 'enabled', budget_tokens: N }
 *   - Gemini: thinkingConfig: { thinkingBudget: N } (default 24576, max 32768)
 *   - OpenAI: systemPromptPrefix CoT nudge (polyfill_cot, no API change)
 *   - DeepSeek: extractReasoningMiddleware=true (inline_blocks, <think> extraction)
 *   - NVIDIA: mode=null (capability hint: switch to Anthropic/Gemini)
 */

import type { ThinkingRequest, ThinkingResponse } from '@/lib/providers/types';
import type { StackId } from '@/lib/providers/dispatcher';
import { getAdapter } from '@/lib/providers/dispatcher';

/**
 * Resolves the per-provider thinking configuration for a given stack.
 *
 * @param stackId - The active provider stack ID
 * @param request - Thinking request with optional effort + budgetTokens
 * @returns Resolved thinking config with providerPayload for injection into ChatRequest
 */
export function resolveThinkingConfig(
  stackId: StackId,
  request: Partial<ThinkingRequest> = {},
): ThinkingResponse {
  const adapter = getAdapter(stackId);
  const manifest = adapter.getManifest();

  const fullRequest: ThinkingRequest = {
    extendedThinkingMode: manifest.extendedThinking,
    effort: request.effort ?? 'medium',
    budgetTokens: request.budgetTokens,
  };

  return adapter.thinking(fullRequest);
}

/**
 * Returns true if the given stack has native (non-polyfill) thinking support.
 * Used to conditionally render the ReasoningProgress component.
 */
export function stackHasNativeThinking(stackId: StackId): boolean {
  const adapter = getAdapter(stackId);
  const manifest = adapter.getManifest();
  return manifest.extendedThinking === 'native_effort' ||
    manifest.extendedThinking === 'native_budget';
}

/**
 * Returns true if the given stack has any thinking support (native or polyfill).
 * Used by PreTokenIndicator to show "Thinking… Ns" label.
 */
export function stackHasAnyThinking(stackId: StackId): boolean {
  const adapter = getAdapter(stackId);
  const manifest = adapter.getManifest();
  return manifest.extendedThinking !== null;
}
