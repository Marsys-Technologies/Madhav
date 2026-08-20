/**
 * pariprashna/observability/turn_metrics.ts — lane P2-E (PPR-33, GAP-14).
 *
 * A pure, in-memory collector for the per-turn measurements the roadmap names:
 * TTFT, per-event latency (the max gap between two consecutive provider
 * events), delta→commit lag, the register-lint firing rate, and token usage.
 *
 * Deliberately pure and DB-free: `synthesis_stage.ts` (the only caller) feeds
 * it events and lint verdicts as they happen on the live stream, and reads
 * `snapshot()` once at turn end to build the `llm_usage_events` row (see
 * `./synthesis_observation.ts`) and the always-on `synthesis_turn_metrics`
 * flag. Being pure/DB-free is also what makes this file's tests real per-call
 * assertions rather than mocked-DB theatre.
 */

import type { ChatEvent } from '@/lib/providers/types'
import { ZERO_USAGE, type TokenUsage } from '@/lib/llm/observability/types'

export interface RegisterLintTotals {
  /** Every `lintReaderProse` call this turn (i.e. every text delta linted). */
  delta_calls: number
  /** Calls where `leakCount > 0` — the lint actually rewrote/redacted something. */
  fires: number
  /** Sum of `leakCount` across all firing calls. */
  leaks_total: number
}

export interface DeltaCommitLagStats {
  /** Number of blocks whose delta→commit lag was measured this turn. */
  count: number
  total_ms: number
  max_ms: number
}

export interface TurnMetricsSnapshot {
  /** ms from turn start to the first provider event (any type). `null` if none arrived. */
  ttft_ms: number | null
  event_count: number
  events_by_type: Record<string, number>
  /** Largest gap between two consecutive provider events. `null` with fewer than 2 events. */
  max_event_gap_ms: number | null
  usage: TokenUsage
  register_lint: RegisterLintTotals
  delta_commit_lag_ms: DeltaCommitLagStats
  /** Adaptive-pass count this turn (starts at 1; incremented on every real seam). */
  pass_count: number
}

export class TurnMetricsCollector {
  private readonly startedAtMs: number
  private firstEventAtMs: number | null = null
  private lastEventAtMs: number | null = null
  private maxGapMs = 0
  private eventCount = 0
  private readonly eventsByType = new Map<string, number>()
  private usage: TokenUsage = { ...ZERO_USAGE }
  private lintDeltaCalls = 0
  private lintFires = 0
  private lintLeaksTotal = 0
  private lagCount = 0
  private lagTotalMs = 0
  private lagMaxMs = 0
  private passCount = 1

  constructor(startedAtMs: number = Date.now()) {
    this.startedAtMs = startedAtMs
  }

  /** Record one raw provider event. Never mutates or filters the event itself. */
  recordEvent(event: ChatEvent, nowMs: number = Date.now()): void {
    if (this.firstEventAtMs === null) this.firstEventAtMs = nowMs
    if (this.lastEventAtMs !== null) {
      const gap = nowMs - this.lastEventAtMs
      if (gap > this.maxGapMs) this.maxGapMs = gap
    }
    this.lastEventAtMs = nowMs
    this.eventCount += 1
    this.eventsByType.set(event.type, (this.eventsByType.get(event.type) ?? 0) + 1)

    if (event.type === 'usage') {
      this.usage = {
        input_tokens: this.usage.input_tokens + (event.inputTokens ?? 0),
        output_tokens: this.usage.output_tokens + (event.outputTokens ?? 0),
        cache_read_tokens: this.usage.cache_read_tokens + (event.cacheReadTokens ?? 0),
        cache_write_tokens: this.usage.cache_write_tokens + (event.cacheCreationTokens ?? 0),
        // ChatEvent's 'usage' member carries no reasoning-token field today —
        // an honest gap (§N.7 item 6), left at whatever it already was (0,
        // via ZERO_USAGE) rather than invented.
        reasoning_tokens: this.usage.reasoning_tokens,
      }
    }
  }

  /** Record one `lintReaderProse` verdict for this turn. */
  recordRegisterLint(leakCount: number): void {
    this.lintDeltaCalls += 1
    if (leakCount > 0) {
      this.lintFires += 1
      this.lintLeaksTotal += leakCount
    }
  }

  /** Record one block's delta→commit lag (ms from its first delta to its commit). */
  recordDeltaCommitLag(lagMs: number): void {
    if (!Number.isFinite(lagMs) || lagMs < 0) return
    this.lagCount += 1
    this.lagTotalMs += lagMs
    if (lagMs > this.lagMaxMs) this.lagMaxMs = lagMs
  }

  /** Record one real adaptive-pass boundary (mirrors `assembler.passId += 1`). */
  recordPass(): void {
    this.passCount += 1
  }

  snapshot(): TurnMetricsSnapshot {
    return {
      ttft_ms: this.firstEventAtMs === null ? null : this.firstEventAtMs - this.startedAtMs,
      event_count: this.eventCount,
      events_by_type: Object.fromEntries(this.eventsByType),
      max_event_gap_ms: this.eventCount > 1 ? this.maxGapMs : null,
      usage: { ...this.usage },
      register_lint: {
        delta_calls: this.lintDeltaCalls,
        fires: this.lintFires,
        leaks_total: this.lintLeaksTotal,
      },
      delta_commit_lag_ms: { count: this.lagCount, total_ms: this.lagTotalMs, max_ms: this.lagMaxMs },
      pass_count: this.passCount,
    }
  }
}
