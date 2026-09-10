import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { id: chartId } = await params

  // P2-B-001 / E-012: this handler used to check only that the caller was
  // *some* authenticated user — never that they owned or had a grant on
  // THIS chart_id — letting any authenticated user read any other user's
  // sensitive birth data. Route through the shared authorization brain
  // (same one the sibling DELETE handler below uses for its owner/
  // super_admin check) before touching chart rows.
  const profileResult = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id = $1',
    [user.uid],
  )
  const role = (profileResult.rows[0]?.role as string) ?? 'guest'

  const permission = await authorizeChartAccess({
    principal: { uid: user.uid, role: role === 'super_admin' ? 'super_admin' : 'guest' },
    chartId,
    db: { query },
  })
  if (permission === 'deny') {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  const result = await query<{
    subject_name: string
    birth_date: string
    birth_time: string
    birth_place: string
  }>(
    'SELECT subject_name, birth_date::text, birth_time::text, birth_place FROM charts WHERE id = $1',
    [chartId],
  )

  const row = result.rows[0] ?? null
  if (!row) return NextResponse.json({ error: 'Not found' }, { status: 404 })

  return NextResponse.json({
    subject_name: row.subject_name,
    birth_date: row.birth_date,
    birth_time: row.birth_time,
    birth_place: row.birth_place,
  })
}

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

    // Build orchestrator data (new schema — build_run_assets cascade from build_runs)
    await query('DELETE FROM asset_throughput WHERE chart_id = $1', [chartId])
    await query('DELETE FROM build_runs WHERE chart_id = $1', [chartId])

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
