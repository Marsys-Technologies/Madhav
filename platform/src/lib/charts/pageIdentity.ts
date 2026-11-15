import 'server-only'
import { query } from '@/lib/db/client'
import type { StoredChartRow } from '@/lib/charts/updateChart'

/**
 * Identity-owned page projections. Callers retain their existing admission guards,
 * sequencing, null handling and error policy. These reads grant no access.
 */

export function readCockpitChartIdentity(id: string) {
  return query<{
    id: string
    name: string
    birth_date: string
    birth_time: string
    birth_place: string
    created_at: string
  }>('SELECT id, name, birth_date, birth_time::text AS birth_time, birth_place, created_at FROM charts WHERE id=$1', [id])
}

export function readConsultChartIdentity(id: string) {
  return query<{ name: string; birth_date: string; birth_place: string; client_id: string }>('SELECT name, birth_date, birth_place, client_id FROM charts WHERE id=$1', [id])
}

export function readEditableChartIdentity(id: string) {
  return query<StoredChartRow & { id: string }>(`SELECT id, name, preferred_name, subject_name,
            birth_date::text AS birth_date, birth_time::text AS birth_time, birth_place,
            birth_lat::float8 AS birth_lat, birth_lng::float8 AS birth_lng, timezone_id, ayanamsa
       FROM charts WHERE id = $1`, [id])
}

// Keep the callers' prior nullable/non-nullable query annotations without changing
// the returned rows at runtime. Both projections share this exact SQL operation.
function readChartName<Name extends string | null>(id: string) {
  return query<{ name: Name }>('SELECT name FROM charts WHERE id=$1', [id])
}

export function readChartTitleName(id: string) {
  return readChartName<string>(id)
}

export function readChartPageName(id: string) {
  return readChartName<string | null>(id)
}

export function readPreparationChartName(id: string) {
  return query<{ subject_name: string | null }>('SELECT subject_name FROM charts WHERE id=$1', [id])
}

export function readPreparationChartIdentity(id: string) {
  return query<{ subject_name: string | null; birth_date: string | null; birth_time: string | null; birth_place: string | null }>('SELECT subject_name, birth_date, birth_time::text, birth_place FROM charts WHERE id=$1', [id])
}

export function readConsultationChartPin(id: string) {
  return query<{ name: string; birth_date: string; birth_time: string; birth_place: string }>('SELECT name, birth_date, birth_time, birth_place FROM charts WHERE id=$1', [id])
}
