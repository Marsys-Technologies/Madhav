import 'server-only'
import type { UIMessage } from 'ai'
import { query } from '@/lib/db/client'
import type { ConversationModule } from '@/lib/db/types'

export interface ConversationSummary {
  id: string
  chart_id: string
  user_id: string
  module: ConversationModule
  title: string | null
  created_at: string
  updated_at: string | null
  archived_at: string | null
}

export async function listConversations(params: {
  chartId: string
  userId: string
  module: ConversationModule
  includeArchived?: boolean
}): Promise<ConversationSummary[]> {
  const { includeArchived = false } = params
  const archiveClause = includeArchived ? '' : 'AND archived_at IS NULL'
  const { rows } = await query(
    `SELECT id, chart_id, user_id, module, title, created_at, updated_at, archived_at
     FROM conversations
     WHERE chart_id=$1 AND user_id=$2 AND module=$3 ${archiveClause}
     ORDER BY COALESCE(updated_at, created_at) DESC
     LIMIT 100`,
    [params.chartId, params.userId, params.module]
  )
  return rows.map(row => ({
    ...(row as ConversationSummary),
    module: row.module as ConversationModule,
    updated_at: (row.updated_at ?? row.created_at) as string,
  }))
}

export async function createConversation(params: {
  chartId: string
  userId: string
  module: ConversationModule
}): Promise<ConversationSummary> {
  const { rows } = await query(
    'INSERT INTO conversations (chart_id, user_id, module, title) VALUES ($1,$2,$3,NULL) RETURNING id, chart_id, user_id, module, title, created_at',
    [params.chartId, params.userId, params.module]
  )
  const data = rows[0]
  if (!data) throw new Error('Failed to create conversation')
  return { ...(data as ConversationSummary), module: data.module as ConversationModule, updated_at: data.created_at as string }
}

export async function insertConversationWithId(params: {
  id: string
  chartId: string
  userId: string
  module: ConversationModule
}): Promise<void> {
  await query(
    'INSERT INTO conversations (id, chart_id, user_id, module, title) VALUES ($1,$2,$3,$4,NULL) ON CONFLICT (id) DO NOTHING',
    [params.id, params.chartId, params.userId, params.module]
  )
}

export async function getConversation(params: {
  id: string
  userId: string
  isSuperAdmin: boolean
}): Promise<ConversationSummary | null> {
  const { rows } = await query(
    'SELECT id, chart_id, user_id, module, title, created_at, updated_at, archived_at FROM conversations WHERE id=$1',
    [params.id]
  )
  const data = rows[0] ?? null
  if (!data) return null
  if (!params.isSuperAdmin && data.user_id !== params.userId) return null
  return {
    ...(data as ConversationSummary),
    module: data.module as ConversationModule,
    updated_at: (data.updated_at ?? data.created_at) as string,
    archived_at: data.archived_at ?? null,
  }
}

export async function loadConversationMessages(conversationId: string): Promise<UIMessage[]> {
  const { rows } = await query(
    'SELECT id, role, content, tool_calls, created_at FROM messages WHERE conversation_id=$1 ORDER BY created_at ASC',
    [conversationId]
  )
  const out: UIMessage[] = []
  for (const row of rows) {
    if (row.role === 'user' || row.role === 'assistant') {
      let parts: UIMessage['parts'] | null = null
      if (Array.isArray(row.tool_calls)) {
        parts = row.tool_calls as UIMessage['parts']
      } else if (row.content) {
        parts = [{ type: 'text', text: row.content }] as UIMessage['parts']
      } else {
        parts = []
      }
      out.push({ id: row.id, role: row.role, parts: parts ?? [] } as UIMessage)
    }
  }
  return out
}

export async function replaceConversationMessages(params: {
  conversationId: string
  messages: UIMessage[]
}) {
  await query('DELETE FROM messages WHERE conversation_id=$1', [params.conversationId])
  if (params.messages.length === 0) return
  for (const m of params.messages) {
    const text = m.parts
      .filter(p => p.type === 'text')
      .map(p => (p as { text: string }).text)
      .join('')
    await query(
      'INSERT INTO messages (id, conversation_id, role, content, tool_calls) VALUES ($1,$2,$3,$4,$5)',
      [
        crypto.randomUUID(),
        params.conversationId,
        m.role === 'assistant' || m.role === 'user' ? m.role : 'assistant',
        text || null,
        JSON.stringify(m.parts),
      ]
    )
  }
}

export async function updateConversationTitle(id: string, title: string) {
  await query('UPDATE conversations SET title=$1 WHERE id=$2', [title, id])
}

export async function deleteConversation(id: string) {
  await query('DELETE FROM conversations WHERE id=$1', [id])
}
