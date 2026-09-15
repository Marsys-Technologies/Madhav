/**
 * Paripraśna pipeline — EVIDENCE STAGE (P0-C / RF-1).
 *
 * Ports: `ToolBroker → EvidenceBundle`.
 *
 * Retrieval pass 1 over the SAME in-process registry the consult route uses
 * (`getToolByName` → `executeWithCache` — a direct function call, ZERO HTTP to
 * any MCP edge), plus the bundle hydration and the completeness receipt built
 * from the pass's own outcomes.
 *
 * Every dispatch is surfaced as an `activity.upsert` triple (running → done |
 * error) whose `label_key` is resolved through the closed lexicon, never a raw
 * tool name (gate 11 [integrity]).
 */

import { hydrateBundle } from '@/lib/bundle/bundle_hydrator'
import { getToolByName, resolveToolUri } from '@/lib/retrieval/registry/tool_name_bridge'
import { createToolCache, executeWithCache } from '@/lib/cache/index'
import { getSharedQosDispatchQueue } from '@/lib/retrieval/qos/dispatch_queue'
import type { ToolBundle, RetrievalTool } from '@/lib/retrieval/shared_types'
import {
  buildWebCompletenessReceipt,
  type WebCompletenessReceipt,
} from '@/lib/pipeline/completeness_wiring'
import type { PipelinePlan } from '@/lib/pipeline/types'
import type { ChartOrientation } from '@/lib/retrieval/orientation'
import type { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'
import { loadManifest } from '@/lib/bundle/manifest_reader'

import { resolveActivityLabel } from './stage_context'
import type { LegacyQueryPlan } from './plan_stage'
import { bindingForInquiryItem, classifyInquiryResult, deriveInquiryPaginationReceipt, failInquiryForOverlayDrift, finalizeInquiryContract, recordInquiryExecution, type InquiryContract } from '@/lib/vidhi/inquiry'
import { getPinnedCapabilityKnowledgeSnapshot, loadChartCapabilityOverlay } from '@/lib/retrieval/registry/knowledge'
import { stableFingerprint } from '@/lib/retrieval/registry/knowledge/stable'

/** The pass id every first-pass retrieval event carries. */
export const PASS_ONE = 1

export interface ToolEventLogEntry {
  name: string
  status: 'done' | 'error'
  ms: number
  ok_count: number
  err_count: number
  /**
   * Distinguishes the failure class when status==='error' (V3-E-034). Both classes are
   * recorded IDENTICALLY in shape here (status:'error') — a registry-lookup miss (the tool
   * name failed `getToolByName`, so nothing was ever dispatched) and a dispatch throw (the
   * tool was found but the call itself threw) are the same failure severity and both deserve a
   * `toolEventLog` row. This field lets a downstream consumer (completeness_wiring.ts) report a
   * distinct, honest `empty_reason` for each class instead of collapsing a registry-unresolvable
   * authorized tool into the same bucket as a tool that was never authorized at all.
   */
  error_kind?: 'registry_unresolvable' | 'dispatch_error'
}

export interface EvidenceStageOutput {
  bundle: Awaited<ReturnType<typeof hydrateBundle>>
  validToolResults: ToolBundle[]
  toolEventLog: ToolEventLogEntry[]
  completenessReceipt: WebCompletenessReceipt | null
  orientation: ChartOrientation | null
  inquiryContract: InquiryContract | null
}

export async function runEvidenceStage(args: {
  em: PariprashnaEmitter
  request: Request
  chartId: string
  userUid: string
  plan: PipelinePlan
  queryPlan: LegacyQueryPlan
  manifest: Awaited<ReturnType<typeof loadManifest>>
  toolsAuthorized: string[]
  orientationPromise: Promise<ChartOrientation | null>
  inquiryContract?: InquiryContract | null
}): Promise<EvidenceStageOutput> {
  const { em, request, chartId, userUid, plan, queryPlan, manifest, toolsAuthorized, orientationPromise } = args

  em.phase({ phase: 'retrieve', status: 'start', pass_id: PASS_ONE })
  // V3-E-016: `chartId` scopes which native-bound corpus assets may enter this
  // turn's synthesis prompt. Never omit it — the hydrator has no unscoped path.
  const bundle = await hydrateBundle(plan, manifest, { chartId })

  const plannerParamsMap = new Map<string, Record<string, unknown>>(
    plan.tool_calls.map((tc) => [tc.tool_name, tc.params]),
  )
  const cache = createToolCache()
  const toolEventLog: ToolEventLogEntry[] = []
  const retrieveStart = Date.now()

  const toolResults = await Promise.all(
    toolsAuthorized.map(async (toolName): Promise<ToolBundle | null> => {
      if (request.signal.aborted) return null
      const activityLabel = resolveActivityLabel(toolName)
      em.activity({ key: `retrieve:${toolName}`, label_key: activityLabel, pass_id: PASS_ONE, status: 'running' })
      const t = getToolByName(toolName) as RetrievalTool | undefined
      if (!t) {
        em.activity({ key: `retrieve:${toolName}`, label_key: activityLabel, pass_id: PASS_ONE, status: 'error' })
        // V3-E-034: a registry-lookup miss is the same failure severity as a dispatch throw
        // below — record it identically (a toolEventLog row with status:'error') rather than
        // letting it silently escape the log with zero rows, which downstream collapsed into
        // the SAME empty_reason as "correctly never authorized" (completeness_wiring.ts).
        toolEventLog.push({ name: toolName, status: 'error', ms: 0, ok_count: 0, err_count: 1, error_kind: 'registry_unresolvable' })
        return null
      }
      const toolStart = Date.now()
      try {
        const result = await getSharedQosDispatchQueue().submit({
          principalId: userUid,
          priorityClass: 'interactive',
          units: t.dispatch_units ?? 1,
          run: () => executeWithCache(t, queryPlan, cache, plannerParamsMap.get(toolName)),
        })
        const ms = Date.now() - toolStart
        em.activity({ key: `retrieve:${toolName}`, label_key: activityLabel, pass_id: PASS_ONE, status: 'done', count: result.results.length, ms })
        toolEventLog.push({ name: toolName, status: 'done', ms, ok_count: result.results.length, err_count: 0 })
        return result
      } catch {
        const ms = Date.now() - toolStart
        em.activity({ key: `retrieve:${toolName}`, label_key: activityLabel, pass_id: PASS_ONE, status: 'error', ms })
        toolEventLog.push({ name: toolName, status: 'error', ms, ok_count: 0, err_count: 1, error_kind: 'dispatch_error' })
        return null
      }
    }),
  )
  const validToolResults = toolResults.filter((r): r is ToolBundle => r !== null)
  em.phase({ phase: 'retrieve', status: 'end', pass_id: PASS_ONE, ms: Date.now() - retrieveStart })

  // Completeness receipt — always built for deep_dive; otherwise when the plan
  // carried a scope_tuple. Surfaced as a `grade` by the receipt stage.
  let completenessReceipt: WebCompletenessReceipt | null = null
  if (plan.scope_tuple) {
    completenessReceipt = buildWebCompletenessReceipt(
      plan.scope_tuple,
      chartId,
      toolEventLog.map((e) => ({ name: e.name, status: e.status, ok_count: e.ok_count, error_kind: e.error_kind })),
    )
  }

  const orientation = await orientationPromise

  let inquiryContract = args.inquiryContract ?? null
  if (inquiryContract) {
    const snapshot = getPinnedCapabilityKnowledgeSnapshot()
    const resultsByUri = new Map(toolResults.flatMap((result, index) => {
      const uri = resolveToolUri(toolsAuthorized[index] ?? '')
      return result && uri ? [[uri, result] as const] : []
    }))
    const eventsByUri = new Map(toolEventLog.flatMap((event) => {
      const uri = resolveToolUri(event.name)
      return uri ? [[uri, event] as const] : []
    }))
    for (const item of [...inquiryContract.plan_items]) {
      const capabilityUri = item.binding_id?.replace(/^registry:/, '')
      const event = capabilityUri ? eventsByUri.get(capabilityUri) : undefined
      if (!event) continue
      const binding = bindingForInquiryItem(snapshot, inquiryContract, item.item_id)
      if (event.status === 'error') {
        inquiryContract = recordInquiryExecution(inquiryContract, {
          item_id: item.item_id, disposition: 'failed', evidence_refs: [], gap_reason: event.error_kind ?? 'dispatch_error',
          pagination: { semantics: binding?.pagination ?? 'none', exhausted: true, next: null },
          request_position_path: binding?.pagination_contract?.request_position_path,
        })
        continue
      }
      const raw = capabilityUri ? resultsByUri.get(capabilityUri) : undefined
      if (!raw) continue
      const disposition = classifyInquiryResult(binding, raw)
      const pagination = deriveInquiryPaginationReceipt(binding, raw, item.args)
      inquiryContract = recordInquiryExecution(inquiryContract, {
        item_id: item.item_id, disposition,
        evidence_refs: [`retrieval:${event.name}:pass-${PASS_ONE}:${stableFingerprint(raw)}`],
        ...(disposition === 'failed' ? { gap_reason: 'tool_failure_envelope' } : {}),
        pagination, request_position_path: binding?.pagination_contract?.request_position_path,
      })
    }

    let pass = PASS_ONE + 1
    while (inquiryContract.iteration < inquiryContract.max_iterations && !request.signal.aborted) {
      const item = inquiryContract.plan_items.find((candidate) => candidate.state === 'ready'
        && candidate.observation !== null && candidate.binding_id?.startsWith('registry:'))
      if (!item?.binding_id) break
      const capabilityUri = item.binding_id.slice('registry:'.length)
      const toolName = toolsAuthorized.find((name) => resolveToolUri(name) === capabilityUri)
      const tool = toolName ? getToolByName(toolName) as RetrievalTool | undefined : undefined
      const binding = bindingForInquiryItem(snapshot, inquiryContract, item.item_id)
      if (!toolName || !tool || !binding) break
      const started = Date.now()
      try {
        const raw = await getSharedQosDispatchQueue().submit({
          principalId: userUid,
          priorityClass: 'interactive',
          units: tool.dispatch_units ?? 1,
          // A continuation has distinct server-authorized cursor arguments.
          // Execute it directly so request/shared cache normalization can never
          // replay page one under a later page's authorization envelope.
          run: () => tool.retrieve(queryPlan, item.args),
        })
        const ms = Date.now() - started
        validToolResults.push(raw)
        toolEventLog.push({ name: toolName, status: 'done', ms, ok_count: raw.results.length, err_count: 0 })
        const disposition = classifyInquiryResult(binding, raw)
        const pagination = deriveInquiryPaginationReceipt(binding, raw, item.args)
        inquiryContract = recordInquiryExecution(inquiryContract, {
          item_id: item.item_id, disposition,
          evidence_refs: [`retrieval:${toolName}:pass-${pass}:${stableFingerprint(raw)}`],
          ...(disposition === 'failed' ? { gap_reason: 'tool_failure_envelope' } : {}),
          pagination, request_position_path: binding.pagination_contract?.request_position_path,
        })
      } catch {
        const ms = Date.now() - started
        toolEventLog.push({ name: toolName, status: 'error', ms, ok_count: 0, err_count: 1, error_kind: 'dispatch_error' })
        inquiryContract = recordInquiryExecution(inquiryContract, {
          item_id: item.item_id, disposition: 'failed', evidence_refs: [], gap_reason: 'dispatch_error',
          pagination: { semantics: binding.pagination, exhausted: true, next: null },
          request_position_path: binding.pagination_contract?.request_position_path,
        })
      }
      pass += 1
    }
    const currentOverlay = await loadChartCapabilityOverlay(snapshot, chartId)
    inquiryContract = currentOverlay.overlay_version === inquiryContract.chart_availability_version
      && currentOverlay.build_id === inquiryContract.chart_build_id
      ? finalizeInquiryContract(inquiryContract)
      : failInquiryForOverlayDrift(inquiryContract)
  }

  return { bundle, validToolResults, toolEventLog, completenessReceipt, orientation, inquiryContract }
}
