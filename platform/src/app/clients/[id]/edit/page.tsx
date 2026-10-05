import { redirect } from 'next/navigation'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { EditClientForm } from '@/components/clients/EditClientForm'
import { SharingPanel } from '@/components/sharing/SharingPanel'
import { PageTitle } from '@/components/journey1/Titles'
import { query } from '@/lib/db/client'
import { normalizeStoredChart, resolveTimezoneOffsetMinutes, type StoredChartRow } from '@/lib/charts/updateChart'
import '@/components/profile/jataka-workspace.css'

/**
 * Edit chart details — owners and super-admins only; view grantees return to
 * the workspace. Loads every stored editable field; the initial offset comes
 * from the same resolver `PATCH /api/charts/[id]` verifies against, and a
 * missing or invalid timezone is surfaced for correction rather than defaulted.
 */
export default async function EditPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')
  if (!access.canBuild) redirect(`/clients/${id}`)

  const chartResult = await query<StoredChartRow & { id: string }>(
    `SELECT id, name, preferred_name, subject_name,
            birth_date::text AS birth_date, birth_time::text AS birth_time, birth_place,
            birth_lat::float8 AS birth_lat, birth_lng::float8 AS birth_lng, timezone_id, ayanamsa
       FROM charts WHERE id = $1`,
    [id],
  )
  const row = chartResult.rows[0] ?? null
  if (!row) redirect('/dashboard')

  const stored = normalizeStoredChart(row)
  let tzOffsetHours: number | null = null
  if (stored.timezone_id) {
    try {
      tzOffsetHours = resolveTimezoneOffsetMinutes(stored.birth_date, stored.birth_time, stored.timezone_id) / 60
    } catch {
      tzOffsetHours = null
    }
  }

  return (
    <div data-testid="edit-page-root">
      <EditClientForm
        chart={{
          id: row.id,
          name: row.name,
          preferred_name: row.preferred_name,
          subject_name: row.subject_name,
          birth_date: stored.birth_date,
          birth_time: stored.birth_time,
          birth_place: row.birth_place,
          birth_lat: row.birth_lat === null ? null : Number(row.birth_lat),
          birth_lng: row.birth_lng === null ? null : Number(row.birth_lng),
          timezone_id: stored.timezone_id,
          tz_offset_hours: tzOffsetHours,
          ayanamshas: stored.ayanamshas,
        }}
      />
      {access.role === 'super_admin' && <section id="sharing" className="j1-panel mx-auto mb-8 max-w-2xl" aria-label="Chart access"><PageTitle name="access" as="h2" compact/><SharingPanel chartId={id}/></section>}
    </div>
  )
}
