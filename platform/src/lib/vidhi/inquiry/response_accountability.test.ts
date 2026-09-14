import { describe, expect, it } from 'vitest'
import { getCatalog } from '../../retrieval/registry/catalog'
import { compileCapabilityKnowledge } from '../../retrieval/registry/knowledge/compiler'
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

function completeContract(): InquiryContract {
  const initial = compileInquiryContract({
    snapshot,
    chart_id: 'chart-fixture',
    question: 'Give me a complete wealth outlook',
    scope_tuple: wealthScope,
  })
  return finalizeInquiryContract(applyInquiryObservations(initial, initial.plan_items.map((item) => ({
    item_id: item.item_id,
    disposition: 'served' as const,
    evidence_refs: [`retrieval:${item.item_id}:sha256:evidence`],
  }))))
}

function part(register: ReturnType<typeof buildInquiryFactRegister>, factIds: readonly string[], suffix = 'all'): InquiryResponseDeliveryPart {
  return {
    part_id: `structured-findings:${suffix}`,
    kind: 'structured_findings',
    content_hash: inquiryResponsePartContentHash(register, factIds, 'structured_findings'),
    fact_ids: factIds,
    exclusion_reason: null,
  }
}

describe('Wave 4 response accountability', () => {
  it('registers every obligation and required frontier identity exactly once', () => {
    const contract = completeContract()
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
    const contract = completeContract()
    const register = buildInquiryFactRegister(contract)
    const omitted = register.required_fact_ids[0]!
    const delivered = register.facts.map((fact) => fact.fact_id).filter((factId) => factId !== omitted)
    const receipt = buildResponseCoverageReceipt({ contract, fact_register: register, delivery_parts: [part(register, delivered)] })

    expect(receipt.status).toBe('INCOMPLETE_RESUMABLE')
    expect(receipt.missing_required_fact_ids).toEqual([omitted])
    expect(receipt.coverage.required_delivered).toBe(receipt.coverage.required_total - 1)
    expect(receipt.resume_required).toBe(true)
  })

  it('does not allow a required fact to disappear behind a permitted-exclusion claim', () => {
    const contract = completeContract()
    const register = buildInquiryFactRegister(contract)
    const omitted = register.required_fact_ids[0]!
    const receipt = buildResponseCoverageReceipt({
      contract,
      fact_register: register,
      delivery_parts: [{
        ...part(register, [omitted], 'excluded'),
        kind: 'permitted_exclusion',
        exclusion_reason: 'compressed for length',
        content_hash: inquiryResponsePartContentHash(register, [omitted], 'permitted_exclusion', 'compressed for length'),
      }],
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
    const observed = applyInquiryObservations(initial, initial.plan_items
      .filter((item) => item.item_id !== paged.item_id)
      .map((item) => ({ item_id: item.item_id, disposition: 'served' as const, evidence_refs: [`receipt:${item.item_id}`] })))
    const blocked = finalizeInquiryContract(recordInquiryExecution(observed, {
      item_id: paged.item_id,
      disposition: 'served',
      evidence_refs: ['receipt:page-1'],
      pagination: { semantics: 'offset', exhausted: false, next: 50 },
      request_position_path: 'offset',
    }))
    const envelope = buildStructuredResponseAccountability(blocked, { response_text: 'Explicitly blocked with an open continuation.' })

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
    const otherObserved = applyInquiryObservations(initial, initial.plan_items
      .filter((item) => item.item_id !== paged.item_id)
      .map((item) => ({ item_id: item.item_id, disposition: 'served' as const, evidence_refs: [`receipt:${item.item_id}`] })))
    const firstPage = recordInquiryExecution(otherObserved, {
      item_id: paged.item_id,
      disposition: 'served',
      evidence_refs: ['receipt:page-1'],
      pagination: { semantics: 'offset', exhausted: false, next: 50 },
      request_position_path: 'offset',
    })
    expect(buildStructuredResponseAccountability(firstPage, { response_text: 'Interim synthesis.' })
      .response_coverage_receipt.status).toBe('INCOMPLETE_RESUMABLE')

    const exhausted = finalizeInquiryContract(recordInquiryExecution(firstPage, {
      item_id: paged.item_id,
      disposition: 'empty',
      evidence_refs: ['receipt:page-2'],
      pagination: { semantics: 'offset', exhausted: true, next: null },
      request_position_path: 'offset',
    }))
    const envelope = buildStructuredResponseAccountability(exhausted, { response_text: 'Complete synthesis.' })
    const pagedFact = envelope.fact_register.facts.find((fact) => fact.obligation_id
      && exhausted.plan_items.find((item) => item.item_id === paged.item_id)?.obligation_ids.includes(fact.obligation_id))!

    expect(pagedFact.evidence_refs).toEqual(expect.arrayContaining(['receipt:page-1', 'receipt:page-2']))
    expect(envelope.response_coverage_receipt.status).toBe('COMPLETE')
    expect(envelope.response_coverage_receipt.continuation.frontier_ids).toEqual([])
    expect(envelope.response_coverage_receipt.resume_required).toBe(false)
  })

  it('emits a normalized complete receipt only when the structured findings deliver every fact', () => {
    const contract = completeContract()
    const first = buildStructuredResponseAccountability(contract, { response_text: 'Complete grounded synthesis.' })
    const second = buildStructuredResponseAccountability({
      ...contract,
      obligations: [...contract.obligations].reverse(),
      plan_items: [...contract.plan_items].reverse(),
    }, { response_text: 'Complete grounded synthesis.' })

    expect(first.response_coverage_receipt.status).toBe('COMPLETE')
    expect(first.response_coverage_receipt.coverage.all_delivered).toBe(first.response_coverage_receipt.coverage.all_total)
    expect(first.response_coverage_receipt.coverage.synthesis_present).toBe(true)
    expect(first.response_coverage_receipt.missing_fact_ids).toEqual([])
    expect(first.response_coverage_receipt.receipt_hash).toBe(second.response_coverage_receipt.receipt_hash)
    expect(first.fact_register.register_hash).toBe(second.fact_register.register_hash)
  })

  it('cannot call a fact-only envelope complete when synthesis is absent', () => {
    const receipt = buildStructuredResponseAccountability(completeContract()).response_coverage_receipt

    expect(receipt.status).toBe('INCOMPLETE_RESUMABLE')
    expect(receipt.coverage.synthesis_present).toBe(false)
    expect(receipt.resume_required).toBe(true)
  })

  it('rejects unknown fact identities instead of counting them as coverage', () => {
    const contract = completeContract()
    const register = buildInquiryFactRegister(contract)
    const receipt = buildResponseCoverageReceipt({
      contract,
      fact_register: register,
      delivery_parts: [part(register, [...register.facts.map((fact) => fact.fact_id), 'fact:invented'])],
    })

    expect(receipt.status).toBe('INCOMPLETE_RESUMABLE')
    expect(receipt.invalid_delivery_claims).toContain('unknown fact fact:invented')
  })

  it('recomputes the contract-derived denominator and rejects a forged partial register', () => {
    const contract = completeContract()
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
    })

    expect(receipt.status).toBe('INCOMPLETE_RESUMABLE')
    expect(receipt.invalid_delivery_claims).toContain(
      'fact register does not match the complete contract-derived denominator',
    )
    expect(receipt.coverage.all_total).toBe(register.facts.length)
  })
})
