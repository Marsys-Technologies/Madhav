/**
 * spend_ceiling.ts — NCD-8 pre-dispatch spend ceilings for both serving doors.
 *
 * ── The ruling ───────────────────────────────────────────────────────────────
 * `00_ARCHITECTURE/PARIPRASHNA_DECISION_REGISTER_v1_0.md`:
 *     | NCD-8 | Spend caps $2/turn · $40/day, pre-dispatch, both doors | RULED · 2026-08-18 |
 * `00_ARCHITECTURE/PARIPRASHNA_ARCHITECTURE_v1_0.md` (PPR-25):
 *     "Rate limits and spend ceilings ($2/turn · $40/day, ruled) MUST block before
 *      dispatch on both serving doors"
 * The two doors are the WEB door (`/api/pariprashna`, gated in
 * `pariprashna/pipeline/safety_gate.ts`) and the MCP door (`/api/mcp/prashna_ask`,
 * gated before `callPipelinePlanner`). Both gates run BEFORE the first LLM call.
 *
 * ── Why "pre-dispatch" needs a PROJECTION, and what that projection honestly is ─
 * A turn's actual cost is unknowable before the turn runs, so a genuinely
 * pre-dispatch per-turn ceiling can only ask one answerable question:
 *
 *     "Given the model this turn has already bound and the token budget it is
 *      permitted to spend, can this turn cost more than $2?"
 *
 * That is what {@link projectTurnCostUsd} computes: a WORST-CASE UPPER BOUND from
 * real registry pricing — (input budget x input price) + (output cap x output price).
 * It is deliberately conservative. A turn is refused when its own ceiling ALLOWS a
 * breach, not when a breach is likely. Per CLAUDE.md §N.8 this is a real detector:
 * it reads false for a cheap model (gemini-2.5-flash projects to fractions of a
 * cent) and true for an expensive one (claude-opus-4-7 at 128K in / 64K out projects
 * to $6.72 — a turn that genuinely could breach $2 and is therefore refused). It is
 * never a proxy for the claim and never a hardcoded green.
 *
 * The DAILY ceiling needs no projection: already-spent USD is a fact, read from
 * `llm_usage_events.computed_cost_usd` (the existing cost ledger — NO new table).
 * The gate refuses when `spent_today + projected_turn > $40`, i.e. it will not START
 * a turn whose own upper bound carries the user past the day's ceiling.
 *
 * ── Fail-open, but never silently ────────────────────────────────────────────
 * If the spend query fails, this module allows the turn (matching the existing
 * `mcp/rate_limiter.ts` convention — a DB blip must not take the product down) but
 * sets `daily_spend_known: false` on the decision. An unknown day-spend is reported
 * as unknown, never as "under the ceiling" (§N.7 item 6, §N.8).
 *
 * @module limits/spend_ceiling
 */

import { query } from '@/lib/db/client'
import { getModelPricingSync } from '@/lib/llm/pricing'
import { getModelMeta } from '@/lib/models/registry'
import type { ServingChannel } from '@/lib/llm/observability/types'

// ── The ruled ceilings (NCD-8) ────────────────────────────────────────────────

/** NCD-8: $2 per turn. Env override exists for staging drills, not for production relaxation. */
export const SPEND_CEILING_PER_TURN_USD = Number(
  process.env.MARSYS_SPEND_CEILING_PER_TURN_USD ?? '2',
)

/** NCD-8: $40 per user per UTC day. */
export const SPEND_CEILING_PER_DAY_USD = Number(
  process.env.MARSYS_SPEND_CEILING_PER_DAY_USD ?? '40',
)

// ── Channel vocabulary ────────────────────────────────────────────────────────

/**
 * The serving door a costed call came through.
 *
 * ALIASED, not redeclared: the vocabulary is owned by the ledger the ceiling reads
 * (`llm_usage_events.channel`, migration 574), so it is declared once next to that
 * row shape in `@/lib/llm/observability/types` and re-exported here. A second copy
 * of the union would be free to drift from the column that actually stores it.
 */
export type SpendChannel = ServingChannel

// ── Projection ────────────────────────────────────────────────────────────────

/**
 * Default input-token budget used for the projection when a caller supplies none.
 *
 * 128_000 is not a fresh number: it is the exact `synthesis_model_max_context` the
 * budget arbiter already uses on BOTH doors (`arbitrateBudgets(...)` in
 * `/api/mcp/prashna_ask/route.ts` and in the web door's plan stage). Using the
 * arbiter's own figure keeps the projection describing the turn the pipeline will
 * actually run rather than a hypothetical one.
 */
export const DEFAULT_PROJECTION_INPUT_TOKENS = 128_000

export interface TurnCostProjection {
  /** Worst-case USD this turn can cost, or null when the model has no registry pricing. */
  projected_max_usd: number | null
  /** Input tokens the projection assumed. */
  input_tokens: number
  /** Output tokens the projection assumed. */
  output_tokens: number
  /** Set when `projected_max_usd` is null — names the reason rather than defaulting to 0. */
  unpriced_reason?: 'model_not_in_registry'
}

/**
 * Worst-case USD upper bound for one turn on `modelId`.
 *
 * Returns `projected_max_usd: null` — NOT 0 — for a model absent from the registry.
 * An unknown price is unknown; treating it as free would let an unpriced model walk
 * straight through the ceiling (§N.7 item 6).
 */
export function projectTurnCostUsd(
  modelId: string,
  opts?: { inputTokens?: number; outputTokens?: number },
): TurnCostProjection {
  const pricing = getModelPricingSync(modelId)
  const meta = getModelMeta(modelId)

  // Cap the assumed input at what the model actually accepts, when it declares a
  // limit — projecting 128K into a 32K-context model would overstate the bound.
  const requestedInput = opts?.inputTokens ?? DEFAULT_PROJECTION_INPUT_TOKENS
  const inputTokens = meta?.maxInputTokens
    ? Math.min(requestedInput, meta.maxInputTokens)
    : requestedInput
  const outputTokens = opts?.outputTokens ?? meta?.maxOutputTokens ?? 0

  if (!pricing) {
    return {
      projected_max_usd: null,
      input_tokens: inputTokens,
      output_tokens: outputTokens,
      unpriced_reason: 'model_not_in_registry',
    }
  }

  const usd =
    (inputTokens / 1e6) * pricing.input_per_1m_usd +
    (outputTokens / 1e6) * pricing.output_per_1m_usd

  return {
    projected_max_usd: Math.round(usd * 1e6) / 1e6,
    input_tokens: inputTokens,
    output_tokens: outputTokens,
  }
}

// ── Daily spend (reads the EXISTING ledger) ───────────────────────────────────

export interface DailySpend {
  usd: number
  /** False when the query failed. `usd` is then 0 and must not be read as "under ceiling". */
  known: boolean
}

/**
 * Sum this user's costed LLM calls since the start of the current UTC day.
 *
 * Reads `llm_usage_events` — the codebase's existing per-user cost ledger. NCD-8
 * introduces no cost table of its own; migration 574 only adds the `channel`
 * dimension and the index this query needs.
 */
export async function getDailySpendUsd(userId: string): Promise<DailySpend> {
  try {
    const { rows } = await query<{ total: string | null }>(
      `SELECT COALESCE(SUM(computed_cost_usd), 0)::text AS total
         FROM llm_usage_events
        WHERE user_id = $1
          AND started_at >= date_trunc('day', now() AT TIME ZONE 'utc')`,
      [userId],
    )
    const parsed = Number.parseFloat(rows[0]?.total ?? '0')
    return { usd: Number.isFinite(parsed) ? parsed : 0, known: true }
  } catch (err) {
    console.warn('[limits:spend_ceiling] daily spend query failed; failing open', err)
    return { usd: 0, known: false }
  }
}

/**
 * Per-(user, channel, model) cost attribution rollup for one UTC day.
 *
 * This is the read side of the attribution the `channel` column exists for. It is
 * not on the gate's critical path — the ceiling itself only needs the user total —
 * but it is the surface that makes the added dimension actually useful, and it is
 * what proves the wiring is real rather than a column nothing reads.
 */
export interface SpendAttributionRow {
  user_id: string
  channel: SpendChannel | null
  model: string
  calls: number
  cost_usd: number
}

export async function getSpendAttribution(
  userId: string,
  opts?: { sinceUtcDayStart?: boolean },
): Promise<SpendAttributionRow[]> {
  const since = opts?.sinceUtcDayStart === false ? '' : `AND started_at >= date_trunc('day', now() AT TIME ZONE 'utc')`
  try {
    const { rows } = await query<{
      user_id: string
      channel: string | null
      model: string
      calls: string
      cost_usd: string | null
    }>(
      `SELECT user_id, channel, model,
              COUNT(*)::text AS calls,
              COALESCE(SUM(computed_cost_usd), 0)::text AS cost_usd
         FROM llm_usage_events
        WHERE user_id = $1 ${since}
        GROUP BY user_id, channel, model
        ORDER BY COALESCE(SUM(computed_cost_usd), 0) DESC`,
      [userId],
    )
    return rows.map((r) => ({
      user_id: r.user_id,
      channel: (r.channel as SpendChannel | null) ?? null,
      model: r.model,
      calls: Number.parseInt(r.calls, 10) || 0,
      cost_usd: Number.parseFloat(r.cost_usd ?? '0') || 0,
    }))
  } catch (err) {
    console.warn('[limits:spend_ceiling] attribution query failed', err)
    return []
  }
}

// ── The gate ──────────────────────────────────────────────────────────────────

export type SpendCeilingReason = 'turn_ceiling_exceeded' | 'daily_ceiling_exceeded'

export interface SpendCeilingDecision {
  allowed: boolean
  /** Present only when `allowed` is false. */
  reason?: SpendCeilingReason
  /** The ceiling that was breached, in USD. */
  ceiling_usd?: number
  /** Worst-case USD this turn could cost. Null when the model is unpriced. */
  projected_turn_usd: number | null
  /** USD already spent by this user in the current UTC day. */
  spent_today_usd: number
  /** False when the spend query failed — `spent_today_usd` is then not a measurement. */
  daily_spend_known: boolean
  channel: SpendChannel
  model_id: string
}

export interface SpendCeilingArgs {
  userId: string
  channel: SpendChannel
  modelId: string
  /** Override the projection's assumed input budget (defaults to the arbiter's 128K). */
  inputTokens?: number
  /** Override the projection's assumed output cap (defaults to the model's own max). */
  outputTokens?: number
}

/**
 * The NCD-8 pre-dispatch gate. Call this BEFORE the first LLM call on either door.
 *
 * Turn ceiling is checked first (it needs no DB round-trip, so a turn that cannot
 * run at all is refused without paying for a query). Daily ceiling second.
 *
 * An unpriced model (`projected_turn_usd === null`) does NOT bypass the gate: the
 * turn ceiling cannot be evaluated against an unknown price, so the decision falls
 * through to the daily ceiling using the known spend alone. That is the honest
 * behaviour — an unknown is not a zero and not a breach.
 */
export async function checkSpendCeilings(args: SpendCeilingArgs): Promise<SpendCeilingDecision> {
  const { userId, channel, modelId } = args

  const projection = projectTurnCostUsd(modelId, {
    inputTokens: args.inputTokens,
    outputTokens: args.outputTokens,
  })
  const projected = projection.projected_max_usd

  if (projected !== null && projected > SPEND_CEILING_PER_TURN_USD) {
    return {
      allowed: false,
      reason: 'turn_ceiling_exceeded',
      ceiling_usd: SPEND_CEILING_PER_TURN_USD,
      projected_turn_usd: projected,
      spent_today_usd: 0,
      daily_spend_known: false,
      channel,
      model_id: modelId,
    }
  }

  const daily = await getDailySpendUsd(userId)
  const wouldTotal = daily.usd + (projected ?? 0)

  if (daily.known && wouldTotal > SPEND_CEILING_PER_DAY_USD) {
    return {
      allowed: false,
      reason: 'daily_ceiling_exceeded',
      ceiling_usd: SPEND_CEILING_PER_DAY_USD,
      projected_turn_usd: projected,
      spent_today_usd: daily.usd,
      daily_spend_known: true,
      channel,
      model_id: modelId,
    }
  }

  return {
    allowed: true,
    projected_turn_usd: projected,
    spent_today_usd: daily.usd,
    daily_spend_known: daily.known,
    channel,
    model_id: modelId,
  }
}

// ── The designed failure state ────────────────────────────────────────────────

/** Stable machine-readable code the client branches on. Never a 500. */
export const SPEND_CEILING_ERROR_CODE = 'LIMIT_SPEND_CEILING_EXCEEDED'

/** Stable machine-readable code for the rate-limit door. */
export const RATE_LIMIT_ERROR_CODE = 'LIMIT_RATE_LIMIT_EXCEEDED'

/**
 * Reader-facing message for a refused turn. States the ceiling and what happened —
 * a spend refusal is a normal, explainable state of the product, not an error to
 * apologise vaguely for.
 */
export function spendCeilingMessage(decision: SpendCeilingDecision): string {
  if (decision.reason === 'turn_ceiling_exceeded') {
    return (
      `This turn is not permitted to run: its cost ceiling is ` +
      `$${SPEND_CEILING_PER_TURN_USD.toFixed(2)} per turn, and the selected model ` +
      `(${decision.model_id}) could cost up to $${(decision.projected_turn_usd ?? 0).toFixed(2)}. ` +
      `Choose a less expensive model or a shorter reading.`
    )
  }
  return (
    `Daily spend ceiling reached: $${SPEND_CEILING_PER_DAY_USD.toFixed(2)} per day. ` +
    `$${decision.spent_today_usd.toFixed(2)} has been spent so far today. ` +
    `The ceiling resets at 00:00 UTC.`
  )
}
