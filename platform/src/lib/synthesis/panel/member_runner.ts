/**
 * MARSYS-JIS Phase 7 — Panel Member Runner
 * schema_version: 1.0
 *
 * Runs all panel members concurrently. Each member call uses the concurrent
 * retry pattern (N=3 attempts; first success wins). A member that permanently
 * fails returns a structured PanelMemberOutput with status:'failed' rather
 * than throwing — the panel proceeds with surviving members subject to the
 * PANEL_DEGRADE_2_OF_3 flag.
 *
 * Degrade behavior:
 *   PANEL_DEGRADE_2_OF_3=true  → proceed with ≥2 surviving members; attach DegradeNotice
 *   PANEL_DEGRADE_2_OF_3=false → any member failure halts the panel with a structured error
 */

import 'server-only'

import { generateText } from 'ai'
import { resolveModel } from '@/lib/models/resolver'
import { getFlag } from '@/lib/config/index'
import { telemetry } from '@/lib/telemetry/index'
import { concurrentRetry } from './concurrent_retry'
import { loadPanelMemberPrompt } from './prompt_loader'
import { recordAiSdkCall } from '@/lib/llm/observability/observe_ai_sdk'
import type { PanelMemberConfig, PanelMemberOutput, DegradeNotice } from './types'
import type { SynthesisRequest } from '../types'

const MEMBER_TIMEOUT_MS = 30_000
const RETRY_ATTEMPTS = 3

export interface PanelMembersResult {
  member_outputs: PanelMemberOutput[]
  degrade_notice?: DegradeNotice
}

export class PanelDegradedError extends Error {
  constructor(public readonly failed_index: number, cause: Error) {
    super(`Panel member ${failed_index} failed and PANEL_DEGRADE_2_OF_3=false: ${cause.message}`)
    this.name = 'PanelDegradedError'
  }
}

export async function runPanelMembers(
  request: SynthesisRequest,
  members: PanelMemberConfig[],
): Promise<PanelMembersResult> {
  const memberPromises = members.map((config, idx) =>
    runSingleMember(request, config, idx),
  )

  const settlements = await Promise.allSettled(memberPromises)

  const outputs: PanelMemberOutput[] = settlements.map((s, idx) => {
    if (s.status === 'fulfilled') return s.value
    return {
      member_index: idx,
      model_id: members[idx].model_id,
      provider_family: members[idx].provider_family,
      status: 'failed' as const,
      error: s.reason instanceof Error ? s.reason.message : String(s.reason),
      latency_ms: 0,
    }
  })

  const failed = outputs.filter(o => o.status === 'failed')
  const succeeded = outputs.filter(o => o.status === 'success')

  telemetry.recordMetric('panel', 'members_attempted', members.length)
  telemetry.recordMetric('panel', 'members_succeeded', succeeded.length)

  if (failed.length === 0) {
    return { member_outputs: outputs }
  }

  // At least one member failed — check degrade policy.
  if (!getFlag('PANEL_DEGRADE_2_OF_3')) {
    const firstFailed = failed[0]
    throw new PanelDegradedError(
      firstFailed.member_index,
      new Error(firstFailed.error ?? 'unknown member failure'),
    )
  }

  if (succeeded.length < 2) {
    throw new PanelDegradedError(
      failed[0].member_index,
      new Error(`Only ${succeeded.length} member(s) succeeded; need ≥2 for degrade mode`),
    )
  }

  telemetry.recordMetric('panel', 'degrade_engaged', 1)
  const degrade_notice: DegradeNotice = {
    failed_member_index: failed[0].member_index,
    reason: failed[0].error ?? 'member failure',
    surviving_members: succeeded.length,
  }

  return { member_outputs: outputs, degrade_notice }
}

async function runSingleMember(
  request: SynthesisRequest,
  config: PanelMemberConfig,
  idx: number,
): Promise<PanelMemberOutput> {
  const started = Date.now()

  try {
    const answer = await concurrentRetry(async (_signal: AbortSignal) => {
      const prompt = loadPanelMemberPrompt(
        config.prompt_variant_tag ?? 'panel_member_v1',
        request,
      )

      const timeoutPromise = new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error(`Member ${idx} timed out after ${MEMBER_TIMEOUT_MS}ms`)), MEMBER_TIMEOUT_MS),
      )

      const callStartedAt = new Date()
      const callPromise = generateText({
        model: resolveModel(config.model_id),
        messages: [{ role: 'user', content: prompt }],
        maxOutputTokens: 65536,
      }).then(r => {
        recordAiSdkCall({
          pipeline_stage: 'compose',
          model_id: config.model_id,
          conversation_id: request.conversation_id ?? request.query_plan.query_plan_id,
          prompt_id: `${request.query_plan.query_plan_id}:panel:member_${idx}`,
          user_id: 'native',
          parameters: { model: config.model_id, role: `panel_member_${idx}` },
          usage: r.usage,
          status: 'success',
          started_at: callStartedAt,
          finished_at: new Date(),
        })
        return r.text
      })

      return Promise.race([callPromise, timeoutPromise])
    }, RETRY_ATTEMPTS)

    const latency_ms = Date.now() - started
    telemetry.recordLatency('panel', `member_${idx}`, latency_ms)

    return {
      member_index: idx,
      model_id: config.model_id,
      provider_family: config.provider_family,
      status: 'success',
      answer,
      latency_ms,
    }
  } catch (err) {
    telemetry.recordMetric('panel', `member_${idx}_failed`, 1)
    throw err
  }
}
