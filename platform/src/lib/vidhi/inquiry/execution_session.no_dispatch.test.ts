import { beforeEach, describe, expect, it, vi } from 'vitest'

// Real compiler (only the lifecycle store is faked): the mocked-compiler session tests cannot see
// that recordInquiryExecution re-readies a failed item, which is exactly what stranded a
// never-dispatched successor item.
const lifecycle = vi.hoisted(() => ({
  create: vi.fn(), get: vi.fn(), list: vi.fn(), reserve: vi.fn(), mark: vi.fn(), commit: vi.fn(), finalize: vi.fn(),
  failClose: vi.fn(), createSuccessor: vi.fn(),
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

import { getCatalog } from '../../retrieval/registry/catalog'
import { compileCapabilityKnowledge } from '../../retrieval/registry/knowledge/compiler'
import { compileInquiryContract, recordInquiryExecution } from './compiler'
import { ManagedInquiryExecutionSession } from './execution_session'
import type { ScopeTuple } from '../types'

const scope: ScopeTuple = {
  intent: 'wealth_deepdive', domains: ['wealth'], width: 'panoramic', depth: 'deepdive',
  horizon: 'multi_year', intervention: false, entitlement: 'native',
}
const inquiryId = 'aaaaaaaa-1111-4000-8000-000000000009'

describe('never-dispatched managed item terminalizes (re-review finding)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    lifecycle.get.mockResolvedValue(null)
    lifecycle.create.mockImplementation(async (args: { inquiry_id: string; contract: unknown; expires_at: string }) => ({
      inquiry_id: args.inquiry_id, parent_inquiry_id: null, principal_uid: 'user-1', chart_id: 'chart-fixture',
      semantic_contract_hash: 's', execution_plan_hash: 'p', capability_content_hash: 'c',
      capability_compatibility_version: 'v', chart_overlay_version: 'o', chart_build_id: 'b',
      authorization_jsonb: args.contract, contract_jsonb: args.contract, status: 'INCOMPLETE',
      revision: 0, current_jti_hash: 'managed:initial', expires_at: args.expires_at,
    }))
    lifecycle.reserve.mockResolvedValue({ status: 'acquired', reservation_hash: 'managed:dispatch', recovered: false })
    lifecycle.mark.mockResolvedValue(undefined)
    lifecycle.commit.mockResolvedValue('receipt')
    lifecycle.finalize.mockResolvedValue(undefined)
  })

  it('is not re-readied by the retry rule, so the lifecycle can finalize', async () => {
    const snapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-13T00:00:00.000Z')
    const contract = { ...compileInquiryContract({ snapshot, chart_id: 'chart-fixture', question: 'Complete wealth outlook', scope_tuple: scope }), max_iterations: 10 }
    const target = contract.plan_items.find((item) => item.state === 'ready')!

    // Documents the real behavior this fix compensates for.
    const naive = recordInquiryExecution(contract, {
      item_id: target.item_id, disposition: 'failed', evidence_refs: ['x'], gap_reason: 'successor_capability_not_authorized_for_request',
      pagination: { semantics: 'none', exhausted: true, next: null },
    })
    expect(naive.plan_items.find((item) => item.item_id === target.item_id)?.state).toBe('ready')

    const session = await ManagedInquiryExecutionSession.open({
      inquiry_id: inquiryId, principal_uid: 'user-1', contract, expires_at: '2026-09-18T00:00:00.000Z',
    })
    expect(await session.beginAction(target.item_id)).toBe('acquired')
    await session.persistAcceptedObservation({
      plan_item_id: target.item_id, obligation_ids: target.obligation_ids, scu_id: target.scu_id,
      binding_id: target.binding_id!, tool_name: 'x', bundle: undefined, disposition: 'failed',
      gap_reason: 'successor_capability_not_authorized_for_request',
      pagination: { semantics: 'none', exhausted: true, next: null }, invocation_args: target.args,
    })

    const committed = lifecycle.commit.mock.calls.at(-1)![0] as { contract: typeof contract }
    const stored = committed.contract.plan_items.find((item) => item.item_id === target.item_id)!
    expect(stored.state).toBe('observed')
    expect(stored.observation).toMatchObject({ disposition: 'failed', gap_reason: 'successor_capability_not_authorized_for_request' })
    expect(session.readyActionIds).not.toContain(target.item_id)
  })
})
