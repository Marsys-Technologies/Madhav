/**
 * pariprashna/observability/queries.ts — lane P2-E (PPR-33, GAP-14).
 *
 * Read-side aggregate queries over the durable stores this lane wires or
 * already exist. Every function here reads REAL rows — none synthesizes a
 * result (CLAUDE.md §N.8: a rate needs a real detector behind it, or it is
 * null, not green). Two-week-baseline intent (per the roadmap line this lane
 * implements): these are measurement surfaces, not SLO gates — nothing here
 * pass/fails a threshold.
 *
 * Deliberately NOT wired into a UI page: `components/cockpit/**` is the L1
 * asset-build cockpit (BuildButton/AssetTable/LiveBuildGraph) — unrelated to
 * Paripraśna — and the roadmap sizes this lane "M". These functions are the
 * reusable surface a future dashboard (or a one-off admin query) calls.
 */

import { query } from '@/lib/db/client'
import { getReconnectCounters } from '../protocol/ring_buffer'

// ---------------------------------------------------------------------------
// Cost / latency / TTFT (the llm_usage_events rows this lane's
// `synthesis_observation.ts` writes — pipeline_stage='synthesize' scopes to
// Paripraśna's synthesis calls specifically).
// ---------------------------------------------------------------------------

export interface SynthesisLatencyStats {
  turns: number
  avg_latency_ms: number | null
  p50_latency_ms: number | null
  p95_latency_ms: number | null
  avg_ttft_ms: number | null
  p95_ttft_ms: number | null
  since_days: number
}

/**
 * Latency/TTFT distribution over completed synthesis turns. TTFT is read from
 * `parameters->>'ttft_ms'` (this lane's own field — see
 * `synthesis_observation.ts#buildSynthesisParameters`); latency is the
 * EXISTING `latency_ms` column, so nothing here is a proxy for a value the
 * schema already tracks.
 */
export async function getSynthesisLatencyStats(sinceDays = 14): Promise<SynthesisLatencyStats> {
  const { rows } = await query<{
    turns: string
    avg_latency_ms: string | null
    p50_latency_ms: string | null
    p95_latency_ms: string | null
    avg_ttft_ms: string | null
    p95_ttft_ms: string | null
  }>(
    `SELECT
       COUNT(*)::text AS turns,
       AVG(latency_ms)::text AS avg_latency_ms,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latency_ms)::text AS p50_latency_ms,
       PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms)::text AS p95_latency_ms,
       AVG((parameters->>'ttft_ms')::numeric)::text AS avg_ttft_ms,
       PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY (parameters->>'ttft_ms')::numeric)::text AS p95_ttft_ms
     FROM llm_usage_events
    WHERE pipeline_stage = 'synthesize'
      AND started_at >= now() - ($1 || ' days')::interval`,
    [String(sinceDays)],
  )
  const r = rows[0]
  const num = (s: string | null | undefined): number | null => (s === null || s === undefined ? null : Number.parseFloat(s))
  return {
    turns: r ? Number.parseInt(r.turns, 10) || 0 : 0,
    avg_latency_ms: num(r?.avg_latency_ms),
    p50_latency_ms: num(r?.p50_latency_ms),
    p95_latency_ms: num(r?.p95_latency_ms),
    avg_ttft_ms: num(r?.avg_ttft_ms),
    p95_ttft_ms: num(r?.p95_ttft_ms),
    since_days: sinceDays,
  }
}

export interface SynthesisCostAttributionRow {
  user_id: string
  channel: string | null
  model: string
  calls: number
  cost_usd: number
}

/**
 * Cost per (user, channel, model) for Paripraśna synthesis calls specifically.
 * `@/lib/limits/spend_ceiling.ts#getSpendAttribution` already covers the
 * per-user rollup across ALL `llm_usage_events` rows (any pipeline_stage);
 * this is the pariprashna-scoped, cross-user cut the ceiling doesn't need and
 * doesn't compute — reusing the same ledger, not a second cost table.
 */
export async function getSynthesisCostAttribution(sinceDays = 14): Promise<SynthesisCostAttributionRow[]> {
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
      WHERE pipeline_stage = 'synthesize'
        AND started_at >= now() - ($1 || ' days')::interval
      GROUP BY user_id, channel, model
      ORDER BY COALESCE(SUM(computed_cost_usd), 0) DESC`,
    [String(sinceDays)],
  )
  return rows.map((r) => ({
    user_id: r.user_id,
    channel: r.channel,
    model: r.model,
    calls: Number.parseInt(r.calls, 10) || 0,
    cost_usd: Number.parseFloat(r.cost_usd ?? '0') || 0,
  }))
}

// ---------------------------------------------------------------------------
// Register-lint firing rate (the health signal that the primary defenses work).
// ---------------------------------------------------------------------------

export interface RegisterLintFiringRate {
  turns_measured: number
  delta_calls: number
  fires: number
  leaks_total: number
  /** fires / delta_calls, i.e. the fraction of streamed prose deltas the lint had to touch. */
  firing_rate: number | null
  since_days: number
}

/**
 * Aggregated from `llm_usage_events.parameters->'register_lint'` — the SAME
 * per-turn totals `synthesis_stage.ts` already reports live via the
 * `register_leak_scrubbed` SSE flag; this is their durable, queryable
 * rollup. Zero rows (flag OFF, or before this lane's identity wiring lands
 * in route.ts) reports `firing_rate: null`, never 0 — an unmeasured rate is
 * not the same claim as a zero rate (§N.7 item 6).
 */
export async function getRegisterLintFiringRate(sinceDays = 14): Promise<RegisterLintFiringRate> {
  const { rows } = await query<{
    turns: string
    delta_calls: string | null
    fires: string | null
    leaks_total: string | null
  }>(
    `SELECT
       COUNT(*)::text AS turns,
       SUM((parameters->'register_lint'->>'delta_calls')::numeric)::text AS delta_calls,
       SUM((parameters->'register_lint'->>'fires')::numeric)::text AS fires,
       SUM((parameters->'register_lint'->>'leaks_total')::numeric)::text AS leaks_total
     FROM llm_usage_events
    WHERE pipeline_stage = 'synthesize'
      AND parameters ? 'register_lint'
      AND started_at >= now() - ($1 || ' days')::interval`,
    [String(sinceDays)],
  )
  const r = rows[0]
  const turns = r ? Number.parseInt(r.turns, 10) || 0 : 0
  const deltaCalls = Number.parseFloat(r?.delta_calls ?? '0') || 0
  const fires = Number.parseFloat(r?.fires ?? '0') || 0
  const leaksTotal = Number.parseFloat(r?.leaks_total ?? '0') || 0
  return {
    turns_measured: turns,
    delta_calls: deltaCalls,
    fires,
    leaks_total: leaksTotal,
    firing_rate: deltaCalls > 0 ? fires / deltaCalls : null,
    since_days: sinceDays,
  }
}

// ---------------------------------------------------------------------------
// Gate verdict rates (SafetyPolicyGate — pariprashna_safety_decisions).
// ---------------------------------------------------------------------------

export interface GateVerdictRate {
  action: string
  count: number
  rate: number
}

export interface GateVerdictRatesResult {
  total: number
  rates: GateVerdictRate[]
  since_days: number
}

/**
 * Verdict distribution from `pariprashna_safety_decisions` (written on EVERY
 * enforced turn — `safety/audit.ts`'s own docstring: "a safety table
 * containing only the turns that fired cannot answer 'out of how many?'").
 * `total: 0` is the honest, expected reading while
 * `PARIPRASHNA_SAFETY_GATE_ENABLED` is off (its documented default) — the
 * gate writes nothing in that state (`gate.ts`'s flag-off branch returns
 * before `appendSafetyDecision` is ever called), so an empty table means
 * "not measured yet", not "0% of turns triggered anything".
 */
export async function getGateVerdictRates(sinceDays = 14): Promise<GateVerdictRatesResult> {
  const { rows } = await query<{ action: string; n: string }>(
    `SELECT action, COUNT(*)::text AS n
       FROM pariprashna_safety_decisions
      WHERE recorded_at >= now() - ($1 || ' days')::interval
      GROUP BY action`,
    [String(sinceDays)],
  )
  const total = rows.reduce((sum, r) => sum + (Number.parseInt(r.n, 10) || 0), 0)
  const rates = rows.map((r) => {
    const count = Number.parseInt(r.n, 10) || 0
    return { action: r.action, count, rate: total > 0 ? count / total : 0 }
  })
  return { total, rates, since_days: sinceDays }
}

// ---------------------------------------------------------------------------
// Reconnect / snapshot-fallback rates (ring_buffer.ts).
// ---------------------------------------------------------------------------

export interface ReconnectRates {
  resume_attempts: number
  evicted_fallbacks: number
  unknown_turn: number
  /** evicted_fallbacks / resume_attempts. `null` with zero attempts observed. */
  snapshot_fallback_rate: number | null
  /**
   * PROCESS-LOCAL (see `ring_buffer.ts`'s counter docstring) — this instance's
   * counters since last process start/reset, not a fleet-wide total. Honest
   * baseline, not a claim of cross-instance aggregation.
   */
  process_local: true
}

export function getReconnectRates(): ReconnectRates {
  const c = getReconnectCounters()
  return {
    resume_attempts: c.resumeAttempts,
    evicted_fallbacks: c.evictedFallbacks,
    unknown_turn: c.unknownTurn,
    snapshot_fallback_rate: c.resumeAttempts > 0 ? c.evictedFallbacks / c.resumeAttempts : null,
    process_local: true,
  }
}

// ---------------------------------------------------------------------------
// Prediction capture + resolution coverage (brahma_mimamsa_prediction_ledger).
// ---------------------------------------------------------------------------

export interface PredictionCoverageResult {
  captured_total: number
  by_lifecycle_status: Record<string, number>
  /** Rows that reached 'outcome_recorded' — an actual measured Brier-scoreable outcome. */
  resolved_total: number
  /** resolved_total / captured_total. `null` when nothing was captured. */
  resolution_coverage: number | null
  since_days: number
}

/**
 * Capture + resolution coverage from the ledger `samiksha/*` already writes
 * to (`LEDGER_TABLE` in `samiksha/schema.ts`). 'outcome_recorded' is the ONE
 * lifecycle state with a measured outcome (`samiksha/schema.ts`'s
 * `TRANSITIONS` map: `window_closed -> outcome_recorded`); every other
 * terminal state (`dismissed`, `lapsed`, `unverifiable`, `lapsed_unconfirmed`)
 * is a real, non-shameful disposition (W-2) but not a resolved prediction, so
 * it is reported in `by_lifecycle_status` without being counted toward
 * `resolved_total`.
 */
export async function getPredictionCaptureResolutionCoverage(sinceDays = 14): Promise<PredictionCoverageResult> {
  const { rows } = await query<{ lifecycle_status: string; n: string }>(
    `SELECT lifecycle_status, COUNT(*)::text AS n
       FROM brahma_mimamsa_prediction_ledger
      WHERE created_at >= now() - ($1 || ' days')::interval
      GROUP BY lifecycle_status`,
    [String(sinceDays)],
  )
  const byStatus: Record<string, number> = {}
  let capturedTotal = 0
  for (const r of rows) {
    const n = Number.parseInt(r.n, 10) || 0
    byStatus[r.lifecycle_status] = n
    capturedTotal += n
  }
  const resolvedTotal = byStatus.outcome_recorded ?? 0
  return {
    captured_total: capturedTotal,
    by_lifecycle_status: byStatus,
    resolved_total: resolvedTotal,
    resolution_coverage: capturedTotal > 0 ? resolvedTotal / capturedTotal : null,
    since_days: sinceDays,
  }
}
