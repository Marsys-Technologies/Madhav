export type AcceptanceDoor = 'portal' | 'managed_mcp' | 'raw_mcp'
export type CollectionTerminal = 'complete' | 'incomplete' | 'blocked' | 'transport_error'

export interface AcceptanceCase {
  readonly id: string
  readonly question: string
  readonly scope_tuple: Record<string, unknown>
  readonly requiredDimensions: readonly string[]
  readonly expected: 'supported_complete' | 'honest_insufficient'
}

/** A redacted reference only; raw evidence stays in the configured restricted directory. */
export interface CollectedCase {
  readonly caseId: string
  readonly door: AcceptanceDoor
  readonly inquiryId: string | null
  readonly expectedRevision: string
  readonly observedRevision: string | null
  readonly snapshotHash: string | null
  readonly chartBuildId: string | null
  readonly answer: string
  /** Typed server envelope retained for independent answer assessment. */
  readonly responseAccountability: unknown | null
  readonly receiptRefs: readonly string[]
  readonly materialFactIds: readonly string[]
  readonly deliveredFactIds: readonly string[]
  readonly unresolvedObligationIds: readonly string[]
  readonly networkCallCount: number
  readonly source: 'candidate' | 'live' | 'fixture'
  readonly terminal: CollectionTerminal
  readonly diagnostic: string | null
}

export interface DoorClient { collect(input: AcceptanceCase): Promise<CollectedCase> }

export function isLiveEvidence(row: CollectedCase): boolean {
  return row.source !== 'fixture'
    && row.networkCallCount > 0
    && row.terminal === 'complete'
    && row.observedRevision === row.expectedRevision
    && row.receiptRefs.length > 0
}

export function assertLiveEvidence(row: CollectedCase): void {
  if (!isLiveEvidence(row)) throw new Error('PURNA_COLLECTION_NOT_LIVE_EVIDENCE')
}
