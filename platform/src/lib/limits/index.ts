/**
 * limits/ — the NCD-8 pre-dispatch gate, shared by both serving doors.
 *
 * `enforceTurnLimits()` is the ONE function a door calls before its first LLM
 * call. It bundles the two ruled checks in the order that costs least:
 *
 *   1. Feature flag. OFF (the default) short-circuits to allowed before any DB or
 *      pricing work runs — this lane ships dark and must be free when dark.
 *   2. Per-user rate limit, via the SAME rolling-window counter `lib/mcp/
 *      rate_limiter.ts` uses (imported from `rate_limiter_core.ts` — one
 *      implementation, see that file's header). In-process, no DB.
 *   3. Spend ceilings ($2/turn, $40/day), which needs one indexed DB read.
 *
 * The result is a discriminated union, so a door cannot forget to handle a
 * refusal: the `allowed: false` arm carries the code, the HTTP status, and a
 * reader-facing message, and TypeScript will not let it be read as allowed.
 *
 * @module limits
 */

import { configService } from '@/lib/config/index'
import { checkRpm } from '@/lib/mcp/rate_limiter_core'

import {
  RATE_LIMIT_ERROR_CODE,
  SPEND_CEILING_ERROR_CODE,
  checkSpendCeilings,
  spendCeilingMessage,
  type SpendCeilingDecision,
  type SpendChannel,
} from './spend_ceiling'

export {
  DEFAULT_PROJECTION_INPUT_TOKENS,
  RATE_LIMIT_ERROR_CODE,
  SPEND_CEILING_ERROR_CODE,
  SPEND_CEILING_PER_DAY_USD,
  SPEND_CEILING_PER_TURN_USD,
  checkSpendCeilings,
  getDailySpendUsd,
  getSpendAttribution,
  projectTurnCostUsd,
  spendCeilingMessage,
  type SpendAttributionRow,
  type SpendCeilingDecision,
  type SpendCeilingReason,
  type SpendChannel,
  type TurnCostProjection,
} from './spend_ceiling'

/** True when the NCD-8 gates are armed. Default false — see feature_flags.ts. */
export function limitsEnabled(): boolean {
  return configService.getFlag('PARIPRASHNA_LIMITS_ENABLED')
}

/**
 * Build the per-user rate-limit key for a door. Namespaced by channel so the web
 * and MCP doors cannot consume each other's window, and prefixed so a uid can
 * never collide with an MCP `key_id` in the shared counter Map.
 */
export function rateLimitKey(channel: SpendChannel, principalId: string): string {
  return `${channel}:user:${principalId}`
}

export type TurnLimitRefusal = {
  allowed: false
  /** `LIMIT_RATE_LIMIT_EXCEEDED` | `LIMIT_SPEND_CEILING_EXCEEDED`. */
  code: typeof RATE_LIMIT_ERROR_CODE | typeof SPEND_CEILING_ERROR_CODE
  /** Always 429. A refusal is a designed state, never a 5xx. */
  status: 429
  /** Reader-facing, states the actual ceiling and what happened. */
  message: string
  /** Present for rate-limit refusals when the window's remaining time is known. */
  retry_after_seconds?: number
  /** Present for spend refusals — the full decision, for logging and telemetry. */
  spend?: SpendCeilingDecision
}

export type TurnLimitDecision =
  | { allowed: true; enforced: boolean; spend?: SpendCeilingDecision }
  | TurnLimitRefusal

export interface EnforceTurnLimitsArgs {
  /** The authenticated principal this turn is billed to (`user.uid` / `x-mcp-user`). */
  userId: string
  /** Which serving door. Also namespaces the rate-limit window. */
  channel: SpendChannel
  /** The synthesis model already bound for this turn. */
  modelId: string
  /** Override the projection's assumed input budget. */
  inputTokens?: number
  /** Override the projection's assumed output cap. */
  outputTokens?: number
  /**
   * Rate-limit key override. The MCP door passes its `key_id` so the limit tracks
   * the credential, matching what every other `/api/mcp/*` route already does.
   */
  rateLimitPrincipalId?: string
}

/**
 * The pre-dispatch gate. Call BEFORE the first LLM call on either door.
 *
 * `enforced` on the allowed arm reports whether the gates actually ran, so a caller
 * never has to infer "allowed" from "flag off" — a permitted turn and an unchecked
 * turn are distinguishable (CLAUDE.md §N.8).
 */
export async function enforceTurnLimits(
  args: EnforceTurnLimitsArgs,
): Promise<TurnLimitDecision> {
  if (!limitsEnabled()) {
    return { allowed: true, enforced: false }
  }

  const principalId = args.rateLimitPrincipalId ?? args.userId
  const rpm = checkRpm(rateLimitKey(args.channel, principalId))
  if (!rpm.allowed) {
    return {
      allowed: false,
      code: RATE_LIMIT_ERROR_CODE,
      status: 429,
      message: rpm.retry_after_seconds
        ? `Too many requests. Try again in ${rpm.retry_after_seconds}s.`
        : 'Too many requests. Please slow down.',
      retry_after_seconds: rpm.retry_after_seconds,
    }
  }

  const spend = await checkSpendCeilings({
    userId: args.userId,
    channel: args.channel,
    modelId: args.modelId,
    inputTokens: args.inputTokens,
    outputTokens: args.outputTokens,
  })

  if (!spend.allowed) {
    return {
      allowed: false,
      code: SPEND_CEILING_ERROR_CODE,
      status: 429,
      message: spendCeilingMessage(spend),
      spend,
    }
  }

  return { allowed: true, enforced: true, spend }
}
