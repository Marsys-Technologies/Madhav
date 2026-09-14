import { describe, expect, it, vi } from 'vitest'
import type { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'
import { getCatalog } from '@/lib/retrieval/registry/catalog'
import { compileCapabilityKnowledge } from '@/lib/retrieval/registry/knowledge/compiler'
import {
  applyInquiryObservations,
  compileInquiryContract,
  finalizeInquiryContract,
  recordInquiryExecution,
} from '@/lib/vidhi/inquiry'
import type { ScopeTuple } from '@/lib/vidhi/types'
import { emitCompletenessReceipt } from '../receipt_stage'

const wealthScope: ScopeTuple = {
  intent: 'wealth_deepdive',
  domains: ['wealth'],
  width: 'panoramic',
  depth: 'deepdive',
  horizon: 'multi_year',
  intervention: false,
  entitlement: 'native',
}

describe('inquiry completeness receipt', () => {
  it('reports required capped frontier items as unresolved', () => {
    const snapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-13T00:00:00.000Z')
    const initial = compileInquiryContract({
      snapshot,
      chart_id: 'chart-fixture',
      question: 'Complete wealth outlook',
      scope_tuple: wealthScope,
      max_iterations: 1,
    })
    const paged = initial.plan_items.find((item) => item.scu_id === 'scu.yoga.firing_and_cancellation')!
    const observed = applyInquiryObservations(initial, initial.plan_items
      .filter((item) => item.item_id !== paged.item_id)
      .map((item) => ({ item_id: item.item_id, disposition: 'served' as const, evidence_refs: [`receipt:${item.item_id}`] })))
    const contract = finalizeInquiryContract(recordInquiryExecution(observed, {
      item_id: paged.item_id,
      disposition: 'served',
      evidence_refs: ['receipt:page-1'],
      pagination: { semantics: 'offset', exhausted: false, next: 50 },
      request_position_path: 'offset',
    }))
    const grade = vi.fn()

    const doorParity = emitCompletenessReceipt({
      em: { grade } as unknown as PariprashnaEmitter,
      completenessReceipt: null,
      inquiryContract: contract,
    })

    expect(grade).toHaveBeenCalledWith(expect.objectContaining({
      subject: 'inquiry_contract',
      grade: 'BLOCKED',
      detail: expect.stringContaining('1 required frontier items unresolved'),
    }))
    const responseCall = grade.mock.calls.find(([value]) => value.subject === 'response_accountability')
    expect(responseCall?.[0]).toMatchObject({
      subject: 'response_accountability',
      grade: 'BLOCKED',
    })
    const accountability = JSON.parse(responseCall![0].detail)
    expect(accountability.fact_register.facts).toHaveLength(
      contract.obligations.length + contract.material_frontier.length,
    )
    expect(accountability.response_coverage_receipt.continuation.frontier_ids).not.toEqual([])
    expect(doorParity).toMatchObject({
      parity_version: 'inquiry-door-parity-v1',
      semantic_contract_hash: contract.semantic_contract_hash,
      status: 'BLOCKED',
    })
  })
})
