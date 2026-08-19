/**
 * Paripraśna — CONSENT, SUBJECTS AND EXCLUSIONS (lane G1-B · NCD-9 · PPR-14).
 *
 * Shared types + the injectable DB port. Nothing in this directory reaches for
 * `@/lib/db/client` directly: every entry point takes a `ConsentDb`, which the
 * production callers fill with `defaultConsentDb()` and the tests fill with an
 * in-memory or scratch-DB double. That is what makes "nothing here is reachable
 * until the flag is ON" a testable claim rather than a promise.
 */

/** Subject kinds, per the §4 schema. `native_self` is STRICT — see resolve.ts. */
export type SubjectKind = 'native_self' | 'cohort' | 'test'

/** §3.5.D.3 — attribution only by ACTIVE election; the default is `anonymous`. */
export type AnonymizationChoice = 'anonymous' | 'attributed'

export type ConsentState = 'granted' | 'withdrawn'

export type ConsentEventKind =
  | 'granted'
  | 'withdrawn'
  | 'redaction_requested'
  | 'anonymization_changed'
  | 'vulnerable_flag_set'
  | 'vulnerable_flag_cleared'
  | 'deletion_verified'
  | 'deletion_disputed'
  | 'deletion_dispute_resolved'

/** The excluded-subject register's reason vocabulary (§3.5.F). */
export type ExclusionReason =
  | 'minor'
  | 'consent_incapacity'
  | 'vulnerable_subject'
  | 'consent_withdrawn'
  | 'no_consent_row'
  | 'native_self_claim_invalid'
  | 'subject_deleted'
  | 'birth_date_unavailable'

export interface ConsentRow {
  chart_id: string
  subject_kind: SubjectKind
  subject_principal_id: string | null
  guardian_principal_id: string | null
  consent_document_ref: string | null
  consent_state: ConsentState
  granted_at: string | null
  withdrawn_at: string | null
  anonymization_choice: AnonymizationChoice
  redaction_requests: unknown[]
  vulnerable_exclusion_flag: boolean
  verified_deletion_at: string | null
  recorded_by_principal_id: string | null
  created_at: string
  updated_at: string
}

export interface ConsentEventRow {
  event_id?: number
  chart_id: string
  seq: number
  event_kind: ConsentEventKind
  actor_principal_id: string | null
  payload: Record<string, unknown>
  recorded_at: string
  prev_hash: string | null
  entry_hash: string
}

export interface ExclusionRow {
  exclusion_id?: number
  chart_id: string
  exclusion_reason: ExclusionReason
  detector: string
  subject_age_years: number | null
  evidence: Record<string, unknown>
  detected_at: string
  cleared_at: string | null
  cleared_reason: string | null
}

export interface TombstoneRow {
  tombstone_id?: number
  chart_id: string
  withdrawal_event_seq: number
  table_name: string
  table_present: boolean
  row_count: number
  content_hash: string | null
  verified_empty: boolean
  deleted_at: string
}

export interface DeletionDisputeRow {
  dispute_id?: number
  chart_id: string
  dr_class: string
  dr_id: string | null
  opened_by_session: string
  parties: string[]
  description: string
  requested_scope: string[]
  applied_scope: string[]
  dr_entry_yaml: string
  status: 'open' | 'resolved' | 'escalated' | 'reopened'
  resolution: string | null
  opened_at: string
  resolved_at: string | null
}

/** The minimal chart facts consent resolution needs. */
export interface ChartSubjectRow {
  id: string
  owner_id: string | null
  role: string | null
  birth_date: string | null
  name: string | null
  subject_name: string | null
  birth_place: string | null
}

// ── DB port ──────────────────────────────────────────────────────────────────

export interface ConsentQueryable {
  query<T = Record<string, unknown>>(sql: string, params?: unknown[]): Promise<{ rows: T[] }>
}

export interface ConsentDb extends ConsentQueryable {
  /**
   * Run `fn` inside ONE transaction on ONE connection. The withdrawal sweep is
   * multi-statement and must not interleave with another writer, so it may not
   * be expressed as a series of pool-level `query()` calls (each of which can
   * land on a different connection).
   */
  withTransaction<T>(fn: (tx: ConsentQueryable) => Promise<T>): Promise<T>
}

/** Raised when a consent entry point is called while the flag is OFF. */
export class ConsentFeatureDisabledError extends Error {
  readonly code = 'SUBJECT_CONSENT_DISABLED'
  constructor(operation: string) {
    super(
      `SUBJECT_CONSENT_DISABLED: ${operation} requires the SUBJECT_CONSENT_ENFORCEMENT ` +
        `feature flag. It is OFF, so this operation does not exist for this deploy.`,
    )
    this.name = 'ConsentFeatureDisabledError'
  }
}
