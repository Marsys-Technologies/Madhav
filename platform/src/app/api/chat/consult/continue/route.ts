import 'server-only'
import { createUIMessageStream, createUIMessageStreamResponse } from 'ai'
import { streamText } from 'ai'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { getConversation } from '@/lib/conversations'
import { loadConversationMessagesV2 } from '@/lib/persistence/conversation_writer'
import { res } from '@/lib/errors'
import { DEFAULT_STACK_ID } from '@/lib/models/registry'
import { getEffectiveModel } from '@/lib/models/runtime_config'
import { resolveModel } from '@/lib/models/resolver'
import type { ModelMessage } from 'ai'
import { configService } from '@/lib/config'
import { AiConsoleError } from '@/lib/ai-console/errors'
import { getConversationSelection } from '@/lib/ai-console/repository'
import { prepareByokTurn } from '@/lib/pariprashna/pipeline/byok_preflight'

export const maxDuration = 120

const CONTINUATION_INSTRUCTION =
  'Continue exactly from where the previous response was cut off. Do not repeat any content. Begin mid-sentence if needed.'

/**
 * POST /api/chat/consult/continue
 *
 * Thin continuation route. Loads the conversation, prepends a continuation
 * system instruction, and delegates to the synthesis model via streamText.
 * Returns the same createUIMessageStreamResponse format as the main route.
 *
 * Body: { conversation_id: string, last_message_id: string }
 */
export async function POST(request: Request) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  let body: { conversation_id?: string; last_message_id?: string }
  try {
    body = await request.json()
  } catch {
    return res.badRequest('invalid body')
  }

  const { conversation_id, last_message_id } = body
  if (!conversation_id || !last_message_id) {
    return res.badRequest('conversation_id and last_message_id are required')
  }

  // Resolve access: owner or super_admin.
  let isSuperAdmin = false
  try {
    const result = await query<{ role: string; status: string }>(
      'SELECT role,status FROM profiles WHERE id=$1',
      [user.uid],
    )
    if (configService.getFlag('AI_CONSOLE_BYOK') && result.rows[0]?.status !== 'active') {
      return Response.json(new AiConsoleError('AI_PERMISSION_DENIED').toJSON(), { status: 403 })
    }
    isSuperAdmin = result.rows[0]?.role === 'super_admin'
  } catch {
    return res.dbError()
  }

  const conv = await getConversation({
    id: conversation_id,
    userId: user.uid,
    isSuperAdmin,
  }).catch(() => null)

  if (!conv) return res.notFound('conversation')

  // Load conversation messages for context.
  let uiMessages
  try {
    uiMessages = await loadConversationMessagesV2(conversation_id)
  } catch {
    return res.dbError()
  }

  if (configService.getFlag('AI_CONSOLE_BYOK')) {
    try {
      const selection = await getConversationSelection(user.uid, conversation_id)
      const turnId = crypto.randomUUID()
      const runtime = await prepareByokTurn({
        userId: user.uid,
        role: isSuperAdmin ? 'super_admin' : 'guest',
        chartId: conv.chart_id,
        conversationId: conversation_id,
        isFirstTurn: false,
        turnId,
        requestedSelection: selection,
        questionChars: CONTINUATION_INSTRUCTION.length,
        source: 'consult',
      })
      const history = uiMessages.map(message => ({
        role: message.role as 'user' | 'assistant',
        content: message.parts
          .filter((part): part is { type: 'text'; text: string } => part.type === 'text')
          .map(part => part.text).join(''),
      }))
      const uiStream = createUIMessageStream({
        execute: async ({ writer }) => {
          const id = crypto.randomUUID()
          writer.write({ type: 'start', messageId: crypto.randomUUID() } as never)
          writer.write({ type: 'text-start', id } as never)
          const reader = runtime.executors.synthesizer.stream({
            systemPrompt: CONTINUATION_INSTRUCTION,
            messages: history,
            abortSignal: request.signal,
          }).getReader()
          try {
            while (true) {
              const next = await reader.read()
              if (next.done) break
              if (next.value.type === 'text_delta') {
                writer.write({ type: 'text-delta', id, delta: next.value.text } as never)
              }
            }
            writer.write({ type: 'text-end', id } as never)
            writer.write({ type: 'finish', finishReason: 'stop' } as never)
          } catch (error) {
            const safe = error instanceof AiConsoleError
              ? error : new AiConsoleError('AI_EXECUTION_FAILED', 'synthesizer')
            writer.write({ type: 'error', errorText: safe.message } as never)
          } finally {
            runtime.releaseAdmission()
            reader.releaseLock()
          }
        },
      })
      return createUIMessageStreamResponse({ stream: uiStream })
    } catch (error) {
      const safe = error instanceof AiConsoleError ? error : new AiConsoleError('AI_EXECUTION_FAILED')
      return Response.json(safe.toJSON(), { status: safe.code === 'AI_RATE_LIMITED' ? 429 : 400 })
    }
  }

  // Resolve synthesis model — use stack stored in conversation metadata if available;
  // fall back to DEFAULT_STACK_ID.
  const modelId = await getEffectiveModel(DEFAULT_STACK_ID, 'synthesis', 'primary', request)
  const model = resolveModel(modelId)

  // Convert UIMessage history to ModelMessage format for streamText.
  const history: ModelMessage[] = uiMessages.map(m => ({
    role: m.role as 'user' | 'assistant',
    content: m.parts
      .filter((p): p is { type: 'text'; text: string } => p.type === 'text')
      .map(p => p.text)
      .join(''),
  }))

  const abortSignal = request.signal

  const stream = streamText({
    model,
    system: CONTINUATION_INSTRUCTION,
    messages: history,
    abortSignal,
  })

  const uiStream = createUIMessageStream({
    execute: async ({ writer }) => {
      writer.merge(stream.toUIMessageStream())
    },
  })

  return createUIMessageStreamResponse({ stream: uiStream })
}
