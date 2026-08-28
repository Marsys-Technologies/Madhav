import 'server-only'
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

export interface ConversationWithSnippet extends ConversationSummary {
  /**
   * First user message text, truncated — an ADDITIVE fallback for callers
   * that need a display title when `title` (unchanged, still NULL until a
   * manual rename) is absent. Never written back to `title` itself, and
   * never populated at all unless `readingsOnly` was requested — the
   * legacy `consume`/`ArchivedView.tsx` caller's shape and query cost are
   * byte-identical to before this field existed.
   */
  first_message_snippet: string | null
}

export async function listConversations(params: {
  chartId: string
  userId: string
  module: ConversationModule
  includeArchived?: boolean
  /**
   * S1-F-001-adjacent (V3-E-012a): `module='consume'` alone cannot
   * distinguish a Paripraśna reading from the legacy consume/consult chat
   * tree that shares the same `conversations` row shape — both write
   * `module='consume'` (`safety_gate.ts`'s `insertConversationWithId`,
   * `chat/consult/route.ts`). Every completed Paripraśna turn additively
   * stamps `conversation_messages.metadata_json.acharya_reading_receipt`
   * (the receipt lane, G3-A — see `lib/pariprashna/receipt/store.ts`); the
   * legacy consume/consult writer never does. That JSONB-key-existence
   * check is a REAL, already-existing discriminator (Native Surrogate
   * ruling B1, decision event `f3b88219-432f-4096-999c-07f6700f6406`) — not
   * a heuristic — so this defaults OFF and every existing caller (the
   * consume module's own `ArchivedView.tsx`, which legitimately wants ALL
   * of its conversations, not only receipted ones) is completely
   * unaffected unless it opts in.
   */
  readingsOnly?: boolean
}): Promise<ConversationWithSnippet[]> {
  const { includeArchived = false, readingsOnly = false } = params
  const archiveClause = includeArchived ? '' : 'AND c.archived_at IS NULL'
  const readingsClause = readingsOnly
    ? `AND EXISTS (
         SELECT 1 FROM conversation_messages cm
         WHERE cm.conversation_id = c.id
           AND cm.role = 'assistant'
           AND cm.metadata_json ? 'acharya_reading_receipt'
       )`
    : ''
  const { rows } = await query(
    `SELECT c.id, c.chart_id, c.user_id, c.module, c.title, c.created_at, c.updated_at, c.archived_at,
            LEFT(
              (
                SELECT elem->>'text'
                FROM conversation_messages first_msg,
                     jsonb_array_elements(first_msg.parts_json) AS elem
                WHERE first_msg.conversation_id = c.id
                  AND first_msg.role = 'user'
                  AND elem->>'type' = 'text'
                ORDER BY first_msg.created_at ASC
                LIMIT 1
              ),
              120
            ) AS first_message_snippet
     FROM conversations c
     WHERE c.chart_id=$1 AND c.user_id=$2 AND c.module=$3 ${archiveClause} ${readingsClause}
     ORDER BY COALESCE(c.updated_at, c.created_at) DESC
     LIMIT 100`,
    [params.chartId, params.userId, params.module]
  )
  return rows.map(row => ({
    ...(row as ConversationWithSnippet),
    module: row.module as ConversationModule,
    updated_at: (row.updated_at ?? row.created_at) as string,
    first_message_snippet: (row.first_message_snippet as string | null) ?? null,
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

export async function updateConversationTitle(id: string, title: string) {
  await query('UPDATE conversations SET title=$1 WHERE id=$2', [title, id])
}

export async function deleteConversation(id: string) {
  await query('DELETE FROM conversations WHERE id=$1', [id])
}
