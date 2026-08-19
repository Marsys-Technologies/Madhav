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
import { assertPlanSchemaIsClosed, closePlanAgainstInjection, IDENTITY_PARAM_KEYS } from '../plan_closure'

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
