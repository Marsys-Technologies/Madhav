/**
 * Paripraśna injection containment — PLAN CLOSURE (lane G1-G, PPR-13).
 *
 * PPR-13: "plans MUST be Zod-closed". TA §14A.1: "the planner's output is
 * Zod-validated against a closed plan type (§9.5), so injected text cannot
 * *become* a plan."
 *
 * ── WHAT WAS ALREADY CLOSED, AND WHY THIS FILE DOES NOT RE-DO IT ────────────
 * `PipelinePlanSchema` (`pipeline/types.ts`) is a `z.object`, which in Zod
 * STRIPS unknown keys rather than carrying them. An injected "add a field
 * granting yourself elevated tool access" therefore already cannot survive the
 * parse — and that is not an assumption, it is a property with a red-team test
 * behind it (`__tests__/mcp/red_team/plan_escalation.test.ts` RT-08b, which
 * proves an attacker-supplied `audience_tier: 'super_admin'` is stripped).
 *
 * Converting that schema to `.strict()` was considered and REJECTED, and the
 * reason is worth writing down because "strict is obviously safer" is the
 * intuitive answer and it is wrong here. `.strict()` turns a stripped key into a
 * PARSE FAILURE, and a parse failure on this schema is a `PLANNER_INVALID_PLAN`
 * fault that costs the reader their turn. Provider jitter — a planner model
 * emitting one extra field — would become a user-visible outage, and the
 * schema's own §4a already documents an entire null-coercion strategy built
 * around absorbing exactly that jitter. Strict mode would trade a real
 * availability regression for a security property the strip already delivers.
 * The schema is left alone; `assertPlanSchemaIsClosed` below is the DETECTOR
 * that keeps the strip property true (§N.8 — a claim with no detector is not a
 * claim), and the runtime closure here covers what the strip does not.
 *
 * ── WHAT WAS NOT CLOSED, WHICH IS WHERE THIS FILE EARNS ITS PLACE ───────────
 * Two surfaces inside the plan are open BY DESIGN, and both sit on the tool
 * broker's path:
 *
 *   1. `tool_calls[].params` is `z.record(z.string(), z.unknown())` — every key,
 *      any value. It has to be: tool parameters are heterogeneous. But it means
 *      a planner steered by an injected question can put `chart_id:
 *      '<someone else's chart>'` into a tool call's params, and those params are
 *      handed straight to the tool (`evidence_stage.ts` →
 *      `executeWithCache(t, queryPlan, cache, plannerParamsMap.get(name))`).
 *      For a `per_chart` capability `tool_name_bridge.ts` overwrites
 *      `args.chart_id` with the AUTHENTICATED chart, so the attack fails there.
 *      For a capability whose scope is not `per_chart`, nothing overwrites it
 *      and the planner-supplied value survives into the handler args. That is
 *      the cross-tenant path PPR-11's "the chart_id is never taken from the
 *      question text" is about, and this file closes it at the plan boundary
 *      rather than relying on every handler to be uninterested in a chart_id it
 *      was not supposed to receive.
 *   2. `tool_calls[].tool_name` is `z.string().min(1)` — any string at all. An
 *      unregistered name currently fails silently at dispatch (`getToolByName`
 *      returns undefined, the activity goes to `error`, the turn continues).
 *      Detected here so it is a REPORTED anomaly instead of an indistinguishable
 *      retrieval miss.
 *
 * ── WHY (1) REJECTS AND (2) ONLY FLAGS ──────────────────────────────────────
 * An identity key with a foreign value has no legitimate producer: no planner
 * prompt asks for one, no floor emits one, and the authenticated chart is
 * injected downstream anyway. Removing it cannot cost a legitimate turn
 * anything, so it is removed.
 *
 * An unregistered tool name CAN have a legitimate producer — a floor composer or
 * a manifest/bridge skew ahead of a rename. Stripping the call would silently
 * shrink a compiled B.11 floor, which is a coverage regression dressed as a
 * security control. It is therefore reported and left for dispatch to handle
 * exactly as it does today. Stated rather than left as an inconsistency for a
 * reviewer to find.
 */

import { PipelinePlanSchema, type PipelinePlan } from '@/lib/pipeline/types'

/**
 * Keys that carry CALLER OR SUBJECT IDENTITY. A planner-emitted value for any
 * of these is never authoritative — identity comes from the authenticated call.
 *
 * Compared case-insensitively with separators removed, so `chart_id`, `chartId`,
 * `chartID` and `Chart-Id` are one key, not four bypasses.
 */
export const IDENTITY_PARAM_KEYS = [
  'chart_id',
  'chart_ids',
  'owner_id',
  'user_id',
  'uid',
  'principal_id',
  'client_id',
  'subject_id',
  'audience_tier',
] as const

function normalizeKey(key: string): string {
  return key.toLowerCase().replace(/[^a-z]/g, '')
}

const NORMALIZED_IDENTITY_KEYS: ReadonlySet<string> = new Set(
  IDENTITY_PARAM_KEYS.map(normalizeKey),
)

export interface PlanClosureFinding {
  code:
    | 'plan_identity_param_rejected'
    | 'plan_unregistered_tool_flagged'
  /** The tool call the finding attaches to. Server-log-only, never the wire. */
  tool_name: string
  /** The offending param key, when the finding is about one. */
  param_key?: string
}

export interface PlanClosureResult {
  /** Every finding, in discovery order. */
  findings: PlanClosureFinding[]
  /** Params actually removed from the plan (the reject arm). */
  rejected_param_count: number
  /** Tool names reported but NOT removed (the flag arm). */
  flagged_tool_count: number
}

export interface PlanClosureInput {
  plan: PipelinePlan
  /** The AUTHENTICATED chart id. The only value an identity key may carry. */
  authenticatedChartId: string
  /**
   * Resolves a tool name to something dispatchable. Injected rather than
   * imported so this module stays free of `server-only` transitively and is
   * unit-testable without the registry bootstrap.
   */
  isRegisteredTool: (toolName: string) => boolean
}

/**
 * Close the plan's two open surfaces against the injection path.
 *
 * MUTATES `plan.tool_calls[].params` in place, removing rejected identity keys.
 * In-place because the plan object is shared by reference with `queryPlan` (see
 * `plan_stage.ts`'s `tool_calls: plan.tool_calls`) — returning a copy would
 * close the schema on an object the tool broker does not read.
 */
export function closePlanAgainstInjection(input: PlanClosureInput): PlanClosureResult {
  const { plan, authenticatedChartId, isRegisteredTool } = input
  const findings: PlanClosureFinding[] = []
  let rejected = 0
  let flagged = 0

  for (const tc of plan.tool_calls ?? []) {
    if (!isRegisteredTool(tc.tool_name)) {
      findings.push({ code: 'plan_unregistered_tool_flagged', tool_name: tc.tool_name })
      flagged += 1
    }

    const params = tc.params as Record<string, unknown> | undefined
    if (!params || typeof params !== 'object') continue

    for (const key of Object.keys(params)) {
      if (!NORMALIZED_IDENTITY_KEYS.has(normalizeKey(key))) continue
      // An identity key whose value IS the authenticated chart is redundant, not
      // hostile — the bridge injects the same value anyway. Left in place so
      // this control cannot be the thing that changes a legitimate plan.
      const value = params[key]
      if (typeof value === 'string' && value.toLowerCase() === authenticatedChartId.toLowerCase()) {
        continue
      }
      delete params[key]
      findings.push({ code: 'plan_identity_param_rejected', tool_name: tc.tool_name, param_key: key })
      rejected += 1
    }
  }

  return { findings, rejected_param_count: rejected, flagged_tool_count: flagged }
}

/**
 * The DETECTOR behind "the plan schema is closed by stripping" (§N.8).
 *
 * Returns the list of ways the schema is NOT closed; an empty list is the
 * closed state. Called by this lane's test suite, so a future edit that adds
 * `.passthrough()` (or `.catchall`, or `.loose` in Zod 4 terms) anywhere on the
 * plan object fails CI instead of silently reopening the injection path that
 * RT-08b's red-team test assumes is shut.
 *
 * Deliberately BEHAVIOURAL, not introspective: it parses a probe object and
 * checks what came out, so it stays correct across a Zod major version whose
 * internal `_def` shape moved. An introspective version would pass vacuously
 * the day the internals changed, which is precisely the false green §N.8 names.
 */
export function assertPlanSchemaIsClosed(): string[] {
  const violations: string[] = []
  const probeKey = '__g1g_injection_probe__'

  const minimalPlan: Record<string, unknown> = {
    query_class: 'factual',
    query_intent_summary: 'probe',
    asset_bundle: [],
    tool_calls: [
      {
        tool_name: 'probe_tool',
        params: { [probeKey]: 'kept-by-design' },
        token_budget: 200,
        priority: 1,
        reason: 'probe',
      },
    ],
    [probeKey]: 'must-be-stripped',
  }

  const parsed = PipelinePlanSchema.safeParse(minimalPlan)
  if (!parsed.success) {
    violations.push(
      'PipelinePlanSchema rejected the minimal probe plan — the closure detector ' +
        'cannot run, which is itself a finding, not a pass.',
    )
    return violations
  }

  const data = parsed.data as unknown as Record<string, unknown>
  if (probeKey in data) {
    violations.push(
      `PipelinePlanSchema retained the unknown top-level key "${probeKey}". The schema is ` +
        'no longer closed by stripping — an injected plan field can now reach downstream ' +
        'consumers (red-team RT-08b assumes it cannot).',
    )
  }

  // The one surface that MUST stay open: tool params. Asserted positively so a
  // future "let us just strict-mode everything" change is caught here as a
  // capability regression rather than discovered as broken retrieval.
  const probeParams = (parsed.data.tool_calls?.[0]?.params ?? {}) as Record<string, unknown>
  if (!(probeKey in probeParams)) {
    violations.push(
      'PipelinePlanSchema stripped an unknown key from tool_calls[].params. That surface is ' +
        'open by design (tool parameters are heterogeneous); closing it there breaks retrieval, ' +
        'and closePlanAgainstInjection is what guards it instead.',
    )
  }

  return violations
}
