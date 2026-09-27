import 'server-only'
import { query } from '@/lib/db/client'
import { checkReadingReadiness } from '@/lib/charts/readingGate'
import { CONVERSATION_ARCHIVED_READ_ONLY, isCorrectionArchived } from '@/lib/conversations/readOnly'

/**
 * Persistence-boundary write guard (Jātaka chart workspace).
 *
 * Admission gates run when a reading starts; a chart correction can commit
 * while the reading is still streaming. This guard is re-evaluated at the
 * moment the reading would be persisted: a conversation archived by a chart
 * correction, a conversation that no longer belongs to the chart, a chart that
 * is no longer Ready, or an unreadable state all refuse the write. Migration
 * 1121's trigger enforces the archive half inside the database as well.
 */
export type ConversationWriteGuardResult =
  | { ok: true }
  | { ok: false; code: 'CONVERSATION_ARCHIVED_READ_ONLY' | 'CHART_RECOMPUTE_REQUIRED'; message: string }

const ARCHIVED_MESSAGE =
  'This reading was not saved: the chart details were corrected while it was being prepared, and earlier readings are now read-only history.'

export async function checkConversationWritable(args: {
  conversationId: string
  chartId: string
}): Promise<ConversationWriteGuardResult> {
  try {
    const { rows } = await query<{ chart_id: string; archive_reason: string | null }>(
      'SELECT chart_id, archive_reason FROM conversations WHERE id = $1',
      [args.conversationId],
    )
    const row = rows[0]
    if (row && (isCorrectionArchived(row) || row.chart_id !== args.chartId)) {
      return { ok: false, code: CONVERSATION_ARCHIVED_READ_ONLY, message: ARCHIVED_MESSAGE }
    }
    const gate = await checkReadingReadiness(args.chartId)
    if (!gate.ok) return { ok: false, code: gate.code, message: gate.message }
    return { ok: true }
  } catch (err) {
    console.error('[conversations/writeGuard] check failed:', (err as Error)?.message)
    return { ok: false, code: 'CHART_RECOMPUTE_REQUIRED', message: 'This reading could not be saved safely. Please try again shortly.' }
  }
}
