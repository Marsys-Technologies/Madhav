import 'server-only'
import { query } from '@/lib/db/client'
import { checkReadingReadiness } from '@/lib/charts/readingGate'
import {
  ARCHIVED_WRITE_REFUSED_MESSAGE,
  CONVERSATION_ARCHIVED_READ_ONLY,
  isCorrectionArchived,
} from '@/lib/conversations/readOnly'

export { PersistenceRefusedError, persistenceRefusalOf } from '@/lib/conversations/readOnly'

/**
 * Persistence-boundary write guard (Jātaka chart workspace).
 *
 * Admission gates run when a reading starts; a chart correction can commit
 * while the reading is still streaming. This guard is re-evaluated at the
 * moment the reading would be persisted: a conversation archived by a chart
 * correction, a conversation that no longer belongs to the chart, or an
 * unreadable state all refuse the write. Callers whose admission policy
 * requires a Ready chart also re-check readiness here. Migration 1121's
 * trigger enforces the archive half inside the database as well.
 */
export type ConversationWriteGuardResult =
  | { ok: true }
  | { ok: false; code: 'CONVERSATION_ARCHIVED_READ_ONLY' | 'CHART_RECOMPUTE_REQUIRED'; message: string }

export async function checkConversationWritable(args: {
  conversationId: string
  chartId: string
  readinessPolicy?: 'require-ready' | 'allow-incomplete'
}): Promise<ConversationWriteGuardResult> {
  try {
    const { rows } = await query<{ chart_id: string; archive_reason: string | null }>(
      'SELECT chart_id, archive_reason FROM conversations WHERE id = $1',
      [args.conversationId],
    )
    const row = rows[0]
    if (row && (isCorrectionArchived(row) || row.chart_id !== args.chartId)) {
      return { ok: false, code: CONVERSATION_ARCHIVED_READ_ONLY, message: ARCHIVED_WRITE_REFUSED_MESSAGE }
    }
    if (args.readinessPolicy !== 'allow-incomplete') {
      const gate = await checkReadingReadiness(args.chartId)
      if (!gate.ok) return { ok: false, code: gate.code, message: gate.message }
    }
    return { ok: true }
  } catch (err) {
    console.error('[conversations/writeGuard] check failed:', (err as Error)?.message)
    return { ok: false, code: 'CHART_RECOMPUTE_REQUIRED', message: 'This reading could not be saved safely. Please try again shortly.' }
  }
}
