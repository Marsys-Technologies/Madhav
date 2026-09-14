import type { PipelinePlan } from '@/lib/pipeline/types'
import { resolveToolUri } from '@/lib/retrieval/registry/tool_name_bridge'
import type { CapabilityKnowledgeSnapshot } from '@/lib/retrieval/registry/knowledge/types'
import type { AiInquiryProposal, InquiryContract } from './types'

function words(value: unknown): string[] {
  return typeof value === 'string' ? value.toLowerCase().match(/[a-z0-9]+/g) ?? [] : []
}

/** Convert the managed planning model's decomposition into non-authoritative AI hints. */
export function managedPlanToAiInquiryProposal(plan: PipelinePlan): AiInquiryProposal {
  const terms = [...new Set([
    ...words(plan.query_intent_summary),
    ...plan.tool_calls.flatMap((call) => words(call.reason)),
  ])].slice(0, 48)
  const hypotheses = [plan.planning_rationale, plan.synthesis_guidance]
    .filter((value): value is string => typeof value === 'string' && value.trim().length > 0)
    .map((value) => value.trim().slice(0, 500))
  return {
    question_facets: terms.length ? [{ label: 'Managed planner decomposition', terms, materiality: 'supporting' }] : [],
    uncommon_adjacencies: [],
    hypotheses,
  }
}

/**
 * Make server-compiled Inquiry actions authoritative for managed dispatch.
 * The resulting dispatch list contains only ready registry actions authorized
 * by the contract. Existing aliases may be retained for broker compatibility,
 * but unmatched planner calls are removed.
 */
export function adoptInquiryPlanItems(plan: PipelinePlan, contract: InquiryContract): string[] {
  const original = [...plan.tool_calls]
  const adopted: PipelinePlan['tool_calls'] = []
  for (const item of contract.plan_items) {
    if (item.state !== 'ready' || !item.binding_id?.startsWith('registry:')) continue
    const capabilityUri = item.binding_id.slice('registry:'.length)
    const existing = original.find((call) => resolveToolUri(call.tool_name) === capabilityUri)
    const required = contract.obligations.some((obligation) => item.obligation_ids.includes(obligation.obligation_id)
      && obligation.materiality === 'required')
    if (existing) {
      adopted.push({
        ...existing,
        params: { ...item.args },
        priority: required ? 1 : Math.min(existing.priority, 2) as 1 | 2,
        reason: `Inquiry Contract ${item.item_id}`,
      })
    } else {
      adopted.push({
        tool_name: capabilityUri,
        params: { ...item.args },
        token_budget: 800,
        priority: required ? 1 : 2,
        reason: `Inquiry Contract ${item.item_id}`,
      })
    }
  }
  plan.tool_calls.splice(0, plan.tool_calls.length, ...adopted)
  return [...new Set(adopted.map((call) => call.tool_name))]
}

/** Binding lookup shared by managed evidence adapters. */
export function bindingForInquiryItem(snapshot: CapabilityKnowledgeSnapshot, contract: InquiryContract, itemId: string) {
  const item = contract.plan_items.find((candidate) => candidate.item_id === itemId)
  if (!item?.binding_id) return undefined
  return snapshot.scus.find((scu) => scu.scu_id === item.scu_id)
    ?.bindings.find((binding) => binding.binding_id === item.binding_id)
}
