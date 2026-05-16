/**
 * Per-provider synthesis retry policy.
 *
 * maxRetries: SDK-level retries before surfacing an error to the route-level
 *   fallback. Set to 1 for providers that support clean retry semantics;
 *   0 for NIM which has its own adapter-level retry logic.
 *
 * retryOn: informational — documents which error classes trigger a retry.
 *   AI SDK retries on network errors and 5xx by default; 429-with-retry-after
 *   is retried when the response carries a Retry-After header.
 */

import type { Provider } from '@/lib/models/registry'

export interface ProviderQuirks {
  maxRetries: number
  retryOn: string[]
}

export const providerQuirks: Record<Provider, ProviderQuirks> = {
  anthropic: { maxRetries: 1, retryOn: ['network', '5xx', '429-with-retry-after'] },
  google:    { maxRetries: 1, retryOn: ['network', '5xx'] },
  openai:    { maxRetries: 1, retryOn: ['network', '5xx', '429-with-retry-after'] },
  deepseek:  { maxRetries: 1, retryOn: ['network', '5xx'] },
  nvidia:    { maxRetries: 0, retryOn: [] }, // NIM adapter has its own retry logic
}

export function getMaxRetries(provider: Provider): number {
  return providerQuirks[provider]?.maxRetries ?? 0
}
