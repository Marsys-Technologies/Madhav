import { describe, expect, it } from 'vitest'
import type { PipelinePlan } from '@/lib/pipeline/types'
import { getCatalog } from '../../retrieval/registry/catalog'
import { compileCapabilityKnowledge } from '../../retrieval/registry/knowledge/compiler'
import { resolveToolUri } from '../../retrieval/registry/tool_name_bridge'
import { compileInquiryContract } from './compiler'
import { adoptInquiryPlanItems, managedPlanToAiInquiryProposal } from './managed_bridge'

const scope = {
  intent: 'domain_assessment', domains: ['wealth'], width: 'broad', depth: 'deep',
  horizon: 'far', intervention: 'none', entitlement: 'native',
} as const

function managedPlan(): PipelinePlan {
  return {
    query_class: 'holistic', query_intent_summary: 'deep wealth mechanisms and timing',
    asset_bundle: [], tool_calls: [{ tool_name: 'assess_wealth', params: { invented: true }, token_budget: 400, priority: 2, reason: 'assess wealth' }],
    scope_tuple: scope, domains: ['wealth'], planning_rationale: 'Check promise against inhibitors.',
  } as unknown as PipelinePlan
}

describe('managed Inquiry Contract bridge', () => {
  const snapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-13T00:00:00.000Z')

  it('keeps semantic obligations channel-neutral while enforcing channel-specific execution', () => {
    const ai = managedPlanToAiInquiryProposal(managedPlan())
    const platform = compileInquiryContract({ snapshot, chart_id: 'chart-1', question: 'wealth outlook', scope_tuple: scope, ai_proposal: ai, execution_channel: 'platform_internal' })
    const raw = compileInquiryContract({ snapshot, chart_id: 'chart-1', question: 'wealth outlook', scope_tuple: scope, ai_proposal: ai, execution_channel: 'mcp_full' })
    expect(raw.semantic_contract_hash).toBe(platform.semantic_contract_hash)
    expect(raw.obligations.map((item) => item.obligation_id)).toEqual(platform.obligations.map((item) => item.obligation_id))
    expect(raw.execution_plan_hash).not.toBe(platform.execution_plan_hash)
    expect(raw.plan_items.filter((item) => item.state === 'ready').every((item) => {
      const binding = snapshot.scus.find((scu) => scu.scu_id === item.scu_id)?.bindings.find((candidate) => candidate.binding_id === item.binding_id)
      return binding?.execution_channels?.includes('mcp_full') === true
    })).toBe(true)
  })

  it('replaces planner-invented params with exact server-compiled action args', () => {
    const plan = managedPlan()
    plan.tool_calls.push({ tool_name: 'query_classical_texts', params: { invented: true }, token_budget: 400, priority: 1, reason: 'planner-only extra' })
    const contract = compileInquiryContract({ snapshot, chart_id: 'chart-1', question: 'wealth outlook', scope_tuple: scope, execution_channel: 'platform_internal' })
    const authorized = adoptInquiryPlanItems(plan, contract)
    const financeItem = contract.plan_items.find((item) => item.scu_id === 'scu.finance.prosperity_assessment')!
    const call = plan.tool_calls.find((item) => item.tool_name === 'assess_wealth')!
    expect(call.params).toEqual(financeItem.args)
    expect(call.params).not.toHaveProperty('invented')
    expect(authorized).toContain('assess_wealth')
    expect(plan.tool_calls.every((candidate) => contract.plan_items.some((item) =>
      item.state === 'ready' && item.binding_id === `registry:${resolveToolUri(candidate.tool_name)}`,
    ))).toBe(true)
    expect(plan.tool_calls.some((candidate) => candidate.tool_name === 'query_classical_texts')).toBe(false)
  })
})
