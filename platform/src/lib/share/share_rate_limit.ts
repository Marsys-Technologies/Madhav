import { BoundedRateLimiter } from '@/lib/security/bounded_rate_limiter'
import {
  SHARE_MUTATION_LIMIT,
  SHARE_MUTATION_MAX_ENTRIES,
  SHARE_MUTATION_WINDOW_MS,
} from './constants'

/**
 * Per-user limiter for share create (POST) and revoke (DELETE), keyed on the
 * VERIFIED firebase uid (never a client-supplied value). One shared bucket for
 * both methods: the abuse being bounded is link churn, whichever direction.
 *
 * Memory is bounded by `BoundedRateLimiter` (hard cap + TTL sweep). Per-instance,
 * like the other in-process limiters in this repo.
 */
export const shareMutationLimiter = new BoundedRateLimiter({
  limit: SHARE_MUTATION_LIMIT,
  windowMs: SHARE_MUTATION_WINDOW_MS,
  maxEntries: SHARE_MUTATION_MAX_ENTRIES,
})
