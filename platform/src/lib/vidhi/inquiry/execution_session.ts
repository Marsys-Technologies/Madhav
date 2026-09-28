import { createHash, randomUUID } from 'node:crypto'
import { stableFingerprint } from '@/lib/retrieval/registry/knowledge/stable'
import type { CapabilityKnowledgeSnapshot, ChartCapabilityOverlay } from '@/lib/retrieval/registry/knowledge/types'
import {
  closeInquiryForEvidenceSuccessor,
  compileInquirySuccessorContract,
  failInquiryForAmbiguousDispatch,
  recordInquiryExecution,
  type InquiryContract,
  type InquiryPaginationReceipt,
} from './index'
import type { DiscoveredEvidenceFrontier } from './evidence_frontier'
import { MAX_SUCCESSOR_DEPTH, type SuccessorAdmissionDecision, type SuccessorAdmissionLiveContext } from './authorization_envelope'
import {
  commitInquiryObservation,
  commitInquiryFinalization,
  createInquiryLifecycle,
  createInquirySuccessorLifecycle,
  failCloseAmbiguousInquiryAction,
  getInquiryLifecycle,
  listInquiryEvidence,
  markInquiryActionDispatched,
  reserveInquiryAction,
  type InquiryLifecycleRow,
} from './lifecycle_store'

const EVIDENCE_SUCCESSOR_REASON = 'evidence-admitted successor issued'
// One ceiling for the whole lineage, shared with the authorization envelope's depth limit.
const MAX_MANAGED_SUCCESSOR_CHAIN = MAX_SUCCESSOR_DEPTH

/**
 * The one successor identity a managed parent can ever have. Deterministic, so a worker that
 * recovers the job after the successor transition resumes that exact lifecycle instead of
 * treating the terminal parent as the job's final result.
 */
export function managedEvidenceSuccessorInquiryId(parentInquiryId: string): string {
  const hex = createHash('sha256').update(`managed-evidence-successor:${parentInquiryId}`).digest('hex')
  const variant = ((parseInt(hex[16]!, 16) & 0x3) | 0x8).toString(16)
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-5${hex.slice(13, 16)}-${variant}${hex.slice(17, 20)}-${hex.slice(20, 32)}`
}

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
    if (existing) return ManagedInquiryExecutionSession.resumeChain(existing, args.principal_uid)

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
      if (recovered) return ManagedInquiryExecutionSession.resumeChain(recovered, args.principal_uid)
      throw error
    }
  }

  /** Follow a terminal parent to the evidence successor it handed its work to, if any. */
  private static async resumeChain(row: InquiryLifecycleRow, principalUid: string): Promise<ManagedInquiryExecutionSession> {
    let current = row
    for (let depth = 0; depth < MAX_MANAGED_SUCCESSOR_CHAIN; depth += 1) {
      if (current.current_jti_hash !== 'terminal' || !(current.contract_jsonb.status_reasons ?? []).includes(EVIDENCE_SUCCESSOR_REASON)) break
      const successor = await getInquiryLifecycle(managedEvidenceSuccessorInquiryId(current.inquiry_id), principalUid, current.chart_id)
      if (!successor) break
      current = successor
    }
    return new ManagedInquiryExecutionSession(current, current.contract_jsonb)
  }

  get inquiryId(): string { return this.row.inquiry_id }
  /** The durable lifecycle owner: the principal the row is scoped to (read from the row, not the request). */
  get principalUid(): string { return this.row.principal_uid }
  /** Non-null exactly when the durable row is an evidence successor: an independent marker of lineage. */
  get parentInquiryId(): string | null { return this.row.parent_inquiry_id }
  get currentContract(): InquiryContract { return this.contract }
  get readyActionIds(): readonly string[] {
    return this.contract.plan_items.filter((item) => item.state === 'ready').map((item) => item.item_id)
  }

  async recoveredEvidence(): Promise<Array<{ tool_name: string; bundle: unknown }>> {
    // A successor's answer accounts for its parents' evidence too (the register inherits it).
    const inquiryIds = [this.row.inquiry_id]
    let parentId = this.row.parent_inquiry_id
    while (parentId && inquiryIds.length <= MAX_MANAGED_SUCCESSOR_CHAIN) {
      inquiryIds.unshift(parentId)
      const parent = await getInquiryLifecycle(parentId, this.row.principal_uid, this.row.chart_id)
      parentId = parent?.parent_inquiry_id ?? null
    }
    const evidence = (await Promise.all(inquiryIds.map((inquiryId) =>
      listInquiryEvidence(inquiryId, this.row.principal_uid, this.row.chart_id)))).flat()
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
      // On recovery this is the stored reservation hash. The original source
      // JTI was consumed before dispatch and must never be reconstructed.
      expected_reservation_hash: this.row.current_jti_hash,
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
    /** `undefined` records an item that was never dispatched (e.g. its capability was not
     *  authorized for this request): the receipt is retained, but no result enters recovered evidence. */
    bundle: unknown
    disposition: 'served' | 'empty' | 'failed'
    pagination: InquiryPaginationReceipt
    gap_reason?: string
    invocation_args: Readonly<Record<string, unknown>>
    /** The binding's pagination request path. Without it a proven continuation cannot be
     *  re-readied, and the managed door would stop after the first page (RC-5.5). */
    request_position_path?: string
    /** Capabilities this served observation calls for (RC-5.4); admitted only via a successor. */
    evidence_frontier?: readonly DiscoveredEvidenceFrontier[]
    /** The dispatch-time envelope decision for a successor item (admit or refuse); receipted with the observation. */
    successor_dispatch?: SuccessorAdmissionDecision
  }): Promise<void> {
    const fingerprintSource = args.bundle === undefined
      ? { not_dispatched: true, gap_reason: args.gap_reason ?? null }
      : args.bundle
    let observed = recordInquiryExecution(this.contract, {
      item_id: args.plan_item_id,
      disposition: args.disposition,
      evidence_refs: [`managed:${stableFingerprint(fingerprintSource)}`],
      ...(args.gap_reason ? { gap_reason: args.gap_reason } : {}),
      pagination: args.pagination,
      ...(args.request_position_path ? { request_position_path: args.request_position_path } : {}),
      ...(args.evidence_frontier?.length ? { evidence_frontier: args.evidence_frontier } : {}),
      ...(args.successor_dispatch ? { successor_dispatch: args.successor_dispatch } : {}),
    })
    if (args.bundle === undefined) {
      // A never-dispatched item is terminal. recordInquiryExecution re-readies a failed item for
      // retry while iterations remain, but retrying something that was never authorized would
      // strand the lifecycle (finalizeWhenNoReady refuses while any item is ready).
      observed = {
        ...observed,
        plan_items: observed.plan_items.map((item) => item.item_id === args.plan_item_id
          ? { ...item, state: 'observed' as const }
          : item),
      }
    }
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
        raw_result_hash: stableFingerprint(fingerprintSource),
        disposition: args.disposition,
        pagination: args.pagination,
        // Retaining the accepted bundle is what lets a recovered worker
        // synthesize with prior evidence instead of re-dispatching it.
        payload: {
          tool_name: args.tool_name,
          bundle: args.bundle,
          ...(args.successor_dispatch ? { admission: args.successor_dispatch } : {}),
        },
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

  /**
   * Hand the remaining evidence-admitted work to one durable successor (RC-5.4) instead of
   * finalizing. Only a cross-capability frontier discovered from served evidence qualifies — a
   * capped pagination frontier never carries the job past its own budget. The parent is
   * terminalized and the successor created atomically, under the deterministic successor id.
   * Returns false, changing nothing, when no successor is admissible.
   */
  async continueWithEvidenceSuccessor(args: {
    snapshot: CapabilityKnowledgeSnapshot
    overlay: ChartCapabilityOverlay
    /** The door's server-held state for the shared authorization envelope; omitting it refuses every item. */
    admission?: SuccessorAdmissionLiveContext
  }): Promise<boolean> {
    if (this.row.status !== 'INCOMPLETE' || this.row.current_jti_hash === 'terminal') return false
    if (this.contract.plan_items.some((item) => item.state === 'ready')) return false
    let parentFinal: InquiryContract
    let successor: InquiryContract
    try {
      parentFinal = closeInquiryForEvidenceSuccessor(this.contract)
      successor = compileInquirySuccessorContract({
        snapshot: args.snapshot, overlay: args.overlay, parent_inquiry_id: this.row.inquiry_id,
        parent: parentFinal, cross_capability_only: true, ...(args.admission ? { admission: args.admission } : {}),
      })
    } catch {
      return false
    }
    const created = await createInquirySuccessorLifecycle({
      parent: this.row,
      expected_parent_jti_hash: this.row.current_jti_hash,
      parent_final_contract: parentFinal,
      inquiry_id: managedEvidenceSuccessorInquiryId(this.row.inquiry_id),
      contract: successor,
      jti_hash: `managed:${stableFingerprint(randomUUID())}`,
      expires_at: this.row.expires_at,
    })
    this.row = created
    this.contract = created.contract_jsonb
    return true
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
