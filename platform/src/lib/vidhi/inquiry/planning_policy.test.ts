import { describe, expect, it } from 'vitest'
import generatedCapabilityKnowledge from '../../../generated/capability_knowledge.snapshot.json'
import type { CapabilityKnowledgeSnapshot } from '../../retrieval/registry/knowledge/types'
import { compileInquiryContract } from './compiler'
import { deterministicCompilerProvenance, selectInquiryPlanningPolicy, serverPlannerProvenance } from './planning_policy'

const snapshot = generatedCapabilityKnowledge as CapabilityKnowledgeSnapshot

describe('inquiry planning provenance (RC-5.6)', () => {
  it('records the deep planner slot, requested reasoning, and the fallback model that actually planned', () => {
    expect(serverPlannerProvenance('deep', { active_model_id: 'gemini-2.5-pro', fallback_used: true })).toEqual({
      planner: 'model', ai_proposal_source: 'server_planner', call_type: 'planner_deep',
      reasoning_requested: 'enable', model_id: 'gemini-2.5-pro', fallback_used: true,
    })
    expect(serverPlannerProvenance('standard', { active_model_id: 'gemini-3.7-flash', fallback_used: false }))
      .toMatchObject({ call_type: 'planner_fast', reasoning_requested: 'auto', fallback_used: false })
  })

  it('records an honest null instead of inventing a model when the planner reported none', () => {
    expect(serverPlannerProvenance('deep', undefined)).toMatchObject({ model_id: null, fallback_used: null })
  })

  it('declares the raw door as deterministic compilation of a caller proposal, never a model planner', () => {
    expect(deterministicCompilerProvenance(true)).toMatchObject({ planner: 'deterministic_compiler', ai_proposal_source: 'caller', call_type: null })
    expect(deterministicCompilerProvenance(false)).toMatchObject({ ai_proposal_source: 'none' })
  })

  it('keeps provenance on the contract without changing its semantic or execution identity', () => {
    const base = {
      snapshot, chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
      question: 'How is wealth shaped in this chart?',
      scope_tuple: { intent: 'domain_assessment', domains: ['wealth'], width: 'standard', depth: 'deep', horizon: 'natal', intervention: 'none', entitlement: 'native' },
      temporal_anchor_date: '2026-09-27',
    } as unknown as Parameters<typeof compileInquiryContract>[0]
    const plain = compileInquiryContract(base)
    const recorded = compileInquiryContract({ ...base, planning_provenance: serverPlannerProvenance('deep', { active_model_id: 'm', fallback_used: true }) })

    expect(recorded.planning_provenance).toMatchObject({ call_type: 'planner_deep', fallback_used: true })
    expect(plain.planning_provenance).toBeUndefined()
    expect(recorded.contract_id).toBe(plain.contract_id)
    expect(recorded.semantic_contract_hash).toBe(plain.semantic_contract_hash)
    expect(recorded.execution_plan_hash).toBe(plain.execution_plan_hash)
  })

  it('keeps the deterministic policy that selects the planner slot', () => {
    expect(selectInquiryPlanningPolicy('deep')).toEqual({ callType: 'planner_deep', reasoning: 'enable' })
  })
})
