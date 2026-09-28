import { errorResponse } from '@/lib/errors'

/**
 * Chart-correction read-only lock (Jātaka chart workspace).
 *
 * A conversation archived because its chart's birth details were corrected
 * (`archive_reason = 'chart_details_changed'`, migration 1120) belongs to the
 * earlier details: readable, never continued or mutated. This is the single
 * predicate every turn-writing and mutating door checks. It fails closed on the
 * reason alone — migration 1120's CHECK already keeps such a row archived.
 * Manual archives (reason NULL) keep their existing semantics.
 *
 * Pure (no server-only import) so route tests that stub `@/lib/conversations`
 * still exercise the real predicate.
 */
export const CONVERSATION_ARCHIVED_READ_ONLY = 'CONVERSATION_ARCHIVED_READ_ONLY'

export function isCorrectionArchived(
  conversation: { archived_at?: string | null; archive_reason?: string | null } | null | undefined,
): boolean {
  return conversation?.archive_reason === 'chart_details_changed'
}

/** 409 in the canonical API error envelope. */
export function archivedReadOnlyResponse() {
  return errorResponse(CONVERSATION_ARCHIVED_READ_ONLY, 'This conversation is historical and read-only.', 409, {
    retry: false,
  })
}

export const ARCHIVED_WRITE_REFUSED_MESSAGE =
  'This reading was not saved: the chart details were corrected while it was being prepared, and earlier readings are now read-only history.'

/**
 * Thrown from inside a persistence step when a re-check refuses the write.
 * Carries the same code/message pair the write guard returns.
 */
export class PersistenceRefusedError extends Error {
  constructor(
    readonly code: string,
    message: string,
  ) {
    super(message)
    this.name = 'PersistenceRefusedError'
  }
}

/**
 * Maps an error thrown by a persistence step to a refusal, or null for an
 * ordinary failure. Recognises a re-check refusal and migration 1121's trigger
 * (check_violation whose message starts with CONVERSATION_ARCHIVED_READ_ONLY).
 */
export function persistenceRefusalOf(err: unknown): { code: string; message: string } | null {
  if (err instanceof PersistenceRefusedError) return { code: err.code, message: err.message }
  const e = err as { code?: unknown; message?: unknown } | null
  if (e && e.code === '23514' && typeof e.message === 'string' && e.message.startsWith(CONVERSATION_ARCHIVED_READ_ONLY)) {
    return { code: CONVERSATION_ARCHIVED_READ_ONLY, message: ARCHIVED_WRITE_REFUSED_MESSAGE }
  }
  return null
}
