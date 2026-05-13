/**
 * MARSYS-JIS Phase 7 — Panel Adjudicator
 * schema_version: 1.0
 *
 * The adjudicator is a separate LLM call from a provider family that is
 * different from every panel member. It receives anonymized member outputs
 * (model identity stripped) and synthesizes them — it does NOT pick a winner.
 *
 * Family-level exclusion is enforced programmatically via selectAdjudicator().
 * Anonymization is enforced via anonymizePanelOutputs() — tests verify that
 * no model/provider names appear in the rendered prompt.
 */

import 'server-only'

import { generateText } from 'ai'
import { z } from 'zod'
import { resolveModel } from '@/lib/models/resolver'
import { telemetry } from '@/lib/telemetry/index'
import { recordAiSdkCall } from '@/lib/llm/observability/observe_ai_sdk'
import { selectAdjudicator, DEFAULT_PANEL_SLATE, ADJUDICATOR_CANDIDATE_POOL } from './default_slate'
import { loadAdjudicatorPrompt } from './prompt_loader'
import type { PanelMemberConfig, PanelMemberOutput, AnonymizedMemberOutput, AdjudicationResult, DivergenceSummary, MemberAlignment } from './types'
import type { SynthesisRequest } from '../types'

const ADJUDICATOR_TIMEOUT_MS = 45_000

// ── Anonymization ──────────────────────────────────────────────────────────────

/** Strip model identity from outputs. Test that the rendered prompt has no model/provider names. */
export function anonymizePanelOutputs(outputs: PanelMemberOutput[]): AnonymizedMemberOutput[] {
  return outputs
    .filter(o => o.status === 'success' && o.answer)
    .map((o, i) => ({
      member_label: `Member ${i + 1}`,
      answer: o.answer!,
      latency_ms: o.latency_ms,
    }))
}

// ── LLM output schema ──────────────────────────────────────────────────────────

const MemberAlignmentSchema = z.enum(['aligned', 'partial', 'dissent'])

const AdjudicatorOutputSchema = z.object({
  final_answer: z.string().min(1),
  divergence_summary: z.object({
    has_divergence: z.boolean(),
    divergence_count: z.number().int().min(0),
    summary_text: z.string(),
  }),
  member_alignment: z.record(z.string(), MemberAlignmentSchema),
})

type AdjudicatorOutput = z.infer<typeof AdjudicatorOutputSchema>

// ── Main entry ─────────────────────────────────────────────────────────────────

export async function adjudicate(
  memberOutputs: PanelMemberOutput[],
  request: SynthesisRequest,
  memberSlate: PanelMemberConfig[] = DEFAULT_PANEL_SLATE,
): Promise<AdjudicationResult> {
  const adjConfig = selectAdjudicator(memberSlate, ADJUDICATOR_CANDIDATE_POOL)

  const anonymized = anonymizePanelOutputs(memberOutputs)
  if (anonymized.length < 2) {
    throw new Error(
      `Adjudicator requires ≥2 anonymized member outputs; got ${anonymized.length}`,
    )
  }

  const prompt = loadAdjudicatorPrompt('adjudicator_v1', anonymized, request)

  // Safety check: prompt must not contain any model or provider identifiers.
  assertNoModelNamesInPrompt(prompt, memberOutputs)

  const started = Date.now()

  const timeoutPromise = new Promise<never>((_, reject) =>
    setTimeout(
      () => reject(new Error(`Adjudicator timed out after ${ADJUDICATOR_TIMEOUT_MS}ms`)),
      ADJUDICATOR_TIMEOUT_MS,
    ),
  )

  const callStartedAt = new Date(started)
  const callPromise = generateText({
    model: resolveModel(adjConfig.model_id),
    messages: [{ role: 'user', content: prompt }],
    maxOutputTokens: 65536,
  }).then(r => {
    recordAiSdkCall({
      pipeline_stage: 'audit',
      model_id: adjConfig.model_id,
      conversation_id: request.conversation_id ?? request.query_plan.query_plan_id,
      prompt_id: `${request.query_plan.query_plan_id}:panel:adjudicator`,
      user_id: 'native',
      parameters: { model: adjConfig.model_id, role: 'adjudicator' },
      usage: r.usage,
      status: 'success',
      started_at: callStartedAt,
      finished_at: new Date(),
    })
    return r.text
  })

  const raw = await Promise.race([callPromise, timeoutPromise])
  const latency_ms = Date.now() - started

  telemetry.recordLatency('panel', 'adjudicator', latency_ms)

  const parsed = parseAdjudicatorOutput(raw, adjConfig.model_id, latency_ms)
  return parsed
}

// ── Parsing ────────────────────────────────────────────────────────────────────

function parseAdjudicatorOutput(
  raw: string,
  adjudicator_model_id: string,
  latency_ms: number,
): AdjudicationResult {
  let json: unknown
  try {
    // Strip markdown fences if present
    const cleaned = raw.trim().replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '')
    json = JSON.parse(cleaned)
  } catch {
    telemetry.recordMetric('panel', 'adjudicator_parse_error', 1)
    // Fallback: treat raw as final_answer with no divergence
    return {
      final_answer: raw,
      divergence_summary: {
        has_divergence: false,
        divergence_count: 0,
        summary_text: 'parse error — adjudicator output was not JSON',
      },
      member_alignment: {},
      adjudicator_model_id,
      latency_ms,
    }
  }

  const result = AdjudicatorOutputSchema.safeParse(json)
  if (!result.success) {
    telemetry.recordMetric('panel', 'adjudicator_schema_error', 1)
    const data = json as Partial<AdjudicatorOutput>
    return {
      final_answer: typeof data?.final_answer === 'string' ? data.final_answer : raw,
      divergence_summary: {
        has_divergence: false,
        divergence_count: 0,
        summary_text: 'schema validation failed — adjudicator output malformed',
      },
      member_alignment: {},
      adjudicator_model_id,
      latency_ms,
    }
  }

  const { final_answer, divergence_summary, member_alignment } = result.data

  return {
    final_answer,
    divergence_summary: divergence_summary as DivergenceSummary,
    member_alignment: member_alignment as Record<string, MemberAlignment>,
    adjudicator_model_id,
    latency_ms,
  }
}

// ── Anonymization verification ─────────────────────────────────────────────────

const KNOWN_PROVIDER_NAMES = [
  'anthropic', 'claude', 'openai', 'gpt', 'google', 'gemini', 'deepseek',
]

/** Throws if the adjudicator prompt leaks any model/provider names. */
export function assertNoModelNamesInPrompt(
  prompt: string,
  memberOutputs: PanelMemberOutput[],
): void {
  const promptLower = prompt.toLowerCase()

  // Check known provider family names
  for (const name of KNOWN_PROVIDER_NAMES) {
    if (promptLower.includes(name)) {
      throw new Error(
        `Anonymization violation: prompt contains provider/model identifier "${name}". ` +
          `Strip all model/provider identities before passing to adjudicator.`,
      )
    }
  }

  // Check specific model IDs from member outputs
  for (const output of memberOutputs) {
    if (promptLower.includes(output.model_id.toLowerCase())) {
      throw new Error(
        `Anonymization violation: prompt contains model id "${output.model_id}"`,
      )
    }
  }
}
