import { redirect } from 'next/navigation'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { EditClientForm } from '@/components/clients/EditClientForm'
import { query } from '@/lib/db/client'

export default async function EditPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')
  if (!access.canBuild) redirect(`/clients/${id}`)

  const chartResult = await query<{
    id: string
    name: string
    birth_date: string
    birth_time: string
    birth_place: string
    birth_lat: number | null
    birth_lng: number | null
    ayanamsa: string
    created_at: string
  }>(
    `SELECT id, name, birth_date, birth_time, birth_place, birth_lat, birth_lng, ayanamsa, created_at
     FROM charts WHERE id = $1`,
    [id]
  )
  const chart = chartResult.rows[0] ?? null
  if (!chart) redirect('/dashboard')

  return (
    <div data-testid="edit-page-root">
      <EditClientForm chart={chart} />
    </div>
  )
}
