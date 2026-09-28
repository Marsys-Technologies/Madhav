/** Durable raw-MCP Inquiry Contract lifecycle. No synthesis occurs here. */
import 'server-only'
import { randomUUID } from 'node:crypto'
import { NextResponse } from 'next/server'
import { z } from 'zod'
import { validateMcpServiceRequest } from '@/lib/mcp/service_token'
import { resolveMcpPrincipalRole } from '@/lib/mcp/auth'
import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import { query } from '@/lib/db/client'
import '@/lib/retrieval/registry/catalog'
import { assertPinnedCapabilityKnowledgeCurrent, loadChartCapabilityOverlay } from '@/lib/retrieval/registry/knowledge'
import { stableFingerprint } from '@/lib/retrieval/registry/knowledge/stable'
import { getToolByName } from '@/lib/retrieval/registry/tool_name_bridge'
import { getCapability } from '@/lib/retrieval/registry'
import { InquiryScopeInputSchema } from '@/lib/vidhi/inquiry/intent_normalization'
import { isInquirySafeRegistryDescriptor, isInquiryServerDispatchEligible } from '@/lib/vidhi/inquiry/execution_policy'
import {
  buildInquiryClosureReceipt,
  buildInquiryDoorParityProjection,
  classifyInquiryResult,
  closeInquiryForEvidenceSuccessor,
  compileInquiryContract,
  compileInquirySuccessorContract,
  deriveInquiryPaginationReceipt,
  finalizeInquiryContract,
  failInquiryForAmbiguousDispatch,
  failInquiryForOverlayDrift,
  hashJti,
  inquiryAuthorizationHashes,
  issueInquiryLifecycleToken,
  loadInquiryLifecycleSigningKeyRing,
  recordInquiryExecution,
  verifyInquiryLifecycleToken,
  type InquiryContract,
} from '@/lib/vidhi/inquiry'
import {
  commitInquiryFinalization,
  commitInquiryObservation,
  createInquiryLifecycle,
  createInquirySuccessorLifecycle,
  failCloseAmbiguousInquiryAction,
  getInquiryLifecycle,
  markInquiryActionDispatched,
  reserveInquiryAction,
} from '@/lib/vidhi/inquiry/lifecycle_store'
import { deterministicCompilerProvenance } from '@/lib/vidhi/inquiry/planning_policy'
import { deriveEvidenceFrontier } from '@/lib/vidhi/inquiry/evidence_frontier'
import { readBoundedRequestBody } from './bounded_body'
import {
  buildStructuredResponseAccountability,
  inquiryCitedHandles,
  stripInquiryCitationMarkers,
  successorChain,
} from '@/lib/vidhi/inquiry/response_accountability'

export const maxDuration = 60

const AiProposalSchema = z.object({
  question_facets: z.array(z.object({
    label: z.string().trim().min(1).max(160),
    terms: z.array(z.string().trim().min(1).max(80)).max(32),
    materiality: z.enum(['required', 'supporting']),
  }).strict()).max(16),
  uncommon_adjacencies: z.array(z.object({
    from_scu_id: z.string().trim().min(1).max(200),
    to_scu_id: z.string().trim().min(1).max(200),
    rationale: z.string().trim().min(1).max(500),
  }).strict()).max(16),
  hypotheses: z.array(z.string().trim().min(1).max(500)).max(16),
}).strict()

const MAX_RESULT_BYTES = 512 * 1024
const MAX_CERTIFY_PAYLOADS = 64
// Bound the certify body before it is parsed: every committed payload at its maximum size, the
// answer, and envelope overhead.
const MAX_REQUEST_BYTES = MAX_CERTIFY_PAYLOADS * MAX_RESULT_BYTES + 1024 * 1024
// Every other action is small by schema (question <= 4000 chars, lifecycle token <= 16 KiB, a
// bounded AI proposal), so it gets a small limit; only a body whose first key is
// `"action":"certify"` may use the large one. The MCP client serializes `action` first.
const MAX_NON_CERTIFY_REQUEST_BYTES = 256 * 1024
const CERTIFY_PREFIX_BYTES = 4096
const CERTIFY_LEADING_ACTION = /^\s*\{\s*"action"\s*:\s*"certify"\s*[,}]/
// Bound certification work: each cited span re-hashes the findings it cites.
const MAX_CERTIFY_CITED_SPANS = 256
const MAX_CERTIFY_CITATIONS = 2048
// A cited span must carry some interpretation of its own, not markers alone.
const MIN_INTERPRETATION_CHARS = 24

const BodySchema = z.discriminatedUnion('action', [
  z.object({
    action: z.literal('start'), chart_id: z.string().uuid(),
    question: z.string().trim().min(1).max(4000), scope_tuple: z.unknown(),
    ai_proposal: AiProposalSchema.optional(),
    temporal_anchor_date: z.string().max(32).optional(),
  }).strict(),
  z.object({
    action: z.literal('execute'), lifecycle_token: z.string().min(1).max(16384),
    action_id: z.string().regex(/^item-[0-9]{3}$/),
  }).strict(),
  z.object({ action: z.literal('finalize'), lifecycle_token: z.string().min(1).max(16384) }).strict(),
  z.object({ action: z.literal('continue'), lifecycle_token: z.string().min(1).max(16384) }).strict(),
  // Server-side certification of an externally synthesized answer (RC-6.4 raw). Read-only.
  z.object({
    action: z.literal('certify'), lifecycle_token: z.string().min(1).max(16384),
    response_text: z.string().min(1).max(200_000),
    evidence_payloads: z.array(z.unknown()).max(MAX_CERTIFY_PAYLOADS),
  }).strict(),
])
type Body = z.infer<typeof BodySchema>

const PUBLIC_ERROR_CODES = new Set([
  'INQUIRY_TOKEN_MALFORMED', 'INQUIRY_TOKEN_INVALID_SIGNATURE', 'INQUIRY_TOKEN_WRONG_AUDIENCE',
  'INQUIRY_TOKEN_UNKNOWN_KID', 'INQUIRY_TOKEN_WRONG_SUBJECT', 'INQUIRY_TOKEN_EXPIRED', 'INQUIRY_TOKEN_REPLAYED_OR_STALE',
  'INQUIRY_DISPATCH_OUTCOME_AMBIGUOUS', 'INQUIRY_ACTION_IN_PROGRESS',
  'INQUIRY_ACTIVE_LIMIT_REACHED', 'INQUIRY_CREATION_RATE_LIMITED',
])

async function entitled(uid: string, chartId: string): Promise<boolean> {
  const role = await resolveMcpPrincipalRole(uid)
  return (await authorizeChartAccess({ principal: { uid, role }, chartId, db: { query } })) !== 'deny'
}

function nextReady(contract: InquiryContract): string[] {
  return contract.plan_items.filter((item) => item.state === 'ready').map((item) => item.item_id)
}

function response(data: Record<string, unknown>, status = 200) {
  // Preserve the exact public error envelopes. Successful lifecycle evidence,
  // unlike an error code, needs a revision binding for acceptance.
  const payload = data.ok === true
    ? {
        ...data,
        // Null is an explicit non-production/local state and cannot satisfy
        // acceptance; clients must not infer a revision from a token.
        deployed_revision: process.env.NIRMANA_DEPLOYED_SHA ?? null,
      }
    : data
  return NextResponse.json(payload, { status })
}

const FORBIDDEN_PATH_SEGMENTS = new Set(['__proto__', 'prototype', 'constructor'])

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function removeGuardedPath(value: Readonly<Record<string, unknown>>, path: readonly string[]): Record<string, unknown> | null {
  const [key, ...rest] = path
  const output: Record<string, unknown> = { ...value }
  if (!Object.prototype.hasOwnProperty.call(value, key)) return output
  if (rest.length === 0) {
    delete output[key]
    return output
  }
  const child = value[key]
  if (!isRecord(child)) return null
  const withoutChildPath = removeGuardedPath(child, rest)
  if (!withoutChildPath) return null
  if (Object.keys(withoutChildPath).length === 0) delete output[key]
  else output[key] = withoutChildPath
  return output
}

function readGuardedPath(value: Readonly<Record<string, unknown>>, path: readonly string[]): { found: boolean; value?: unknown } | null {
  let cursor: unknown = value
  for (const segment of path) {
    if (!isRecord(cursor)) return null
    if (!Object.prototype.hasOwnProperty.call(cursor, segment)) return { found: false }
    cursor = cursor[segment]
  }
  return { found: true, value: cursor }
}

function writeGuardedPath(base: Readonly<Record<string, unknown>>, path: readonly string[], value: unknown): Record<string, unknown> | null {
  const [key, ...rest] = path
  if (rest.length === 0) return { ...base, [key]: value }
  const existing = base[key]
  if (existing !== undefined && !isRecord(existing)) return null
  const child = writeGuardedPath(isRecord(existing) ? existing : {}, rest, value)
  return child ? { ...base, [key]: child } : null
}

function authorizedArgs(base: Readonly<Record<string, unknown>>, current: Readonly<Record<string, unknown>>, positionPath?: string): Record<string, unknown> | null {
  if (!positionPath) {
    return stableFingerprint(base) === stableFingerprint(current) ? { ...base } : null
  }
  const path = positionPath.split('.')
  if (path.some((segment) => !segment || FORBIDDEN_PATH_SEGMENTS.has(segment))) return null
  const baseWithoutPosition = removeGuardedPath(base, path)
  const currentWithoutPosition = removeGuardedPath(current, path)
  if (!baseWithoutPosition || !currentWithoutPosition
    || stableFingerprint(baseWithoutPosition) !== stableFingerprint(currentWithoutPosition)) return null
  const position = readGuardedPath(current, path)
  if (!position) return null
  if (!position.found || position.value === undefined) return { ...base }
  return writeGuardedPath(base, path, position.value)
}

export async function POST(request: Request) {
  if (!(await validateMcpServiceRequest(request))) return response({ ok: false, error: 'Unauthorized' }, 401)
  const principalUid = request.headers.get('x-mcp-user')
  const principalKeyId = request.headers.get('x-mcp-key-id')
  if (!principalUid || !principalKeyId) return response({ ok: false, error: 'X-MCP-User and X-MCP-Key-Id headers required' }, 401)
  const principalSubject = `${principalUid}:${principalKeyId}`
  // Early-rejection optimization only: an honestly oversized Content-Length lets us refuse
  // before reading a single byte. It is never trusted as the enforcement mechanism itself —
  // see readBoundedRequestBody (./bounded_body) for the actual, unbypassable limit.
  if (Number(request.headers.get('content-length') ?? 0) > MAX_REQUEST_BYTES) {
    return response({ ok: false, error: 'INQUIRY_REQUEST_TOO_LARGE' }, 413)
  }
  const bounded = await readBoundedRequestBody(request, MAX_REQUEST_BYTES, {
    initialBytes: MAX_NON_CERTIFY_REQUEST_BYTES,
    prefixBytes: CERTIFY_PREFIX_BYTES,
    allow: (prefix) => CERTIFY_LEADING_ACTION.test(prefix),
  })
  if (!bounded.ok) return response({ ok: false, error: 'INQUIRY_REQUEST_TOO_LARGE' }, 413)
  let rawBody: unknown
  try { rawBody = JSON.parse(bounded.text) } catch { return response({ ok: false, error: 'INVALID_JSON' }, 400) }
  const parsedBody = BodySchema.safeParse(rawBody)
  if (!parsedBody.success) return response({ ok: false, error: 'INVALID_REQUEST' }, 400)
  const body: Body = parsedBody.data

  try {
    const key = loadInquiryLifecycleSigningKeyRing()
    if (body.action === 'start') {
      if (!(await entitled(principalUid, body.chart_id))) return response({ ok: false, error: 'AUTHZ_DENIED' }, 401)
      // Accept both classifier and canonical compiler scope vocabularies. The
      // compiler owns their deterministic normalization and semantic hash.
      const scope = InquiryScopeInputSchema.parse(body.scope_tuple)
      const snapshot = assertPinnedCapabilityKnowledgeCurrent()
      const overlay = await loadChartCapabilityOverlay(snapshot, body.chart_id)
      const contract = compileInquiryContract({
        snapshot, overlay, chart_id: body.chart_id, question: body.question,
        scope_tuple: scope, ai_proposal: body.ai_proposal, execution_channel: 'mcp_full',
        temporal_anchor_date: body.temporal_anchor_date,
        // The raw door makes no model call: any AI decomposition is the caller's (RC-5.3).
        planning_provenance: deterministicCompilerProvenance(body.ai_proposal !== undefined),
      })
      const inquiryId = randomUUID()
      const ready = nextReady(contract)
      const issued = issueInquiryLifecycleToken({
        sub: principalSubject, inquiry_id: inquiryId, chart_id: body.chart_id,
        contract_hash: contract.semantic_contract_hash, execution_plan_hash: contract.execution_plan_hash,
        contract_state_hash: stableFingerprint(contract),
        catalog_hash: snapshot.content_hash, compatibility_version: snapshot.compatibility_version,
        overlay_version: contract.chart_availability_version, chart_build_id: contract.chart_build_id, revision: 0,
        allowed_transition: ready.length ? 'execute' : 'finalize', next_action_ids: ready,
      }, key)
      await createInquiryLifecycle({ inquiry_id: inquiryId, principal_uid: principalUid, contract, jti_hash: hashJti(issued.claims.jti), expires_at: new Date(issued.claims.exp * 1000).toISOString() })
      return response({ ok: true, inquiry_id: inquiryId, contract, lifecycle_token: issued.token, next_action_ids: issued.claims.next_action_ids })
    }

    const claims = verifyInquiryLifecycleToken(body.lifecycle_token, key, principalSubject, (kid) => {
      // KID is public JWT-header metadata. Never log the token, signature or key material.
      console.info('[mcp:inquiry] lifecycle token verified', { kid })
    })
    if (!(await entitled(principalUid, claims.chart_id))) return response({ ok: false, error: 'AUTHZ_DENIED' }, 401)
    const row = await getInquiryLifecycle(claims.inquiry_id, principalUid, claims.chart_id)
    const authorization = row?.authorization_jsonb
    const authorizationHashes = authorization ? inquiryAuthorizationHashes(authorization) : null
    if (!row || !authorization || !authorizationHashes) {
      return response({ ok: false, error: 'INQUIRY_TOKEN_REPLAYED_OR_STALE' }, 409)
    }
    if (body.action === 'certify') return certifyExternalAnswer(body, claims, row)
    if (row.chart_id !== claims.chart_id || row.semantic_contract_hash !== claims.contract_hash ||
      row.execution_plan_hash !== claims.execution_plan_hash || row.capability_content_hash !== claims.catalog_hash ||
      row.capability_compatibility_version !== claims.compatibility_version || row.revision !== claims.revision ||
      ((body.action === 'finalize' || body.action === 'continue') && row.current_jti_hash !== hashJti(claims.jti)) ||
      row.chart_overlay_version !== claims.overlay_version ||
      row.chart_build_id !== claims.chart_build_id ||
      stableFingerprint(row.contract_jsonb) !== claims.contract_state_hash ||
      authorizationHashes.semantic_contract_hash !== row.semantic_contract_hash ||
      authorizationHashes.execution_plan_hash !== row.execution_plan_hash ||
      authorizationHashes.contract_id !== authorization.contract_id ||
      row.contract_jsonb.contract_id !== authorization.contract_id ||
      row.contract_jsonb.semantic_contract_hash !== authorization.semantic_contract_hash ||
      row.contract_jsonb.execution_plan_hash !== authorization.execution_plan_hash) {
      return response({ ok: false, error: 'INQUIRY_TOKEN_REPLAYED_OR_STALE' }, 409)
    }

    const snapshot = assertPinnedCapabilityKnowledgeCurrent()
    if (snapshot.content_hash !== claims.catalog_hash) return response({ ok: false, error: 'CAPABILITY_KNOWLEDGE_STALE' }, 409)
    const currentOverlay = await loadChartCapabilityOverlay(snapshot, claims.chart_id)
    if (currentOverlay.overlay_version !== claims.overlay_version || currentOverlay.build_id !== claims.chart_build_id) {
      return response({ ok: false, error: 'CAPABILITY_OVERLAY_STALE' }, 409)
    }

    if (body.action === 'execute') {
      if (claims.allowed_transition !== 'execute' || !claims.next_action_ids.includes(body.action_id)) return response({ ok: false, error: 'INQUIRY_ACTION_NOT_AUTHORIZED' }, 409)
      const contract = row.contract_jsonb
      const currentItem = contract.plan_items.find((candidate) => candidate.item_id === body.action_id && candidate.state === 'ready')
      const item = authorization.plan_items.find((candidate) => candidate.item_id === body.action_id)
      if (!currentItem || !item?.binding_id || currentItem.scu_id !== item.scu_id
        || stableFingerprint(currentItem.obligation_ids) !== stableFingerprint(item.obligation_ids)) {
        return response({ ok: false, error: 'INQUIRY_ACTION_NOT_EXECUTABLE' }, 409)
      }
      const uri = item.binding_id.replace(/^registry:/, '')
      const scu = snapshot.scus.find((candidate) => candidate.scu_id === item.scu_id)
      const binding = scu?.bindings.find((candidate) => candidate.binding_id === item.binding_id)
      const tool = getToolByName(uri)
      const descriptor = getCapability(uri)
      if (!binding || !isInquiryServerDispatchEligible(binding, 'raw_mcp')
        || !isInquirySafeRegistryDescriptor(binding, descriptor) || !tool) {
        return response({ ok: false, error: 'INQUIRY_BINDING_UNAVAILABLE' }, 409)
      }
      const invocationArgs = authorizedArgs(item.args, currentItem.args, binding.pagination_contract?.request_position_path)
      if (!invocationArgs) return response({ ok: false, error: 'INQUIRY_ARGS_NOT_AUTHORIZED' }, 409)

      const reservationHash = `reserved:${hashJti(randomUUID())}`
      const reservation = await reserveInquiryAction({
        row,
        expected_jti_hash: hashJti(claims.jti),
        reservation_hash: reservationHash,
        plan_item_id: item.item_id,
      })
      if (reservation.status === 'in_progress') {
        return response({
          ok: false,
          error: 'INQUIRY_ACTION_IN_PROGRESS',
          retry_after_seconds: reservation.retry_after_seconds,
        }, 409)
      }
      if (reservation.status === 'ambiguous') {
        const blocked = failInquiryForAmbiguousDispatch(contract, item.item_id)
        await failCloseAmbiguousInquiryAction({
          row,
          expected_source_jti_hash: hashJti(claims.jti),
          plan_item_id: item.item_id,
          contract: blocked,
        })
        return response({ ok: false, error: 'INQUIRY_DISPATCH_OUTCOME_AMBIGUOUS', contract: blocked }, 409)
      }
      await markInquiryActionDispatched({ row, plan_item_id: item.item_id, reservation_hash: reservation.reservation_hash })

      let raw: unknown
      let disposition: 'served' | 'empty' | 'failed' = 'served'
      let gapReason: string | undefined
      const traceId = randomUUID()
      try {
        raw = await tool.retrieve({ chart_id: claims.chart_id, domains: contract.scope_tuple.domains }, invocationArgs)
        disposition = classifyInquiryResult(binding, raw)
        if (disposition === 'failed') gapReason = 'TOOL_FAILURE_ENVELOPE'
      } catch (error) {
        disposition = 'failed'
        gapReason = 'TOOL_DISPATCH_FAILED'
        console.error('[mcp:inquiry] tool dispatch failed', { traceId, inquiryId: row.inquiry_id, itemId: item.item_id, error })
        raw = { ok: false, error: gapReason, trace_id: traceId }
      }
      const postDispatchOverlay = await loadChartCapabilityOverlay(snapshot, claims.chart_id)
      if (postDispatchOverlay.overlay_version !== claims.overlay_version || postDispatchOverlay.build_id !== claims.chart_build_id) {
        console.error('[mcp:inquiry] chart overlay changed during dispatch', { traceId, inquiryId: row.inquiry_id, itemId: item.item_id })
        const blocked = failInquiryForOverlayDrift(contract)
        await commitInquiryFinalization({
          row,
          expected_jti_hash: reservation.reservation_hash,
          contract: blocked,
          action: { plan_item_id: item.item_id, terminal_state: 'failed_closed' },
        })
        return response({ ok: false, error: 'CAPABILITY_OVERLAY_CHANGED' }, 409)
      }
      let serialized = JSON.stringify(raw)
      if (Buffer.byteLength(serialized) > MAX_RESULT_BYTES) {
        const oversizedHash = stableFingerprint(raw)
        disposition = 'failed'
        gapReason = 'RESULT_LIMIT_EXCEEDED'
        raw = { ok: false, error: gapReason, trace_id: traceId, result_hash: oversizedHash }
        serialized = JSON.stringify(raw)
      }
      // Commit, derive from, and hand back exactly the JSON the client receives, so a payload
      // the client later presents for certification hashes to the ref committed here
      // (in-memory values such as undefined fields or Dates do not survive the wire).
      raw = JSON.parse(serialized)
      const pagination = deriveInquiryPaginationReceipt(binding, raw, invocationArgs)
      const observed = recordInquiryExecution(contract, {
        item_id: item.item_id, disposition, evidence_refs: [`raw:${stableFingerprint(raw)}`], gap_reason: gapReason,
        pagination, request_position_path: binding.pagination_contract?.request_position_path,
        // A served result may warrant a different capability (RC-5.4); it is pursued only
        // through the governed `continue` successor, never dispatched ad hoc.
        evidence_frontier: disposition === 'served'
          ? deriveEvidenceFrontier({ contract, item_id: item.item_id, evidence_payload: raw, snapshot })
          : [],
      })
      const remaining = observed.iteration >= observed.max_iterations ? [] : nextReady(observed)
      const issued = issueInquiryLifecycleToken({
        sub: principalSubject, inquiry_id: row.inquiry_id, chart_id: row.chart_id,
        contract_hash: row.semantic_contract_hash, execution_plan_hash: row.execution_plan_hash,
        contract_state_hash: stableFingerprint(observed),
        catalog_hash: row.capability_content_hash, compatibility_version: row.capability_compatibility_version,
        overlay_version: row.chart_overlay_version, chart_build_id: row.chart_build_id, revision: row.revision + 1,
        allowed_transition: remaining.length ? 'execute' : 'finalize', next_action_ids: remaining,
      }, key)
      const receiptId = await commitInquiryObservation({
        row, expected_jti_hash: reservation.reservation_hash, next_jti_hash: hashJti(issued.claims.jti), contract: observed,
        evidence: { plan_item_id: item.item_id, obligation_ids: item.obligation_ids, scu_id: item.scu_id, binding_id: item.binding_id,
          canonical_args_hash: stableFingerprint(invocationArgs), raw_result_hash: stableFingerprint(raw), disposition,
          pagination, payload: { trace_id: traceId, result_bytes: Buffer.byteLength(serialized) } },
      })
      return response({ ok: true, inquiry_id: row.inquiry_id, evidence_receipt_id: receiptId, raw_result: raw, disposition, pagination, contract: observed, lifecycle_token: issued.token, next_action_ids: issued.claims.next_action_ids })
    }

    if (claims.allowed_transition !== 'finalize') return response({ ok: false, error: 'INQUIRY_FINALIZE_NOT_AUTHORIZED' }, 409)
    if (body.action === 'continue') {
      let parentFinal: InquiryContract
      let successor: InquiryContract
      try {
        parentFinal = closeInquiryForEvidenceSuccessor(row.contract_jsonb)
        successor = compileInquirySuccessorContract({
          snapshot, overlay: currentOverlay, parent_inquiry_id: row.inquiry_id, parent: parentFinal,
        })
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error)
        if (message === 'INQUIRY_SUCCESSOR_PARENT_NOT_TERMINAL' || message === 'INQUIRY_SUCCESSOR_NO_EVIDENCE_ADMITTED_FRONTIER') {
          return response({ ok: false, error: 'INQUIRY_SUCCESSOR_NOT_AUTHORIZED' }, 409)
        }
        throw error
      }
      const inquiryId = randomUUID()
      const ready = nextReady(successor)
      const issued = issueInquiryLifecycleToken({
        sub: principalSubject, inquiry_id: inquiryId, chart_id: row.chart_id,
        contract_hash: successor.semantic_contract_hash, execution_plan_hash: successor.execution_plan_hash,
        contract_state_hash: stableFingerprint(successor),
        catalog_hash: successor.capability_content_hash, compatibility_version: successor.capability_compatibility_version,
        overlay_version: successor.chart_availability_version, chart_build_id: successor.chart_build_id, revision: 0,
        allowed_transition: ready.length ? 'execute' : 'finalize', next_action_ids: ready,
      }, key)
      await createInquirySuccessorLifecycle({
        parent: row, expected_parent_jti_hash: hashJti(claims.jti), parent_final_contract: parentFinal,
        inquiry_id: inquiryId, contract: successor, jti_hash: hashJti(issued.claims.jti),
        expires_at: new Date(issued.claims.exp * 1000).toISOString(),
      })
      return response({ ok: true, inquiry_id: inquiryId, parent_inquiry_id: row.inquiry_id,
        contract: successor, lifecycle_token: issued.token, next_action_ids: issued.claims.next_action_ids })
    }
    const final = finalizeInquiryContract(row.contract_jsonb)
    await commitInquiryFinalization({ row, expected_jti_hash: hashJti(claims.jti), contract: final })
    return response({
      ok: true,
      inquiry_id: row.inquiry_id,
      // A governed raw-MCP client owns its synthesis. It still needs the exact
      // terminal contract that the server committed in order to build and
      // validate an accountable external answer; a closure summary alone is
      // not an auditable fact-register denominator.
      contract: final,
      closure: buildInquiryClosureReceipt(final),
      inquiry_door_parity: buildInquiryDoorParityProjection(final),
    })
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    if (message === 'INQUIRY_TOKEN_REPLAYED_OR_STALE') return response({ ok: false, error: message }, 409)
    if (PUBLIC_ERROR_CODES.has(message)) {
      const status = message.includes('RATE_LIMITED') || message.includes('ACTIVE_LIMIT') ? 429 : message.includes('TOKEN') ? 401 : 400
      return response({ ok: false, error: message }, status)
    }
    const traceId = randomUUID()
    console.error('[mcp:inquiry] request failed', { traceId, error })
    return response({ ok: false, error: 'INQUIRY_REQUEST_FAILED', trace_id: traceId }, 500)
  }
}

/**
 * Certify an externally synthesized answer against the server's own record (RC-6.4 raw).
 *
 * The raw door hands evidence to the client and lets the client write the answer, so a
 * client-built accountability envelope is only self-attested. Certification rebuilds the fact
 * register and coverage receipt server-side from the FINALIZED contract the server committed and
 * from payloads the client proves it received (each must hash to a `raw:` evidence ref the
 * server committed). It is read-only: nothing is reserved, consumed, or written.
 */
function certifyExternalAnswer(
  body: Extract<Body, { action: 'certify' }>,
  claims: ReturnType<typeof verifyInquiryLifecycleToken>,
  row: NonNullable<Awaited<ReturnType<typeof getInquiryLifecycle>>>,
) {
  // Only the last token issued before the lifecycle went terminal may certify it, and only once
  // terminal. That token is whichever one closed it — a finalize, or an execute that failed
  // closed — so a BLOCKED closure is certifiable too (it simply cannot certify complete).
  if (row.current_jti_hash !== 'terminal' || claims.revision !== row.revision - 1
    || row.chart_id !== claims.chart_id || row.semantic_contract_hash !== claims.contract_hash
    || row.execution_plan_hash !== claims.execution_plan_hash || row.capability_content_hash !== claims.catalog_hash
    || row.contract_jsonb.semantic_contract_hash !== row.semantic_contract_hash
    || row.contract_jsonb.execution_plan_hash !== row.execution_plan_hash
    || row.contract_jsonb.contract_id !== row.authorization_jsonb.contract_id) {
    return response({ ok: false, error: 'INQUIRY_CERTIFICATION_NOT_AUTHORIZED' }, 409)
  }
  const final = row.contract_jsonb
  const snapshot = assertPinnedCapabilityKnowledgeCurrent()
  if (snapshot.content_hash !== final.capability_content_hash) {
    return response({ ok: false, error: 'CAPABILITY_KNOWLEDGE_STALE' }, 409)
  }
  // A successor answer accounts for its parents' evidence too (the register inherits it).
  const committedHashes = new Set(successorChain(final).flatMap((member) => [
    ...member.obligations.flatMap((obligation) => obligation.evidence_refs),
    ...member.plan_items.flatMap((item) => item.observation?.evidence_refs ?? []),
  ]).filter((ref) => ref.startsWith('raw:')).map((ref) => ref.slice('raw:'.length)))
  const supplied = new Map<string, unknown>()
  for (const payload of body.evidence_payloads) {
    if (Buffer.byteLength(JSON.stringify(payload) ?? '') > MAX_RESULT_BYTES) {
      return response({ ok: false, error: 'INQUIRY_CERTIFICATION_PAYLOAD_TOO_LARGE' }, 400)
    }
    const hash = stableFingerprint(payload)
    if (!committedHashes.has(hash)) return response({ ok: false, error: 'INQUIRY_CERTIFICATION_EVIDENCE_UNCOMMITTED' }, 409)
    if (supplied.has(hash)) return response({ ok: false, error: 'INQUIRY_CERTIFICATION_EVIDENCE_DUPLICATED' }, 400)
    supplied.set(hash, payload)
  }
  const citedSpans = body.response_text.split(/\n{2,}/)
    .map((span) => ({ span, handles: inquiryCitedHandles(span) }))
    .filter((entry) => entry.handles.length > 0)
  if (citedSpans.length > MAX_CERTIFY_CITED_SPANS
    || citedSpans.reduce((total, entry) => total + entry.handles.length, 0) > MAX_CERTIFY_CITATIONS) {
    return response({ ok: false, error: 'INQUIRY_CERTIFICATION_TOO_MANY_CITATIONS' }, 400)
  }
  const missingEvidence = [...committedHashes].filter((hash) => !supplied.has(hash)).sort()
  const envelope = buildStructuredResponseAccountability(final, {
    response_text: body.response_text,
    evidence_payloads: [...supplied.values()],
    knowledge_snapshot: snapshot,
  })
  const receipt = envelope.response_coverage_receipt
  // Certification attests evidence COVERAGE: every committed payload was delivered and every
  // required finding is cited by a span that says something of its own. Whether that prose is
  // faithful to the evidence it cites is not decidable here; the independent judge owns it.
  const uncertifiedReasons = [
    ...(receipt.status === 'COMPLETE' ? [] : [`coverage_${receipt.status.toLowerCase()}`]),
    ...(missingEvidence.length ? ['committed_evidence_missing'] : []),
    ...(citedSpans.some(({ span }) => stripInquiryCitationMarkers(span).replace(/[^\p{L}\p{N}]/gu, '').length < MIN_INTERPRETATION_CHARS)
      ? ['citation_without_interpretation'] : []),
  ]
  return response({
    ok: true,
    inquiry_id: row.inquiry_id,
    coverage_certified: uncertifiedReasons.length === 0,
    certification: {
      attests: 'evidence_coverage',
      does_not_attest: 'faithfulness of the prose to the evidence it cites (independent judgment)',
      uncertified_reasons: uncertifiedReasons,
      contract_id: final.contract_id,
      contract_status: final.status,
      chart_build_id: final.chart_build_id,
      response_text_hash: stableFingerprint(body.response_text),
      coverage_receipt_hash: receipt.receipt_hash,
      missing_committed_evidence: missingEvidence,
    },
    response_accountability: envelope,
  })
}
