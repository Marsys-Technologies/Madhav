import { describe, expect, it } from 'vitest'
import { getCatalog } from '../../retrieval/registry/catalog'
import { compileCapabilityKnowledge } from '../../retrieval/registry/knowledge/compiler'
import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import { applyInquiryObservations, compileInquiryContract, finalizeInquiryContract, recordInquiryExecution } from './compiler'
import {
  buildInquiryFactRegister,
  buildResponseCoverageReceipt,
  buildStructuredResponseAccountability,
  inquiryResponsePartContentHash,
} from './response_accountability'
import type { InquiryContract, InquiryResponseDeliveryPart, InquiryScopeTuple } from './types'

const wealthScope: InquiryScopeTuple = {
  intent: 'wealth_deepdive',
  domains: ['wealth'],
  width: 'panoramic',
  depth: 'deepdive',
  horizon: 'multi_year',
  intervention: false,
  entitlement: 'native',
}

const snapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-13T00:00:00.000Z')

function completeFixture(): { contract: InquiryContract; evidencePayloads: readonly unknown[] } {
  const initial = compileInquiryContract({
    snapshot,
    chart_id: 'chart-fixture',
    question: 'Give me a complete wealth outlook',
    scope_tuple: wealthScope,
  })
  const evidencePayloads = initial.plan_items.map((item) => ({ item_id: item.item_id, rows: [`finding:${item.item_id}`] }))
  const byItem = new Map(initial.plan_items.map((item, index) => [item.item_id, evidencePayloads[index]!]))
  const contract = finalizeInquiryContract(applyInquiryObservations(initial, initial.plan_items.map((item) => ({
    item_id: item.item_id,
    disposition: 'served' as const,
    evidence_refs: [`retrieval:${item.item_id}:${stableFingerprint(byItem.get(item.item_id))}`],
  }))))
  return { contract, evidencePayloads }
}

function part(register: ReturnType<typeof buildInquiryFactRegister>, factIds: readonly string[], suffix = 'all'): InquiryResponseDeliveryPart {
  const selected = new Set(factIds)
  const evidencePayloadHashes = [...new Set(register.facts
    .filter((fact) => selected.has(fact.fact_id))
    .flatMap((fact) => fact.evidence_refs.map((ref) => ref.match(/sha256:[a-f0-9]{64}$/)?.[0]).filter(Boolean) as string[]))]
    .sort()
  return {
    part_id: `structured-findings:${suffix}`,
    kind: 'structured_findings',
    content_hash: inquiryResponsePartContentHash(register, factIds, 'structured_findings', null, evidencePayloadHashes),
    fact_ids: factIds,
    evidence_payload_hashes: evidencePayloadHashes,
    exclusion_reason: null,
  }
}

describe('Wave 4 response accountability', () => {
  it('registers every obligation and required frontier identity exactly once', () => {
    const { contract } = completeFixture()
    const register = buildInquiryFactRegister(contract)

    expect(register.register_version).toBe('inquiry-fact-register-v1')
    expect(register.facts.filter((fact) => fact.kind === 'obligation')).toHaveLength(contract.obligations.length)
    expect(new Set(register.facts.map((fact) => fact.fact_id)).size).toBe(register.facts.length)
    expect(register.required_fact_ids).toEqual(register.facts
      .filter((fact) => fact.materiality === 'required')
      .map((fact) => fact.fact_id))
    expect(register.validation_errors).toEqual([])
    expect(register.register_hash).toMatch(/^sha256:[a-f0-9]{64}$/)
  })

  it('fails mandatory delivery when one relevant fact is absent from all response parts', () => {
    const { contract, evidencePayloads } = completeFixture()
    const register = buildInquiryFactRegister(contract)
    const omitted = register.required_fact_ids[0]!
    const delivered = register.facts.map((fact) => fact.fact_id).filter((factId) => factId !== omitted)
    const receipt = buildResponseCoverageReceipt({ contract, fact_register: register, delivery_parts: [part(register, delivered)], evidence_payloads: evidencePayloads })

    expect(receipt.status).toBe('INCOMPLETE_RESUMABLE')
    expect(receipt.missing_required_fact_ids).toEqual([omitted])
    expect(receipt.coverage.required_delivered).toBe(receipt.coverage.required_total - 1)
    expect(receipt.resume_required).toBe(true)
  })

  it('does not allow a required fact to disappear behind a permitted-exclusion claim', () => {
    const { contract, evidencePayloads } = completeFixture()
    const register = buildInquiryFactRegister(contract)
    const omitted = register.required_fact_ids[0]!
    const receipt = buildResponseCoverageReceipt({
      contract,
      fact_register: register,
      delivery_parts: [{
        ...part(register, [omitted], 'excluded'),
        kind: 'permitted_exclusion',
        exclusion_reason: 'compressed for length',
        evidence_payload_hashes: [],
        content_hash: inquiryResponsePartContentHash(register, [omitted], 'permitted_exclusion', 'compressed for length', []),
      }],
      evidence_payloads: evidencePayloads,
    })

    expect(receipt.status).toBe('INCOMPLETE_RESUMABLE')
    expect(receipt.invalid_delivery_claims).toContain(`required fact ${omitted} cannot be excluded`)
    expect(receipt.missing_required_fact_ids).toContain(omitted)
  })

  it('keeps an exhausted pagination continuation blocked and names the resumable frontier', () => {
    const initial = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'Give me a complete wealth outlook',
      scope_tuple: wealthScope,
      max_iterations: 1,
    })
    const paged = initial.plan_items.find((item) => item.scu_id === 'scu.yoga.firing_and_cancellation')!
    const otherPayloads = initial.plan_items
      .filter((item) => item.item_id !== paged.item_id)
      .map((item) => ({ item_id: item.item_id, page: 1 }))
    const payloadByItem = new Map(otherPayloads.map((payload) => [payload.item_id, payload]))
    const pageOne = { item_id: paged.item_id, page: 1 }
    const observed = applyInquiryObservations(initial, initial.plan_items
      .filter((item) => item.item_id !== paged.item_id)
      .map((item) => ({ item_id: item.item_id, disposition: 'served' as const, evidence_refs: [`retrieval:${stableFingerprint(payloadByItem.get(item.item_id))}`] })))
    const blocked = finalizeInquiryContract(recordInquiryExecution(observed, {
      item_id: paged.item_id,
      disposition: 'served',
      evidence_refs: [`retrieval:${stableFingerprint(pageOne)}`],
      pagination: { semantics: 'offset', exhausted: false, next: 50 },
      request_position_path: 'offset',
    }))
    const envelope = buildStructuredResponseAccountability(blocked, {
      response_text: 'Explicitly blocked with an open continuation.',
      evidence_payloads: [...otherPayloads, pageOne],
    })

    expect(envelope.response_coverage_receipt.status).toBe('BLOCKED')
    expect(envelope.response_coverage_receipt.resume_required).toBe(true)
    expect(envelope.response_coverage_receipt.continuation.exhausted).toBe(true)
    expect(envelope.response_coverage_receipt.continuation.frontier_ids).toContain(
      blocked.material_frontier.find((item) => item.scu_id === paged.scu_id)!.frontier_id,
    )
  })

  it('retains cumulative evidence through continuation and closes only after observed exhaustion', () => {
    const initial = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'Give me a complete wealth outlook',
      scope_tuple: wealthScope,
      max_iterations: 4,
    })
    const paged = initial.plan_items.find((item) => item.scu_id === 'scu.yoga.firing_and_cancellation')!
    const otherPayloads = initial.plan_items
      .filter((item) => item.item_id !== paged.item_id)
      .map((item) => ({ item_id: item.item_id, page: 1 }))
    const payloadByItem = new Map(otherPayloads.map((payload) => [payload.item_id, payload]))
    const pageOne = { item_id: paged.item_id, page: 1 }
    const pageTwo = { item_id: paged.item_id, page: 2 }
    const otherObserved = applyInquiryObservations(initial, initial.plan_items
      .filter((item) => item.item_id !== paged.item_id)
      .map((item) => ({ item_id: item.item_id, disposition: 'served' as const, evidence_refs: [`retrieval:${stableFingerprint(payloadByItem.get(item.item_id))}`] })))
    const firstPage = recordInquiryExecution(otherObserved, {
      item_id: paged.item_id,
      disposition: 'served',
      evidence_refs: [`retrieval:${stableFingerprint(pageOne)}`],
      pagination: { semantics: 'offset', exhausted: false, next: 50 },
      request_position_path: 'offset',
    })
    expect(buildStructuredResponseAccountability(firstPage, { response_text: 'Interim synthesis.', evidence_payloads: [...otherPayloads, pageOne] })
      .response_coverage_receipt.status).toBe('INCOMPLETE_RESUMABLE')

    const exhausted = finalizeInquiryContract(recordInquiryExecution(firstPage, {
      item_id: paged.item_id,
      disposition: 'empty',
      evidence_refs: [`retrieval:${stableFingerprint(pageTwo)}`],
      pagination: { semantics: 'offset', exhausted: true, next: null },
      request_position_path: 'offset',
    }))
    const envelope = buildStructuredResponseAccountability(exhausted, {
      response_text: 'Complete synthesis.',
      evidence_payloads: [...otherPayloads, pageOne, pageTwo],
    })
    const pagedFact = envelope.fact_register.facts.find((fact) => fact.obligation_id
      && exhausted.plan_items.find((item) => item.item_id === paged.item_id)?.obligation_ids.includes(fact.obligation_id))!

    expect(pagedFact.evidence_refs).toEqual(expect.arrayContaining([
      `retrieval:${stableFingerprint(pageOne)}`,
      `retrieval:${stableFingerprint(pageTwo)}`,
    ]))
    expect(envelope.response_coverage_receipt.status).toBe('COMPLETE')
    expect(envelope.response_coverage_receipt.continuation.frontier_ids).toEqual([])
    expect(envelope.response_coverage_receipt.resume_required).toBe(false)
  })

  it('emits a normalized complete receipt only when the structured findings deliver every fact', () => {
    const { contract, evidencePayloads } = completeFixture()
    const first = buildStructuredResponseAccountability(contract, { response_text: 'Complete grounded synthesis.', evidence_payloads: evidencePayloads })
    const second = buildStructuredResponseAccountability(contract, {
      response_text: 'Complete grounded synthesis.',
      evidence_payloads: [...evidencePayloads].reverse(),
    })

    expect(first.response_coverage_receipt.status).toBe('COMPLETE')
    expect(first.response_coverage_receipt.coverage.all_delivered).toBe(first.response_coverage_receipt.coverage.all_total)
    expect(first.response_coverage_receipt.coverage.synthesis_present).toBe(true)
    expect(first.response_coverage_receipt.missing_fact_ids).toEqual([])
    expect(first.response_coverage_receipt.receipt_hash).toBe(second.response_coverage_receipt.receipt_hash)
    expect(first.fact_register.register_hash).toBe(second.fact_register.register_hash)
  })

  it('cannot call a fact-only envelope complete when synthesis is absent', () => {
    const { contract, evidencePayloads } = completeFixture()
    const receipt = buildStructuredResponseAccountability(contract, { evidence_payloads: evidencePayloads }).response_coverage_receipt

    expect(receipt.status).toBe('INCOMPLETE_RESUMABLE')
    expect(receipt.coverage.synthesis_present).toBe(false)
    expect(receipt.resume_required).toBe(true)
  })

  it('rejects unknown fact identities instead of counting them as coverage', () => {
    const { contract, evidencePayloads } = completeFixture()
    const register = buildInquiryFactRegister(contract)
    const receipt = buildResponseCoverageReceipt({
      contract,
      fact_register: register,
      delivery_parts: [part(register, [...register.facts.map((fact) => fact.fact_id), 'fact:invented'])],
      evidence_payloads: evidencePayloads,
    })

    expect(receipt.status).toBe('INCOMPLETE_RESUMABLE')
    expect(receipt.invalid_delivery_claims).toContain('unknown fact fact:invented')
  })

  it('recomputes the contract-derived denominator and rejects a forged partial register', () => {
    const { contract, evidencePayloads } = completeFixture()
    const register = buildInquiryFactRegister(contract)
    const forged = {
      ...register,
      facts: register.facts.slice(1),
      required_fact_ids: register.required_fact_ids.slice(1),
    }
    const receipt = buildResponseCoverageReceipt({
      contract,
      fact_register: forged,
      delivery_parts: [part(register, register.facts.map((fact) => fact.fact_id))],
      evidence_payloads: evidencePayloads,
    })

    expect(receipt.status).toBe('INCOMPLETE_RESUMABLE')
    expect(receipt.invalid_delivery_claims).toContain(
      'fact register does not match the complete contract-derived denominator',
    )
    expect(receipt.coverage.all_total).toBe(register.facts.length)
  })

  it('rejects a contract whose immutable obligation denominator no longer matches its authorization hashes', () => {
    const { contract, evidencePayloads } = completeFixture()
    const forged = { ...contract, obligations: contract.obligations.slice(1) }
    const envelope = buildStructuredResponseAccountability(forged, {
      response_text: 'A forged smaller denominator must not complete.',
      evidence_payloads: evidencePayloads,
    })

    expect(envelope.response_coverage_receipt.status).not.toBe('COMPLETE')
    expect(envelope.response_coverage_receipt.invalid_delivery_claims).toContain(
      'inquiry contract authorization hashes do not match immutable contract content',
    )
  })

  it('verifies prose against the canonical response text instead of accepting a syntactic hash', () => {
    const { contract, evidencePayloads } = completeFixture()
    const valid = buildStructuredResponseAccountability(contract, {
      response_text: 'Grounded synthesis.',
      evidence_payloads: evidencePayloads,
    })
    const forgedParts = valid.delivery_parts.map((deliveryPart) => deliveryPart.kind === 'prose'
      ? { ...deliveryPart, content_hash: `sha256:${'0'.repeat(64)}` }
      : deliveryPart)
    const receipt = buildResponseCoverageReceipt({
      contract,
      fact_register: valid.fact_register,
      delivery_parts: forgedParts,
      evidence_payloads: evidencePayloads,
      response_text: 'Grounded synthesis.',
    })

    expect(receipt.status).toBe('INCOMPLETE_RESUMABLE')
    expect(receipt.invalid_delivery_claims).toContainEqual(expect.stringContaining('does not match canonical response text'))
  })

  it('does not deliver a fact when its evidence hash is absent from the canonical response payloads', () => {
    const { contract, evidencePayloads } = completeFixture()
    const envelope = buildStructuredResponseAccountability(contract, {
      response_text: 'Grounded synthesis.',
      evidence_payloads: evidencePayloads.slice(1),
    })

    expect(envelope.response_coverage_receipt.status).toBe('INCOMPLETE_RESUMABLE')
    expect(envelope.response_coverage_receipt.missing_fact_ids.length).toBeGreaterThan(0)
  })

  it('keeps supporting pending work and its open frontier resumable even if the legacy finalizer says complete', () => {
    const initial = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'Give me a complete wealth outlook',
      scope_tuple: wealthScope,
    })
    const supportingItem = initial.plan_items.find((item) => item.obligation_ids.every((obligationId) =>
      initial.obligations.find((obligation) => obligation.obligation_id === obligationId)?.materiality === 'supporting'))!
    const observedItems = initial.plan_items.filter((item) => item.item_id !== supportingItem.item_id)
    const evidencePayloads = observedItems.map((item) => ({ item_id: item.item_id, rows: [`finding:${item.item_id}`] }))
    const payloadByItem = new Map(observedItems.map((item, index) => [item.item_id, evidencePayloads[index]!]))
    const observations = observedItems.map((item, index) => ({
      item_id: item.item_id,
      disposition: 'served' as const,
      evidence_refs: [`retrieval:${stableFingerprint(payloadByItem.get(item.item_id))}`],
      ...(index === 0 ? { discovered_frontier: [{
        scu_id: 'scu.supporting.runtime-frontier',
        materiality: 'supporting' as const,
        reason: 'supporting evidence remains relevant',
      }] } : {}),
    }))
    const contract = finalizeInquiryContract(applyInquiryObservations(initial, observations))
    const envelope = buildStructuredResponseAccountability(contract, {
      response_text: 'Interim synthesis with supporting work still open.',
      evidence_payloads: evidencePayloads,
    })

    expect(contract.status).toBe('COMPLETE')
    expect(envelope.response_coverage_receipt.status).toBe('INCOMPLETE_RESUMABLE')
    expect(envelope.response_coverage_receipt.continuation.next_action_ids).toContain(supportingItem.item_id)
    expect(envelope.response_coverage_receipt.continuation.frontier_ids).not.toEqual([])
    expect(envelope.response_coverage_receipt.resume_required).toBe(true)
  })
})
