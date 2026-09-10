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
 * Compared case-insensitively and separator-insensitively, so `chart_id`,
 * `chartId`, `chartID` and `Chart-Id` are one key, not four bypasses — and, on a
 * word boundary, so is any qualified spelling (`subject_chart_id`,
 * `sourceChartId`). See `compactKey`/`delimitedKey` for why those are two
 * different comparisons rather than one.
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

/**
 * Two normal forms, because the two tests below need different things.
 *
 * `compactKey` removes every separator: `chart_id`, `chartId`, `chartID`,
 * `Chart-Id` and `chartid` all become `chartid`. That is the right form for an
 * EXACT comparison — it collapses spelling variants of the same key.
 *
 * `delimitedKey` keeps a separator at every word boundary, inserting one at a
 * camelCase transition first: `sourceChartId` → `source_chart_id`. That is the
 * right form for a SUFFIX comparison, and using `compactKey` for it was a real
 * false positive an internal review found and an independent one confirmed:
 * with `uid` in the declared set, `'fluid'.endsWith('uid')` is true, so ordinary
 * words — `fluid`, `liquid`, `druid`, `squid`, `guid` — were silently stripped
 * from tool call params whenever they appeared as a key name. (`abuser_id`
 * against `user_id` is the same defect one key over.) Testing on a delimited
 * boundary means a qualified identity key still matches and a word that merely
 * ENDS in those letters does not.
 *
 * The one spelling this narrows away from is a fully-run-together QUALIFIED key
 * (`subjectchartid`), which has no boundary to test and is not a spelling any
 * producer here emits — `subject_chart_id` and `subjectChartId` both still
 * match. Written down rather than left for the next reviewer to rediscover.
 */
function compactKey(key: string): string {
  return key.toLowerCase().replace(/[^a-z0-9]/g, '')
}

function delimitedKey(key: string): string {
  return key
    .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
}

const COMPACT_IDENTITY_KEYS: ReadonlySet<string> = new Set(
  IDENTITY_PARAM_KEYS.map(compactKey),
)
const DELIMITED_IDENTITY_KEYS: readonly string[] = IDENTITY_PARAM_KEYS.map(delimitedKey)

/**
 * True for an identity key, INCLUDING qualified spellings.
 *
 * Exact-set matching alone let `subject_chart_id` and `target_chart_id` through,
 * which is narrower than the docstring's claim of closure at the plan boundary.
 * A key that ENDS in a declared identity key carries the same authority claim
 * regardless of what qualifies it, so the suffix test is the honest one — but it
 * has to be a suffix on a WORD boundary, not on raw characters. See the two
 * normal forms above for the words that were being eaten before it was.
 */
function isIdentityKey(key: string): boolean {
  if (COMPACT_IDENTITY_KEYS.has(compactKey(key))) return true
  const n = delimitedKey(key)
  for (const known of DELIMITED_IDENTITY_KEYS) {
    if (n === known || n.endsWith(`_${known}`)) return true
  }
  return false
}

/**
 * How deep `rejectIdentityParams` walks before it stops and FAILS CLOSED.
 *
 * A cap has to exist: `toolCall.input` is model-chosen and the walk must
 * terminate on a self-referential object. What the cap must NOT do is what it
 * did before — return `[]` at the boundary, i.e. silently allow whatever sits
 * below it, which is a fail-OPEN gap in a control whose entire job is closing
 * one. Past the cap the subtree is now REMOVED and the removal is reported.
 *
 * 6 rather than 4 because the cost of the cap is now borne by legitimate params
 * (a deep-but-honest subtree is dropped), so the cap should sit well clear of
 * anything a real tool schema uses. No capability in the manifest nests tool
 * parameters anywhere near this deep; six levels is already far past
 * `{filter: {range: {start: …}}}`-shaped input.
 */
const MAX_PARAM_DEPTH = 6

/**
 * Path marker for a subtree dropped because it sat past `MAX_PARAM_DEPTH`.
 *
 * A distinct marker rather than a bare key name so an audit can tell "an
 * identity key was rejected here" from "this branch was never inspected and was
 * therefore removed" — two different facts that must not read as one.
 */
export const PARAM_DEPTH_EXCEEDED_MARKER = '<beyond_max_depth>'

/**
 * Strip every identity key whose value is not the authenticated chart, at any
 * nesting depth — THROUGH ARRAYS AS WELL AS OBJECTS — mutating in place.
 * Returns the rejected key paths.
 *
 * Exported because the plan is NOT the only place model-chosen params reach a
 * tool. In the agentic loop `toolCall.input` — chosen by the model, after
 * injected content has entered its context — is forwarded verbatim as tool
 * params (`synthesis/mcp_tool_executor.ts`), and `tool_name_bridge.ts`
 * overwrites `args.chart_id` ONLY for `per_chart` capabilities. For any other
 * scope a foreign identity param would survive into the handler. Closing the
 * plan and leaving that path open would have been a control that guards the
 * quieter half of its own attack surface.
 *
 * ── TWO FAIL-OPEN GAPS THAT USED TO CONTRADICT THE LINE ABOVE ───────────────
 * "at any nesting depth" was a claim, not a description, and a re-verification
 * reproduced both halves of the gap:
 *
 *   1. ARRAYS WERE NEVER WALKED. The guard bailed on `Array.isArray(params)`
 *      before recursing, so `{filters: [{chart_id: <foreign>}]}` — an entirely
 *      ordinary shape for a filter list — survived completely untouched. Arrays
 *      are now walked element-wise at `depth + 1`, and an element's path reads
 *      `filters[0].chart_id` so the report points at the actual location.
 *   2. EXCEEDING THE DEPTH CAP RETURNED `[]`, i.e. "nothing to reject here" —
 *      indistinguishable from a clean subtree, and a silent allow for whatever
 *      sat below. It now removes the subtree and reports the removal, which is
 *      the only reading of the cap consistent with what this function is for.
 *      See `MAX_PARAM_DEPTH` for why the number moved with the semantics.
 */
export function rejectIdentityParams(
  params: unknown,
  authenticatedChartId: string,
  depth = 0,
): string[] {
  if (!params || typeof params !== 'object') return []

  const rejected: string[] = []

  if (Array.isArray(params)) {
    for (let i = 0; i < params.length; i++) {
      const element = params[i]
      if (!element || typeof element !== 'object') continue
      if (depth + 1 > MAX_PARAM_DEPTH) {
        params[i] = null
        rejected.push(`[${i}].${PARAM_DEPTH_EXCEEDED_MARKER}`)
        continue
      }
      for (const k of rejectIdentityParams(element, authenticatedChartId, depth + 1)) {
        rejected.push(`[${i}]${k.startsWith('[') ? '' : '.'}${k}`)
      }
    }
    return rejected
  }

  const record = params as Record<string, unknown>
  for (const key of Object.keys(record)) {
    const value = record[key]
    if (isIdentityKey(key)) {
      // An identity key whose value IS the authenticated chart is redundant,
      // not hostile — the bridge injects the same value anyway. Left in place
      // so this control cannot be the thing that changes a legitimate call.
      if (typeof value === 'string' && value.toLowerCase() === authenticatedChartId.toLowerCase()) {
        continue
      }
      delete record[key]
      rejected.push(key)
      continue
    }
    if (value && typeof value === 'object') {
      if (depth + 1 > MAX_PARAM_DEPTH) {
        delete record[key]
        rejected.push(`${key}.${PARAM_DEPTH_EXCEEDED_MARKER}`)
        continue
      }
      const nested = rejectIdentityParams(value, authenticatedChartId, depth + 1)
      // An array child reports `[0].k`; gluing a `.` in front of that would read
      // `filters.[0].k`, which is not a path anyone writes.
      rejected.push(...nested.map((k) => `${key}${k.startsWith('[') ? '' : '.'}${k}`))
    }
  }
  return rejected
}

export interface PlanClosureFinding {
  code:
    | 'plan_identity_param_rejected'
    | 'plan_param_depth_exceeded'
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
  /**
   * Subtrees removed for sitting past `MAX_PARAM_DEPTH` — counted SEPARATELY
   * from `rejected_param_count` because the two are different facts: one says
   * "an identity key was found and removed", the other says "this branch was
   * never inspected, so it was removed rather than allowed". Reporting the
   * second as the first would be a status signal describing a check that did
   * not run (§N.8).
   */
  depth_exceeded_count: number
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
  let depthExceeded = 0
  let flagged = 0

  for (const tc of plan.tool_calls ?? []) {
    if (!isRegisteredTool(tc.tool_name)) {
      findings.push({ code: 'plan_unregistered_tool_flagged', tool_name: tc.tool_name })
      flagged += 1
    }

    for (const key of rejectIdentityParams(tc.params, authenticatedChartId)) {
      if (key.endsWith(PARAM_DEPTH_EXCEEDED_MARKER)) {
        findings.push({ code: 'plan_param_depth_exceeded', tool_name: tc.tool_name, param_key: key })
        depthExceeded += 1
        continue
      }
      findings.push({ code: 'plan_identity_param_rejected', tool_name: tc.tool_name, param_key: key })
      rejected += 1
    }
  }

  return {
    findings,
    rejected_param_count: rejected,
    depth_exceeded_count: depthExceeded,
    flagged_tool_count: flagged,
  }
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
