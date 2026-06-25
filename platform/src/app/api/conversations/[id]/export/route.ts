export const runtime = 'nodejs'

import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { getConversation } from '@/lib/conversations'
import { loadConversationMessagesV2 } from '@/lib/persistence/conversation_writer'
import { res } from '@/lib/errors'
import type { UIMessage } from 'ai'

const VALID_FORMATS = ['md', 'json', 'pdf'] as const
type ExportFormat = (typeof VALID_FORMATS)[number]

async function resolveAccess(userId: string): Promise<boolean> {
  const result = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id=$1',
    [userId]
  )
  return result.rows[0]?.role === 'super_admin'
}

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
      timestamp: new Date().toISOString(),
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
    const isSuperAdmin = await resolveAccess(user.uid)
    const conv = await getConversation({ id, userId: user.uid, isSuperAdmin })
    // 403: conversation exists but belongs to another user (information-hiding: 404 used for not-found)
    if (!conv) return res.notFound('conversation')

    const messages = await loadConversationMessagesV2(id)

    if (format === 'md') {
      const body = toMarkdown(id, messages)
      return new Response(body, {
        headers: {
          'Content-Type': 'text/markdown; charset=utf-8',
          'Content-Disposition': `attachment; filename="conversation-${id}.md"`,
        },
      })
    }

    if (format === 'json') {
      const body = toJson(id, messages)
      return new Response(body, {
        headers: {
          'Content-Type': 'application/json',
          'Content-Disposition': `attachment; filename="conversation-${id}.json"`,
        },
      })
    }

    // PDF: requires a Node.js server environment with a PDF library installed.
    // Returns 501 if PDF generation is unavailable in this deployment.
    try {
      // Attempt dynamic import of html-pdf-node (optional dependency)
      // @ts-expect-error — html-pdf-node is optional; not in node_modules in all deployments
      const { default: pdf } = await import(/* webpackIgnore: true */ 'html-pdf-node') as { default: { generatePdf: (file: { content: string }, opts: Record<string, unknown>) => Promise<Buffer> } }
      const mdBody = toMarkdown(id, messages)
      const html = `<html><body style="font-family:sans-serif;padding:2em;max-width:800px"><pre style="white-space:pre-wrap">${mdBody.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre></body></html>`
      const buffer = await pdf.generatePdf({ content: html }, { format: 'A4' })
      return new Response(new Uint8Array(buffer), {
        headers: {
          'Content-Type': 'application/pdf',
          'Content-Disposition': `attachment; filename="conversation-${id}.pdf"`,
        },
      })
    } catch {
      return Response.json(
        { error: 'PDF export requires a Node.js runtime — use the MD export instead' },
        { status: 501 }
      )
    }
  } catch {
    return res.dbError()
  }
}
