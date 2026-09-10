/**
 * Paripraśna injection containment — TOOL-SEQUENCE ANOMALY TRACE
 * (lane G1-G, PPR-13).
 *
 * PPR-13: "tool-sequence anomalies MUST be trace-flagged."
 *
 * ── FLAG, NOT BLOCK — AND THE RULING SAYS SO IN THOSE WORDS ─────────────────
 * TA §14A.1's fourth required control reads, verbatim: "Tool-sequence anomaly
 * logging: a plan that reaches for unusual capability combinations is worth a
 * **trace flag, not a block**." This monitor therefore never refuses a call, and
 * nothing that consumes it may turn it into a refusal without amending that
 * ruling first. The reason the ruling is right: "unusual" is a heuristic, and a
 * heuristic that blocks turns a false positive into a lost reading. A flag costs
 * nothing when wrong and is the thing an investigation actually needs.
 *
 * ── THE SURFACE THIS WATCHES, WHICH IS NOT THE ONE YOU EXPECT ───────────────
 * Retrieval pass 1 (`evidence_stage.ts`) iterates `toolsAuthorized` — it cannot
 * call an unplanned tool, because the list IS the plan.
 *
 * The AGENTIC LOOP can. `synthesis_stage.ts` declares only the authorized tools
 * to the provider (`buildChatToolsFromNames(queryPlan.tools_authorized)`), but
 * the executor behind it does not re-check: `synthesis/mcp_tool_executor.ts`
 * resolves `getToolByName(toolCall.name)` and dispatches whatever came back from
 * the model, with no comparison against the authorized set. So the sequence of
 * tools a turn ACTUALLY executes is not guaranteed to equal the sequence the
 * plan authorized, and the gap widens exactly when it matters: after a tool
 * result carrying injected content has entered the loop's context.
 *
 * That gap is what `unplanned_tool` detects. Note precisely what the detection
 * is and is not: it is evidence that the executed sequence diverged from the
 * authorized one. It is NOT proof of injection — a provider quirk or a stale
 * tool alias produces the same signal — and the flag is worded accordingly.
 *
 * ── THE HIGHEST-SIGNAL DETECTOR IS THE FORBIDDEN-SET ONE ────────────────────
 * `excluded_capability_attempted` fires when the loop reaches for a capability
 * the pipeline DELIBERATELY removed this turn — an HS-1/HS-4 mortality
 * capability stripped by `applyCapabilityExclusion`, or one the NO-LEAKAGE
 * filter took out. There is no benign explanation for that combination: the
 * capability was in the registry, was considered, and was taken away, and
 * something asked for it anyway. It is ranked `error`, not `warn`.
 */

export type ToolSequenceAnomalyCode =
  | 'unplanned_tool'
  | 'excluded_capability_attempted'
  | 'repeat_call_excess'
  | 'sequence_length_excess'

export interface ToolSequenceAnomaly {
  code: ToolSequenceAnomalyCode
  /** Server-log-only (gate 11 [integrity]): never placed on the wire. */
  tool_name: string
  /** 1-based position in the executed sequence, for reconstructing order. */
  at_call_index: number
}

/** Defaults are documented where they are declared, not in a config file nobody reads. */
export const DEFAULT_MAX_CALLS_PER_TOOL = 6
/**
 * Floor for the total-call ceiling. The ceiling is `max(this, authorized × 3)`:
 * proportional to the plan so a legitimately wide floor is not penalised, with a
 * floor so a one-tool plan still gets a sane allowance for adaptive re-entry.
 * `DEEP_DIVE_MAX_ITERATIONS` is 16 and each iteration may carry several calls,
 * so 24 is deliberately above any normal deep-dive turn rather than at its edge.
 */
export const MIN_TOTAL_CALL_CEILING = 24

export interface ToolSequenceMonitorConfig {
  /** The plan's authorized tool names, AFTER floors and all exclusions. */
  authorized: readonly string[]
  /**
   * Capabilities deliberately removed this turn (safety exclusion, NO-LEAKAGE).
   * A call to one of these is the strongest single signal in this module.
   */
  forbidden?: readonly string[]
  maxCallsPerTool?: number
  totalCallCeiling?: number
}

/**
 * Records the executed tool sequence and reports how it diverged from the
 * authorized one. Pure in-memory, per turn; never touches a database and never
 * refuses a call.
 */
export class ToolSequenceMonitor {
  private readonly authorized: ReadonlySet<string>
  private readonly forbidden: ReadonlySet<string>
  private readonly maxCallsPerTool: number
  private readonly totalCallCeiling: number
  private readonly counts = new Map<string, number>()
  private totalCalls = 0
  /** Codes already raised, so a runaway loop yields one finding per code, not N. */
  private readonly raised = new Set<string>()
  readonly anomalies: ToolSequenceAnomaly[] = []

  constructor(config: ToolSequenceMonitorConfig) {
    this.authorized = new Set(config.authorized ?? [])
    this.forbidden = new Set(config.forbidden ?? [])
    this.maxCallsPerTool = config.maxCallsPerTool ?? DEFAULT_MAX_CALLS_PER_TOOL
    this.totalCallCeiling =
      config.totalCallCeiling ?? Math.max(MIN_TOTAL_CALL_CEILING, this.authorized.size * 3)
  }

  /** Record one executed tool call. Never throws; never blocks. */
  record(toolName: string): void {
    this.totalCalls += 1
    const name = typeof toolName === 'string' ? toolName : String(toolName)
    const n = (this.counts.get(name) ?? 0) + 1
    this.counts.set(name, n)

    // Forbidden first — it is the strictly stronger statement about the same
    // call, and reporting both would double-count one event.
    if (this.forbidden.has(name)) {
      this.raise('excluded_capability_attempted', name)
    } else if (!this.authorized.has(name)) {
      this.raise('unplanned_tool', name)
    }

    if (n === this.maxCallsPerTool + 1) this.raise('repeat_call_excess', name)
    if (this.totalCalls === this.totalCallCeiling + 1) this.raise('sequence_length_excess', name)
  }

  private raise(code: ToolSequenceAnomalyCode, toolName: string): void {
    // Per (code, tool) — a second unplanned tool is genuinely new information;
    // the same unplanned tool eleven times is not.
    const key = `${code}:${toolName}`
    if (this.raised.has(key)) return
    this.raised.add(key)
    this.anomalies.push({ code, tool_name: toolName, at_call_index: this.totalCalls })
  }

  get anomalous(): boolean {
    return this.anomalies.length > 0
  }

  /**
   * The trace flag itself — the wire/receipt-safe projection.
   *
   * Carries CODES and COUNTS only. Raw capability names stay server-log-only,
   * the same gate-11 discipline `plan_stage.ts` follows for the NO-LEAKAGE and
   * mortality-exclusion flags: a reader must never be able to read an internal
   * tool name out of a safety flag.
   */
  traceFlag(): {
    anomalous: boolean
    anomaly_count: number
    codes: ToolSequenceAnomalyCode[]
    total_calls: number
  } {
    return {
      anomalous: this.anomalous,
      anomaly_count: this.anomalies.length,
      codes: Array.from(new Set(this.anomalies.map((a) => a.code))),
      total_calls: this.totalCalls,
    }
  }

  /**
   * `error` when a deliberately-excluded capability was reached for, `warn`
   * otherwise. The level is computed from what fired, not fixed, so the two
   * very different situations this monitor can report do not arrive looking
   * identical in a log.
   */
  severity(): 'warn' | 'error' {
    return this.anomalies.some((a) => a.code === 'excluded_capability_attempted') ? 'error' : 'warn'
  }
}
