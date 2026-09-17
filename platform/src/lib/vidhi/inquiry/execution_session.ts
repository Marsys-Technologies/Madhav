import { randomUUID } from 'node:crypto'
import { stableFingerprint } from '@/lib/retrieval/registry/knowledge/stable'
import {
  failInquiryForAmbiguousDispatch,
  recordInquiryExecution,
  type InquiryContract,
  type InquiryPaginationReceipt,
} from './index'
import {
  commitInquiryObservation,
  commitInquiryFinalization,
  createInquiryLifecycle,
  failCloseAmbiguousInquiryAction,
  getInquiryLifecycle,
  listInquiryEvidence,
  markInquiryActionDispatched,
  reserveInquiryAction,
  type InquiryLifecycleRow,
} from './lifecycle_store'

/**
 * Server-only continuation state for a managed Prashna job.  The job's
 * immutable request carries this inquiry_id; workers never mint another one
 * after a lease recovery.  Unlike the external raw-MCP door, this service is
 * authenticated by the managed-job principal rather than a client token.
 */
export class ManagedInquiryExecutionSession {
  private constructor(
    private row: InquiryLifecycleRow,
    private contract: InquiryContract,
  ) {}

  static async open(args: {
    inquiry_id: string
    principal_uid: string
    contract: InquiryContract
    expires_at: string
  }): Promise<ManagedInquiryExecutionSession> {
    const existing = await getInquiryLifecycle(args.inquiry_id, args.principal_uid, args.contract.chart_id)
    if (existing) return new ManagedInquiryExecutionSession(existing, existing.contract_jsonb)

    const initialHash = `managed:${stableFingerprint(randomUUID())}`
    try {
      const created = await createInquiryLifecycle({
        inquiry_id: args.inquiry_id,
        principal_uid: args.principal_uid,
        contract: args.contract,
        jti_hash: initialHash,
        expires_at: args.expires_at,
      })
      return new ManagedInquiryExecutionSession(created, created.contract_jsonb)
    } catch (error) {
      // A competing recovered worker may have created the row after our first
      // read. Resolve that exact durable identity; never replace it.
      const recovered = await getInquiryLifecycle(args.inquiry_id, args.principal_uid, args.contract.chart_id)
      if (recovered) return new ManagedInquiryExecutionSession(recovered, recovered.contract_jsonb)
      throw error
    }
  }

  get inquiryId(): string { return this.row.inquiry_id }
  get currentContract(): InquiryContract { return this.contract }
  get readyActionIds(): readonly string[] {
    return this.contract.plan_items.filter((item) => item.state === 'ready').map((item) => item.item_id)
  }

  async recoveredEvidence(): Promise<Array<{ tool_name: string; bundle: unknown }>> {
    const evidence = await listInquiryEvidence(this.row.inquiry_id, this.row.principal_uid, this.row.chart_id)
    return evidence.flatMap((receipt) => {
      const payload = receipt.evidence_jsonb
      if (!payload || typeof payload !== 'object') return []
      const toolName = (payload as { tool_name?: unknown }).tool_name
      const bundle = (payload as { bundle?: unknown }).bundle
      return typeof toolName === 'string' && bundle !== undefined ? [{ tool_name: toolName, bundle }] : []
    })
  }

  /** Reserve and cross the protected dispatch boundary for one exact plan item. */
  async beginAction(planItemId: string): Promise<'acquired' | 'in_progress' | 'ambiguous'> {
    const reservation = await reserveInquiryAction({
      row: this.row,
      // Managed callers hold no client JTI. The persisted CAS hash itself is
      // the server-authenticated expected value under the job's principal RLS.
      expected_jti_hash: this.row.current_jti_hash,
      reservation_hash: `managed:${stableFingerprint(randomUUID())}`,
      plan_item_id: planItemId,
    })
    if (reservation.status !== 'acquired') return reservation.status
    await markInquiryActionDispatched({
      row: this.row,
      plan_item_id: planItemId,
      reservation_hash: reservation.reservation_hash,
    })
    this.row = { ...this.row, current_jti_hash: reservation.reservation_hash }
    return 'acquired'
  }

  async failClosedAmbiguity(planItemId: string): Promise<void> {
    const blocked = failInquiryForAmbiguousDispatch(this.contract, planItemId)
    await failCloseAmbiguousInquiryAction({
      row: this.row,
      expected_source_jti_hash: this.row.current_jti_hash,
      plan_item_id: planItemId,
      contract: blocked,
    })
    this.contract = blocked
    this.row = { ...this.row, contract_jsonb: blocked, status: blocked.status, revision: this.row.revision + 1, current_jti_hash: 'terminal' }
  }

  /**
   * Persist accepted raw evidence and its continuation receipt before the
   * caller acknowledges progress. The lifecycle compare-and-swap also commits
   * the dispatched reservation, so a recovery cannot replay this action.
   */
  async persistAcceptedObservation(args: {
    plan_item_id: string
    obligation_ids: readonly string[]
    scu_id: string
    binding_id: string
    tool_name: string
    bundle: unknown
    disposition: 'served' | 'empty' | 'failed'
    pagination: InquiryPaginationReceipt
    gap_reason?: string
    invocation_args: Readonly<Record<string, unknown>>
  }): Promise<void> {
    const observed = recordInquiryExecution(this.contract, {
      item_id: args.plan_item_id,
      disposition: args.disposition,
      evidence_refs: [`managed:${stableFingerprint(args.bundle)}`],
      ...(args.gap_reason ? { gap_reason: args.gap_reason } : {}),
      pagination: args.pagination,
    })
    const nextHash = `managed:${stableFingerprint(randomUUID())}`
    await commitInquiryObservation({
      row: this.row,
      expected_jti_hash: this.row.current_jti_hash,
      next_jti_hash: nextHash,
      contract: observed,
      evidence: {
        plan_item_id: args.plan_item_id,
        obligation_ids: args.obligation_ids,
        scu_id: args.scu_id,
        binding_id: args.binding_id,
        canonical_args_hash: stableFingerprint(args.invocation_args),
        raw_result_hash: stableFingerprint(args.bundle),
        disposition: args.disposition,
        pagination: args.pagination,
        // Retaining the accepted bundle is what lets a recovered worker
        // synthesize with prior evidence instead of re-dispatching it.
        payload: { tool_name: args.tool_name, bundle: args.bundle },
      },
    })
    this.contract = observed
    this.row = {
      ...this.row,
      contract_jsonb: observed,
      status: observed.status,
      revision: this.row.revision + 1,
      current_jti_hash: nextHash,
    }
  }

  async finalizeWhenNoReady(): Promise<InquiryContract> {
    // The outer managed-job write can be lost after this lifecycle CAS. A
    // recovering worker must reuse the terminal lifecycle/evidence, not try a
    // second finalization against its terminal JTI.
    if (this.row.status !== 'INCOMPLETE' || this.row.current_jti_hash === 'terminal') return this.contract
    if (this.contract.plan_items.some((item) => item.state === 'ready')) return this.contract
    const final = (await import('./compiler')).finalizeInquiryContract(this.contract)
    await commitInquiryFinalization({
      row: this.row,
      expected_jti_hash: this.row.current_jti_hash,
      contract: final,
    })
    this.contract = final
    this.row = { ...this.row, contract_jsonb: final, status: final.status, revision: this.row.revision + 1, current_jti_hash: 'terminal' }
    return final
  }

  /** Persist a non-dispatch terminal condition such as pinned-overlay drift. */
  async failClosed(contract: InquiryContract): Promise<InquiryContract> {
    await commitInquiryFinalization({
      row: this.row,
      expected_jti_hash: this.row.current_jti_hash,
      contract,
    })
    this.contract = contract
    this.row = { ...this.row, contract_jsonb: contract, status: contract.status, revision: this.row.revision + 1, current_jti_hash: 'terminal' }
    return contract
  }
}
