/**
 * Paripraśna durable conversation summaries — PB-2 (SMṚTI) lane M-3 — route splice.
 *
 * The one function `src/app/api/pariprashna/route.ts` calls: given a
 * conversation id, read its canonical turns (M-1's `readTurnParts`, imported
 * not modified), run the threshold/reuse decision (`getOrCreateSummary`), and
 * return the summary text to fold into the FIXED structural slot
 * (`assemble.ts`) ahead of the route's existing system content.
 *
 * KNOWN RESIDUAL (disclosed, not hidden): the live pariprashna route's
 * write-through path still persists turns via the LEGACY
 * `writeConversationMessages` (`@/lib/persistence/conversation_writer`), not
 * M-1's `writeTurn` — wiring that swap is PB-2 lane M-2's job ("the
 * persistence seam"), not this lane's. Until M-2 lands, canonical
 * `message_parts` rows are never written for pariprashna-route conversations,
 * so `listCanonicalMessagesForConversation` returns an empty list for every
 * real conversation today and this function resolves to `null` — a documented
 * no-op, not a silent bug. The moment M-2 wires `writeTurn` into the route,
 * this function starts seeing real canonical turns with zero further changes
 * needed here.
 */
import 'server-only'

import { readTurnParts } from '../store/reader'
import { listCanonicalMessagesForConversation, PgSummaryStore } from './store'
import { LlmSummarizerWorker } from './worker'
import { getOrCreateSummary } from './service'
import type { CanonicalTurn } from './types'

/**
 * Resolve the durable summary text to splice for `conversationId`, or `null`
 * if there is nothing to summarize yet (no canonical turns, or the threshold
 * has not been crossed and no prior summary exists). Never throws — the route
 * treats this as best-effort context enrichment, not a hard dependency; a
 * caller wraps this in its own try/catch per the route's existing
 * non-fatal-helper convention (see `orientationPromise`'s `.catch()` in
 * route.ts).
 */
export async function getConversationSummaryForSplice(conversationId: string): Promise<string | null> {
  const messageRefs = await listCanonicalMessagesForConversation(conversationId)
  if (messageRefs.length === 0) return null

  const turns: CanonicalTurn[] = await Promise.all(
    messageRefs.map(async (ref): Promise<CanonicalTurn> => ({
      message_id: ref.id,
      role: ref.role,
      parts: await readTurnParts(ref.id),
    })),
  )

  const result = await getOrCreateSummary(
    { store: new PgSummaryStore(), worker: new LlmSummarizerWorker() },
    { conversationId, turns },
  )
  return result.summary?.summary_text ?? null
}
