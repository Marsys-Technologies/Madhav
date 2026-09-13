import { describe, expect, it } from 'vitest'
import { getCatalog } from '../../retrieval/registry/catalog'
import { compileCapabilityKnowledge } from '../../retrieval/registry/knowledge/compiler'
import { compileChartCapabilityOverlay } from '../../retrieval/registry/knowledge/overlay'
import { applyInquiryObservations, buildInquiryClosureReceipt, compileInquiryContract, finalizeInquiryContract, inquiryAuthorizationHashes, recordInquiryExecution, validateInquiryContract } from './compiler'
import type { ScopeTuple } from '../types'

const wealthScope: ScopeTuple = {
  intent: 'wealth_deepdive',
  domains: ['wealth'],
  width: 'panoramic',
  depth: 'deepdive',
  horizon: 'multi_year',
  intervention: false,
  entitlement: 'native',
}

describe('versioned inquiry compiler', () => {
  const snapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-13T00:00:00.000Z')

  it('compiles the finance/prosperity golden journey without missing key mechanisms', () => {
    const contract = compileInquiryContract({ snapshot, chart_id: 'chart-fixture', question: 'Give me a complete deep finance and prosperity outlook: promise, inhibitors, cancellations, varga contradictions, and timing.', scope_tuple: wealthScope })
    const selected = new Set(contract.plan_items.map((item) => item.scu_id))
    expect(selected).toEqual(expect.objectContaining(new Set([
      'scu.finance.prosperity_assessment',
      'scu.bodha.mechanism.network',
      'scu.catalog.get_divisionals',
      'scu.yoga.firing_and_cancellation',
      'scu.kala.temporal_activation',
      'scu.catalog.get_dashas',
      'scu.catalog.query_planet_transit',
      'scu.catalog.query_contradictions',
    ])))
    expect(contract.status).toBe('INCOMPLETE')
    expect(finalizeInquiryContract(contract).status).toBe('INCOMPLETE')
  })

  it('allows AI decomposition but drops invented capability ids', () => {
    const contract = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'What supports prosperity?',
      scope_tuple: wealthScope,
      ai_proposal: {
        question_facets: [{ label: 'Support and inhibition', terms: ['prosperity', 'mechanism'], materiality: 'required' }],
        uncommon_adjacencies: [{ from_scu_id: 'scu.fabricated', to_scu_id: 'scu.also_fabricated', rationale: 'model guess' }],
        hypotheses: ['A mechanism may be inhibited; verify from evidence.'],
      },
    })
    expect(contract.plan_items.some((item) => item.scu_id.includes('fabricated'))).toBe(false)
    expect(contract.ai_hypotheses).toHaveLength(1)
  })

  it('canonicalizes question whitespace, domain order, and AI hint order', () => {
    const first = compileInquiryContract({
      snapshot, chart_id: 'chart-fixture', question: '  What   supports prosperity? ',
      scope_tuple: { ...wealthScope, domains: ['wealth', 'finance'] },
      ai_proposal: { question_facets: [{ label: ' Factors ', terms: ['mechanism', 'prosperity'], materiality: 'supporting' }], uncommon_adjacencies: [], hypotheses: [' Verify '] },
    })
    const second = compileInquiryContract({
      snapshot, chart_id: 'chart-fixture', question: 'What supports prosperity?',
      scope_tuple: { ...wealthScope, domains: ['finance', 'wealth', 'wealth'] },
      ai_proposal: { question_facets: [{ label: 'Factors', terms: ['prosperity', 'mechanism'], materiality: 'supporting' }], uncommon_adjacencies: [], hypotheses: ['Verify'] },
    })
    expect(second.semantic_contract_hash).toBe(first.semantic_contract_hash)
    expect(second.execution_plan_hash).toBe(first.execution_plan_hash)
  })

  it('blocks unresolved required JSON Schema arguments and internal-only raw MCP bindings', () => {
    const internal = compileInquiryContract({ snapshot, chart_id: 'chart-fixture', question: 'wealth transit timing', scope_tuple: wealthScope })
    const transit = internal.plan_items.find((item) => item.scu_id === 'scu.catalog.query_planet_transit')
    expect(transit).toMatchObject({ state: 'blocked', binding_id: null })
    expect(transit?.blocked_reason).toContain('planet')

    const raw = compileInquiryContract({ snapshot, chart_id: 'chart-fixture', question: 'wealth varga', scope_tuple: wealthScope, execution_channel: 'mcp_full' })
    expect(raw.plan_items.find((item) => item.scu_id === 'scu.catalog.get_divisionals')).toMatchObject({ state: 'blocked', binding_id: null })
  })

  it('does not authorize a binding that the chart/build overlay leaves dark', () => {
    const overlay = compileChartCapabilityOverlay({ snapshot, chart_id: 'chart-fixture', build_id: 'build-1', evidence: [], generated_at: '2026-09-13T00:00:00.000Z' })
    const contract = compileInquiryContract({ snapshot, overlay, chart_id: 'chart-fixture', question: 'wealth outlook', scope_tuple: wealthScope })
    expect(contract.chart_availability_version).toBe(overlay.overlay_version)
    expect(contract.chart_build_id).toBe('build-1')
    expect(contract.plan_items.every((item) => item.state === 'blocked')).toBe(true)
    expect(finalizeInquiryContract(contract).status).toBe('INCOMPLETE')
  })

  it('admits a validated AI adjacency as a supporting obligation', () => {
    const initial = compileInquiryContract({ snapshot, chart_id: 'chart-fixture', question: 'Complete wealth outlook', scope_tuple: wealthScope })
    const source = initial.plan_items[0]!.scu_id
    const target = snapshot.scus.find((scu) => !initial.plan_items.some((item) => item.scu_id === scu.scu_id))!.scu_id
    const contract = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'Complete wealth outlook',
      scope_tuple: wealthScope,
      ai_proposal: {
        question_facets: [],
        uncommon_adjacencies: [{ from_scu_id: source, to_scu_id: target, rationale: 'uncommon but relevant' }],
        hypotheses: [],
      },
    })
    expect(contract.obligations).toContainEqual(expect.objectContaining({ source: 'ai_decomposition', materiality: 'supporting', scu_ids: [target] }))
    expect(contract.plan_items.some((item) => item.scu_id === target)).toBe(true)
  })

  it('keeps a multi-capability obligation pending until every plan item is observed', () => {
    const initial = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'What supports prosperity?',
      scope_tuple: wealthScope,
      ai_proposal: {
        question_facets: [{ label: 'Multi-capability facet', terms: ['prosperity mechanism timing'], materiality: 'required' }],
        uncommon_adjacencies: [],
        hypotheses: [],
      },
    })
    const obligation = initial.obligations.find((candidate) => candidate.label === 'Multi-capability facet')!
    expect(obligation.scu_ids.length).toBeGreaterThan(1)
    const items = initial.plan_items.filter((item) => item.obligation_ids.includes(obligation.obligation_id))
    const partial = applyInquiryObservations(initial, [{ item_id: items[0]!.item_id, disposition: 'served', evidence_refs: ['receipt:first'] }])
    expect(partial.obligations.find((candidate) => candidate.obligation_id === obligation.obligation_id)?.disposition).toBe('pending')
    const complete = applyInquiryObservations(partial, items.slice(1).map((item) => ({ item_id: item.item_id, disposition: 'empty' as const, evidence_refs: [`receipt:${item.item_id}`] })))
    expect(complete.obligations.find((candidate) => candidate.obligation_id === obligation.obligation_id)).toMatchObject({ disposition: 'served' })
  })

  it('reaches COMPLETE only after every required obligation has evidence and frontier is closed', () => {
    const initial = compileInquiryContract({ snapshot, chart_id: 'chart-fixture', question: 'Complete wealth outlook', scope_tuple: wealthScope })
    const observations = initial.plan_items.map((item) => ({ item_id: item.item_id, disposition: 'served' as const, evidence_refs: [`receipt:${item.item_id}`] }))
    const observed = applyInquiryObservations(initial, observations)
    expect(validateInquiryContract(observed).valid).toBe(true)
    expect(finalizeInquiryContract(observed).status).toBe('COMPLETE')

    const withFrontier = applyInquiryObservations(initial, [{
      ...observations[0],
      discovered_frontier: [{ scu_id: 'scu.catalog.query_contradictions', materiality: 'required' as const, reason: 'retrieval exposed a material contradiction' }],
    }, ...observations.slice(1)])
    expect(finalizeInquiryContract(withFrontier).status).toBe('INCOMPLETE')
  })

  it('executes a verified multi-page item until its frontier is exhausted', () => {
    const initial = compileInquiryContract({ snapshot, chart_id: 'chart-fixture', question: 'Complete wealth outlook', scope_tuple: wealthScope })
    const item = initial.plan_items.find((candidate) => candidate.scu_id === 'scu.yoga.firing_and_cancellation')!
    const first = recordInquiryExecution(initial, {
      item_id: item.item_id, disposition: 'served', evidence_refs: ['receipt:page-1'],
      pagination: { semantics: 'offset', exhausted: false, next: 50 }, request_position_path: 'offset',
    })
    expect(first.plan_items.find((candidate) => candidate.item_id === item.item_id)).toMatchObject({ state: 'ready', args: { offset: 50 } })
    expect(first.material_frontier).toContainEqual(expect.objectContaining({ scu_id: item.scu_id, disposition: 'open' }))
    const second = recordInquiryExecution(first, {
      item_id: item.item_id, disposition: 'empty', evidence_refs: ['receipt:page-2'],
      pagination: { semantics: 'offset', exhausted: true, next: null }, request_position_path: 'offset',
    })
    expect(second.plan_items.find((candidate) => candidate.item_id === item.item_id)).toMatchObject({ state: 'observed' })
    expect(second.material_frontier).toContainEqual(expect.objectContaining({ scu_id: item.scu_id, disposition: 'absorbed' }))
  })

  it('reports BLOCKED honestly when the iteration cap is exhausted', () => {
    const initial = compileInquiryContract({ snapshot, chart_id: 'chart-fixture', question: 'Complete wealth outlook', scope_tuple: wealthScope, max_iterations: 1 })
    const observed = applyInquiryObservations(initial, initial.plan_items.slice(0, 1).map((item) => ({ item_id: item.item_id, disposition: 'dark' as const, evidence_refs: [], gap_reason: 'build output is unavailable' })))
    const final = finalizeInquiryContract(observed)
    expect(final.status).toBe('BLOCKED')
    expect(final.status_reasons).toContain('iteration cap reached before material frontier closure')
  })

  it('recomputes immutable authorization and emits a normalized closure receipt', () => {
    const initial = compileInquiryContract({ snapshot, chart_id: 'chart-fixture', question: 'Complete wealth outlook', scope_tuple: wealthScope })
    expect(inquiryAuthorizationHashes(initial)).toEqual({
      semantic_contract_hash: initial.semantic_contract_hash,
      execution_plan_hash: initial.execution_plan_hash,
      contract_id: initial.contract_id,
    })
    const final = finalizeInquiryContract(initial)
    const receipt = buildInquiryClosureReceipt(final)
    expect(receipt.receipt_hash).toMatch(/^sha256:[a-f0-9]{64}$/)
    expect(receipt.obligation_coverage).toHaveLength(final.obligations.length)
    expect(receipt.status).toBe('INCOMPLETE')
  })

  it('never treats a required failed observation as complete', () => {
    const initial = compileInquiryContract({ snapshot, chart_id: 'chart-fixture', question: 'Complete wealth outlook', scope_tuple: wealthScope })
    const observations = initial.plan_items.map((item, index) => index === 0
      ? { item_id: item.item_id, disposition: 'failed' as const, evidence_refs: [] as string[], gap_reason: 'dispatch error' }
      : { item_id: item.item_id, disposition: 'served' as const, evidence_refs: [`receipt:${item.item_id}`] })
    const final = finalizeInquiryContract(applyInquiryObservations(initial, observations))
    expect(final.status).toBe('INCOMPLETE')
    expect(final.status_reasons).toContain('1 required obligations failed or are dark')
  })
})
