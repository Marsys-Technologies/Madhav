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
    const result = await query<{ role: string }>(
      'SELECT role FROM profiles WHERE id=$1',
      [user.uid],
    )
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
