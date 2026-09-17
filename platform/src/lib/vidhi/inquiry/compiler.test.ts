import { describe, expect, it } from 'vitest'
import { getCatalog } from '../../retrieval/registry/catalog'
import { compileCapabilityKnowledge } from '../../retrieval/registry/knowledge/compiler'
import { compileChartCapabilityOverlay } from '../../retrieval/registry/knowledge/overlay'
import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import { applyInquiryObservations, buildInquiryClosureReceipt, closeInquiryForEvidenceSuccessor, compileInquiryContract, compileInquirySuccessorContract, failInquiryForOverlayDrift, finalizeInquiryContract, inquiryAuthorizationHashes, recordInquiryExecution, validateInquiryContract } from './compiler'
import type { ScopeTuple } from '../types'
import type { InquiryContract } from './types'

const wealthScope: ScopeTuple = {
  intent: 'wealth_deepdive',
  domains: ['wealth'],
  width: 'panoramic',
  depth: 'deepdive',
  horizon: 'multi_year',
  intervention: false,
  entitlement: 'native',
}

function withRecomputedAuthorization(contract: InquiryContract): InquiryContract {
  const hashes = inquiryAuthorizationHashes(contract)
  return { ...contract, ...hashes }
}

describe('versioned inquiry compiler', () => {
  const snapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-13T00:00:00.000Z')

  it('creates a fresh, evidence-admitted successor without mutating the parent authorization', () => {
    const initial = compileInquiryContract({ snapshot, chart_id: 'chart-fixture', question: 'Complete wealth outlook', scope_tuple: wealthScope, max_iterations: 1 })
    const source = initial.plan_items.find((item) => item.state === 'ready'
      && item.obligation_ids.some((id) => initial.obligations.find((obligation) => obligation.obligation_id === id)?.materiality === 'required'))
    expect(source).toBeDefined()
    const observed = recordInquiryExecution(initial, {
      item_id: source!.item_id, disposition: 'served', evidence_refs: ['raw:parent-evidence'],
      pagination: { semantics: 'offset', exhausted: false, next: 50 },
    })
    const parent = closeInquiryForEvidenceSuccessor(observed)
    const successor = compileInquirySuccessorContract({ snapshot, parent_inquiry_id: '11111111-1111-4111-8111-111111111111', parent })

    expect(successor.successor).toMatchObject({
      parent_inquiry_id: '11111111-1111-4111-8111-111111111111',
      parent_contract_hash: parent.semantic_contract_hash,
      admitted_frontier: [expect.objectContaining({ evidence_refs: ['raw:parent-evidence'] })],
    })
    expect(successor.plan_items).not.toHaveLength(0)
    expect(successor.plan_items.every((item) => parent.plan_items.some((prior) => prior.scu_id === item.scu_id))).toBe(true)
    expect(inquiryAuthorizationHashes(successor)).toMatchObject({
      semantic_contract_hash: successor.semantic_contract_hash,
      execution_plan_hash: successor.execution_plan_hash,
      contract_id: successor.contract_id,
    })
    expect(validateInquiryContract(successor)).toEqual({ valid: true, errors: [] })
    expect(parent).toMatchObject({ status: 'BLOCKED', status_reasons: expect.arrayContaining(['evidence-admitted successor issued']) })
  })

  it('refuses a continuation frontier that has no server-observed evidence', () => {
    const parent = compileInquiryContract({ snapshot, chart_id: 'chart-fixture', question: 'Complete wealth outlook', scope_tuple: wealthScope })
    const open = parent.material_frontier.find((frontier) => frontier.materiality === 'required')
    const forged = {
      ...parent,
      status: 'BLOCKED' as const,
      material_frontier: open ? [open] : [{ frontier_id: 'frontier-001', discovered_from: 'item-001', scu_id: parent.plan_items[0]!.scu_id, materiality: 'required' as const, reason: 'forged', disposition: 'open' as const }],
    }
    expect(() => compileInquirySuccessorContract({ snapshot, parent_inquiry_id: '11111111-1111-4111-8111-111111111111', parent: forged })).toThrow('INQUIRY_SUCCESSOR_NO_EVIDENCE_ADMITTED_FRONTIER')
  })

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

  it('normalizes classifier aliases before hashing or floor selection', () => {
    const classifier = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'Detailed career outlook',
      scope_tuple: {
        intent: 'DOMAIN-ASSESSMENT', domains: ['job', 'CAREER'], width: 'broad', depth: 'deep',
        horizon: 'far', intervention: 'none', entitlement: 'native',
      },
    })
    const canonical = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'Detailed career outlook',
      scope_tuple: {
        intent: 'career_deepdive', domains: ['career'], width: 'panoramic', depth: 'deepdive',
        horizon: 'multi_year', intervention: false, entitlement: 'native',
      },
    })

    expect(classifier.scope_tuple).toEqual(canonical.scope_tuple)
    expect(classifier.semantic_contract_hash).toBe(canonical.semantic_contract_hash)
    expect(classifier.scope_normalization?.normalization_version).toBe('inquiry-scope-normalization-v1')
    expect(classifier.plan_items.some((item) => item.scu_id === 'scu.catalog.assess_career')).toBe(true)
  })

  it('uses only source-backed graph edges for AI adjacency and deterministic traversal', () => {
    const contract = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'mechanism network',
      scope_tuple: { ...wealthScope, intent: 'explain', domains: ['all'], depth: 'standard' },
      planning_budget: { max_graph_hops: 0 },
      ai_proposal: {
        question_facets: [],
        uncommon_adjacencies: [
          { from_scu_id: 'scu.bodha.mechanism.network', to_scu_id: 'scu.kala.temporal_activation', rationale: 'reviewed edge' },
          { from_scu_id: 'scu.bodha.mechanism.network', to_scu_id: 'scu.catalog.asset_registry_all', rationale: 'invented pair' },
        ],
        hypotheses: [],
      },
    })

    expect(contract.plan_items.some((item) => item.scu_id === 'scu.kala.temporal_activation')).toBe(true)
    expect(contract.obligations.some((obligation) => obligation.source === 'ai_decomposition'
      && obligation.scu_ids.includes('scu.catalog.asset_registry_all'))).toBe(false)
    expect(contract.graph_traversal?.steps.every((step) => step.source_ref.length > 0)).toBe(true)
  })

  it('fails closed with a material frontier and budget receipt when widening is capped', () => {
    const contract = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'mechanism network',
      scope_tuple: { ...wealthScope, intent: 'explain', domains: ['all'], depth: 'standard' },
      planning_budget: { max_search_hits: 1, max_graph_hops: 1, max_graph_nodes: 1, max_challenger_additions: 0 },
    })

    expect(contract.planning_budget?.truncated).toBe(true)
    expect(contract.material_frontier.some((item) => item.materiality === 'required')).toBe(true)
    expect(finalizeInquiryContract(contract).status).not.toBe('COMPLETE')
  })

  it('requires an explicit temporal anchor and emits a structured transit clarification', () => {
    const internal = compileInquiryContract({ snapshot, chart_id: 'chart-fixture', question: 'wealth transit timing', scope_tuple: wealthScope })
    const transit = internal.plan_items.find((item) => item.scu_id === 'scu.catalog.query_planet_transit')
    expect(transit).toMatchObject({ state: 'blocked', binding_id: null })
    expect(transit?.blocked_reason).toContain('temporal_anchor_date')
    expect(transit?.argument_resolution).toMatchObject({
      resolution_version: 'inquiry-argument-resolution-v1',
      strategy: 'all_graha_single_day_transit',
      status: 'clarification_required',
      clarification: {
        code: 'TEMPORAL_ANCHOR_REQUIRED',
        required_inputs: ['temporal_anchor_date'],
      },
    })

    const invalid = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'wealth transit timing',
      scope_tuple: wealthScope,
      temporal_anchor_date: '2026-02-30',
    })
    expect(invalid.plan_items.find((item) => item.scu_id === 'scu.catalog.query_planet_transit')?.argument_resolution)
      .toMatchObject({ clarification: { code: 'TEMPORAL_ANCHOR_INVALID' } })

    const raw = compileInquiryContract({ snapshot, chart_id: 'chart-fixture', question: 'wealth varga', scope_tuple: wealthScope, execution_channel: 'mcp_full' })
    expect(raw.plan_items.find((item) => item.scu_id === 'scu.catalog.get_divisionals')).toMatchObject({
      state: 'ready',
      binding_id: 'registry:marsys://tool/L1/get_divisionals',
    })
  })

  it('derives one receipted aggregate binding with immutable nine-graha component arguments', () => {
    const first = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'wealth transit timing',
      scope_tuple: wealthScope,
      temporal_anchor_date: '2026-09-15',
    })
    const second = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'wealth transit timing',
      scope_tuple: wealthScope,
      temporal_anchor_date: '2026-09-15',
    })
    const transitItems = first.plan_items.filter((item) => item.scu_id === 'scu.catalog.query_planet_transit')

    expect(transitItems).toHaveLength(1)
    expect(transitItems[0]).toMatchObject({
      state: 'ready',
      binding_id: 'registry:marsys://tool/L0/query_current_transit_snapshot',
      args: { as_of_date: '2026-09-15' },
      argument_resolution: {
        status: 'resolved',
        source: 'caller_temporal_anchor',
        component_arguments: [
          { planet: 'Sun', start_date: '2026-09-15', end_date: '2026-09-15' },
          { planet: 'Moon', start_date: '2026-09-15', end_date: '2026-09-15' },
          { planet: 'Mars', start_date: '2026-09-15', end_date: '2026-09-15' },
          { planet: 'Mercury', start_date: '2026-09-15', end_date: '2026-09-15' },
          { planet: 'Jupiter', start_date: '2026-09-15', end_date: '2026-09-15' },
          { planet: 'Venus', start_date: '2026-09-15', end_date: '2026-09-15' },
          { planet: 'Saturn', start_date: '2026-09-15', end_date: '2026-09-15' },
          { planet: 'Rahu', start_date: '2026-09-15', end_date: '2026-09-15' },
          { planet: 'Ketu', start_date: '2026-09-15', end_date: '2026-09-15' },
        ],
      },
    })
    expect(transitItems[0]?.argument_resolution?.component_arguments.every((item) => item.args_hash.startsWith('sha256:'))).toBe(true)
    expect(transitItems[0]?.argument_resolution?.resolution_hash).toMatch(/^sha256:[a-f0-9]{64}$/)
    expect(first.execution_plan_hash).toBe(second.execution_plan_hash)
    expect(inquiryAuthorizationHashes(first).execution_plan_hash).toBe(first.execution_plan_hash)

    const requestClock = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'wealth transit timing',
      scope_tuple: wealthScope,
      temporal_anchor_date: '2026-09-15',
      temporal_anchor_source: 'request_context_clock',
    })
    expect(requestClock.plan_items.find((item) => item.scu_id === 'scu.catalog.query_planet_transit')?.argument_resolution?.source)
      .toBe('request_context_clock')

    const later = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'wealth transit timing',
      scope_tuple: wealthScope,
      temporal_anchor_date: '2026-09-16',
    })
    expect(later.semantic_contract_hash).toBe(first.semantic_contract_hash)
    expect(later.execution_plan_hash).not.toBe(first.execution_plan_hash)
    expect(later.contract_id).not.toBe(first.contract_id)

    const raw = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'wealth transit timing',
      scope_tuple: wealthScope,
      execution_channel: 'mcp_full',
      temporal_anchor_date: '2026-09-15',
    })
    expect(raw.plan_items.find((item) => item.scu_id === 'scu.catalog.query_planet_transit')).toMatchObject({
      state: 'ready',
      binding_id: 'registry:marsys://tool/L0/query_current_transit_snapshot',
      argument_resolution: { status: 'resolved' },
    })
    expect(validateInquiryContract(raw)).toEqual({ valid: true, errors: [] })
  })

  it('derives the temporal anchor when the aggregate transit SCU is selected directly', () => {
    const contract = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'current transit snapshot',
      scope_tuple: {
        intent: 'retrieval', domains: ['timing'], width: 'focused', depth: 'standard',
        horizon: 'current', intervention: false, entitlement: 'native',
      },
      planning_budget: { max_search_hits: 1 },
      temporal_anchor_date: '2026-09-15',
    })
    const aggregate = contract.plan_items.find((item) => item.scu_id === 'scu.catalog.query_current_transit_snapshot')

    expect(aggregate).toMatchObject({
      state: 'ready',
      binding_id: 'registry:marsys://tool/L0/query_current_transit_snapshot',
      args: { as_of_date: '2026-09-15' },
      argument_resolution: { status: 'resolved', temporal_anchor_date: '2026-09-15' },
    })
    expect(validateInquiryContract(contract)).toEqual({ valid: true, errors: [] })
  })

  it('does not authorize a binding that the chart/build overlay leaves dark', () => {
    const overlay = compileChartCapabilityOverlay({ snapshot, chart_id: 'chart-fixture', build_id: 'build-1', evidence: [], generated_at: '2026-09-13T00:00:00.000Z' })
    const contract = compileInquiryContract({ snapshot, overlay, chart_id: 'chart-fixture', question: 'wealth outlook', scope_tuple: wealthScope })
    expect(contract.chart_availability_version).toBe(overlay.overlay_version)
    expect(contract.chart_build_id).toBe('build-1')
    expect(contract.plan_items.every((item) => item.state === 'blocked')).toBe(true)
    expect(finalizeInquiryContract(contract).status).toBe('INCOMPLETE')
  })

  it('keeps valid transit argument resolution coherent when the overlay blocks dispatch', () => {
    const overlay = compileChartCapabilityOverlay({ snapshot, chart_id: 'chart-fixture', build_id: 'build-dark', evidence: [], generated_at: '2026-09-13T00:00:00.000Z' })
    const contract = compileInquiryContract({
      snapshot,
      overlay,
      chart_id: 'chart-fixture',
      question: 'wealth transit timing',
      scope_tuple: wealthScope,
      temporal_anchor_date: '2026-09-15',
    })
    const transit = contract.plan_items.find((item) => item.scu_id === 'scu.catalog.query_planet_transit')
    expect(transit).toMatchObject({ state: 'blocked', binding_id: null, argument_resolution: { status: 'resolved' } })
    expect(validateInquiryContract(contract)).toEqual({ valid: true, errors: [] })
  })

  it('admits a validated AI adjacency as a supporting obligation', () => {
    const contract = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'career assessment',
      scope_tuple: { ...wealthScope, intent: 'domain_assessment', domains: ['career'], depth: 'standard' },
      planning_budget: { max_search_hits: 1, max_graph_hops: 0 },
      ai_proposal: {
        question_facets: [],
        uncommon_adjacencies: [{ from_scu_id: 'scu.catalog.assess_career', to_scu_id: 'scu.catalog.query_signals', rationale: 'uncommon but relevant' }],
        hypotheses: [],
      },
    })
    expect(contract.obligations).toContainEqual(expect.objectContaining({ source: 'ai_decomposition', materiality: 'supporting', scu_ids: ['scu.catalog.query_signals'] }))
    expect(contract.plan_items.some((item) => item.scu_id === 'scu.catalog.query_signals')).toBe(true)
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
    const initial = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'Complete wealth outlook',
      scope_tuple: wealthScope,
      temporal_anchor_date: '2026-09-15',
    })
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

  it('advances a continuation at the exact reviewed nested argument path', () => {
    const initial = compileInquiryContract({ snapshot, chart_id: 'chart-fixture', question: 'Complete wealth outlook', scope_tuple: wealthScope })
    const item = initial.plan_items.find((candidate) => candidate.scu_id === 'scu.yoga.firing_and_cancellation')!
    const nested = {
      ...initial,
      plan_items: initial.plan_items.map((candidate) => candidate.item_id === item.item_id
        ? { ...candidate, args: { filters: { cursor: 'first', keep: true }, untouched: 'value' } }
        : candidate),
    }
    const continued = recordInquiryExecution(nested, {
      item_id: item.item_id,
      disposition: 'served',
      evidence_refs: ['receipt:nested-page'],
      pagination: { semantics: 'cursor', exhausted: false, next: 'second' },
      request_position_path: 'filters.cursor',
    })
    expect(continued.plan_items.find((candidate) => candidate.item_id === item.item_id)?.args).toEqual({
      filters: { cursor: 'second', keep: true },
      untouched: 'value',
    })
  })

  it('reports BLOCKED honestly when the iteration cap is exhausted', () => {
    const initial = compileInquiryContract({ snapshot, chart_id: 'chart-fixture', question: 'Complete wealth outlook', scope_tuple: wealthScope, max_iterations: 1 })
    const observed = applyInquiryObservations(initial, initial.plan_items.slice(0, 1).map((item) => ({ item_id: item.item_id, disposition: 'dark' as const, evidence_refs: [], gap_reason: 'build output is unavailable' })))
    const final = finalizeInquiryContract(observed)
    expect(final.status).toBe('BLOCKED')
    expect(final.status_reasons).toContain('iteration cap reached before material frontier closure')
  })

  it('never treats a required capped pagination frontier as COMPLETE', () => {
    const initial = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'Complete wealth outlook',
      scope_tuple: wealthScope,
      max_iterations: 1,
    })
    const paged = initial.plan_items.find((item) => item.scu_id === 'scu.yoga.firing_and_cancellation')!
    const otherObservations = initial.plan_items
      .filter((item) => item.item_id !== paged.item_id)
      .map((item) => ({ item_id: item.item_id, disposition: 'served' as const, evidence_refs: [`receipt:${item.item_id}`] }))
    const observed = applyInquiryObservations(initial, otherObservations)
    const capped = recordInquiryExecution(observed, {
      item_id: paged.item_id,
      disposition: 'served',
      evidence_refs: ['receipt:page-1'],
      pagination: { semantics: 'offset', exhausted: false, next: 50 },
      request_position_path: 'offset',
    })

    expect(capped.material_frontier).toContainEqual(expect.objectContaining({
      scu_id: paged.scu_id,
      materiality: 'required',
      disposition: 'capped',
    }))
    const final = finalizeInquiryContract(capped)
    expect(final.status).toBe('BLOCKED')
    expect(final.status_reasons).toContain('1 material frontier items capped before exhaustion proof')
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
    expect(receipt.graph_traversal_hash).toBe(initial.graph_traversal?.traversal_hash)
    expect(receipt.omission_challenge_hash).toBe(initial.omission_challenge?.challenge_hash)
  })

  it('rejects forged normalization, traversal, challenge, budget, and argument-resolution receipts', () => {
    const initial = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'Complete wealth outlook',
      scope_tuple: wealthScope,
      temporal_anchor_date: '2026-09-15',
    })
    const transitIndex = initial.plan_items.findIndex((item) => item.scu_id === 'scu.catalog.query_planet_transit')
    const forgedTransitItems = initial.plan_items.map((item, index) => index === transitIndex
      ? { ...item, argument_resolution: { ...item.argument_resolution!, resolution_hash: 'sha256:forged' } }
      : item)
    const nonCanonicalTransitItems = initial.plan_items.map((item, index) => {
      if (index !== transitIndex) return item
      const componentArguments = item.argument_resolution!.component_arguments.map((component, componentIndex) => componentIndex === 0
        ? { ...component, planet: 'Pluto', args_hash: stableFingerprint({ planet: 'Pluto', start_date: component.start_date, end_date: component.end_date }) }
        : component)
      const resolution = { ...item.argument_resolution!, component_arguments: componentArguments }
      const withoutHash = { ...resolution }
      delete (withoutHash as Partial<typeof withoutHash>).resolution_hash
      return { ...item, argument_resolution: { ...withoutHash, resolution_hash: stableFingerprint(withoutHash) } }
    })
    const forgeries = [
      { ...initial, scope_normalization: { ...initial.scope_normalization!, normalized_scope_hash: 'sha256:forged' } },
      { ...initial, graph_traversal: { ...initial.graph_traversal!, traversal_hash: 'sha256:forged' } },
      { ...initial, omission_challenge: { ...initial.omission_challenge!, challenge_hash: 'sha256:forged' } },
      { ...initial, planning_budget: { ...initial.planning_budget!, budget_hash: 'sha256:forged' } },
      { ...initial, plan_items: forgedTransitItems },
      { ...initial, plan_items: nonCanonicalTransitItems },
    ]
    for (const forged of forgeries) expect(validateInquiryContract(forged).valid).toBe(false)
  })

  it('rejects an aggregate transit binding whose receipt was removed even after authorization hashes are recomputed', () => {
    const initial = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'wealth transit timing',
      scope_tuple: wealthScope,
      temporal_anchor_date: '2026-09-15',
    })
    const strippedItems = initial.plan_items.map((item) => {
      if (item.binding_id !== 'registry:marsys://tool/L0/query_current_transit_snapshot') return item
      const withoutReceipt = { ...item }
      delete (withoutReceipt as Partial<typeof withoutReceipt>).argument_resolution
      return withoutReceipt
    })
    const stripped = withRecomputedAuthorization({ ...initial, plan_items: strippedItems })
    expect(validateInquiryContract(stripped)).toMatchObject({
      valid: false,
      errors: expect.arrayContaining([expect.stringContaining('aggregate transit binding lacks a resolved argument receipt')]),
    })
  })

  it('requires transit receipts for overlay-blocked and clarification-blocked internal plans', () => {
    const darkOverlay = compileChartCapabilityOverlay({ snapshot, chart_id: 'chart-fixture', build_id: 'build-dark', evidence: [], generated_at: '2026-09-13T00:00:00.000Z' })
    const resolvedBlocked = compileInquiryContract({
      snapshot,
      overlay: darkOverlay,
      chart_id: 'chart-fixture',
      question: 'wealth transit timing',
      scope_tuple: wealthScope,
      temporal_anchor_date: '2026-09-15',
    })
    const clarificationBlocked = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'wealth transit timing',
      scope_tuple: wealthScope,
    })
    for (const original of [resolvedBlocked, clarificationBlocked]) {
      const stripped = withRecomputedAuthorization({
        ...original,
        plan_items: original.plan_items.map((item) => {
          if (item.scu_id !== 'scu.catalog.query_planet_transit') return item
          const withoutReceipt = { ...item }
          delete (withoutReceipt as Partial<typeof withoutReceipt>).argument_resolution
          return withoutReceipt
        }),
      })
      expect(validateInquiryContract(stripped)).toMatchObject({
        valid: false,
        errors: expect.arrayContaining([expect.stringContaining('internal transit plan lacks an argument resolution receipt')]),
      })
    }

    const receipt = clarificationBlocked.plan_items.find((item) => item.scu_id === 'scu.catalog.query_planet_transit')!.argument_resolution!
    const nonTransit = clarificationBlocked.plan_items.find((item) => item.scu_id !== 'scu.catalog.query_planet_transit' && item.state === 'blocked')!
    const transplanted = withRecomputedAuthorization({
      ...clarificationBlocked,
      plan_items: clarificationBlocked.plan_items.map((item) => item.item_id === nonTransit.item_id
        ? { ...item, argument_resolution: receipt }
        : item),
    })
    expect(validateInquiryContract(transplanted)).toMatchObject({
      valid: false,
      errors: expect.arrayContaining([expect.stringContaining('carries a transit argument receipt outside the internal transit plan')]),
    })
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

  it('blocks overlay drift even when every obligation is supporting', () => {
    const initial = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'chart overview',
      scope_tuple: { ...wealthScope, intent: 'overview', domains: ['general'], depth: 'standard' },
    })
    const supportingOnly = {
      ...initial,
      obligations: initial.obligations.map((obligation) => ({ ...obligation, materiality: 'supporting' as const })),
    }
    const drifted = failInquiryForOverlayDrift(supportingOnly)
    expect(drifted.status).toBe('BLOCKED')
    expect(drifted.status_reasons).toContain('chart capability overlay changed during dispatch')
    expect(drifted.obligations.some((obligation) => obligation.disposition === 'failed')).toBe(true)
  })
})
