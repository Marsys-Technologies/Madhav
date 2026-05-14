/**
 * conversations/title.ts — generates a concise chat title from the first user
 * message. Extracted out of the consume route so the route makes zero direct
 * LLM calls (the planner + synthesis are the only LLM stages on the request
 * path; the title is a side-effect that fires after the response is sent).
 */

import { runAdapter } from '@/lib/adapters'
import type { UIMessage } from 'ai'
import { TITLE_MODEL_ID } from '@/lib/models/registry'
import { writeLlmCallLog, resolveProvider } from '@/lib/db/monitoring-write'
import { computeCostUsd, getModelPricingSync } from '@/lib/llm/pricing'
import { persistObservation, computeCost } from '@/lib/llm/observability'
import { getStorageClient } from '@/lib/storage'
import type { ProviderName, TokenUsage } from '@/lib/llm/observability/types'

function fallbackTitle(text: string): string {
  const firstLine = text.split('\n')[0].trim()
  if (firstLine.length <= 60) return firstLine
  const slice = firstLine.slice(0, 60)
  const lastSpace = slice.lastIndexOf(' ')
  return (lastSpace > 20 ? slice.slice(0, lastSpace) : slice) + '…'
}

export async function generateConversationTitle(
  messages: UIMessage[],
  monCtx?: { queryId?: string; conversationId?: string | null; userId?: string },
): Promise<string | null> {
  const firstUser = messages.find(m => m.role === 'user')
  if (!firstUser) return null
  const text = firstUser.parts
    .filter(p => p.type === 'text')
    .map(p => (p as { text: string }).text)
    .join(' ')
    .trim()
  if (!text) return null

  const start = Date.now()
  let usage: { inputTokens?: number; outputTokens?: number } | undefined
  let errorCode: string | null = null
  try {
    const interaction = await runAdapter({
      callType: 'worker',
      modelOverride: { modelId: TITLE_MODEL_ID },
      systemPrompt: 'Summarize the user question as a concise 3-6 word chat title. No quotes, no trailing punctuation, Title Case.',
      messages: [{ role: 'user', content: text.slice(0, 500) }],
      maxOutputTokens: 40,
    })
    usage = { inputTokens: interaction.usage.inputTokens, outputTokens: interaction.usage.outputTokens }
    const cleaned = (interaction.finalText ?? '').replace(/^["']|["']$/g, '').trim().slice(0, 80)
    return cleaned || fallbackTitle(text)
  } catch (err) {
    errorCode = err instanceof Error ? err.message : String(err)
    return fallbackTitle(text)
  } finally {
    if (monCtx?.queryId) {
      const latency_ms = Date.now() - start
      void writeLlmCallLog({
        query_id: monCtx.queryId,
        conversation_id: monCtx.conversationId ?? null,
        call_stage: 'title',
        model_id: TITLE_MODEL_ID,
        provider: resolveProvider(TITLE_MODEL_ID),
        input_tokens: usage?.inputTokens ?? null,
        output_tokens: usage?.outputTokens ?? null,
        reasoning_tokens: null,
        latency_ms,
        cost_usd: computeCostUsd(getModelPricingSync(TITLE_MODEL_ID), {
          input_tokens: usage?.inputTokens ?? null,
          output_tokens: usage?.outputTokens ?? null,
        }),
        fallback_used: false,
        error_code: errorCode,
        payload: null,
      })
      // OBS-S1: Observatory per-call telemetry (title stage)
      {
        const obsStartedAt = new Date(start)
        const obsFinishedAt = new Date(start + latency_ms)
        const obsUsage: TokenUsage = {
          input_tokens: usage?.inputTokens ?? 0,
          output_tokens: usage?.outputTokens ?? 0,
          cache_read_tokens: 0,
          cache_write_tokens: 0,
          reasoning_tokens: 0,
        }
        const obsProvider = (resolveProvider(TITLE_MODEL_ID) ?? 'unknown') as ProviderName
        const obsDb = getStorageClient()
        void (async () => {
          const costResult = await computeCost(obsProvider, TITLE_MODEL_ID, obsUsage, obsStartedAt, obsDb).catch(() => null)
          await persistObservation(
            {
              provider: obsProvider,
              model: TITLE_MODEL_ID,
              prompt_text: null,
              system_prompt: null,
              parameters: { model: TITLE_MODEL_ID },
              conversation_id: monCtx.conversationId ?? monCtx.queryId ?? 'unknown',
              conversation_name: null,
              prompt_id: `${monCtx.queryId}:title`,
              user_id: monCtx.userId ?? 'native',
              pipeline_stage: 'title',
            },
            {
              response_text: null,
              usage: obsUsage,
              status: errorCode ? 'error' : 'success',
              error_code: errorCode ?? undefined,
              started_at: obsStartedAt,
              finished_at: obsFinishedAt,
            },
            costResult,
            obsDb,
          )
        })()
      }
    }
  }
}
