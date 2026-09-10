/**
 * History sidebar data contract (§10.1, §5.8.0 ruling 3, BRIEF_PB-4 Lane F-1).
 *
 * SCOPE NOTE: this lane's file scope is presentational
 * (`components/pariprashna/**` + the page server component) and excludes
 * `lib/pariprashna/**` and API routes. There is today no backend surface
 * that lists Paripraśna threads distinctly from the older `consult`/
 * `consume` chat trees — `conversations.module` is `'consume'` for BOTH
 * (see `lib/pariprashna/pipeline/safety_gate.ts`'s
 * `insertConversationWithId({ ..., module: 'consume' })`), so a query
 * against `conversations` alone cannot honestly distinguish "past
 * Paripraśna readings" from the legacy chat surface without a schema change
 * (out of scope — no migrations this lane). `PariprashnaApp.tsx` therefore
 * derives a `ThreadSummary[]` from the CURRENT session's real, live
 * `ThreadState` only (one real, correctly-behaving entry: title, chart,
 * streaming state, active tick) rather than fabricating cross-session
 * history. Multi-thread / cross-session listing is a genuine residual for
 * the data-layer lane that owns `lib/pariprashna/store` + a threads-listing
 * endpoint — this component is built to the full grouped-by-chart contract
 * below and is ready to render real data the moment that lane exists.
 */
export interface ThreadSummary {
  id: string
  chartId: string
  /** Display label for the chart-group header and the row's glyph tooltip. */
  chartName: string
  title: string
  updatedAtMs: number
  /** This thread is the one currently open in the conversation column. */
  active: boolean
  /** §5.1 F-1 "streaming thread shows a quiet gold dot." */
  streaming: boolean
}
