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
