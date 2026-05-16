/**
 * MARSYS-JIS Stream E — Panel Mode Orchestrator
 * schema_version: 2.0 (β9 — honest streaming adjudicator)
 *
 * Orchestrates the full panel synthesis pipeline:
 *   1. runPanelMembers → concurrent multi-provider member calls
 *   2. streamAdjudicate → streaming adjudicator whose output IS the user stream
 *   3. runCheckpoint8_5 (panel-aware variant, inside adjudicator onFinish)
 *   4. classifyDivergence → heuristic-only (no structured adjudicator JSON in β9)
 *
 * β9 change: PASSTHROUGH_MODEL removed. The adjudicator's streamText call is
 * the user-visible stream — no secondary LLM call to re-emit a pre-computed answer.
 * Member stage events are buffered and returned in SynthesisResult.panelStageEvents
 * for the route to replay via writer.write() before merging the adjudicator stream.
 *
 * Flag-off: when PANEL_MODE_ENABLED=false or panel_opt_in=false the
 * createOrchestrator() factory never instantiates this class — so this file
 * has zero runtime cost on the single-model path.
 */

import 'server-only'

import { getFlag } from '@/lib/config/index'
import { telemetry } from '@/lib/telemetry/index'

import { runCheckpoint8_5 } from '@/lib/checkpoints/checkpoint_8_5'

import { recordAiSdkCall } from '@/lib/llm/observability/observe_ai_sdk'
import { runPanelMembers } from './panel/member_runner'
import { streamAdjudicate } from './panel/adjudicator'
import { DEFAULT_PANEL_SLATE } from './panel/default_slate'
import { stagePart } from '@/lib/streams/data_parts'

import type {
  SynthesisRequest,
  SynthesisResult,
  SynthesisMetadata,
  SynthesisAuditEvent,
  SynthesisOrchestrator,
  PanelAuditPayload,
} from './types'
import type { PanelMemberOutput } from './panel/types'

export class PanelModeOrchestrator implements SynthesisOrchestrator {
  async synthesize(request: SynthesisRequest): Promise<SynthesisResult> {
    const {
      query,
      query_plan,
      bundle,
      cache: _cache,
      onAuditEvent,
    } = request

    const started_at = new Date().toISOString()

    // ── Step 1: Run panel members concurrently ────────────────────────────────
    // Collect stage events: emit running for each member at start, done after allSettled.
    // Since runPanelMembers awaits allSettled, we pre-populate running events before
    // calling it, then done events after it returns.
    const memberCount = DEFAULT_PANEL_SLATE.length
    const panelStageEvents: Array<{ type: string; data: unknown }> = []

    // running events for all members (emitted before they actually finish — optimistic)
    for (let i = 0; i < memberCount; i++) {
      const stageName = `panel:member:${i + 1}` as `panel:member:${1 | 2 | 3}`
      panelStageEvents.push({ type: 'data-stage', data: stagePart(stageName, 'running') })
    }

    const memberStartMs = Date.now()
    const { member_outputs, degrade_notice } = await runPanelMembers(request, DEFAULT_PANEL_SLATE)
    const memberElapsedMs = Date.now() - memberStartMs

    telemetry.recordMetric('panel', 'orchestrator_members_done', member_outputs.length)

    // done events for each member
    for (const output of member_outputs) {
      const stageName = `panel:member:${output.member_index + 1}` as `panel:member:${1 | 2 | 3}`
      const status = output.status === 'success' ? 'done' : 'error'
      panelStageEvents.push({
        type: 'data-stage',
        data: stagePart(stageName, status, output.latency_ms),
      })
    }

    // adjudicator running event
    panelStageEvents.push({ type: 'data-stage', data: stagePart('panel:adjudicator', 'running') })

    // ── Step 2: Divergence heuristic (member-only, no structured adjudicator JSON) ──
    // β9: the streaming adjudicator outputs plain prose, not JSON.  We compute a
    // lightweight divergence estimate from member outputs alone.
    const hasDivergence = estimateDivergence(member_outputs)

    const metadata: SynthesisMetadata = {
      synthesis_prompt_version: '2.0',
      synthesizer_model_id: 'panel:streaming',
      bundle_hash: bundle.bundle_hash,
      started_at,
    }

    // ── Step 3: Stream adjudicator — this IS the user-visible stream ──────────
    const adjudicatorStartedAt = new Date()

    // Mutable holders populated inside rawOnFinish
    const adjudicatorModelHolder: { value: string } = { value: 'unknown' }

    const rawResult = streamAdjudicate(
      member_outputs,
      request,
      DEFAULT_PANEL_SLATE,
      async ({ finishReason, usage, text }) => {
        // checkpoint 8.5 runs post-stream (non-blocking for the user; stream already done)
        if (getFlag('CHECKPOINT_8_5_ENABLED')) {
          const panelAwareText = `[PANEL-SYNTHESIZED]\n\n${text ?? ''}`
          try {
            await runCheckpoint8_5({
              synthesized_text: panelAwareText,
              query_class: query_plan.query_class,
              validator_results: [],
            })
          } catch {
            telemetry.recordMetric('panel', 'checkpoint_8_5_late_halt', 1)
          }
        }

        // Build panel audit payload using heuristic divergence
        const panelPayload: PanelAuditPayload = {
          panel_slate: DEFAULT_PANEL_SLATE.map(m => m.model_id),
          adjudicator_model_id: adjudicatorModelHolder.value,
          member_statuses: member_outputs.map(o => o.status),
          divergence_classification: {
            has_divergence: hasDivergence,
            instances: [],
            member_alignment_summary: {},
          },
          degrade_notice: degrade_notice
            ? `Member ${degrade_notice.failed_member_index} failed (${degrade_notice.reason}); ${degrade_notice.surviving_members} members survived`
            : undefined,
        }

        const updatedMetadata: SynthesisMetadata = {
          ...metadata,
          synthesizer_model_id: `panel:${adjudicatorModelHolder.value}`,
        }

        telemetry.recordMetric('panel', 'orchestrator_adjudication_done', 1)
        telemetry.recordLatency('panel', 'full_pipeline', Date.now() - adjudicatorStartedAt.getTime() + (memberElapsedMs))

        recordAiSdkCall({
          pipeline_stage: 'synthesize',
          model_id: adjudicatorModelHolder.value,
          conversation_id: request.conversation_id ?? query_plan.query_plan_id,
          prompt_id: `${query_plan.query_plan_id}:panel:orchestrator`,
          user_id: 'native',
          parameters: { model: adjudicatorModelHolder.value, role: 'panel_orchestrator' },
          usage,
          status: finishReason === 'error' ? 'error' : 'success',
          error_code: finishReason === 'error' ? finishReason : null,
          started_at: adjudicatorStartedAt,
          finished_at: new Date(),
        })

        const auditEvent: SynthesisAuditEvent = {
          event_type: 'synthesis_complete',
          query_plan_id: query_plan.query_plan_id,
          bundle_id: bundle.bundle_id,
          synthesis_prompt_version: updatedMetadata.synthesis_prompt_version,
          synthesizer_model_id: updatedMetadata.synthesizer_model_id,
          finish_reason: finishReason,
          validator_votes: {},
          started_at: updatedMetadata.started_at,
          finished_at: new Date().toISOString(),
          input_tokens: usage?.inputTokens ?? 0,
          output_tokens: usage?.outputTokens ?? 0,
          final_output: text ?? '',
          panel: panelPayload,
        }

        telemetry.recordMetric('panel', 'audit_event', 1, { event_type: 'synthesis_complete' })
        console.log('[panel] audit event:', JSON.stringify(auditEvent))
        onAuditEvent?.(auditEvent)
      },
    )

    adjudicatorModelHolder.value = rawResult.adjudicator_model_id

    // Suppress unused variable warning for query (used by member runner via request)
    void query

    return {
      result: rawResult.result,
      metadata: { ...metadata, synthesizer_model_id: `panel:${rawResult.adjudicator_model_id}` },
      panelStageEvents,
    }
  }
}

// ── Heuristic divergence estimate (β9 — no structured adjudicator output) ────

/** Returns true if member answers show detectable divergence by length or content overlap. */
function estimateDivergence(memberOutputs: PanelMemberOutput[]): boolean {
  const answers = memberOutputs.filter(o => o.status === 'success' && o.answer).map(o => o.answer!)
  if (answers.length < 2) return false

  // Length heuristic: if longest answer is >2x shortest, likely divergence in scope.
  const lengths = answers.map(a => a.length)
  const maxLen = Math.max(...lengths)
  const minLen = Math.min(...lengths)
  if (minLen > 0 && maxLen / minLen > 2) return true

  // First-sentence heuristic: if no common bigrams in opening sentences, likely divergence.
  const firstSentences = answers.map(a => a.split(/[.!?]/)[0]?.toLowerCase() ?? '')
  const bigrams = (s: string) => {
    const words = s.split(/\s+/).filter(Boolean)
    return new Set(words.slice(0, -1).map((w, i) => `${w} ${words[i + 1]}`))
  }
  const sets = firstSentences.map(bigrams)
  if (sets.length >= 2) {
    const intersection = [...sets[0]].filter(b => sets[1].has(b))
    if (intersection.length === 0) return true
  }

  return false
}
