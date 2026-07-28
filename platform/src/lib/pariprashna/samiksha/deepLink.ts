/**
 * SAMĪKṢĀ deep links — PB-3 (SAMĪKṢĀ) lane L-3.
 *
 * A ledger row links back to the settled conversation turn its claim was detected on. The
 * link is READ-ONLY by construction: it is a plain URL string rendered into an `<a href>`.
 * Navigating it is a GET to an existing route with a hash anchor — it triggers no write path,
 * so P1 ("settled turns stay byte-identical") holds trivially: there is nothing here that
 * could mutate a turn.
 *
 * ── ROUTE SHAPE (documented inference) ──────────────────────────────────────────────────────
 * BRIEF_PB-3 §F1 (L-3) specifies the link target as `/pariprashna/t/{thread}#turn-{n}` per the
 * design doc §3.3. That literal route DOES NOT EXIST in this codebase: the Paripraśna thread
 * surface is served at `/clients/{chartId}/pariprashna` (see
 * src/app/clients/[id]/pariprashna/page.tsx), there is no `/pariprashna/t/{thread}` segment,
 * and `conversation_messages` carries no turn-ordinal column. The brief explicitly authorises
 * inferring the shape "from how PB-1/PB-2's own thread routes are structured — search the
 * codebase." So this builder targets the REAL route and carries the thread (conversation) id as
 * a query param plus the turn ordinal as the hash anchor:
 *   /clients/{chartId}/pariprashna?thread={conversationId}#turn-{turnOrdinal}
 * The `#turn-{n}` fragment matches the brief's anchor contract; the thread renderer (PB-2 / L-2
 * territory) is the owner of emitting matching `id="turn-{n}"` anchors. The divergence from the
 * brief's literal path is disclosed in REPORT terms and flagged as an integration follow-up.
 *
 * Isomorphic (no server-only) so components can build hrefs directly.
 */

export interface TurnDeepLinkTarget {
  chartId: string
  /** The conversation (thread) id the turn lives in. */
  conversationId: string
  /** 1-based ordinal of the turn within its thread (assistant turns, chronological). */
  turnOrdinal: number
}

/**
 * Build the read-only deep-link URL from a ledger row's resolved turn anchor. Pure: same input
 * → same string, no I/O, no side effect. The result is always a relative app URL safe to place
 * in an `<a href>`.
 */
export function buildTurnDeepLink(target: TurnDeepLinkTarget): string {
  const { chartId, conversationId, turnOrdinal } = target
  const thread = encodeURIComponent(conversationId)
  return `/clients/${encodeURIComponent(chartId)}/pariprashna?thread=${thread}#turn-${turnOrdinal}`
}
