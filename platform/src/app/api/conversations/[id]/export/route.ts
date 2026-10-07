export const runtime = 'nodejs'

import { getServerUser } from '@/lib/firebase/server'
import { ownedReading, readingMessages } from '@/lib/conversations/reading'
import { uuidLike } from '@/lib/conversations/consultation'
import { res } from '@/lib/errors'
import type { UIMessage } from 'ai'
import { savedReadingTimestamp } from '@/lib/conversations/readingTimestamp'

const VALID_FORMATS = ['md', 'json', 'pdf'] as const
type ExportFormat = (typeof VALID_FORMATS)[number]

function extractText(msg: UIMessage): string {
  return (msg.parts ?? [])
    .filter((p): p is { type: 'text'; text: string } => p.type === 'text' && typeof (p as { text?: unknown }).text === 'string')
    .map(p => p.text)
    .join('')
}

function toMarkdown(id: string, messages: UIMessage[]): string {
  const lines: string[] = [`# Conversation ${id}`, '']
  for (const msg of messages) {
    const text = extractText(msg)
    if (!text) continue
    const savedAt = savedReadingTimestamp(msg.metadata)
    if (savedAt) lines.push(`**Saved:** ${savedAt}`, '')
    if (msg.role === 'user') {
      lines.push(`**User:** ${text}`)
    } else {
      lines.push(text)
    }
    lines.push('---')
  }
  return lines.join('\n')
}

function toJson(id: string, messages: UIMessage[]): string {
  const output = {
    id,
    messages: messages.map(msg => ({
      role: msg.role,
      content: extractText(msg),
      timestamp: savedReadingTimestamp(msg.metadata),
    })),
  }
  return JSON.stringify(output, null, 2)
}

export async function GET(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  const url = new URL(req.url)
  const format = url.searchParams.get('format') as ExportFormat | null

  if (!format || !VALID_FORMATS.includes(format)) {
    return Response.json({ error: 'format must be one of: pdf, md, json' }, { status: 400 })
  }

  try {
    const conv = await ownedReading(id, user.uid)
    if (!conv) return res.notFound('conversation')

    const messageId = url.searchParams.get('messageId')
    if (messageId && !uuidLike.test(messageId)) return res.badRequest('Valid answer required')
    const messages = await readingMessages(id, messageId)
    if (messageId && messages.length === 0) return res.notFound('answer')

    if (format === 'md') {
      const body = toMarkdown(id, messages)
      return new Response(body, {
        headers: {
          'Content-Type': 'text/markdown; charset=utf-8',
          'Cache-Control': 'private, no-store',
          'Content-Disposition': `attachment; filename="conversation-${id}.md"`,
        },
      })
    }

    if (format === 'json') {
      const body = toJson(id, messages)
      return new Response(body, {
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'private, no-store',
          'Content-Disposition': `attachment; filename="conversation-${id}.json"`,
        },
      })
    }

    const target = new URL(`/clients/${conv.chart_id}/pariprashna/print`, req.url)
    target.searchParams.set('conversationId', id)
    if (messageId) target.searchParams.set('messageId', messageId)
    return new Response(null, { status: 307, headers: { Location: target.toString(), 'Cache-Control': 'private, no-store' } })
  } catch {
    return res.dbError()
  }
}
