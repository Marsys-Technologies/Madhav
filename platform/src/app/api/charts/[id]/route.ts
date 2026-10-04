import { NextRequest, NextResponse } from 'next/server'
import type { PoolClient } from 'pg'
import { getServerUser } from '@/lib/firebase/server'
import { getPool, query } from '@/lib/db/client'
import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import { requireChartPermission } from '@/lib/auth/requireChartPermission'
import { ChartUpdateError, updateChartAndMaybeRecompute } from '@/lib/charts/recomputeChart'
import {
  CHART_DELETION_ENABLED,
  CHART_DELETION_UNAVAILABLE_CODE,
  CHART_DELETION_UNAVAILABLE_MESSAGE,
} from '@/lib/charts/chartDeletionAvailability'

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

  // Chart deletion is unavailable until the full completeness program lands
  // (CHART_DELETION_COMPLETENESS_DESIGN_v1_0.md): refuse BEFORE opening a
  // transaction or issuing any DELETE, rather than attempt a delete that cannot
  // complete and could lose part of the user's data. Auth/ownership above stay.
  if (!CHART_DELETION_ENABLED) {
    return NextResponse.json(
      { error: CHART_DELETION_UNAVAILABLE_MESSAGE, code: CHART_DELETION_UNAVAILABLE_CODE },
      { status: 503 },
    )
  }

  // Atomic hard wipeout — all chart-scoped rows in dependency order.
  //
  // The whole transaction runs on ONE dedicated connection. BEGIN / COMMIT /
  // ROLLBACK issued through the pool-level query() can land on different pooled
  // connections, so a ROLLBACK would not undo the deletes (design section 2.1,
  // R2). NOTE: the statement list below is the legacy list and is known to be
  // incomplete/invalid (`messages` and `conversation_branches.chart_id` do not
  // exist); it is unreachable while CHART_DELETION_ENABLED is false and is
  // replaced by the full program before the flag is flipped.
  let client: PoolClient
  try {
    client = await (await getPool()).connect()
  } catch (err) {
    console.error('[DELETE /api/charts/:id] could not check out a connection', err)
    return NextResponse.json({ error: 'Delete failed' }, { status: 500 })
  }
  let discard = false
  try {
    await client.query('BEGIN')
    // Conversation data
    await client.query(
      `DELETE FROM messages WHERE conversation_id IN (
         SELECT id FROM conversations WHERE chart_id = $1
       )`,
      [chartId],
    )
    await client.query('DELETE FROM conversations WHERE chart_id = $1', [chartId])
    await client.query('DELETE FROM conversation_branches WHERE chart_id = $1', [chartId])

    // Build orchestrator data (new schema — build_run_assets cascade from build_runs)
    await client.query('DELETE FROM asset_throughput WHERE chart_id = $1', [chartId])
    await client.query('DELETE FROM build_runs WHERE chart_id = $1', [chartId])

    // Pyramid + chart
    await client.query('DELETE FROM pyramid_layers WHERE chart_id = $1', [chartId])
    await client.query('DELETE FROM chart_grants WHERE chart_id = $1', [chartId])
    await client.query('DELETE FROM charts WHERE id = $1', [chartId])

    await client.query('COMMIT')
  } catch (err) {
    // A connection that cannot even roll back is not returned to the pool.
    try {
      await client.query('ROLLBACK')
    } catch {
      discard = true
    }
    console.error('[DELETE /api/charts/:id] rollback', err)
    return NextResponse.json({ error: 'Delete failed' }, { status: 500 })
  } finally {
    if (discard) client.release(true)
    else client.release()
  }

  return NextResponse.json({ deleted: true, chart_id: chartId }, { status: 200 })
}

/**
 * PATCH /api/charts/[id] — correct a chart's details (Jātaka chart workspace).
 *
 * Owner/super-admin only (`write`; a view grant or an absent chart gets the same
 * non-enumerating 403). The server validates, normalises and classifies the
 * change; a computation-affecting correction keeps the chart UUID and grants,
 * archives prior conversations read-only, invalidates old derived data and
 * starts one full recomputation. Every failure carries a stable `code`.
 */
export async function PATCH(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const user = await getServerUser()
  if (!user) {
    return NextResponse.json({ error: 'Authentication required', code: 'UNAUTHENTICATED' }, { status: 401 })
  }
  const { id: chartId } = await params
  const denied = await requireChartPermission({ uid: user.uid, chartId, access: 'write' })
  if (denied) return denied

  let input: unknown
  try {
    input = await req.json()
  } catch {
    return NextResponse.json(
      { error: 'Request body must be JSON.', code: 'VALIDATION_FAILED', fields: { body: 'Invalid JSON' } },
      { status: 422 },
    )
  }

  try {
    const result = await updateChartAndMaybeRecompute({ chartId, principalId: user.uid, input })
    if (result.mode === 'needs-rebuild') {
      return NextResponse.json(
        { error: 'Chart details were saved, but the rebuild did not start.', code: 'JOB_DISPATCH_FAILED', data: result },
        { status: 503 },
      )
    }
    return NextResponse.json({ data: result }, { status: result.mode === 'recompute-started' ? 202 : 200 })
  } catch (error) {
    if (error instanceof ChartUpdateError) {
      return NextResponse.json(
        { error: error.message, code: error.code, ...(error.fields ? { fields: error.fields } : {}) },
        { status: error.status },
      )
    }
    console.error('[PATCH /api/charts/:id] unexpected failure', error)
    return NextResponse.json(
      { error: 'Chart correction could not be prepared; nothing was changed.', code: 'RECOMPUTE_PREPARATION_FAILED' },
      { status: 500 },
    )
  }
}
