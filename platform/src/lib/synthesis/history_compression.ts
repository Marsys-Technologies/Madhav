import 'server-only'
import type { ModelMessage } from 'ai'
import { streamAdapterRaw } from '@/lib/adapters'

const HAIKU_MODEL = 'claude-haiku-4-5-20251001'
const DEFAULT_TAIL_SIZE = 4     // keep last N user+assistant turn-pairs verbatim
const DEFAULT_TOKEN_BUDGET = 32_000

export type SummarizerFn = (messages: ModelMessage[]) => Promise<string>

// In-process cache: key = "{conversationId}:{tailStart}" — cleared on process restart.
const compressionCache = new Map<string, string>()

/**
 * Rough token estimate: 1 token ≈ 4 chars (ASCII text average).
 * Good enough for a soft budget gate; not a billing-accurate count.
 */
export function estimateTokens(messages: ModelMessage[]): number {
  let chars = 0
  for (const m of messages) {
    if (typeof m.content === 'string') {
      chars += m.content.length
    } else if (Array.isArray(m.content)) {
      for (const part of m.content as Array<{ text?: string }>) {
        if (typeof part.text === 'string') chars += part.text.length
      }
    }
  }
  return Math.ceil(chars / 4)
}

/**
 * Split conversation into head (to be compressed) and tail (kept verbatim).
 * tailSize is the number of turn-pairs to preserve (each pair = 1 user + 1 assistant).
 */
export function splitHistory(
  messages: ModelMessage[],
  tailSize: number,
): { head: ModelMessage[]; tail: ModelMessage[] } {
  const verbatimCount = tailSize * 2
  if (messages.length <= verbatimCount) {
    return { head: [], tail: messages }
  }
  return {
    head: messages.slice(0, -verbatimCount),
    tail: messages.slice(-verbatimCount),
  }
}

/** Cache key encodes both the conversation identity and where the verbatim tail begins. */
export function makeCacheKey(conversationId: string, tailStart: number): string {
  return `${conversationId}:${tailStart}`
}

async function defaultSummarizer(messages: ModelMessage[]): Promise<string> {
  const transcript = messages
    .map(m => {
      const role = m.role === 'user' ? 'User' : 'Assistant'
      const content =
        typeof m.content === 'string'
          ? m.content.slice(0, 800)
          : '[multipart content]'
      return `${role}: ${content}`
    })
    .join('\n\n')

  const { result } = streamAdapterRaw({
    callType: 'planner_fast',
    modelOverride: { modelId: HAIKU_MODEL },
    systemPrompt:
      'You are a conversation archivist. Summarize the following conversation turns concisely ' +
      '(≤300 words). Preserve every factual claim, astrological observation, and topic discussed.',
    messages: [{ role: 'user', content: transcript }],
    maxOutputTokens: 1024,
    disableSdkRetry: true,
  })

  return await result.text
}

export interface CompressionOptions {
  /** Number of recent turn-pairs (user+assistant) to keep verbatim. Default 4. */
  tailSize?: number
  /** Estimated-token budget above which compression fires. Default 32 000. */
  tokenBudget?: number
  /** Override the LLM summarizer — useful for tests. */
  summarizer?: SummarizerFn
}

/**
 * Compress conversation history using sliding-window summarization.
 *
 * - If estimated tokens ≤ tokenBudget: returns messages unchanged.
 * - Otherwise: summarizes the head turns via a Haiku call (cached by
 *   conversationId + tailStart index), prepends the summary as a synthetic
 *   user/assistant pair, and appends the verbatim tail.
 *
 * Called from route.ts when HISTORY_COMPRESSION_ENABLED=true.
 */
export async function compressHistory(
  messages: ModelMessage[],
  conversationId: string,
  opts?: CompressionOptions,
): Promise<ModelMessage[]> {
  const tailSize = opts?.tailSize ?? DEFAULT_TAIL_SIZE
  const tokenBudget = opts?.tokenBudget ?? DEFAULT_TOKEN_BUDGET
  const summarizer = opts?.summarizer ?? defaultSummarizer

  if (estimateTokens(messages) <= tokenBudget) return messages

  const { head, tail } = splitHistory(messages, tailSize)
  if (head.length === 0) return messages

  const tailStart = messages.length - tail.length
  const cacheKey = makeCacheKey(conversationId, tailStart)

  let summary = compressionCache.get(cacheKey)
  if (!summary) {
    summary = await summarizer(head)
    compressionCache.set(cacheKey, summary)
  }

  const summaryMessage: ModelMessage = {
    role: 'user',
    content: `[CONVERSATION SUMMARY — ${head.length} earlier turns compressed]\n\n${summary}`,
  }
  const assistantAck: ModelMessage = {
    role: 'assistant',
    content: 'I have the summary of our earlier conversation and will build on it.',
  }

  return [summaryMessage, assistantAck, ...tail]
}
