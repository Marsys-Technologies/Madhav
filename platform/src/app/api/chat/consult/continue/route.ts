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
import { BYOK_MAX_OUTPUT_TOKENS, validateByokUiMessages } from '@/lib/limits/byok_admission'
import type { RoleExecutionEvent } from '@/lib/ai-console/execution'

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
      uiMessages = await validateByokUiMessages(uiMessages)
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
      try {
      const history = uiMessages.map(message => ({
        role: message.role as 'user' | 'assistant',
        content: message.parts
          .filter((part): part is { type: 'text'; text: string } => part.type === 'text')
          .map(part => part.text).join(''),
      }))
      const turnAbort = new AbortController()
      const turnSignal = AbortSignal.any([request.signal, turnAbort.signal])
      let execution: Promise<void> | undefined
      const uiStream = createUIMessageStream({
        onError: () => new AiConsoleError('AI_EXECUTION_FAILED').message,
        execute: ({ writer }) => {
          execution = (async () => {
          let reader: ReadableStreamDefaultReader<RoleExecutionEvent> | undefined
          let completed = false
          let abortCleanup: Promise<void> | undefined
          let cancelOnAbort: (() => void) | undefined
          try {
            const id = crypto.randomUUID()
            writer.write({ type: 'start', messageId: crypto.randomUUID() } as never)
            writer.write({ type: 'text-start', id } as never)
            reader = runtime.executors.synthesizer.stream({
              systemPrompt: CONTINUATION_INSTRUCTION,
              messages: history,
              abortSignal: turnSignal,
              maxOutputTokens: BYOK_MAX_OUTPUT_TOKENS,
            }).getReader()
            cancelOnAbort = () => {
              abortCleanup ??= reader!.cancel().catch(() => undefined)
            }
            turnSignal.addEventListener('abort', cancelOnAbort, { once: true })
            while (true) {
              const next = await reader.read()
              if (next.done) { completed = true; break }
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
            if (cancelOnAbort) turnSignal.removeEventListener('abort', cancelOnAbort)
            if (reader && !completed) abortCleanup ??= reader.cancel().catch(() => undefined)
            await abortCleanup
            runtime.releaseAdmission()
            reader?.releaseLock()
          }
          })()
          return execution
        },
      })
      const response = createUIMessageStreamResponse({ stream: uiStream })
      if (!response.body) return response
      const wireReader = response.body.getReader()
      const guardedBody = new ReadableStream<Uint8Array>({
        async pull(controller) {
          try {
            const next = await wireReader.read()
            if (next.done) controller.close()
            else controller.enqueue(next.value)
          } catch (error) { controller.error(error) }
        },
        async cancel(reason) {
          turnAbort.abort()
          await wireReader.cancel(reason).catch(() => undefined)
          await execution?.catch(() => undefined)
        },
      })
      return new Response(guardedBody, { status: response.status, statusText: response.statusText,
        headers: response.headers })
      } catch (error) { runtime.releaseAdmission(); throw error }
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
