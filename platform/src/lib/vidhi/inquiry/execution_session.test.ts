import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { InquiryContract } from './types'

const lifecycle = vi.hoisted(() => ({
  create: vi.fn(), get: vi.fn(), list: vi.fn(), reserve: vi.fn(), mark: vi.fn(), commit: vi.fn(), finalize: vi.fn(), failClose: vi.fn(),
}))

vi.mock('./lifecycle_store', () => ({
  createInquiryLifecycle: lifecycle.create,
  getInquiryLifecycle: lifecycle.get,
  listInquiryEvidence: lifecycle.list,
  reserveInquiryAction: lifecycle.reserve,
  markInquiryActionDispatched: lifecycle.mark,
  commitInquiryObservation: lifecycle.commit,
  commitInquiryFinalization: lifecycle.finalize,
  failCloseAmbiguousInquiryAction: lifecycle.failClose,
}))

vi.mock('./index', () => ({
  recordInquiryExecution: vi.fn((contract: InquiryContract, observation: { item_id: string }) => ({
    ...contract,
    plan_items: contract.plan_items.map((item) => item.item_id === observation.item_id
      ? { ...item, state: 'observed' as const, observation: { disposition: 'served' as const, evidence_refs: ['managed:receipt'], gap_reason: null } }
      : item),
  })),
  failInquiryForAmbiguousDispatch: vi.fn((contract: InquiryContract) => ({ ...contract, status: 'BLOCKED' as const })),
}))

import { ManagedInquiryExecutionSession } from './execution_session'

const inquiryId = 'aaaaaaaa-1111-4000-8000-000000000001'
const chartId = 'bbbbbbbb-1111-4000-8000-000000000001'
const contract = {
  contract_id: 'contract-1', chart_id: chartId, status: 'INCOMPLETE',
  plan_items: [{ item_id: 'item-001', obligation_ids: ['obligation-1'], scu_id: 'scu.test', binding_id: 'registry:marsys://tool/L1/test', args: {}, state: 'ready', blocked_reason: null, observation: null }],
} as unknown as InquiryContract

function row(current = 'managed:initial', currentContract = contract) {
  return {
    inquiry_id: inquiryId, principal_uid: 'user-1', chart_id: chartId,
    semantic_contract_hash: 'semantic', execution_plan_hash: 'plan', capability_content_hash: 'catalog',
    capability_compatibility_version: 'v1', chart_overlay_version: 'overlay', chart_build_id: 'build',
    authorization_jsonb: contract, contract_jsonb: currentContract, status: currentContract.status,
    revision: 0, current_jti_hash: current, expires_at: '2026-09-18T00:00:00.000Z',
  }
}

describe('managed inquiry execution session', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    lifecycle.create.mockResolvedValue(row())
    lifecycle.reserve.mockResolvedValue({ status: 'acquired', reservation_hash: 'managed:dispatch', recovered: false })
    lifecycle.mark.mockResolvedValue(undefined)
    lifecycle.commit.mockResolvedValue('receipt-1')
  })

  it('recovers the exact inquiry and accepted evidence after a crash before terminal delivery without replaying its protected action', async () => {
    lifecycle.get.mockResolvedValueOnce(null)
    const first = await ManagedInquiryExecutionSession.open({
      inquiry_id: inquiryId, principal_uid: 'user-1', contract, expires_at: '2026-09-18T00:00:00.000Z',
    })
    expect(await first.beginAction('item-001')).toBe('acquired')
    await first.persistAcceptedObservation({
      plan_item_id: 'item-001', obligation_ids: ['obligation-1'], scu_id: 'scu.test',
      binding_id: 'registry:marsys://tool/L1/test', tool_name: 'test_tool', bundle: { results: [{ id: 'one' }] },
      disposition: 'served', pagination: { semantics: 'none', exhausted: true, next: null }, invocation_args: {},
    })

    const observed = {
      ...contract,
      plan_items: [{ ...contract.plan_items[0], state: 'observed' as const, observation: { disposition: 'served' as const, evidence_refs: ['managed:receipt'], gap_reason: null } }],
    } as unknown as InquiryContract
    lifecycle.get.mockResolvedValueOnce(row('managed:next', observed))
    lifecycle.list.mockResolvedValueOnce([{ inquiry_id: inquiryId, revision: 1, evidence_jsonb: { tool_name: 'test_tool', bundle: { results: [{ id: 'one' }] } } }])

    const recovered = await ManagedInquiryExecutionSession.open({
      inquiry_id: inquiryId, principal_uid: 'user-1', contract, expires_at: '2026-09-18T00:00:00.000Z',
    })
    expect(recovered.inquiryId).toBe(inquiryId)
    expect(recovered.currentContract.plan_items[0]?.state).toBe('observed')
    expect(recovered.readyActionIds).toEqual([])
    expect(await recovered.recoveredEvidence()).toEqual([{ tool_name: 'test_tool', bundle: { results: [{ id: 'one' }] } }])
    expect(lifecycle.create).toHaveBeenCalledTimes(1)
    expect(lifecycle.reserve).toHaveBeenCalledTimes(1)
    expect(lifecycle.commit).toHaveBeenCalledTimes(1)
  })

  it('reuses an already-finalized lifecycle after an outer-job completion gap without a second finalization CAS', async () => {
    const terminal = { ...contract, status: 'COMPLETE' as const, plan_items: [{ ...contract.plan_items[0], state: 'observed' as const }] } as unknown as InquiryContract
    lifecycle.get.mockResolvedValueOnce(row('terminal', terminal))
    lifecycle.list.mockResolvedValueOnce([{ inquiry_id: inquiryId, revision: 1, evidence_jsonb: { tool_name: 'test_tool', bundle: { results: [{ id: 'one' }] } } }])

    const recovered = await ManagedInquiryExecutionSession.open({
      inquiry_id: inquiryId, principal_uid: 'user-1', contract, expires_at: '2026-09-18T00:00:00.000Z',
    })
    expect(await recovered.finalizeWhenNoReady()).toBe(terminal)
    expect(await recovered.recoveredEvidence()).toEqual([{ tool_name: 'test_tool', bundle: { results: [{ id: 'one' }] } }])
    expect(lifecycle.finalize).not.toHaveBeenCalled()
    expect(lifecycle.create).not.toHaveBeenCalled()
  })

  it('closes an expired dispatched reservation by its stored hash without replaying the action', async () => {
    lifecycle.get.mockResolvedValueOnce(null)
    lifecycle.reserve
      .mockResolvedValueOnce({ status: 'acquired', reservation_hash: 'managed:dispatch', recovered: false })
      .mockResolvedValueOnce({ status: 'ambiguous', reservation_hash: 'managed:dispatch' })
    const first = await ManagedInquiryExecutionSession.open({
      inquiry_id: inquiryId, principal_uid: 'user-1', contract, expires_at: '2026-09-18T00:00:00.000Z',
    })
    expect(await first.beginAction('item-001')).toBe('acquired')

    lifecycle.get.mockResolvedValueOnce(row('managed:dispatch', contract))
    const recovered = await ManagedInquiryExecutionSession.open({
      inquiry_id: inquiryId, principal_uid: 'user-1', contract, expires_at: '2026-09-18T00:00:00.000Z',
    })
    expect(await recovered.beginAction('item-001')).toBe('ambiguous')
    await recovered.failClosedAmbiguity('item-001')

    expect(lifecycle.mark).toHaveBeenCalledTimes(1)
    expect(lifecycle.failClose).toHaveBeenCalledWith(expect.objectContaining({
      expected_reservation_hash: 'managed:dispatch', plan_item_id: 'item-001',
    }))
    expect(recovered.currentContract.status).toBe('BLOCKED')
  })
})
