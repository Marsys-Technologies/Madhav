import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export async function DELETE(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { id: chartId } = await params

  // Verify the chart exists and the caller is owner or super_admin.
  const profileResult = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id = $1',
    [user.uid],
  )
  const role = (profileResult.rows[0]?.role as string) ?? 'guest'

  const chartResult = await query<{ owner_id: string; client_id: string }>(
    'SELECT owner_id, client_id FROM charts WHERE id = $1',
    [chartId],
  )
  const chart = chartResult.rows[0] ?? null
  if (!chart) return NextResponse.json({ error: 'Not found' }, { status: 404 })

  const isOwner = chart.owner_id === user.uid || chart.client_id === user.uid
  if (role !== 'super_admin' && !isOwner) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  // Atomic hard wipeout — all chart-scoped rows in dependency order.
  await query('BEGIN', [])
  try {
    // Conversation data
    await query(
      `DELETE FROM messages WHERE conversation_id IN (
         SELECT id FROM conversations WHERE chart_id = $1
       )`,
      [chartId],
    )
    await query('DELETE FROM conversations WHERE chart_id = $1', [chartId])
    await query('DELETE FROM conversation_branches WHERE chart_id = $1', [chartId])

    // Build orchestrator data
    await query('DELETE FROM build_events WHERE build_id IN (SELECT build_id FROM builds WHERE chart_id = $1)', [chartId])
    await query('DELETE FROM build_steps WHERE build_id IN (SELECT build_id FROM builds WHERE chart_id = $1)', [chartId])
    await query(
      `DELETE FROM notification_views WHERE build_id IN (
         SELECT build_id FROM builds WHERE chart_id = $1
       )`,
      [chartId],
    )
    await query(
      `DELETE FROM build_notifications WHERE build_id IN (
         SELECT build_id FROM builds WHERE chart_id = $1
       )`,
      [chartId],
    )
    await query('DELETE FROM builds WHERE chart_id = $1', [chartId])

    // Pyramid + chart
    await query('DELETE FROM pyramid_layers WHERE chart_id = $1', [chartId])
    await query('DELETE FROM chart_grants WHERE chart_id = $1', [chartId])
    await query('DELETE FROM charts WHERE id = $1', [chartId])

    await query('COMMIT', [])
  } catch (err) {
    await query('ROLLBACK', [])
    console.error('[DELETE /api/charts/:id] rollback', err)
    return NextResponse.json({ error: 'Delete failed' }, { status: 500 })
  }

  return NextResponse.json({ deleted: true, chart_id: chartId }, { status: 200 })
}
