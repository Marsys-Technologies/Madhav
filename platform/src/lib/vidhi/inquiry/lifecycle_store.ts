import type { PoolClient } from 'pg'
import type { InquiryContract } from './types'
import type { InquiryPaginationReceipt } from './pagination'
import { withInquiryStoreContext } from './store_pool'

export interface InquiryLifecycleRow {
  inquiry_id: string
  principal_uid: string
  chart_id: string
  semantic_contract_hash: string
  execution_plan_hash: string
  capability_content_hash: string
  capability_compatibility_version: string
  chart_overlay_version: string | null
  chart_build_id: string | null
  authorization_jsonb: InquiryContract
  contract_jsonb: InquiryContract
  status: InquiryContract['status']
  revision: number
  current_jti_hash: string
  expires_at: string
}

export interface InquiryActionReservationRow {
  inquiry_id: string
  revision: number
  plan_item_id: string
  source_jti_hash: string
  reservation_hash: string
  state: 'reserved' | 'dispatched' | 'committed' | 'failed_closed'
  lease_expires_at: string
  lease_expired: boolean
}

export interface InquiryEvidenceRow {
  readonly inquiry_id: string
  readonly revision: number
  readonly evidence_jsonb: unknown
}

export type InquiryReservationResult =
  | { status: 'acquired'; reservation_hash: string; recovered: boolean }
  | { status: 'in_progress'; reservation_hash: string; retry_after_seconds: number }
  | { status: 'ambiguous'; reservation_hash: string }

export async function createInquiryLifecycle(args: {
  inquiry_id: string
  principal_uid: string
  contract: InquiryContract
  jti_hash: string
  expires_at: string
}): Promise<InquiryLifecycleRow> {
  return withInquiryStoreContext(args.principal_uid, args.contract.chart_id, async (client) => {
    const result = await client.query<InquiryLifecycleRow>(
    `SELECT * FROM create_planner_inquiry_lifecycle(
       $1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$10::jsonb,$11,$12,$13
     )`,
    [args.inquiry_id, args.principal_uid, args.contract.chart_id, args.contract.semantic_contract_hash,
      args.contract.execution_plan_hash, args.contract.capability_content_hash, args.contract.capability_compatibility_version,
      args.contract.chart_availability_version, args.contract.chart_build_id, JSON.stringify(args.contract), args.contract.status,
      args.jti_hash, args.expires_at],
  )
    return result.rows[0]
  })
}

/**
 * Atomically consume the one-use token before dispatch. A reservation that
 * never reached `dispatched` may be recovered after its lease expires by the
 * same signed source JTI. Once `dispatched` is durable, retry is forbidden:
 * the external outcome is ambiguous and must be failed closed.
 */
export async function reserveInquiryAction(args: {
  row: InquiryLifecycleRow
  expected_jti_hash: string
  reservation_hash: string
  plan_item_id: string
  lease_seconds?: number
}): Promise<InquiryReservationResult> {
  return withInquiryStoreContext(args.row.principal_uid, args.row.chart_id, async (client) => {
    const lifecycle = await client.query<Pick<InquiryLifecycleRow, 'current_jti_hash' | 'status'>>(
      `SELECT current_jti_hash, status
         FROM planner_inquiry_lifecycles
        WHERE inquiry_id=$1 AND principal_uid=$2 AND revision=$3
          AND status='INCOMPLETE' AND expires_at > now()
        FOR UPDATE`,
      [args.row.inquiry_id, args.row.principal_uid, args.row.revision],
    )
    const current = lifecycle.rows[0]
    if (!current) throw new Error('INQUIRY_TOKEN_REPLAYED_OR_STALE')

    const existingResult = await client.query<InquiryActionReservationRow>(
      `SELECT inquiry_id, revision, plan_item_id, source_jti_hash, reservation_hash,
              state, lease_expires_at::text, lease_expires_at <= now() AS lease_expired
         FROM planner_inquiry_action_reservations
        WHERE inquiry_id=$1 AND revision=$2 AND plan_item_id=$3`,
      [args.row.inquiry_id, args.row.revision, args.plan_item_id],
    )
    const existing = existingResult.rows[0]
    const leaseSeconds = Math.max(1, Math.min(args.lease_seconds ?? 30, 300))

    if (!existing) {
      if (current.current_jti_hash !== args.expected_jti_hash) throw new Error('INQUIRY_TOKEN_REPLAYED_OR_STALE')
      const updated = await client.query(
        `UPDATE planner_inquiry_lifecycles
            SET current_jti_hash=$1, updated_at=now()
          WHERE inquiry_id=$2 AND principal_uid=$3 AND revision=$4
            AND current_jti_hash=$5 AND status='INCOMPLETE' AND expires_at > now()`,
        [args.reservation_hash, args.row.inquiry_id, args.row.principal_uid, args.row.revision, args.expected_jti_hash],
      )
      if (!updated.rowCount) throw new Error('INQUIRY_TOKEN_REPLAYED_OR_STALE')
      await client.query(
        `INSERT INTO planner_inquiry_action_reservations
           (inquiry_id, revision, plan_item_id, source_jti_hash, reservation_hash, lease_expires_at)
         VALUES ($1,$2,$3,$4,$5,now() + make_interval(secs => $6))`,
        [args.row.inquiry_id, args.row.revision, args.plan_item_id, args.expected_jti_hash, args.reservation_hash, leaseSeconds],
      )
      return { status: 'acquired', reservation_hash: args.reservation_hash, recovered: false }
    }

    // A recovered managed worker has only the lifecycle's current durable
    // reservation hash, not the original pre-reservation source JTI. Accept
    // that exact current hash solely for this existing reservation; it cannot
    // authorize a different action or mint a new dispatch.
    const resumesExistingReservation = existing.reservation_hash === args.expected_jti_hash
      && current.current_jti_hash === existing.reservation_hash
    if (existing.source_jti_hash !== args.expected_jti_hash && !resumesExistingReservation) {
      throw new Error('INQUIRY_TOKEN_REPLAYED_OR_STALE')
    }
    if (existing.state === 'dispatched') {
      if (!existing.lease_expired) {
        return {
          status: 'in_progress',
          reservation_hash: existing.reservation_hash,
          retry_after_seconds: Math.max(1, Math.ceil((Date.parse(existing.lease_expires_at) - Date.now()) / 1000)),
        }
      }
      return { status: 'ambiguous', reservation_hash: existing.reservation_hash }
    }
    if (existing.state !== 'reserved' || !existing.lease_expired
      || current.current_jti_hash !== existing.reservation_hash) {
      throw new Error('INQUIRY_TOKEN_REPLAYED_OR_STALE')
    }
    await client.query(
      `UPDATE planner_inquiry_lifecycles
          SET current_jti_hash=$1, updated_at=now()
        WHERE inquiry_id=$2 AND principal_uid=$3 AND revision=$4
          AND current_jti_hash=$5 AND status='INCOMPLETE'`,
      [args.reservation_hash, args.row.inquiry_id, args.row.principal_uid, args.row.revision, existing.reservation_hash],
    )
    const recovered = await client.query(
      `UPDATE planner_inquiry_action_reservations
          SET reservation_hash=$1, lease_expires_at=now() + make_interval(secs => $2)
        WHERE inquiry_id=$3 AND revision=$4 AND plan_item_id=$5
          AND reservation_hash=$6 AND state='reserved' AND lease_expires_at <= now()`,
      [args.reservation_hash, leaseSeconds, args.row.inquiry_id, args.row.revision, args.plan_item_id, existing.reservation_hash],
    )
    if (!recovered.rowCount) throw new Error('INQUIRY_TOKEN_REPLAYED_OR_STALE')
    return { status: 'acquired', reservation_hash: args.reservation_hash, recovered: true }
  })
}

/** Persist the at-most-once boundary before invoking the external tool. */
export async function markInquiryActionDispatched(args: {
  row: InquiryLifecycleRow
  plan_item_id: string
  reservation_hash: string
  dispatch_timeout_seconds?: number
}): Promise<void> {
  await withInquiryStoreContext(args.row.principal_uid, args.row.chart_id, async (client) => {
    const dispatchTimeoutSeconds = Math.max(1, Math.min(args.dispatch_timeout_seconds ?? 65, 300))
    const updated = await client.query(
      `UPDATE planner_inquiry_action_reservations reservation
          SET state='dispatched', dispatch_started_at=now(),
              lease_expires_at=now() + make_interval(secs => $6)
        WHERE reservation.inquiry_id=$1 AND reservation.revision=$2
          AND reservation.plan_item_id=$3 AND reservation.reservation_hash=$4
          AND reservation.state='reserved'
          AND EXISTS (
            SELECT 1 FROM planner_inquiry_lifecycles lifecycle
             WHERE lifecycle.inquiry_id=reservation.inquiry_id
               AND lifecycle.principal_uid=$5 AND lifecycle.revision=reservation.revision
               AND lifecycle.current_jti_hash=reservation.reservation_hash
               AND lifecycle.status='INCOMPLETE' AND lifecycle.expires_at > now()
          )`,
      [args.row.inquiry_id, args.row.revision, args.plan_item_id, args.reservation_hash,
        args.row.principal_uid, dispatchTimeoutSeconds],
    )
    if (!updated.rowCount) throw new Error('INQUIRY_TOKEN_REPLAYED_OR_STALE')
  })
}

/** Close an action whose prior process crossed the dispatch boundary but lost its result. */
export async function failCloseAmbiguousInquiryAction(args: {
  row: InquiryLifecycleRow
  /** The lifecycle's current stored reservation hash, never a reconstructed source JTI. */
  expected_reservation_hash?: string
  /** Legacy raw-MCP callers still prove the original source JTI. */
  expected_source_jti_hash?: string
  plan_item_id: string
  contract: InquiryContract
}): Promise<void> {
  await withInquiryStoreContext(args.row.principal_uid, args.row.chart_id, async (client) => {
    const expectedHash = args.expected_reservation_hash ?? args.expected_source_jti_hash
    if (!expectedHash) throw new Error('INQUIRY_TOKEN_REPLAYED_OR_STALE')
    const reservation = await client.query<{ reservation_hash: string }>(
      `UPDATE planner_inquiry_action_reservations
          SET state='failed_closed', committed_at=now()
        WHERE inquiry_id=$1 AND revision=$2 AND plan_item_id=$3
          AND (reservation_hash=$4 OR source_jti_hash=$4)
          AND state='dispatched' AND lease_expires_at <= now()
        RETURNING reservation_hash`,
      [args.row.inquiry_id, args.row.revision, args.plan_item_id, expectedHash],
    )
    const reservationHash = reservation.rows[0]?.reservation_hash
    if (!reservationHash) throw new Error('INQUIRY_TOKEN_REPLAYED_OR_STALE')
    const updated = await client.query(
      `UPDATE planner_inquiry_lifecycles
          SET contract_jsonb=$1::jsonb, status='BLOCKED', revision=revision+1,
              current_jti_hash='terminal', updated_at=now()
        WHERE inquiry_id=$2 AND principal_uid=$3 AND revision=$4
          AND current_jti_hash=$5 AND status='INCOMPLETE'`,
      [JSON.stringify(args.contract), args.row.inquiry_id, args.row.principal_uid, args.row.revision, reservationHash],
    )
    if (!updated.rowCount) throw new Error('INQUIRY_TOKEN_REPLAYED_OR_STALE')
  })
}

export async function getInquiryLifecycle(inquiryId: string, principalUid: string, chartId: string): Promise<InquiryLifecycleRow | null> {
  return withInquiryStoreContext(principalUid, chartId, async (client) => {
    const result = await client.query<InquiryLifecycleRow>(
    `SELECT * FROM planner_inquiry_lifecycles
     WHERE inquiry_id=$1 AND principal_uid=$2 AND expires_at > now()`,
    [inquiryId, principalUid],
  )
    return result.rows[0] ?? null
  })
}

/** Ordered accepted evidence for a managed recovery. The same principal/chart
 * RLS context as the lifecycle is mandatory; this is not a public receipt API. */
export async function listInquiryEvidence(inquiryId: string, principalUid: string, chartId: string): Promise<InquiryEvidenceRow[]> {
  return withInquiryStoreContext(principalUid, chartId, async (client) => {
    const result = await client.query<InquiryEvidenceRow>(
      `SELECT inquiry_id, revision, evidence_jsonb
         FROM planner_inquiry_evidence_receipts
        WHERE inquiry_id=$1
        ORDER BY revision ASC`,
      [inquiryId],
    )
    return result.rows
  })
}

export async function commitInquiryObservation(args: {
  row: InquiryLifecycleRow
  expected_jti_hash: string
  next_jti_hash: string
  contract: InquiryContract
  evidence: {
    plan_item_id: string
    obligation_ids: readonly string[]
    scu_id: string
    binding_id: string
    canonical_args_hash: string
    raw_result_hash: string
    disposition: 'served' | 'empty' | 'dark' | 'failed'
    pagination: InquiryPaginationReceipt
    payload: unknown
  }
}): Promise<string> {
  return withInquiryStoreContext(args.row.principal_uid, args.row.chart_id, async (client: PoolClient) => {
    const updated = await client.query<{ inquiry_id: string }>(
      `UPDATE planner_inquiry_lifecycles
       SET contract_jsonb=$1::jsonb, status=$2, revision=revision+1,
           current_jti_hash=$3, updated_at=now()
       WHERE inquiry_id=$4 AND principal_uid=$5 AND revision=$6
         AND current_jti_hash=$7 AND status='INCOMPLETE' AND expires_at > now()
       RETURNING inquiry_id`,
      [JSON.stringify(args.contract), args.contract.status, args.next_jti_hash,
        args.row.inquiry_id, args.row.principal_uid, args.row.revision, args.expected_jti_hash],
    )
    if (!updated.rowCount) throw new Error('INQUIRY_TOKEN_REPLAYED_OR_STALE')
    const receipt = await client.query<{ receipt_id: string }>(
      `INSERT INTO planner_inquiry_evidence_receipts
         (inquiry_id, revision, obligation_ids, plan_item_id, scu_id, binding_id,
          canonical_args_hash, raw_result_hash, disposition, pagination_jsonb, evidence_jsonb)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$11::jsonb)
       RETURNING receipt_id`,
      [args.row.inquiry_id, args.row.revision + 1, args.evidence.obligation_ids,
        args.evidence.plan_item_id, args.evidence.scu_id, args.evidence.binding_id,
        args.evidence.canonical_args_hash, args.evidence.raw_result_hash,
        args.evidence.disposition, JSON.stringify(args.evidence.pagination), JSON.stringify(args.evidence.payload)],
    )
    const reservation = await client.query(
      `UPDATE planner_inquiry_action_reservations
          SET state='committed', committed_at=now()
        WHERE inquiry_id=$1 AND revision=$2 AND plan_item_id=$3
          AND reservation_hash=$4 AND state='dispatched'`,
      [args.row.inquiry_id, args.row.revision, args.evidence.plan_item_id, args.expected_jti_hash],
    )
    if (!reservation.rowCount) throw new Error('INQUIRY_TOKEN_REPLAYED_OR_STALE')
    return receipt.rows[0].receipt_id
  })
}

export async function commitInquiryFinalization(args: {
  row: InquiryLifecycleRow
  expected_jti_hash: string
  contract: InquiryContract
  action?: { plan_item_id: string; terminal_state: 'failed_closed' }
}): Promise<void> {
  await withInquiryStoreContext(args.row.principal_uid, args.row.chart_id, async (client) => {
    const updated = await client.query(
    `UPDATE planner_inquiry_lifecycles
     SET contract_jsonb=$1::jsonb, status=$2, revision=revision+1,
         current_jti_hash='terminal', updated_at=now()
     WHERE inquiry_id=$3 AND principal_uid=$4 AND revision=$5
       AND current_jti_hash=$6 AND status='INCOMPLETE' AND expires_at > now()`,
    [JSON.stringify(args.contract), args.contract.status, args.row.inquiry_id,
      args.row.principal_uid, args.row.revision, args.expected_jti_hash],
    )
    if (!updated.rowCount) throw new Error('INQUIRY_TOKEN_REPLAYED_OR_STALE')
    if (args.action) {
      const reservation = await client.query(
        `UPDATE planner_inquiry_action_reservations
            SET state=$1, committed_at=now()
          WHERE inquiry_id=$2 AND revision=$3 AND plan_item_id=$4
            AND reservation_hash=$5 AND state='dispatched'`,
        [args.action.terminal_state, args.row.inquiry_id, args.row.revision,
          args.action.plan_item_id, args.expected_jti_hash],
      )
      if (!reservation.rowCount) throw new Error('INQUIRY_TOKEN_REPLAYED_OR_STALE')
    }
  })
}
