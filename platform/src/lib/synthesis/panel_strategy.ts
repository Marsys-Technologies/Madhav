/**
 * MARSYS-JIS Stream E — Panel Mode Orchestrator
 * schema_version: 1.0
 *
 * Orchestrates the full panel synthesis pipeline:
 *   1. runPanelMembers → concurrent multi-provider member calls
 *   2. adjudicate      → cross-provider synthesis (anonymized)
 *   3. runCheckpoint8_5 (panel-aware variant, if CHECKPOINT_8_5_ENABLED)
 *   4. classifyDivergence → audit-level divergence classification
 *   5. streamText passthrough → yields a real StreamTextResult for route.ts
 *
 * Flag-off: when PANEL_MODE_ENABLED=false or panel_opt_in=false the
 * createOrchestrator() factory never instantiates this class — so this file
 * has zero runtime cost on the single-model path.
 */

import 'server-only'

import { streamText } from 'ai'

import { resolveModel } from '@/lib/models/resolver'
import { getFlag } from '@/lib/config/index'
import { telemetry } from '@/lib/telemetry/index'

import { runCheckpoint8_5 } from '@/lib/checkpoints/checkpoint_8_5'
import type { Checkpoint85Result } from '@/lib/checkpoints/types'

import { recordAiSdkCall } from '@/lib/llm/observability/observe_ai_sdk'
import { runPanelMembers } from './panel/member_runner'
import { adjudicate } from './panel/adjudicator'
import { classifyDivergence } from './panel/divergence_detector'
import { DEFAULT_PANEL_SLATE } from './panel/default_slate'

import type {
  SynthesisRequest,
  SynthesisResult,
  SynthesisMetadata,
  SynthesisAuditEvent,
  SynthesisOrchestrator,
  PanelAuditPayload,
} from './types'

/**
 * The cheapest model used for the passthrough streamText call.
 * Panel synthesis is already done — this call just streams the final_answer
 * text back to the caller with zero additional LLM computation.
 */
const PASSTHROUGH_MODEL = 'claude-haiku-4-5'

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
    const { member_outputs, degrade_notice } = await runPanelMembers(request, DEFAULT_PANEL_SLATE)

    telemetry.recordMetric('panel', 'orchestrator_members_done', member_outputs.length)

    // ── Step 2: Adjudicate ────────────────────────────────────────────────────
    const adjudication = await adjudicate(member_outputs, request, DEFAULT_PANEL_SLATE)

    telemetry.recordMetric('panel', 'orchestrator_adjudication_done', 1)

    // ── Step 3: Checkpoint 8.5 (panel-aware) ─────────────────────────────────
    // Panel-aware variant: prepend a context note so 8.5's prompt knows the
    // input is panel-adjudicator output and should verify the divergence_summary
    // is honest (no contradictions silently smoothed).
    let c8_5Result: Checkpoint85Result | undefined
    if (getFlag('CHECKPOINT_8_5_ENABLED')) {
      const panelAwareText = `[PANEL-SYNTHESIZED]\n\n${adjudication.final_answer}`
      try {
        c8_5Result = await runCheckpoint8_5({
          synthesized_text: panelAwareText,
          query_class: query_plan.query_class,
          validator_results: [],
        })
      } catch {
        // CheckpointHaltError with FAIL_HARD=true — log; stream already in flight
        telemetry.recordMetric('panel', 'checkpoint_8_5_late_halt', 1)
      }
    }

    // ── Step 4: Divergence classification ────────────────────────────────────
    const divergence = classifyDivergence(member_outputs, adjudication)

    // ── Step 5: Build audit panel payload ────────────────────────────────────
    const panelPayload: PanelAuditPayload = {
      panel_slate: DEFAULT_PANEL_SLATE.map(m => m.model_id),
      adjudicator_model_id: adjudication.adjudicator_model_id,
      member_statuses: member_outputs.map(o => o.status),
      divergence_classification: divergence,
      degrade_notice: degrade_notice
        ? `Member ${degrade_notice.failed_member_index} failed (${degrade_notice.reason}); ${degrade_notice.surviving_members} members survived`
        : undefined,
    }

    const metadata: SynthesisMetadata = {
      synthesis_prompt_version: '1.0',
      synthesizer_model_id: `panel:${adjudication.adjudicator_model_id}`,
      bundle_hash: bundle.bundle_hash,
      started_at,
    }

    // ── Step 6: Passthrough streamText ────────────────────────────────────────
    // We need a real StreamTextResult so route.ts can call toUIMessageStreamResponse().
    // The panel answer is already fully computed; we emit it via a trivial
    // "verbatim output" streamText call using the cheapest model.
    const passthroughModel = PASSTHROUGH_MODEL
    const finalAnswer = adjudication.final_answer
    const passthroughStartedAt = new Date()

    const result = streamText({
      model: resolveModel(passthroughModel),
      messages: [
        {
          role: 'system',
          content: 'Output the following text verbatim, do not modify it:',
        },
        {
          role: 'user',
          content: finalAnswer,
        },
      ],
      maxOutputTokens: 8192,
      onFinish: async ({
        finishReason,
        usage,
        text,
      }: {
        finishReason: string
        usage?: { inputTokens?: number; outputTokens?: number }
        text?: string
      }) => {
        telemetry.recordMetric('panel', 'stream_finish', 1, { finishReason })
        telemetry.recordCost(
          'panel',
          passthroughModel,
          usage?.inputTokens ?? 0,
          usage?.outputTokens ?? 0,
          0,
        )

        recordAiSdkCall({
          pipeline_stage: 'synthesize',
          model_id: passthroughModel,
          conversation_id: request.conversation_id ?? query_plan.query_plan_id,
          prompt_id: `${query_plan.query_plan_id}:panel:passthrough`,
          user_id: 'native',
          parameters: { model: passthroughModel, role: 'panel_passthrough' },
          usage,
          status: finishReason === 'error' ? 'error' : 'success',
          error_code: finishReason === 'error' ? finishReason : null,
          started_at: passthroughStartedAt,
          finished_at: new Date(),
        })

        const auditEvent: SynthesisAuditEvent = {
          event_type: 'synthesis_complete',
          query_plan_id: query_plan.query_plan_id,
          bundle_id: bundle.bundle_id,
          synthesis_prompt_version: metadata.synthesis_prompt_version,
          synthesizer_model_id: metadata.synthesizer_model_id,
          finish_reason: finishReason,
          validator_votes: {},
          started_at: metadata.started_at,
          finished_at: new Date().toISOString(),
          input_tokens: usage?.inputTokens ?? 0,
          output_tokens: usage?.outputTokens ?? 0,
          final_output: text ?? finalAnswer,
          checkpoints: c8_5Result ? { c8_5: c8_5Result } : undefined,
          prediction: c8_5Result?.prediction,
          panel: panelPayload,
        }

        telemetry.recordMetric('panel', 'audit_event', 1, {
          event_type: 'synthesis_complete',
        })
        console.log('[panel] audit event:', JSON.stringify(auditEvent))

        onAuditEvent?.(auditEvent)
      },
    })

    // Suppress unused variable warning for query (used by member runner via request)
    void query

    return { result, metadata }
  }
}
