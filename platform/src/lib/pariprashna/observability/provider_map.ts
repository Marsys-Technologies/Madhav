/**
 * pariprashna/observability/provider_map.ts — lane P2-E (PPR-33, GAP-14).
 *
 * The synthesis stage's adapter registry (`@/lib/providers/dispatcher`) keys
 * providers by `StackId` ('anthropic' | 'google' | 'openai' | 'deepseek' |
 * 'nvidia'). The EXISTING `llm_usage_events` schema (migration 001's
 * `llm_usage_events_provider_check`) keys providers by a DIFFERENT vocabulary:
 * ('anthropic' | 'openai' | 'gemini' | 'deepseek' | 'nim') — the same one
 * `@/lib/llm/observability/types.ts`'s `ProviderName` declares.
 *
 * Two names disagree ('google' vs 'gemini', 'nvidia' vs 'nim'). Writing a
 * `StackId` straight into `llm_usage_events.provider` would violate the CHECK
 * constraint for both of those and silently fail every Gemini/NIM turn's
 * observability write. This module is the one place that translates between
 * the two vocabularies, so nothing else has to know both exist.
 */

import type { StackId } from '@/lib/providers/dispatcher'
import type { ProviderName } from '@/lib/llm/observability/types'

const STACK_ID_TO_PROVIDER_NAME: Record<StackId, ProviderName> = {
  anthropic: 'anthropic',
  google: 'gemini',
  openai: 'openai',
  deepseek: 'deepseek',
  nvidia: 'nim',
}

/** Translate a synthesis-stage `StackId` into the `llm_usage_events.provider` vocabulary. */
export function mapStackIdToProviderName(stackId: StackId): ProviderName {
  return STACK_ID_TO_PROVIDER_NAME[stackId]
}
