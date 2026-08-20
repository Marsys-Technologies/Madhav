/**
 * pariprashna/observability/synthesis_observation.ts — lane P2-E (PPR-33, GAP-14).
 *
 * Persists ONE `llm_usage_events` row per completed synthesis-stage turn —
 * the EXISTING schema (migration 001, `channel` column added by migration
 * 574) that this lane's brief calls "dead": built (`@/lib/llm/observability`,
 * `@/lib/llm/providers/*_observed.ts`) but never called from the live
 * pariprashna path (`synthesis_stage.ts` calls `@/lib/providers/dispatcher`'s
 * `getAdapter(...).chat()` / `runAgenticLoop`, a completely separate adapter
 * family from the `*_observed.ts` wrappers — confirmed by grep: nothing
 * outside `lib/llm/providers/**` and its own tests imports them). This module
 * is the wiring: it reuses `computeCost` + `persistObservation` exactly as
 * built, from the ONE call site that actually serves production reads.
 *
 * ── WHY IDENTITY IS OPTIONAL, AND WHAT HAPPENS WHEN IT'S ABSENT ─────────────
 * `llm_usage_events.conversation_id` / `.user_id` are NOT NULL. This lane's
 * `may_touch` is `lib/pariprashna/**` + `components/pariprashna/**` +
 * `components/cockpit/**` — it does NOT include `app/api/pariprashna/route.ts`,
 * the one caller of `runSynthesisStage`, which is where the real `turnId` /
 * `conversationId` / `user.uid` already live in scope (see its `identity` and
 * `user` locals). Rather than fabricate a conversation_id/user_id to satisfy
 * the NOT NULL constraint (CLAUDE.md §N.7 item 6 — "an honest null beats an
 * invented judgment"), this module makes identity an OPTIONAL argument: when
 * absent, the write is honestly SKIPPED and `warnObservabilityIdentityMissing`
 * logs once (never spams). The wiring is real and tested; it activates the
 * moment a future, in-scope change to route.ts adds:
 *
 *   observability: { turnId: identity.turnId, conversationId: identity.conversationId, userId: user.uid }
 *
 * to its existing `runSynthesisStage({...})` call — see the P2-E report.
 */

import { query } from '@/lib/db/client'
import { computeCost, PricingNotFoundError } from '@/lib/llm/observability/cost'
import { persistObservation } from '@/lib/llm/observability/persist'
import type {
  ObservedLLMRequest,
  ObservedLLMResponse,
  ObservatoryDb,
  ServingChannel,
} from '@/lib/llm/observability/types'
import type { StackId } from '@/lib/providers/dispatcher'

import { mapStackIdToProviderName } from './provider_map'
import type { TurnMetricsSnapshot } from './turn_metrics'

export interface SynthesisObservationIdentity {
  /** `identity.turnId` at the route — doubles as `llm_usage_events.prompt_id`. */
  turnId: string
  conversationId: string
  userId: string
  /**
   * Defaults to 'web': `runSynthesisStage` is called from exactly one place,
   * `app/api/pariprashna/route.ts` (confirmed by grep — the MCP door,
   * `app/api/mcp/prashna_ask/route.ts`, does not call it), which IS the web
   * door. Overridable for forward-compatibility, never asserted as fact when
   * unprovided.
   */
  channel?: ServingChannel
}

export interface RecordSynthesisTurnObservationArgs {
  identity: SynthesisObservationIdentity | undefined
  stackId: StackId
  modelId: string
  startedAt: Date
  finishedAt: Date
  status: 'success' | 'error'
  errorCode?: string
  snapshot: TurnMetricsSnapshot
  /** Injectable for tests. Defaults to the real DB pool. */
  db?: ObservatoryDb
}

/**
 * Adapt `@/lib/db/client`'s pool `query` (generic constrained to
 * `T extends QueryResultRow`) to `ObservatoryDb`'s unconstrained `query<T>`.
 * Same bridge `scripts/observatory/smoke_test.ts` uses for `pg.Pool.query`
 * directly; needed HERE too because the constrained generic does not
 * structurally satisfy the unconstrained one without an explicit wrapper.
 */
function defaultObservatoryDb(): ObservatoryDb {
  return {
    query: async <T = unknown>(sql: string, params?: unknown[]) => {
      const result = await query<Record<string, unknown>>(sql, params)
      return { rows: result.rows as unknown as T[], rowCount: result.rowCount }
    },
  }
}

let warnedNoIdentity = false

/** Reset the one-time warning latch. Test-only. */
export function __resetObservabilityWarnLatchForTests(): void {
  warnedNoIdentity = false
}

function warnIdentityMissingOnce(): void {
  if (warnedNoIdentity) return
  warnedNoIdentity = true
  console.warn(
    '[pariprashna/observability] runSynthesisStage completed without an `observability` identity ' +
      '(turnId/conversationId/userId) — this turn\'s llm_usage_events row (and every turn\'s, until ' +
      'this is wired) is honestly SKIPPED rather than written with a fabricated conversation_id/user_id. ' +
      'Lane P2-E (PPR-33/GAP-14): app/api/pariprashna/route.ts needs to pass `observability: ' +
      '{ turnId: identity.turnId, conversationId: identity.conversationId, userId: user.uid }` into its ' +
      'existing runSynthesisStage(...) call — outside this lane\'s may_touch scope. (This warning logs once per process.)',
  )
}

/** Build the JSONB `parameters` payload carrying every metric that has no dedicated column. */
export function buildSynthesisParameters(snapshot: TurnMetricsSnapshot): Record<string, unknown> {
  return {
    lane: 'P2-E',
    ttft_ms: snapshot.ttft_ms,
    max_event_gap_ms: snapshot.max_event_gap_ms,
    event_count: snapshot.event_count,
    events_by_type: snapshot.events_by_type,
    pass_count: snapshot.pass_count,
    register_lint: snapshot.register_lint,
    delta_commit_lag_ms: snapshot.delta_commit_lag_ms,
  }
}

/**
 * Persist one `llm_usage_events` row for a completed synthesis-stage turn.
 * Fire-and-forget from the caller (`void recordSynthesisTurnObservation(...)`):
 * never throws, never blocks turn completion — the same discipline
 * `stream_capture.ts`/`ring_buffer.ts` already use for telemetry sinks on this
 * hot path.
 */
export async function recordSynthesisTurnObservation(args: RecordSynthesisTurnObservationArgs): Promise<void> {
  if (!args.identity) {
    warnIdentityMissingOnce()
    return
  }
  const db: ObservatoryDb = args.db ?? defaultObservatoryDb()
  try {
    const provider = mapStackIdToProviderName(args.stackId)
    const usage = args.snapshot.usage

    const request: ObservedLLMRequest = {
      provider,
      model: args.modelId,
      prompt_text: null,
      system_prompt: null,
      parameters: buildSynthesisParameters(args.snapshot),
      conversation_id: args.identity.conversationId,
      conversation_name: null,
      prompt_id: args.identity.turnId,
      user_id: args.identity.userId,
      pipeline_stage: 'synthesize',
      channel: args.identity.channel ?? 'web',
    }
    const response: ObservedLLMResponse = {
      response_text: null,
      usage,
      status: args.status,
      error_code: args.errorCode,
      started_at: args.startedAt,
      finished_at: args.finishedAt,
    }

    let cost = null
    try {
      cost = await computeCost(provider, args.modelId, usage, args.startedAt, db)
    } catch (err) {
      if (!(err instanceof PricingNotFoundError)) {
        console.error('[pariprashna/observability] computeCost failed (non-fatal):', err)
      }
      // PricingNotFoundError is an EXPECTED, honest gap until `llm_pricing_versions`
      // carries a row for every model this pipeline can bind to — degrade to a
      // null cost (persistObservation writes NULL, never a fabricated number).
    }

    await persistObservation(request, response, cost, db)
  } catch (err) {
    console.error('[pariprashna/observability] recordSynthesisTurnObservation failed (non-fatal):', err)
  }
}
