/**
 * An in-memory stand-in for `lifecycle_store` that keeps the durable store's compare-and-swap,
 * reservation and terminalization semantics, so tests can drive the REAL compiler and the REAL
 * managed/raw lifecycle through state transitions (a mocked session or a mocked compiler hides
 * exactly the re-readying and recovery behaviour these tests exist to prove). Test-only.
 */
import type { InquiryLifecycleRow, InquiryReservationResult } from '../lifecycle_store'
import type { InquiryContract } from '../types'

interface Reservation {
  source_jti_hash: string
  reservation_hash: string
  state: 'reserved' | 'dispatched' | 'committed' | 'failed_closed'
  lease_expired: boolean
}

export interface StoredEvidence {
  inquiry_id: string
  revision: number
  plan_item_id: string
  disposition: string
  evidence_jsonb: unknown
}

const STALE = 'INQUIRY_TOKEN_REPLAYED_OR_STALE'

export function createInMemoryLifecycleStore() {
  const rows = new Map<string, InquiryLifecycleRow>()
  const reservations = new Map<string, Reservation>()
  const evidence: StoredEvidence[] = []
  const key = (id: string, revision: number, item: string) => `${id}:${revision}:${item}`
  const live = (id: string): InquiryLifecycleRow => {
    const row = rows.get(id)
    if (!row) throw new Error(STALE)
    return row
  }
  const write = (row: InquiryLifecycleRow, patch: Partial<InquiryLifecycleRow>) => {
    const next = { ...row, ...patch }
    rows.set(row.inquiry_id, next)
    return next
  }

  return {
    rows,
    reservations,
    evidence,
    /** Every dispatched-but-uncommitted lease is now expired (a crashed worker's abandoned action). */
    expireLeases() { for (const reservation of reservations.values()) reservation.lease_expired = true },

    async createInquiryLifecycle(args: { inquiry_id: string; principal_uid: string; contract: InquiryContract; jti_hash: string; expires_at: string }): Promise<InquiryLifecycleRow> {
      if (rows.has(args.inquiry_id)) throw new Error('duplicate inquiry')
      const row: InquiryLifecycleRow = {
        inquiry_id: args.inquiry_id, parent_inquiry_id: null, principal_uid: args.principal_uid, chart_id: args.contract.chart_id,
        semantic_contract_hash: args.contract.semantic_contract_hash, execution_plan_hash: args.contract.execution_plan_hash,
        capability_content_hash: args.contract.capability_content_hash,
        capability_compatibility_version: args.contract.capability_compatibility_version,
        chart_overlay_version: args.contract.chart_availability_version, chart_build_id: args.contract.chart_build_id,
        authorization_jsonb: args.contract, contract_jsonb: args.contract, status: args.contract.status,
        revision: 0, current_jti_hash: args.jti_hash, expires_at: args.expires_at,
      }
      rows.set(row.inquiry_id, row)
      return row
    },

    async getInquiryLifecycle(inquiryId: string, principalUid: string, chartId: string): Promise<InquiryLifecycleRow | null> {
      const row = rows.get(inquiryId)
      return row && row.principal_uid === principalUid && row.chart_id === chartId ? row : null
    },

    async listInquiryEvidence(inquiryId: string): Promise<Array<{ inquiry_id: string; revision: number; evidence_jsonb: unknown }>> {
      return evidence.filter((entry) => entry.inquiry_id === inquiryId).sort((left, right) => left.revision - right.revision)
    },

    async createInquirySuccessorLifecycle(args: {
      parent: InquiryLifecycleRow; expected_parent_jti_hash: string; parent_final_contract: InquiryContract
      inquiry_id: string; contract: InquiryContract; jti_hash: string; expires_at: string
    }): Promise<InquiryLifecycleRow> {
      const parent = live(args.parent.inquiry_id)
      if (parent.revision !== args.parent.revision || parent.current_jti_hash !== args.expected_parent_jti_hash || parent.status !== 'INCOMPLETE') throw new Error(STALE)
      write(parent, { contract_jsonb: args.parent_final_contract, status: 'BLOCKED', revision: parent.revision + 1, current_jti_hash: 'terminal' })
      const child: InquiryLifecycleRow = {
        inquiry_id: args.inquiry_id, parent_inquiry_id: parent.inquiry_id, principal_uid: parent.principal_uid, chart_id: parent.chart_id,
        semantic_contract_hash: args.contract.semantic_contract_hash, execution_plan_hash: args.contract.execution_plan_hash,
        capability_content_hash: args.contract.capability_content_hash,
        capability_compatibility_version: args.contract.capability_compatibility_version,
        chart_overlay_version: args.contract.chart_availability_version, chart_build_id: args.contract.chart_build_id,
        authorization_jsonb: args.contract, contract_jsonb: args.contract, status: args.contract.status,
        revision: 0, current_jti_hash: args.jti_hash, expires_at: args.expires_at,
      }
      rows.set(child.inquiry_id, child)
      return child
    },

    async reserveInquiryAction(args: { row: InquiryLifecycleRow; expected_jti_hash: string; reservation_hash: string; plan_item_id: string }): Promise<InquiryReservationResult> {
      const current = live(args.row.inquiry_id)
      if (current.revision !== args.row.revision || current.status !== 'INCOMPLETE') throw new Error(STALE)
      const slot = key(current.inquiry_id, current.revision, args.plan_item_id)
      const existing = reservations.get(slot)
      if (!existing) {
        if (current.current_jti_hash !== args.expected_jti_hash) throw new Error(STALE)
        write(current, { current_jti_hash: args.reservation_hash })
        reservations.set(slot, { source_jti_hash: args.expected_jti_hash, reservation_hash: args.reservation_hash, state: 'reserved', lease_expired: false })
        return { status: 'acquired', reservation_hash: args.reservation_hash, recovered: false }
      }
      const resumes = existing.reservation_hash === args.expected_jti_hash && current.current_jti_hash === existing.reservation_hash
      if (existing.source_jti_hash !== args.expected_jti_hash && !resumes) throw new Error(STALE)
      if (existing.state === 'dispatched') {
        return existing.lease_expired
          ? { status: 'ambiguous', reservation_hash: existing.reservation_hash }
          : { status: 'in_progress', reservation_hash: existing.reservation_hash, retry_after_seconds: 30 }
      }
      throw new Error(STALE)
    },

    async markInquiryActionDispatched(args: { row: InquiryLifecycleRow; plan_item_id: string; reservation_hash: string }): Promise<void> {
      const current = live(args.row.inquiry_id)
      const slot = key(current.inquiry_id, current.revision, args.plan_item_id)
      const reservation = reservations.get(slot)
      if (!reservation || reservation.reservation_hash !== args.reservation_hash || reservation.state !== 'reserved'
        || current.current_jti_hash !== args.reservation_hash) throw new Error(STALE)
      reservation.state = 'dispatched'
    },

    async commitInquiryObservation(args: {
      row: InquiryLifecycleRow; expected_jti_hash: string; next_jti_hash: string; contract: InquiryContract
      evidence: { plan_item_id: string; disposition: string; payload: unknown }
    }): Promise<string> {
      const current = live(args.row.inquiry_id)
      if (current.revision !== args.row.revision || current.current_jti_hash !== args.expected_jti_hash || current.status !== 'INCOMPLETE') throw new Error(STALE)
      const slot = key(current.inquiry_id, current.revision, args.evidence.plan_item_id)
      const reservation = reservations.get(slot)
      if (!reservation || reservation.state !== 'dispatched' || reservation.reservation_hash !== args.expected_jti_hash) throw new Error(STALE)
      // The real store round-trips through JSON, which drops undefined (e.g. a never-dispatched bundle).
      const contract = JSON.parse(JSON.stringify(args.contract)) as InquiryContract
      write(current, { contract_jsonb: contract, status: contract.status, revision: current.revision + 1, current_jti_hash: args.next_jti_hash })
      reservation.state = 'committed'
      evidence.push({
        inquiry_id: current.inquiry_id, revision: current.revision + 1, plan_item_id: args.evidence.plan_item_id,
        disposition: args.evidence.disposition, evidence_jsonb: JSON.parse(JSON.stringify(args.evidence.payload)),
      })
      return `receipt-${evidence.length}`
    },

    async commitInquiryFinalization(args: { row: InquiryLifecycleRow; expected_jti_hash: string; contract: InquiryContract }): Promise<void> {
      const current = live(args.row.inquiry_id)
      if (current.revision !== args.row.revision || current.current_jti_hash !== args.expected_jti_hash) throw new Error(STALE)
      write(current, { contract_jsonb: JSON.parse(JSON.stringify(args.contract)), status: args.contract.status, revision: current.revision + 1, current_jti_hash: 'terminal' })
    },

    async failCloseAmbiguousInquiryAction(args: {
      row: InquiryLifecycleRow; expected_reservation_hash?: string; expected_source_jti_hash?: string; plan_item_id: string; contract: InquiryContract
    }): Promise<void> {
      const current = live(args.row.inquiry_id)
      const slot = key(current.inquiry_id, current.revision, args.plan_item_id)
      const reservation = reservations.get(slot)
      const expected = args.expected_reservation_hash ?? args.expected_source_jti_hash
      if (!reservation || reservation.state !== 'dispatched' || !reservation.lease_expired
        || (reservation.reservation_hash !== expected && reservation.source_jti_hash !== expected)) throw new Error(STALE)
      reservation.state = 'failed_closed'
      write(current, { contract_jsonb: JSON.parse(JSON.stringify(args.contract)), status: 'BLOCKED', revision: current.revision + 1, current_jti_hash: 'terminal' })
    },
  }
}

export type InMemoryLifecycleStore = ReturnType<typeof createInMemoryLifecycleStore>
