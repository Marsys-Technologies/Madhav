/** Durable raw-MCP Inquiry Contract lifecycle. No synthesis occurs here. */
import 'server-only'
import { randomUUID } from 'node:crypto'
import { NextResponse } from 'next/server'
import { validateServiceToken } from '@/lib/mcp/service_token'
import { resolveMcpPrincipalRole } from '@/lib/mcp/auth'
import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import { query } from '@/lib/db/client'
import { getCatalog } from '@/lib/retrieval/registry/catalog'
import { compileCapabilityKnowledge } from '@/lib/retrieval/registry/knowledge'
import { stableFingerprint } from '@/lib/retrieval/registry/knowledge/stable'
import { getToolByName } from '@/lib/retrieval/registry/tool_name_bridge'
import { ScopeTupleSchema } from '@/lib/vidhi/scope_classifier'
import {
  applyInquiryObservations,
  classifyInquiryResult,
  compileInquiryContract,
  deriveInquiryPaginationReceipt,
  finalizeInquiryContract,
  hashJti,
  issueInquiryLifecycleToken,
  verifyInquiryLifecycleToken,
  type InquiryContract,
} from '@/lib/vidhi/inquiry'
import { commitInquiryFinalization, commitInquiryObservation, createInquiryLifecycle, getInquiryLifecycle } from '@/lib/vidhi/inquiry/lifecycle_store'

export const maxDuration = 60

type Body =
  | { action: 'start'; chart_id: string; question: string; scope_tuple: unknown }
  | { action: 'execute'; lifecycle_token: string; action_id: string }
  | { action: 'finalize'; lifecycle_token: string }

function signingKey(): string {
  const key = process.env.INQUIRY_LIFECYCLE_SIGNING_KEY ?? ''
  if (key.length < 32) throw new Error('INQUIRY_LIFECYCLE_SIGNING_KEY is missing or too short')
  return key
}

async function entitled(uid: string, chartId: string): Promise<boolean> {
  const role = await resolveMcpPrincipalRole(uid)
  return (await authorizeChartAccess({ principal: { uid, role }, chartId, db: { query } })) !== 'deny'
}

function nextReady(contract: InquiryContract): string[] {
  return contract.plan_items.filter((item) => item.state === 'ready').map((item) => item.item_id)
}

function response(data: Record<string, unknown>, status = 200) { return NextResponse.json(data, { status }) }

export async function POST(request: Request) {
  if (!validateServiceToken(request)) return response({ ok: false, error: 'Unauthorized' }, 401)
  const principalUid = request.headers.get('x-mcp-user')
  const principalKeyId = request.headers.get('x-mcp-key-id')
  if (!principalUid || !principalKeyId) return response({ ok: false, error: 'X-MCP-User and X-MCP-Key-Id headers required' }, 401)
  const principalSubject = `${principalUid}:${principalKeyId}`
  let body: Body
  try { body = await request.json() as Body } catch { return response({ ok: false, error: 'Invalid JSON' }, 400) }

  try {
    const key = signingKey()
    if (body.action === 'start') {
      if (!(await entitled(principalUid, body.chart_id))) return response({ ok: false, error: 'AUTHZ_DENIED' }, 401)
      const scope = ScopeTupleSchema.parse(body.scope_tuple)
      const snapshot = compileCapabilityKnowledge(getCatalog())
      const contract = compileInquiryContract({ snapshot, chart_id: body.chart_id, question: body.question, scope_tuple: scope })
      const inquiryId = randomUUID()
      const issued = issueInquiryLifecycleToken({
        sub: principalSubject, inquiry_id: inquiryId, chart_id: body.chart_id,
        contract_hash: contract.semantic_contract_hash, execution_plan_hash: contract.execution_plan_hash,
        catalog_hash: snapshot.content_hash, compatibility_version: snapshot.compatibility_version,
        overlay_version: contract.chart_availability_version, revision: 0,
        allowed_transition: 'execute', next_action_ids: nextReady(contract),
      }, key)
      await createInquiryLifecycle({ inquiry_id: inquiryId, principal_uid: principalUid, contract, jti_hash: hashJti(issued.claims.jti), expires_at: new Date(issued.claims.exp * 1000).toISOString() })
      return response({ ok: true, inquiry_id: inquiryId, contract, lifecycle_token: issued.token, next_action_ids: issued.claims.next_action_ids })
    }

    const claims = verifyInquiryLifecycleToken(body.lifecycle_token, key, principalSubject)
    if (!(await entitled(principalUid, claims.chart_id))) return response({ ok: false, error: 'AUTHZ_DENIED' }, 401)
    const row = await getInquiryLifecycle(claims.inquiry_id, principalUid, claims.chart_id)
    if (!row || row.chart_id !== claims.chart_id || row.semantic_contract_hash !== claims.contract_hash ||
      row.execution_plan_hash !== claims.execution_plan_hash || row.capability_content_hash !== claims.catalog_hash ||
      row.capability_compatibility_version !== claims.compatibility_version || row.revision !== claims.revision ||
      row.current_jti_hash !== hashJti(claims.jti)) {
      return response({ ok: false, error: 'INQUIRY_TOKEN_REPLAYED_OR_STALE' }, 409)
    }

    if (body.action === 'execute') {
      if (claims.allowed_transition !== 'execute' || !claims.next_action_ids.includes(body.action_id)) return response({ ok: false, error: 'INQUIRY_ACTION_NOT_AUTHORIZED' }, 409)
      const contract = row.contract_jsonb
      const item = contract.plan_items.find((candidate) => candidate.item_id === body.action_id && candidate.state === 'ready')
      if (!item?.binding_id) return response({ ok: false, error: 'INQUIRY_ACTION_NOT_EXECUTABLE' }, 409)
      const uri = item.binding_id.replace(/^registry:/, '')
      const snapshot = compileCapabilityKnowledge(getCatalog())
      if (snapshot.content_hash !== claims.catalog_hash) return response({ ok: false, error: 'CAPABILITY_KNOWLEDGE_STALE' }, 409)
      const scu = snapshot.scus.find((candidate) => candidate.scu_id === item.scu_id)
      const binding = scu?.bindings.find((candidate) => candidate.binding_id === item.binding_id)
      const tool = getToolByName(uri)
      if (!binding?.executable || !tool) return response({ ok: false, error: 'INQUIRY_BINDING_UNAVAILABLE' }, 409)

      let raw: unknown
      let disposition: 'served' | 'empty' | 'failed' = 'served'
      let gapReason: string | undefined
      try {
        raw = await tool.retrieve({ chart_id: claims.chart_id, domains: contract.scope_tuple.domains }, item.args)
        disposition = classifyInquiryResult(binding, raw)
      } catch (error) {
        disposition = 'failed'
        gapReason = error instanceof Error ? error.message : String(error)
        raw = { error: gapReason }
      }
      const pagination = deriveInquiryPaginationReceipt(binding, raw, item.args)
      let observed = applyInquiryObservations(contract, [{
        item_id: item.item_id, disposition, evidence_refs: [`raw:${stableFingerprint(raw)}`], gap_reason: gapReason,
        ...(pagination.exhausted ? {} : { discovered_frontier: [{ scu_id: item.scu_id, materiality: 'required' as const, reason: `Pagination frontier remains open (${String(pagination.next)}).` }] }),
      }])
      if (!pagination.exhausted && pagination.next !== 'unproven' && pagination.next !== null) {
        const positionKey = binding.pagination_contract?.request_position_path?.split('.').at(-1)
        if (positionKey) observed = {
          ...observed,
          plan_items: observed.plan_items.map((candidate) => candidate.item_id === item.item_id
            ? { ...candidate, args: { ...candidate.args, [positionKey]: pagination.next }, state: 'ready' as const }
            : candidate),
        }
      }
      if (disposition === 'failed' && observed.iteration < observed.max_iterations) observed = {
        ...observed,
        plan_items: observed.plan_items.map((candidate) => candidate.item_id === item.item_id
          ? { ...candidate, state: 'ready' as const }
          : candidate),
      }
      const remaining = observed.iteration >= observed.max_iterations ? [] : nextReady(observed)
      const issued = issueInquiryLifecycleToken({
        sub: principalSubject, inquiry_id: row.inquiry_id, chart_id: row.chart_id,
        contract_hash: row.semantic_contract_hash, execution_plan_hash: row.execution_plan_hash,
        catalog_hash: row.capability_content_hash, compatibility_version: row.capability_compatibility_version,
        overlay_version: row.chart_overlay_version, revision: row.revision + 1,
        allowed_transition: remaining.length ? 'execute' : 'finalize', next_action_ids: remaining,
      }, key)
      const receiptId = await commitInquiryObservation({
        row, expected_jti_hash: hashJti(claims.jti), next_jti_hash: hashJti(issued.claims.jti), contract: observed,
        evidence: { plan_item_id: item.item_id, obligation_ids: item.obligation_ids, scu_id: item.scu_id, binding_id: item.binding_id,
          canonical_args_hash: stableFingerprint(item.args), raw_result_hash: stableFingerprint(raw), disposition,
          pagination, payload: raw },
      })
      return response({ ok: true, inquiry_id: row.inquiry_id, evidence_receipt_id: receiptId, raw_result: raw, disposition, pagination, contract: observed, lifecycle_token: issued.token, next_action_ids: issued.claims.next_action_ids })
    }

    if (claims.allowed_transition !== 'finalize') return response({ ok: false, error: 'INQUIRY_FINALIZE_NOT_AUTHORIZED' }, 409)
    const final = finalizeInquiryContract(row.contract_jsonb)
    await commitInquiryFinalization({ row, expected_jti_hash: hashJti(claims.jti), contract: final })
    return response({ ok: true, inquiry_id: row.inquiry_id, closure: { status: final.status, reasons: final.status_reasons, residual_frontier: final.material_frontier.filter((item) => item.disposition === 'open'), contract_hash: final.contract_id, receipt_hash: stableFingerprint({ contract: final.contract_id, status: final.status, reasons: final.status_reasons }) } })
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    return response({ ok: false, error: message }, message.includes('TOKEN') ? 401 : 400)
  }
}
