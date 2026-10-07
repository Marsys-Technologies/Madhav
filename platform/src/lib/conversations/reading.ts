import 'server-only'
import type { UIMessage } from 'ai'
import { query } from '@/lib/db/client'
import { getConversation } from '@/lib/conversations'
import { consultationAccess, uuidLike } from './consultation'
import { CitationBodySchema } from '@/lib/pariprashna/store/schema'
import { loadHistoricalConversationMessages } from './historicalReading'

/** Ownership of a private reading and current chart entitlement are separate checks. */
export async function ownedReading(id: string, userId: string) {
  if (!uuidLike.test(id)) return null
  const conversation = await getConversation({ id, userId, isSuperAdmin: false })
  if (!conversation || conversation.module !== 'consume') return null
  const { rows: profiles } = await query<{ status: string }>('SELECT status FROM profiles WHERE id=$1', [userId])
  if (profiles[0]?.status !== 'active') return null
  const access = await consultationAccess(conversation.chart_id)
  return access?.user.uid === userId ? conversation : null
}

/** One reader transcript for canonical and legacy turns. No provider/tool metadata. */
export async function readingMessages(conversationId: string, messageId?: string | null, includeReasoning = false): Promise<UIMessage[]> {
  const transcript = await loadHistoricalConversationMessages(conversationId)
  let selected = transcript
  if (messageId) {
    const index = transcript.findIndex(m => m.id === messageId && m.role === 'assistant')
    if (index < 0) return []
    const question = transcript.slice(0, index).findLast(m => m.role === 'user')
    selected = [...(question ? [question] : []), transcript[index]]
  }
  const citations = new Map<string, string[]>()
  if (selected.length) {
    const { rows } = await query<{ message_id: string; body: unknown }>(`SELECT message_id, body FROM message_parts
      WHERE message_id=ANY($1::uuid[]) AND kind='citation' ORDER BY message_id,seq`, [selected.map(m => m.id)])
    for (const row of rows) {
      const parsed = CitationBodySchema.safeParse(row.body)
      if (!parsed.success) continue
      const c = parsed.data
      const list = citations.get(row.message_id) ?? []
      list.push(`${c.index}. ${c.reader_label ?? c.signal_id} (${c.layer}) — ${c.snippet}`)
      citations.set(row.message_id, list)
    }
  }
  const reasoning = new Map<string, string>()
  if (includeReasoning && selected.length) {
    const { rows } = await query<{ message_id: string; text: string }>(`SELECT message_id, body->>'text' AS text FROM message_parts
      WHERE message_id=ANY($1::uuid[]) AND kind='reasoning' ORDER BY message_id, seq`, [selected.map(m => m.id)])
    for (const row of rows) if (typeof row.text === 'string') reasoning.set(row.message_id, (reasoning.get(row.message_id) ?? '') + row.text)
    const legacy = await query<{ id: string; parts_json: unknown }>(`SELECT id, parts_json FROM conversation_messages WHERE id=ANY($1::uuid[])`, [selected.map(m => m.id)])
    for (const row of legacy.rows) {
      if (reasoning.has(row.id) || !Array.isArray(row.parts_json)) continue
      const text = row.parts_json.filter(p => p?.type === 'reasoning' && typeof p.text === 'string').map(p => p.text).join('')
      if (text) reasoning.set(row.id, text)
    }
  }
  return selected.map(m => ({ id: m.id, role: m.role, parts: [{ type: 'text' as const, text: m.text + (citations.has(m.id) ? '\n\n## Sources\n\n' + citations.get(m.id)!.join('\n\n') : '') }, ...(reasoning.has(m.id) && m.role === 'assistant' ? [{ type: 'reasoning' as const, text: reasoning.get(m.id)! }] : [])],
    metadata: { createdAt: m.createdAt } }))
}

/** Saved context is authoritative; the current request contributes only its last user question. */
export async function readingContext(conversationId: string, requestMessages: UIMessage[]) {
  const current = requestMessages.filter(m => m.role === 'user').at(-1)
  if (!current) throw new Error('A user question is required')
  const prior = await readingMessages(conversationId)
  // Match the existing model-history bound, measured in reader text rather than tool payloads.
  const tail: UIMessage[] = []
  let chars = 0
  for (const message of prior.slice(-40).reverse()) {
    const text = message.parts.filter(p => p.type === 'text').map(p => p.text).join('')
    if (chars + text.length > 60_000) break
    chars += text.length
    tail.unshift(message)
  }
  return [...tail, current]
}

export async function answerBelongsToReading(conversationId: string, messageId: string) {
  const { rows } = await query(`SELECT id FROM conversation_messages WHERE id=$1 AND conversation_id=$2 AND role='assistant'`, [messageId, conversationId])
  return rows.length === 1
}
