import type { LedgerRow, Outcome } from '@/lib/pariprashna/samiksha/schema'
import type { TurnDeepLinkTarget } from '@/lib/pariprashna/samiksha/deepLink'

/** Serializable review payload the server component hands the client surface. */
export interface ReviewViewModel {
  chartId: string
  chartName: string
  awaiting: LedgerRow[]
  open: LedgerRow[]
  resolvable: LedgerRow[]
  coverage: {
    resolvedCount: number
    unverifiableCount: number
    lapsedCount: number
    openCount: number
    awaitingCount: number
    coverageFraction: number | null
  }
  turnAnchors: Record<string, TurnDeepLinkTarget>
  badgeCount: number
  /** Real wall-clock ISO date, computed server-side and passed down (kāla-rekhā today-dot). */
  nowIso: string
}

// ── Action callbacks (server actions in production; injectable stubs in tests) ──────────────
export type ConfirmAction = (input: { rowId: string; probability: number }) => Promise<void> | void
export type DismissAction = (input: { rowId: string; reason?: string }) => Promise<void> | void
export type EditAction = (input: { rowId: string; claimText: string }) => Promise<void> | void
export type ResolveAction = (input: { rowId: string; outcome: Outcome; note?: string }) => Promise<void> | void
export type BatchResolveAction = (
  items: { rowId: string; outcome: Outcome }[],
) => Promise<void> | void

export interface ReviewActions {
  confirm: ConfirmAction
  dismiss: DismissAction
  edit: EditAction
  resolve: ResolveAction
  batchResolve: BatchResolveAction
}
