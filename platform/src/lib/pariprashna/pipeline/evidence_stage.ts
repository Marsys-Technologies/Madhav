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
import { getToolByName } from '@/lib/retrieval/registry/tool_name_bridge'
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

/** The pass id every first-pass retrieval event carries. */
export const PASS_ONE = 1

export interface ToolEventLogEntry {
  name: string
  status: 'done' | 'error'
  ms: number
  ok_count: number
  err_count: number
}

export interface EvidenceStageOutput {
  bundle: Awaited<ReturnType<typeof hydrateBundle>>
  validToolResults: ToolBundle[]
  toolEventLog: ToolEventLogEntry[]
  completenessReceipt: WebCompletenessReceipt | null
  orientation: ChartOrientation | null
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
}): Promise<EvidenceStageOutput> {
  const { em, request, chartId, userUid, plan, queryPlan, manifest, toolsAuthorized, orientationPromise } = args

  em.phase({ phase: 'retrieve', status: 'start', pass_id: PASS_ONE })
  const bundle = await hydrateBundle(plan, manifest)

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
        return null
      }
      const toolStart = Date.now()
      try {
        const result = await getSharedQosDispatchQueue().submit({
          principalId: userUid,
          priorityClass: 'interactive',
          run: () => executeWithCache(t, queryPlan, cache, plannerParamsMap.get(toolName)),
        })
        const ms = Date.now() - toolStart
        em.activity({ key: `retrieve:${toolName}`, label_key: activityLabel, pass_id: PASS_ONE, status: 'done', count: result.results.length, ms })
        toolEventLog.push({ name: toolName, status: 'done', ms, ok_count: result.results.length, err_count: 0 })
        return result
      } catch {
        const ms = Date.now() - toolStart
        em.activity({ key: `retrieve:${toolName}`, label_key: activityLabel, pass_id: PASS_ONE, status: 'error', ms })
        toolEventLog.push({ name: toolName, status: 'error', ms, ok_count: 0, err_count: 1 })
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
      toolEventLog.map((e) => ({ name: e.name, status: e.status, ok_count: e.ok_count })),
    )
  }

  const orientation = await orientationPromise

  return { bundle, validToolResults, toolEventLog, completenessReceipt, orientation }
}
