import type { ModelMessage } from 'ai'
import type { ChatMessage, ChatRequest } from './types'

/**
 * Converts AI-SDK ModelMessage history + current user turn into the flat
 * ChatMessage[] expected by CapabilityAdapter.chat().
 *
 * Fixes:
 *   Bug A — appends currentUserTurn so the array is never empty on first query.
 *   Bug B — non-text content parts are dropped rather than mapped to '' (empty
 *            string blocks cause Anthropic HTTP 400). Falls back to '[tool result]'
 *            when all parts are non-text so content is never an empty string.
 */
export function buildAdapterMessages(
  history: ModelMessage[],
  currentUserTurn: string,
): ChatMessage[] {
  const messages: ChatMessage[] = history.map(m => ({
    role: m.role as ChatMessage['role'],
    content: Array.isArray(m.content)
      ? (() => {
          const text = m.content
            .map((p: unknown) => {
              const part = p as { type?: string; text?: string }
              return part.type === 'text' ? (part.text ?? '') : ''
            })
            .filter(Boolean)
            .join('')
          return text || '[tool result]'
        })()
      : ((m.content as string) ?? ''),
  }))

  // Bug A fix: append the current user turn (was missing entirely)
  messages.push({ role: 'user', content: currentUserTurn })

  return messages
}

/**
 * Builds the ChatRequest passed to CapabilityAdapter.chat().
 *
 * Bug C fix: accepts optional system prompt (synthesis content + RAG bundle)
 * and attaches it to the request when present.
 */
export function buildAdapterChatRequest(
  messages: ChatMessage[],
  model: string,
  system: string | undefined,
): ChatRequest {
  const req: ChatRequest = { messages, model }
  if (system) req.system = system
  return req
}
