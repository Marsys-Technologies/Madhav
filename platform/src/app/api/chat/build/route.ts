import { stepCountIs, createIdGenerator, convertToModelMessages } from 'ai'
import { streamBuildRaw } from '@/lib/adapters'
import { anthropic } from '@ai-sdk/anthropic'
import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { buildTools } from '@/lib/claude/build-tools'
import { buildSystemPrompt } from '@/lib/claude/system-prompts'
import type { ModelMessage, UIMessage } from 'ai'
import { insertConversationWithId, replaceConversationMessages, getConversation } from '@/lib/conversations'
import { res } from '@/lib/errors'

export const maxDuration = 120

async function requireSuperAdmin() {
  const user = await getServerUser()
  if (!user) return null
  const result = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id=$1',
    [user.uid]
  )
  if (result.rows[0]?.role !== 'super_admin') return null
  return user
}

export async function POST(request: Request) {
  const user = await requireSuperAdmin()
  if (!user) return res.forbidden()

  let body: { chartId?: string; messages?: UIMessage[]; conversationId?: string }
  try {
    body = await request.json()
  } catch {
    return res.badRequest('Invalid JSON body')
  }

  const { chartId, messages } = body
  if (!chartId || !messages) {
    return res.badRequest('chartId and messages are required')
  }

  let chartResult: Awaited<ReturnType<typeof query<{ id: string; name: string; birth_date: string; birth_time: string; birth_place: string }>>>
  let layersResult: Awaited<ReturnType<typeof query<{ layer: string; sublayer: string; status: string }>>>
  try {
    ;[chartResult, layersResult] = await Promise.all([
      query<{ id: string; name: string; birth_date: string; birth_time: string; birth_place: string }>(
        'SELECT id, name, birth_date, birth_time, birth_place FROM charts WHERE id=$1',
        [chartId]
      ),
      query<{ layer: string; sublayer: string; status: string }>(
        'SELECT layer, sublayer, status FROM pyramid_layers WHERE chart_id=$1',
        [chartId]
      ),
    ])
  } catch {
    return res.dbError()
  }

  if (!chartResult.rows[0]) return res.notFound('chart')
  const chart = chartResult.rows[0]
  const layers = layersResult.rows

  const systemPrompt = buildSystemPrompt(chart, layers)

  let conversationId = body.conversationId
  let isFirstTurn = false
  let pendingConversationInsert: Promise<void> | null = null

  if (conversationId) {
    let existing: Awaited<ReturnType<typeof getConversation>>
    try {
      existing = await getConversation({ id: conversationId, userId: user.uid, isSuperAdmin: true })
    } catch {
      return res.dbError()
    }
    if (!existing || existing.chart_id !== chartId) {
      return res.notFound('conversation')
    }
  } else {
    conversationId = crypto.randomUUID()
    isFirstTurn = true
    pendingConversationInsert = insertConversationWithId({
      id: conversationId,
      chartId,
      userId: user.uid,
      module: 'build',
    })
  }

  const finalConversationId = conversationId

  const result = streamBuildRaw({
    model: anthropic('claude-sonnet-4-6'),
    system: systemPrompt,
    messages: await convertToModelMessages(messages),
    tools: buildTools,
    stopWhen: stepCountIs(5),
    maxOutputTokens: 16384,
    providerOptions: {
      anthropic: { cacheControl: { type: 'ephemeral' } },
    },
  })

  result.consumeStream()

  return result.toUIMessageStreamResponse({
    originalMessages: body.messages ?? [],
    generateMessageId: createIdGenerator({ prefix: 'msg', size: 16 }),
    messageMetadata: ({ part }) => {
      if (part.type === 'start' && isFirstTurn) {
        return { conversationId: finalConversationId }
      }
    },
    onError: error => {
      if (error instanceof Error) return error.message
      return 'Something went wrong generating the build response.'
    },
    onFinish: async ({ messages: finalMessages }) => {
      try {
        if (pendingConversationInsert) await pendingConversationInsert
        await replaceConversationMessages({
          conversationId: finalConversationId,
          messages: finalMessages as UIMessage[],
        })
      } catch (err) {
        console.error('[build] persistence failed', err)
      }
    },
  })
}
