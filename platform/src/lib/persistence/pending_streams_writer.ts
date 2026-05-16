import 'server-only'
import { query } from '@/lib/db/client'

const EXPIRY_MS = 30 * 60 * 1000 // 30 minutes
const DEBOUNCE_MS = 100

/**
 * Per-request debounced writer for pending_streams.
 *
 * γ7: Created at stream-start in the consume route. Each text delta increments
 * the sequence counter and schedules a debounced DB write. Called clear() in
 * onFinish after β2 write-through confirms conversation persistence.
 *
 * The table row is keyed by query_id (UUID); an existing row is upserted on
 * every debounced flush so reconnect attempts always see the latest text.
 */
export function createPendingStreamWriter(queryId: string, conversationId: string | null, userId: string) {
  let accumulatedText = ''
  let eventSeq = 0
  let timer: ReturnType<typeof setTimeout> | null = null
  let cleared = false

  async function flushToDB() {
    const text = accumulatedText
    const seq = eventSeq
    const expiresAt = new Date(Date.now() + EXPIRY_MS).toISOString()
    try {
      await query(
        `INSERT INTO pending_streams (query_id, user_id, conversation_id, accumulated_text, last_event_seq, expires_at)
         VALUES ($1, $2, $3, $4, $5, $6)
         ON CONFLICT (query_id) DO UPDATE
           SET accumulated_text  = EXCLUDED.accumulated_text,
               last_event_seq    = EXCLUDED.last_event_seq,
               expires_at        = EXCLUDED.expires_at`,
        [queryId, userId, conversationId, text, seq, expiresAt],
      )
    } catch {
      // Non-fatal: pending stream write failure does not block the response.
    }
  }

  function scheduleFlush() {
    if (cleared) return
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => { void flushToDB() }, DEBOUNCE_MS)
  }

  return {
    /** Called on each text delta from the synthesis stream. */
    onTextDelta(delta: string) {
      if (cleared) return
      accumulatedText += delta
      eventSeq++
      scheduleFlush()
    },

    /** Called on each non-text event (data parts, stage events). */
    onEvent() {
      if (cleared) return
      eventSeq++
      scheduleFlush()
    },

    /**
     * Flush final state and delete the row.
     * Called in onFinish after β2 write-through confirms conversation persistence.
     */
    async clear() {
      cleared = true
      if (timer) clearTimeout(timer)
      try {
        await query('DELETE FROM pending_streams WHERE query_id = $1', [queryId])
      } catch {
        // Non-fatal.
      }
    },

    getAccumulatedText() { return accumulatedText },
    getEventSeq() { return eventSeq },
  }
}

export type PendingStreamWriter = ReturnType<typeof createPendingStreamWriter>
