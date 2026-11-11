import 'server-only'
import { query } from '@/lib/db/client'

/** Call only after authorizing the request for this chart ID. */
export async function readFolioChartIdentity(chartId: string) {
  const { rows } = await query<{
    id: string
    name: string
    birth_date: string
    birth_time: string
    birth_place: string
    timezone_id: string | null
    ayanamsa: string | null
  }>(
    'SELECT id,name,birth_date::text,birth_time::text,birth_place,timezone_id,ayanamsa FROM charts WHERE id=$1',
    [chartId],
  )
  return rows[0] ?? null
}
