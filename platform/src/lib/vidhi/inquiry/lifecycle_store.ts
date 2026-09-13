import type { PoolClient } from 'pg'
import { withChartContext } from '@/lib/db/roles'
import type { InquiryContract } from './types'
import type { InquiryPaginationReceipt } from './pagination'

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

export async function createInquiryLifecycle(args: {
  inquiry_id: string
  principal_uid: string
  contract: InquiryContract
  jti_hash: string
  expires_at: string
}): Promise<InquiryLifecycleRow> {
  return withChartContext(args.contract.chart_id, async (client) => {
    // The lifecycle tables enforce principal/chart RLS even when the broader
    // staged role-separation flag is off. Pin both contexts for the definer
    // purge explicitly so default deployments neither fail nor gain a
    // caller-selectable cross-tenant deletion primitive.
    await client.query('SELECT set_config($1, $2, true), set_config($3, $4, true)', [
      'app.principal_id', args.principal_uid, 'app.chart_context', args.contract.chart_id,
    ])
    await client.query('SELECT prepare_planner_inquiry_creation($1, $2)', [args.principal_uid, args.contract.chart_id])
    const result = await client.query<InquiryLifecycleRow>(
    `INSERT INTO planner_inquiry_lifecycles
       (inquiry_id, principal_uid, chart_id, semantic_contract_hash, execution_plan_hash, capability_content_hash,
        capability_compatibility_version, chart_overlay_version, chart_build_id, authorization_jsonb, contract_jsonb,
        status, revision, current_jti_hash, expires_at)
     VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$10::jsonb,$11,0,$12,$13)
     RETURNING *`,
    [args.inquiry_id, args.principal_uid, args.contract.chart_id, args.contract.semantic_contract_hash,
      args.contract.execution_plan_hash, args.contract.capability_content_hash, args.contract.capability_compatibility_version,
      args.contract.chart_availability_version, args.contract.chart_build_id, JSON.stringify(args.contract), args.contract.status,
      args.jti_hash, args.expires_at],
  )
    return result.rows[0]
  }, { principalId: args.principal_uid })
}

/** Atomically consume the one-use token before any externally costly dispatch. */
export async function reserveInquiryAction(args: {
  row: InquiryLifecycleRow
  expected_jti_hash: string
  reservation_hash: string
}): Promise<void> {
  await withChartContext(args.row.chart_id, async (client) => {
    const updated = await client.query(
      `UPDATE planner_inquiry_lifecycles
          SET current_jti_hash=$1, updated_at=now()
        WHERE inquiry_id=$2 AND principal_uid=$3 AND revision=$4
          AND current_jti_hash=$5 AND status='INCOMPLETE' AND expires_at > now()`,
      [args.reservation_hash, args.row.inquiry_id, args.row.principal_uid, args.row.revision, args.expected_jti_hash],
    )
    if (!updated.rowCount) throw new Error('INQUIRY_TOKEN_REPLAYED_OR_STALE')
  }, { principalId: args.row.principal_uid })
}

export async function getInquiryLifecycle(inquiryId: string, principalUid: string, chartId: string): Promise<InquiryLifecycleRow | null> {
  return withChartContext(chartId, async (client) => {
    const result = await client.query<InquiryLifecycleRow>(
    `SELECT * FROM planner_inquiry_lifecycles
     WHERE inquiry_id=$1 AND principal_uid=$2 AND expires_at > now()`,
    [inquiryId, principalUid],
  )
    return result.rows[0] ?? null
  }, { principalId: principalUid })
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
  return withChartContext(args.row.chart_id, async (client: PoolClient) => {
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
    return receipt.rows[0].receipt_id
  }, { principalId: args.row.principal_uid })
}

export async function commitInquiryFinalization(args: {
  row: InquiryLifecycleRow
  expected_jti_hash: string
  contract: InquiryContract
}): Promise<void> {
  await withChartContext(args.row.chart_id, async (client) => {
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
  }, { principalId: args.row.principal_uid })
}
