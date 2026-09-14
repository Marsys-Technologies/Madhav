import { describe, expect, it } from 'vitest'
import { getCatalog } from '../../retrieval/registry/catalog'
import { compileCapabilityKnowledge } from '../../retrieval/registry/knowledge/compiler'
import { compileInquiryContract, finalizeInquiryContract, validateInquiryContract } from './compiler'
import { challengeInquirySelection } from './omission_challenger'

const scope = {
  intent: 'domain_assessment',
  domains: ['wealth'],
  width: 'broad',
  depth: 'deep',
  horizon: 'far',
  intervention: 'none',
  entitlement: 'native',
} as const

describe('Purna Anvesana Wave 3 acceptance', () => {
  const snapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-14T00:00:00.000Z')

  it('replays normalized intent and deterministic floors byte-identically', () => {
    const first = compileInquiryContract({ snapshot, chart_id: 'chart-1', question: 'Complete wealth outlook', scope_tuple: scope })
    const second = compileInquiryContract({
      snapshot,
      chart_id: 'chart-1',
      question: 'Complete wealth outlook',
      scope_tuple: {
        intent: 'wealth_deepdive', domains: ['finance'], width: 'panoramic', depth: 'deepdive',
        horizon: 'multi_year', intervention: false, entitlement: 'native',
      },
    })
    expect(first.scope_tuple).toEqual(second.scope_tuple)
    expect(first.semantic_contract_hash).toBe(second.semantic_contract_hash)
    expect(first.execution_plan_hash).toBe(second.execution_plan_hash)
    expect(first.obligations.filter((item) => item.source === 'deterministic_floor').length).toBeGreaterThanOrEqual(8)
  })

  it('discovers an adjacent two-hop chain through reviewed ontology edges', () => {
    const contract = compileInquiryContract({
      snapshot,
      chart_id: 'chart-1',
      question: 'prosperity assessment',
      scope_tuple: { ...scope, intent: 'domain_assessment', depth: 'standard', width: 'narrow' },
      planning_budget: { max_search_hits: 1, max_graph_hops: 2, max_graph_nodes: 16 },
    })
    expect(contract.graph_traversal?.steps).toContainEqual(expect.objectContaining({
      from_scu_id: 'scu.finance.prosperity_assessment',
      relation: 'requires',
      to_scu_id: 'scu.kala.temporal_activation',
      hop: 1,
    }))
    expect(contract.graph_traversal?.steps).toContainEqual(expect.objectContaining({
      from_scu_id: 'scu.kala.temporal_activation',
      relation: 'requires',
      to_scu_id: 'scu.catalog.get_dashas',
      hop: 2,
    }))
  })

  it('replays known omission misses through a separate challenger', () => {
    const challenge = challengeInquirySelection({
      snapshot,
      question: 'Give me a complete wealth outlook',
      scope: {
        intent: 'wealth_deepdive', domains: ['wealth'], width: 'panoramic', depth: 'deepdive',
        horizon: 'multi_year', intervention: false, entitlement: 'native',
      },
      selected_scu_ids: ['scu.finance.prosperity_assessment'],
    })
    expect(challenge.findings.map((item) => item.rule_id)).toEqual(expect.arrayContaining([
      'OMIT-BHAVA-BHAVAT',
      'OMIT-CROSS-DOMAIN',
    ]))

    const contract = compileInquiryContract({
      snapshot,
      chart_id: 'chart-1',
      question: 'Give me a complete wealth outlook',
      scope_tuple: scope,
      planning_budget: { max_search_hits: 1, max_graph_hops: 0 },
    })
    expect(contract.omission_challenge?.findings.map((item) => item.rule_id)).toContain('OMIT-CROSS-DOMAIN')
    expect(contract.obligations).toContainEqual(expect.objectContaining({
      source: 'omission_challenger',
      materiality: 'required',
      scu_ids: ['scu.catalog.query_contradictions'],
    }))
  })

  it('fails closed when a required floor disappears from the pinned snapshot', () => {
    const missing = {
      ...snapshot,
      scus: snapshot.scus.filter((scu) => scu.scu_id !== 'scu.catalog.assess_career'),
      edges: snapshot.edges.filter((edge) => edge.from_scu_id !== 'scu.catalog.assess_career'
        && edge.to_scu_id !== 'scu.catalog.assess_career'),
    }
    expect(() => compileInquiryContract({
      snapshot: missing,
      chart_id: 'chart-1',
      question: 'Deep career outlook',
      scope_tuple: { ...scope, domains: ['career'] },
    })).toThrow('INQUIRY_REQUIRED_FLOOR_MISSING:scu.catalog.assess_career')
  })

  it('records capped widening and never finalizes an unresolved material frontier', () => {
    const contract = compileInquiryContract({
      snapshot,
      chart_id: 'chart-1',
      question: 'mechanism network',
      scope_tuple: { ...scope, intent: 'explain', domains: ['all'], depth: 'standard', width: 'narrow' },
      planning_budget: { max_search_hits: 1, max_graph_hops: 0, max_graph_nodes: 1, max_challenger_additions: 0 },
    })
    expect(contract.planning_budget).toMatchObject({ truncated: true, max_challenger_additions: 0 })
    expect(contract.material_frontier.some((item) => item.materiality === 'required' && item.disposition === 'open')).toBe(true)
    expect(finalizeInquiryContract(contract).status).toBe('INCOMPLETE')
  })

  it('rejects a planning-budget receipt whose content was changed without rehashing', () => {
    const contract = compileInquiryContract({ snapshot, chart_id: 'chart-1', question: 'Complete wealth outlook', scope_tuple: scope })
    const forged = {
      ...contract,
      planning_budget: { ...contract.planning_budget!, max_graph_hops: contract.planning_budget!.max_graph_hops + 1 },
    }
    expect(validateInquiryContract(forged)).toMatchObject({ valid: false })
  })

  it('pins the route harness career floor expansion', () => {
    const contract = compileInquiryContract({
      snapshot,
      chart_id: 'chart-harness',
      question: 'How does my career unfold?',
      scope_tuple: {
        intent: 'domain_assessment', domains: ['career'], width: 'standard', depth: 'standard',
        horizon: 'near', intervention: 'none', entitlement: 'native',
      },
      ai_proposal: {
        question_facets: [{ label: 'Managed planner decomposition', terms: ['harness'], materiality: 'supporting' }],
        uncommon_adjacencies: [], hypotheses: ['Answer as an acharya.'],
      },
    })
    expect(contract.obligations.filter((item) => item.materiality === 'required').map((item) => item.scu_ids[0])).toEqual([
      'scu.catalog.assess_career',
      'scu.bodha.mechanism.network',
      'scu.catalog.get_divisionals',
      'scu.kala.temporal_activation',
      'scu.yoga.firing_and_cancellation',
    ])
  })
})
