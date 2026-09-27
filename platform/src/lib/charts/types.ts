/**
 * Shared chart-input types (Jātaka chart workspace).
 *
 * `ChartInputSnapshot` is the immutable pre-correction record stored on a
 * conversation archived by a chart-details correction
 * (`conversations.archived_chart_snapshot`, migration 1120). It holds only the
 * chart-defining inputs as they were — never live chart fields, ownership or
 * derived facts — so historical context is not reconstructed from the
 * corrected chart row.
 */
export interface ChartInputSnapshot {
  name: string
  preferred_name: string | null
  subject_name: string | null
  birth_date: string
  birth_time: string
  birth_place: string
  birth_lat: number
  birth_lng: number
  timezone_id: string
  effective_tz_offset_minutes: number
  ayanamshas: string[]
  captured_at: string
}

export type ConversationArchiveReason = 'chart_details_changed'
