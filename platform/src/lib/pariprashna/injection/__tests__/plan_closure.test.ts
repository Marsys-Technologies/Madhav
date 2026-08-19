/**
 * Lane G1-G · PPR-13 item 2 — THE PLAN, CLOSED AGAINST THE INJECTION PATH.
 *
 * Two claims, tested separately because they have different mechanisms:
 *   · the SCHEMA is closed by stripping (asserted behaviourally, so it stays
 *     true across a Zod version bump — see `assertPlanSchemaIsClosed`);
 *   · the two surfaces the schema leaves open BY DESIGN — `tool_calls[].params`
 *     and `tool_calls[].tool_name` — are closed at runtime instead.
 */
import { describe, it, expect } from 'vitest'

import type { PipelinePlan } from '@/lib/pipeline/types'
import {
  assertPlanSchemaIsClosed,
  closePlanAgainstInjection,
  rejectIdentityParams,
  IDENTITY_PARAM_KEYS,
} from '../plan_closure'

const MINE = '482012f1-710e-4a25-994a-93821f5871aa'
const THEIRS = '1c826d5a-9f3b-4d21-8e77-0a5c4b2e91d0'

function planWith(toolCalls: Array<{ tool_name: string; params: Record<string, unknown> }>): PipelinePlan {
  return {
    query_class: 'factual',
    query_intent_summary: 'test',
    asset_bundle: [],
    tool_calls: toolCalls.map((tc) => ({ ...tc, token_budget: 200, priority: 1 as const, reason: 'test' })),
  } as unknown as PipelinePlan
}

const allRegistered = () => true

describe('the schema-closure detector (§N.8 — the claim needs a detector)', () => {
  it('reports the live PipelinePlanSchema as closed', () => {
    expect(assertPlanSchemaIsClosed()).toEqual([])
  })
})

describe('identity params — REJECTED, because no legitimate producer emits one', () => {
  it('strips a foreign chart_id an injected question steered the planner into emitting', () => {
    const plan = planWith([{ tool_name: 'ganita_dashas_get', params: { chart_id: THEIRS, limit: 5 } }])
    const r = closePlanAgainstInjection({ plan, authenticatedChartId: MINE, isRegisteredTool: allRegistered })

    expect(plan.tool_calls[0].params).toEqual({ limit: 5 })
    expect(r.rejected_param_count).toBe(1)
    expect(r.findings[0]).toMatchObject({ code: 'plan_identity_param_rejected', param_key: 'chart_id' })
  })

  it('LEAVES the authenticated chart_id in place — this control must not break a legal plan', () => {
    const plan = planWith([{ tool_name: 't', params: { chart_id: MINE } }])
    const r = closePlanAgainstInjection({ plan, authenticatedChartId: MINE, isRegisteredTool: allRegistered })
    expect(plan.tool_calls[0].params).toEqual({ chart_id: MINE })
    expect(r.rejected_param_count).toBe(0)
  })

  it('matches the authenticated id case-insensitively', () => {
    const plan = planWith([{ tool_name: 't', params: { chart_id: MINE.toUpperCase() } }])
    closePlanAgainstInjection({ plan, authenticatedChartId: MINE, isRegisteredTool: allRegistered })
    expect(plan.tool_calls[0].params).toHaveProperty('chart_id')
  })

  it('catches every casing/separator spelling of an identity key', () => {
    for (const spelling of ['chart_id', 'chartId', 'chartID', 'Chart-Id', 'CHART_ID']) {
      const plan = planWith([{ tool_name: 't', params: { [spelling]: THEIRS } }])
      closePlanAgainstInjection({ plan, authenticatedChartId: MINE, isRegisteredTool: allRegistered })
      expect(plan.tool_calls[0].params, spelling).toEqual({})
    }
  })

  it('covers the whole declared identity-key set, not just chart_id', () => {
    for (const key of IDENTITY_PARAM_KEYS) {
      const plan = planWith([{ tool_name: 't', params: { [key]: 'attacker-supplied' } }])
      const r = closePlanAgainstInjection({ plan, authenticatedChartId: MINE, isRegisteredTool: allRegistered })
      expect(r.rejected_param_count, key).toBe(1)
    }
  })

  it('rejects a non-string identity value too (an array of chart ids)', () => {
    const plan = planWith([{ tool_name: 't', params: { chart_ids: [MINE, THEIRS] } }])
    const r = closePlanAgainstInjection({ plan, authenticatedChartId: MINE, isRegisteredTool: allRegistered })
    expect(plan.tool_calls[0].params).toEqual({})
    expect(r.rejected_param_count).toBe(1)
  })

  it('leaves ordinary retrieval params completely alone', () => {
    const params = { planet: 'Saturn', house: 10, varga: 'D10', limit: 20, forward_looking: true }
    const plan = planWith([{ tool_name: 't', params: { ...params } }])
    const r = closePlanAgainstInjection({ plan, authenticatedChartId: MINE, isRegisteredTool: allRegistered })
    expect(plan.tool_calls[0].params).toEqual(params)
    expect(r.findings).toEqual([])
  })

  it('mutates IN PLACE, because queryPlan shares the same tool_calls array', () => {
    const plan = planWith([{ tool_name: 't', params: { chart_id: THEIRS } }])
    const sharedRef = plan.tool_calls
    closePlanAgainstInjection({ plan, authenticatedChartId: MINE, isRegisteredTool: allRegistered })
    expect(sharedRef[0].params).toEqual({})
  })
})

describe('rejectIdentityParams — the SECOND door into the same function', () => {
  // `toolCall.input` is model-chosen, arrives after injected content may have
  // entered the loop's context, and reaches the tool as params verbatim. The
  // plan closure never sees it.
  it('strips a foreign identity key from a model-supplied tool input', () => {
    const input: Record<string, unknown> = { chart_id: THEIRS, planet: 'Saturn' }
    expect(rejectIdentityParams(input, MINE)).toEqual(['chart_id'])
    expect(input).toEqual({ planet: 'Saturn' })
  })

  it('reaches a NESTED identity key and reports its path', () => {
    const input: Record<string, unknown> = { filter: { chart_id: THEIRS }, limit: 5 }
    expect(rejectIdentityParams(input, MINE)).toEqual(['filter.chart_id'])
    expect(input).toEqual({ filter: {}, limit: 5 })
  })

  it('catches QUALIFIED spellings exact-set matching missed', () => {
    for (const key of ['subject_chart_id', 'target_chart_id', 'sourceChartId']) {
      const input: Record<string, unknown> = { [key]: THEIRS }
      expect(rejectIdentityParams(input, MINE), key).toEqual([key])
    }
  })

  it('leaves the authenticated chart and ordinary params alone', () => {
    const input: Record<string, unknown> = { chart_id: MINE, filter: { planet: 'Mars' } }
    expect(rejectIdentityParams(input, MINE)).toEqual([])
    expect(input).toEqual({ chart_id: MINE, filter: { planet: 'Mars' } })
  })

  it('is total — null, arrays and primitives do not throw', () => {
    expect(rejectIdentityParams(null, MINE)).toEqual([])
    expect(rejectIdentityParams([1, 2], MINE)).toEqual([])
    expect(rejectIdentityParams('x', MINE)).toEqual([])
  })

  it('terminates on a self-referential params object', () => {
    const input: Record<string, unknown> = { a: {} }
    ;(input.a as Record<string, unknown>).self = input
    expect(() => rejectIdentityParams(input, MINE)).not.toThrow()
  })

  // ── P2: TWO FAIL-OPEN GAPS THE DOCSTRING'S "ANY NESTING DEPTH" DENIED ────
  it('walks ARRAYS — the shape that used to survive completely untouched', () => {
    // The function bailed on `Array.isArray(params)` before recursing, so an
    // ordinary filter list carried a foreign chart id straight through.
    const input: Record<string, unknown> = { filters: [{ chart_id: THEIRS }], limit: 5 }
    expect(rejectIdentityParams(input, MINE)).toEqual(['filters[0].chart_id'])
    expect(input).toEqual({ filters: [{}], limit: 5 })
  })

  it('walks arrays at every position and nested inside each other', () => {
    const input: Record<string, unknown> = {
      groups: [{ ok: 1 }, { inner: { chart_id: THEIRS } }, [{ owner_id: THEIRS }]],
    }
    expect(rejectIdentityParams(input, MINE)).toEqual([
      'groups[1].inner.chart_id',
      'groups[2][0].owner_id',
    ])
    expect(JSON.stringify(input)).not.toContain(THEIRS)
  })

  it('a top-level array of objects is walked, not silently skipped', () => {
    const input: unknown[] = [{ chart_id: THEIRS }]
    expect(rejectIdentityParams(input, MINE)).toEqual(['[0].chart_id'])
    expect(input).toEqual([{}])
  })

  it('an array VALUE on an identity key is rejected, not walked into', () => {
    const input: Record<string, unknown> = { chart_ids: [THEIRS, MINE] }
    expect(rejectIdentityParams(input, MINE)).toEqual(['chart_ids'])
    expect(input).toEqual({})
  })

  it('FAILS CLOSED past the depth cap instead of silently allowing it', () => {
    // Returning `[]` at the cap was indistinguishable from "this subtree is
    // clean" and allowed whatever sat below. The subtree is now removed and the
    // removal reported under its own marker, so an audit can tell "an identity
    // key was found here" from "this branch was never inspected".
    const deep = { a: { b: { c: { d: { e: { f: { g: { chart_id: THEIRS } } } } } } } }
    const input: Record<string, unknown> = deep
    const rejected = rejectIdentityParams(input, MINE)
    expect(rejected).toEqual(['a.b.c.d.e.f.g.<beyond_max_depth>'])
    expect(JSON.stringify(input)).not.toContain(THEIRS)
  })

  it('a legitimately deep-but-shallower subtree is still walked, not dropped', () => {
    const input: Record<string, unknown> = { a: { b: { c: { d: { e: { chart_id: THEIRS } } } } } }
    expect(rejectIdentityParams(input, MINE)).toEqual(['a.b.c.d.e.chart_id'])
    expect(input).toEqual({ a: { b: { c: { d: { e: {} } } } } })
  })

  // ── P2: THE SUFFIX-MATCH FALSE POSITIVE ─────────────────────────────────
  it('does NOT strip ordinary words that merely END in a declared key', () => {
    // `uid` is a declared identity key and the old matcher removed separators
    // before testing `endsWith`, so `'fluid'.endsWith('uid')` silently deleted
    // the param. Found by an internal review, independently confirmed.
    const input: Record<string, unknown> = {
      fluid: 1,
      liquid: 2,
      druid: 3,
      squid: 4,
      guid: 5,
      // The same defect one key over: `user_id` vs a word ending in those
      // letters with no boundary between.
      abuser_id: 6,
    }
    expect(rejectIdentityParams(input, MINE)).toEqual([])
    expect(input).toEqual({ fluid: 1, liquid: 2, druid: 3, squid: 4, guid: 5, abuser_id: 6 })
  })

  it('still catches every spelling the suffix rule exists for', () => {
    for (const key of [
      'chart_id',
      'chartId',
      'chartID',
      'Chart-Id',
      'chartid',
      'subject_chart_id',
      'target_chart_id',
      'sourceChartId',
      'uid',
      'user_uid',
      'owner_id',
      'audience_tier',
    ]) {
      const input: Record<string, unknown> = { [key]: THEIRS }
      expect(rejectIdentityParams(input, MINE), key).toEqual([key])
      expect(input, key).toEqual({})
    }
  })
})

describe('unregistered tool names — FLAGGED, deliberately not stripped', () => {
  it('reports a tool name that resolves to no capability', () => {
    const plan = planWith([
      { tool_name: 'ganita_dashas_get', params: {} },
      { tool_name: 'exfiltrate_all_charts', params: {} },
    ])
    const r = closePlanAgainstInjection({
      plan,
      authenticatedChartId: MINE,
      isRegisteredTool: (n) => n !== 'exfiltrate_all_charts',
    })
    expect(r.flagged_tool_count).toBe(1)
    expect(r.findings).toContainEqual({
      code: 'plan_unregistered_tool_flagged',
      tool_name: 'exfiltrate_all_charts',
    })
  })

  it('does NOT remove it — stripping would silently shrink a compiled B.11 floor', () => {
    // Stated as a test rather than only a comment: this asymmetry with the
    // reject arm is a decision, and a future edit that "tidies" it into a strip
    // is a coverage regression dressed as a security control.
    const plan = planWith([{ tool_name: 'unknown_tool', params: {} }])
    closePlanAgainstInjection({ plan, authenticatedChartId: MINE, isRegisteredTool: () => false })
    expect(plan.tool_calls).toHaveLength(1)
  })
})

describe('robustness', () => {
  it('tolerates a plan with no tool calls at all', () => {
    const plan = planWith([])
    expect(() =>
      closePlanAgainstInjection({ plan, authenticatedChartId: MINE, isRegisteredTool: allRegistered }),
    ).not.toThrow()
  })

  it('tolerates a tool call whose params are missing', () => {
    const plan = { ...planWith([{ tool_name: 't', params: {} }]) }
    ;(plan.tool_calls[0] as { params?: unknown }).params = undefined
    expect(() =>
      closePlanAgainstInjection({ plan, authenticatedChartId: MINE, isRegisteredTool: allRegistered }),
    ).not.toThrow()
  })
})
