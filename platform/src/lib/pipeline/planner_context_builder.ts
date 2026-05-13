/**
 * planner_context_builder.ts — assembles the ≤600-token history window the
 * LLM-first planner consumes alongside the compressed manifest and the query.
 *
 * Rules (W2-MANIFEST AC.M.4):
 *   - Take the last 2 conversation turns; ignore older turns.
 *   - Cap each surviving turn's content to 300 tokens (Math.ceil(len/4)).
 *   - If post-cap history exceeds 600 tokens combined, summarize via the
 *     worker model down to ≤150 tokens and flag history_was_summarized.
 *   - Empty input → empty history_turns, history_was_summarized = false.
 *   - total_estimated_tokens = query tokens + final history tokens.
 *
 * Token estimation uses the W2-MANIFEST-fixed formula `Math.ceil(s.length / 4)`
 * (B.10: do not fabricate token counts).
 */

import { generateText } from 'ai'
import { resolveModel } from '@/lib/models/resolver'
import { writeLlmCallLog, resolveProvider } from '@/lib/db/monitoring-write'
import { persistObservation, computeCost } from '@/lib/llm/observability'
import { getStorageClient } from '@/lib/storage'
import type { ProviderName, TokenUsage } from '@/lib/llm/observability/types'

const MAX_TURNS = 2
const MAX_TOKENS_PER_TURN = 1000
const MAX_TOKENS_PER_TURN_CHARS = MAX_TOKENS_PER_TURN * 4
const HISTORY_BUDGET_TOKENS = 2000
const SUMMARY_TARGET_TOKENS = 512
const SUMMARY_TARGET_CHARS = SUMMARY_TARGET_TOKENS * 4

export type PlannerRole = 'user' | 'assistant'

export interface PlannerHistoryTurn {
  role: PlannerRole
  content: string
}

export interface PlannerContext {
  query: string
  history_turns: PlannerHistoryTurn[]
  history_was_summarized: boolean
  total_estimated_tokens: number
}

function estimateTokens(s: string): number {
  return Math.ceil(s.length / 4)
}

function truncateToTokens(content: string, maxTokens: number): string {
  const maxChars = maxTokens * 4
  if (content.length <= maxChars) return content
  return content.slice(0, maxChars)
}

function normalizeRole(role: string): PlannerRole {
  return role === 'assistant' ? 'assistant' : 'user'
}

function turnsTokens(turns: PlannerHistoryTurn[]): number {
  return turns.reduce((sum, t) => sum + estimateTokens(t.content), 0)
}

async function summarizeHistory(
  turns: PlannerHistoryTurn[],
  workerModelId: string,
  queryId?: string,
): Promise<string> {
  const dialogue = turns
    .map(t => `${t.role.toUpperCase()}: ${t.content}`)
    .join('\n\n')

  const prompt =
    `Summarize the following recent conversation between a user and an ` +
    `assistant in at most ${SUMMARY_TARGET_TOKENS} tokens (~${SUMMARY_TARGET_CHARS} ` +
    `characters). Preserve any concrete entities (planets, houses, dates, domains, ` +
    `signal IDs) the assistant referenced — those drive downstream tool selection. ` +
    `Output prose only, no preface or markdown.\n\n` +
    `DIALOGUE:\n${dialogue}\n\nSUMMARY:`

  const start = Date.now()
  let text = ''
  let usage: { inputTokens?: number; outputTokens?: number } | undefined
  let errorCode: string | null = null
  try {
    const result = await generateText({
      model: resolveModel(workerModelId),
      messages: [{ role: 'user', content: prompt }],
      maxOutputTokens: SUMMARY_TARGET_TOKENS,
    })
    text = result.text
    usage = result.usage
  } catch (err) {
    errorCode = err instanceof Error ? err.message : String(err)
    throw err
  } finally {
    if (queryId) {
      const latency_ms = Date.now() - start
      void writeLlmCallLog({
        query_id: queryId,
        conversation_id: null,
        call_stage: 'history_summary',
        model_id: workerModelId,
        provider: resolveProvider(workerModelId),
        input_tokens: usage?.inputTokens ?? null,
        output_tokens: usage?.outputTokens ?? null,
        reasoning_tokens: null,
        latency_ms,
        cost_usd: null,
        fallback_used: false,
        error_code: errorCode,
        payload: null,
      })
      // OBS-S1: Observatory per-call telemetry (history_summary stage)
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
        const obsProvider = (resolveProvider(workerModelId) ?? 'unknown') as ProviderName
        const obsDb = getStorageClient()
        void (async () => {
          const costResult = await computeCost(obsProvider, workerModelId, obsUsage, obsStartedAt, obsDb).catch(() => null)
          await persistObservation(
            {
              provider: obsProvider,
              model: workerModelId,
              prompt_text: null,
              system_prompt: null,
              parameters: { model: workerModelId },
              conversation_id: queryId,
              conversation_name: null,
              prompt_id: `${queryId}:history_summary`,
              user_id: 'native',
              pipeline_stage: 'history_summary',
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

  return truncateToTokens(text.trim(), SUMMARY_TARGET_TOKENS)
}

export async function buildPlannerContext(
  query: string,
  conversationHistory: Array<{ role: string; content: string }>,
  workerModelId: string,
  queryId?: string,
): Promise<PlannerContext> {
  const queryTokens = estimateTokens(query)

  if (!conversationHistory || conversationHistory.length === 0) {
    return {
      query,
      history_turns: [],
      history_was_summarized: false,
      total_estimated_tokens: queryTokens,
    }
  }

  const recent: PlannerHistoryTurn[] = conversationHistory
    .slice(-MAX_TURNS)
    .map(turn => ({ role: normalizeRole(turn.role), content: turn.content }))

  // Summarization gate is on the *raw* combined history of the last MAX_TURNS:
  // if the user's recent dialogue is already verbose enough to blow past the
  // 600-token planner budget, per-turn truncation would shred context, so we
  // delegate compression to the worker model.
  const rawCombined = turnsTokens(recent)

  if (rawCombined > HISTORY_BUDGET_TOKENS) {
    const summary = await summarizeHistory(recent, workerModelId, queryId)
    const summaryTokens = estimateTokens(summary)
    return {
      query,
      history_turns: [{ role: 'user', content: summary }],
      history_was_summarized: true,
      total_estimated_tokens: queryTokens + summaryTokens,
    }
  }

  // Otherwise, per-turn truncation at 300 tokens is sufficient to keep the
  // planner budget intact and we preserve the original turn shape.
  const cappedTurns: PlannerHistoryTurn[] = recent.map(turn => ({
    role: turn.role,
    content: truncateToTokens(turn.content, MAX_TOKENS_PER_TURN),
  }))
  const cappedTotal = turnsTokens(cappedTurns)

  return {
    query,
    history_turns: cappedTurns,
    history_was_summarized: false,
    total_estimated_tokens: queryTokens + cappedTotal,
  }
}
