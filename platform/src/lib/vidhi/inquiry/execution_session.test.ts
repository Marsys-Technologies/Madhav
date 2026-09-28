import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { InquiryContract } from './types'

const lifecycle = vi.hoisted(() => ({
  create: vi.fn(), get: vi.fn(), list: vi.fn(), reserve: vi.fn(), mark: vi.fn(), commit: vi.fn(), finalize: vi.fn(), failClose: vi.fn(),
  createSuccessor: vi.fn(),
}))
const successorCompiler = vi.hoisted(() => ({
  closeForSuccessor: vi.fn(), compileSuccessor: vi.fn(),
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
  createInquirySuccessorLifecycle: lifecycle.createSuccessor,
}))

vi.mock('./index', () => ({
  recordInquiryExecution: vi.fn((contract: InquiryContract, observation: { item_id: string }) => ({
    ...contract,
    plan_items: contract.plan_items.map((item) => item.item_id === observation.item_id
      ? { ...item, state: 'observed' as const, observation: { disposition: 'served' as const, evidence_refs: ['managed:receipt'], gap_reason: null } }
      : item),
  })),
  failInquiryForAmbiguousDispatch: vi.fn((contract: InquiryContract) => ({ ...contract, status: 'BLOCKED' as const })),
  closeInquiryForEvidenceSuccessor: successorCompiler.closeForSuccessor,
  compileInquirySuccessorContract: successorCompiler.compileSuccessor,
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
    inquiry_id: inquiryId, parent_inquiry_id: null as string | null, principal_uid: 'user-1', chart_id: chartId,
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
    successorCompiler.closeForSuccessor.mockReset()
    successorCompiler.compileSuccessor.mockReset()
    lifecycle.createSuccessor.mockReset()
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

  it('forwards the binding request position so a managed continuation page is re-readied (RC-5.5)', async () => {
    const { recordInquiryExecution } = await import('./index')
    lifecycle.get.mockResolvedValueOnce(null)
    const session = await ManagedInquiryExecutionSession.open({
      inquiry_id: inquiryId, principal_uid: 'user-1', contract, expires_at: '2026-09-18T00:00:00.000Z',
    })
    expect(await session.beginAction('item-001')).toBe('acquired')
    await session.persistAcceptedObservation({
      plan_item_id: 'item-001', obligation_ids: ['obligation-1'], scu_id: 'scu.test',
      binding_id: 'registry:marsys://tool/L1/test', tool_name: 'test_tool', bundle: { results: [{ id: 'one' }] },
      disposition: 'served', pagination: { semantics: 'offset', exhausted: false, next: 50 }, invocation_args: { offset: 0 },
      request_position_path: 'offset',
    })

    expect(recordInquiryExecution).toHaveBeenCalledWith(contract, expect.objectContaining({
      item_id: 'item-001',
      pagination: { semantics: 'offset', exhausted: false, next: 50 },
      request_position_path: 'offset',
    }))
  })

  it('records a never-dispatched item durably without putting any result into recovered evidence', async () => {
    lifecycle.get.mockResolvedValueOnce(null)
    const session = await ManagedInquiryExecutionSession.open({
      inquiry_id: inquiryId, principal_uid: 'user-1', contract, expires_at: '2026-09-18T00:00:00.000Z',
    })
    expect(await session.beginAction('item-001')).toBe('acquired')
    await session.persistAcceptedObservation({
      plan_item_id: 'item-001', obligation_ids: ['obligation-1'], scu_id: 'scu.test',
      binding_id: 'registry:marsys://tool/L1/test', tool_name: 'marsys://tool/L1/test', bundle: undefined,
      disposition: 'failed', gap_reason: 'successor_capability_not_authorized_for_request',
      pagination: { semantics: 'none', exhausted: true, next: null }, invocation_args: {},
    })
    const committed = lifecycle.commit.mock.calls.at(-1)![0] as { evidence: { raw_result_hash: string; disposition: string; payload: { bundle?: unknown } } }
    expect(committed.evidence.disposition).toBe('failed')
    expect(committed.evidence.raw_result_hash).toMatch(/^sha256:[0-9a-f]{64}$/)
    // The persisted payload round-trips through JSON: an undefined bundle is dropped, so recovery
    // (which requires a defined bundle) can never replay a fabricated result into synthesis.
    const roundTripped = JSON.parse(JSON.stringify(committed.evidence.payload)) as { bundle?: unknown }
    expect(roundTripped.bundle).toBeUndefined()
    lifecycle.list.mockResolvedValueOnce([{ inquiry_id: inquiryId, revision: 1, evidence_jsonb: roundTripped }])
    expect(await session.recoveredEvidence()).toEqual([])
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

  describe('evidence-admitted successor (R2B.4b)', () => {
    const snapshot = {} as never
    const overlay = { overlay_version: 'ov', build_id: 'bd' } as never
    const blockedParent = { ...contract, status: 'BLOCKED' as const, status_reasons: ['evidence-admitted successor issued'] } as unknown as InquiryContract
    const successorContract = {
      ...contract, contract_id: 'contract-successor', status: 'INCOMPLETE' as const,
      plan_items: [{ ...contract.plan_items[0], item_id: 'item-901', scu_id: 'scu.discovered' }],
    } as unknown as InquiryContract

    it('hands the remaining work to the deterministic successor id and adopts its lifecycle', async () => {
      lifecycle.get.mockResolvedValueOnce(null)
      const session = await ManagedInquiryExecutionSession.open({
        inquiry_id: inquiryId, principal_uid: 'user-1', contract, expires_at: '2026-09-18T00:00:00.000Z',
      })
      // No ready items left — the precondition continueWithEvidenceSuccessor checks itself.
      Object.defineProperty(session, 'contract', { value: { ...contract, status: 'INCOMPLETE', plan_items: [] }, writable: true })
      successorCompiler.closeForSuccessor.mockReturnValue(blockedParent)
      successorCompiler.compileSuccessor.mockReturnValue(successorContract)
      const created = row('managed:successor-current', successorContract)
      created.inquiry_id = 'deterministic-successor-id'
      created.parent_inquiry_id = inquiryId
      lifecycle.createSuccessor.mockResolvedValue(created)

      const result = await session.continueWithEvidenceSuccessor({ snapshot, overlay })
      expect(result).toBe(true)
      expect(successorCompiler.compileSuccessor).toHaveBeenCalledWith(expect.objectContaining({
        parent_inquiry_id: inquiryId, parent: blockedParent, cross_capability_only: true,
      }))
      expect(lifecycle.createSuccessor).toHaveBeenCalledWith(expect.objectContaining({
        parent_final_contract: blockedParent, contract: successorContract,
      }))
      expect(session.currentContract).toBe(successorContract)
      expect(session.inquiryId).toBe('deterministic-successor-id')
    })

    it('changes nothing when no admissible cross-capability frontier exists', async () => {
      lifecycle.get.mockResolvedValueOnce(null)
      const session = await ManagedInquiryExecutionSession.open({
        inquiry_id: inquiryId, principal_uid: 'user-1', contract, expires_at: '2026-09-18T00:00:00.000Z',
      })
      successorCompiler.closeForSuccessor.mockImplementation(() => { throw new Error('INQUIRY_SUCCESSOR_NO_EVIDENCE_ADMITTED_FRONTIER') })
      const result = await session.continueWithEvidenceSuccessor({ snapshot, overlay })
      expect(result).toBe(false)
      expect(lifecycle.createSuccessor).not.toHaveBeenCalled()
      expect(session.currentContract).toBe(contract)
    })

    it('resumes a recovered parent by following it to its deterministic successor', async () => {
      const { managedEvidenceSuccessorInquiryId } = await import('./execution_session')
      const successorId = managedEvidenceSuccessorInquiryId(inquiryId)
      const terminalParentRow = row('terminal', blockedParent)
      const successorRow = { ...row('managed:successor-current', successorContract), inquiry_id: successorId, parent_inquiry_id: inquiryId }
      lifecycle.get
        .mockResolvedValueOnce(terminalParentRow) // ManagedInquiryExecutionSession.open's own lookup
        .mockResolvedValueOnce(successorRow) // resumeChain's follow
      const session = await ManagedInquiryExecutionSession.open({
        inquiry_id: inquiryId, principal_uid: 'user-1', contract, expires_at: '2026-09-18T00:00:00.000Z',
      })
      expect(session.inquiryId).toBe(successorId)
      expect(session.currentContract).toBe(successorContract)
    })

    it('never fabricates a successor id: two calls for the same parent agree', async () => {
      const { managedEvidenceSuccessorInquiryId } = await import('./execution_session')
      const a = managedEvidenceSuccessorInquiryId(inquiryId)
      const b = managedEvidenceSuccessorInquiryId(inquiryId)
      const other = managedEvidenceSuccessorInquiryId('cccccccc-1111-4000-8000-000000000099')
      expect(a).toBe(b)
      expect(a).not.toBe(other)
      expect(a).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/)
    })

    it('accounts for a parent\'s evidence when recovering a successor\'s receipts', async () => {
      lifecycle.get.mockResolvedValueOnce(null)
      const session = await ManagedInquiryExecutionSession.open({
        inquiry_id: 'successor-1', principal_uid: 'user-1',
        contract: { ...successorContract }, expires_at: '2026-09-18T00:00:00.000Z',
      })
      Object.defineProperty(session, 'row', {
        value: { ...row('managed:x', successorContract), inquiry_id: 'successor-1', parent_inquiry_id: inquiryId },
        writable: true,
      })
      lifecycle.get.mockResolvedValueOnce({ ...row(), inquiry_id: inquiryId, parent_inquiry_id: null })
      lifecycle.list
        .mockResolvedValueOnce([{ inquiry_id: inquiryId, revision: 1, evidence_jsonb: { tool_name: 'parent_tool', bundle: { results: [{ id: 'one' }] } } }])
        .mockResolvedValueOnce([{ inquiry_id: 'successor-1', revision: 0, evidence_jsonb: { tool_name: 'successor_tool', bundle: { results: [{ id: 'two' }] } } }])
      const evidence = await session.recoveredEvidence()
      expect(evidence).toEqual([
        { tool_name: 'parent_tool', bundle: { results: [{ id: 'one' }] } },
        { tool_name: 'successor_tool', bundle: { results: [{ id: 'two' }] } },
      ])
    })
  })
})
