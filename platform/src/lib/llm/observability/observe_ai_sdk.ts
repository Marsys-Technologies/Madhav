// Lightweight bridge from the Vercel AI SDK (`generateText`/`streamText`) into
// the Observatory. Many of MARSYS's pipeline call sites use `generateText`
// directly (panel members, adjudicator, title, planner, history-summary)
// rather than the provider-native shims. Without this bridge those calls were
// invisible to the LLM Observatory — only `synthesize` and `title` showed up,
// which is wrong: every stage that issues an LLM call should report token
// usage and cost so the cost-by-stage chart reflects reality.
//
// Usage:
//   const startedAt = new Date()
//   const result = await generateText({ ... })
//   const finishedAt = new Date()
//   void recordAiSdkCall({
//     pipeline_stage: 'compose',
//     model_id: <modelId>,
//     conversation_id, prompt_id, user_id,
//     usage: result.usage,
//     status: 'success',
//     started_at: startedAt,
//     finished_at: finishedAt,
//   })
//
// Fire-and-forget. Never throws; observability errors must not break the
// caller path.

import 'server-only'

import { computeCost, persistObservation } from './index'
import type { PipelineStage, ProviderName, TokenUsage } from './types'
import { resolveProvider } from '@/lib/db/monitoring-write'
import { getStorageClient } from '@/lib/storage'

interface AiSdkUsage {
  inputTokens?: number | null
  outputTokens?: number | null
  reasoningTokens?: number | null
  cachedInputTokens?: number | null
  cacheCreationInputTokens?: number | null
  cacheReadInputTokens?: number | null
}

export interface RecordAiSdkCallInput {
  pipeline_stage: PipelineStage
  model_id: string
  conversation_id: string
  conversation_name?: string | null
  prompt_id: string
  parent_prompt_id?: string
  user_id: string
  parameters?: unknown
  usage: AiSdkUsage | undefined
  status: 'success' | 'error' | 'timeout'
  error_code?: string | null
  started_at: Date
  finished_at: Date
}

function normalizeUsage(u: AiSdkUsage | undefined): TokenUsage {
  return {
    input_tokens: u?.inputTokens ?? 0,
    output_tokens: u?.outputTokens ?? 0,
    cache_read_tokens: u?.cacheReadInputTokens ?? u?.cachedInputTokens ?? 0,
    cache_write_tokens: u?.cacheCreationInputTokens ?? 0,
    reasoning_tokens: u?.reasoningTokens ?? 0,
  }
}

export function recordAiSdkCall(input: RecordAiSdkCallInput): void {
  const obsUsage = normalizeUsage(input.usage)
  const obsProvider = (resolveProvider(input.model_id) ?? 'unknown') as ProviderName
  const obsDb = getStorageClient()

  void (async () => {
    try {
      const costResult = await computeCost(
        obsProvider,
        input.model_id,
        obsUsage,
        input.started_at,
        obsDb,
      ).catch(() => null)

      await persistObservation(
        {
          provider: obsProvider,
          model: input.model_id,
          prompt_text: null,
          system_prompt: null,
          parameters: input.parameters ?? { model: input.model_id },
          conversation_id: input.conversation_id,
          conversation_name: input.conversation_name ?? null,
          prompt_id: input.prompt_id,
          parent_prompt_id: input.parent_prompt_id,
          user_id: input.user_id,
          pipeline_stage: input.pipeline_stage,
        },
        {
          response_text: null,
          usage: obsUsage,
          status: input.status,
          error_code: input.error_code ?? undefined,
          started_at: input.started_at,
          finished_at: input.finished_at,
        },
        costResult,
        obsDb,
      )
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error('[observability] recordAiSdkCall failed:', err)
    }
  })()
}
