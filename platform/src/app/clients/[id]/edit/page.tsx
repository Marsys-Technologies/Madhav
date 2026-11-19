import { readEditableChartIdentity } from '@/lib/charts/pageIdentity'
import { redirect } from 'next/navigation'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { EditClientForm } from '@/components/clients/EditClientForm'
import { SharingPanel } from '@/components/sharing/SharingPanel'
import { PageTitle } from '@/components/journey1/Titles'
import { getAyanamshaEditPolicy } from '@/lib/charts/ayanamshaEditPolicy'
import { normalizeStoredChart, resolveTimezoneOffsetMinutes } from '@/lib/charts/updateChart'
import '@/components/profile/jataka-workspace.css'
import styles from '../folio.module.css'

/**
 * Edit chart details — owners and super-admins only; view grantees return to
 * the workspace. Loads every stored editable field; the initial offset comes
 * from the same resolver `PATCH /api/charts/[id]` verifies against, and a
 * missing or invalid timezone is surfaced for correction rather than defaulted.
 * The ayanamsha edit policy (`CHART_AYANAMSHA_EDIT_POLICY`) is read here, on the
 * server, and handed to the form; the PATCH route enforces it independently.
 */
export default async function EditPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')
  if (!access.canBuild) redirect(`/clients/${id}`)

  const chartResult = await readEditableChartIdentity(id)
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
    <div className={`${styles.warmWorkspace} ${styles.chartForm}`} data-testid="edit-page-root">
      <EditClientForm
        ayanamshaEditPolicy={getAyanamshaEditPolicy()}
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
      {access.role === 'super_admin' && <section id="sharing" className={`j1-panel ${styles.accessPanel}`} aria-label="Chart access"><PageTitle name="access" as="h2" compact/><SharingPanel chartId={id}/></section>}
    </div>
  )
}
