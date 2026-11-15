import 'server-only'
import { query } from '@/lib/db/client'
import type { LELEvent } from '@/lib/lel/parser'

/** Mīmāṃsā event read; the page checks chart access/existence and redirects first. */
export function readTimelineEvents(id: string) {
  return query<LELEvent>(
    `SELECT event_id AS id,
            CASE date_confidence
              WHEN 'year_only' THEN to_char(event_date, 'YYYY')
              WHEN 'month_known' THEN to_char(event_date, 'YYYY-MM')
              ELSE to_char(event_date, 'YYYY-MM-DD')
            END AS date,
            category, description AS body,
            jsonb_strip_nulls(jsonb_build_object(
              'maha_lord', chart_state->>'dasha_md',
              'antar_lord', chart_state->>'dasha_ad'
            )) AS chart_state
       FROM life_events
      WHERE chart_id = $1
      ORDER BY event_date DESC, event_id ASC`,
    [id],
  )
}
