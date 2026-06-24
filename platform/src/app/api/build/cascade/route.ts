/**
 * GET /api/build/cascade?asset_id=A2&chart_id=<uuid>
 *
 * Returns the ordered list of downstream asset_ids that would be invalidated
 * and requeued if asset_id is rebuilt. Uses the static build_dependencies
 * table — no build_steps query needed.
 *
 * Algorithm: forward-reachability BFS on the depends_on DAG.
 * A node X is downstream of asset_id if any path from asset_id reaches X
 * following the "X depends_on Y → Y is upstream of X" direction.
 */

import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

interface DepRow {
  asset_id: string
  depends_on: string[]
  display_name: string | null
  sort_order: number
  layer: string
}

export async function GET(request: Request): Promise<Response> {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const { searchParams } = new URL(request.url)
  const asset_id = searchParams.get('asset_id')
  const chart_id = searchParams.get('chart_id') // accepted for context; not used in DAG query

  if (!asset_id) {
    return NextResponse.json({ error: 'asset_id is required' }, { status: 400 })
  }

  // ── Load full dependency graph ─────────────────────────────────────────────
  let rows: DepRow[]
  try {
    const result = await query<DepRow>(
      `SELECT asset_id, depends_on, display_name, sort_order, layer
         FROM build_dependencies
        ORDER BY sort_order ASC`,
    )
    rows = result.rows
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    if (msg.includes('does not exist')) {
      return NextResponse.json({
        asset_id,
        chart_id,
        downstream: [],
        total_affected: 0,
        note: 'build_dependencies table absent — migration 158 not yet applied',
      })
    }
    throw err
  }

  if (rows.length === 0) {
    return NextResponse.json({ asset_id, chart_id, downstream: [], total_affected: 0 })
  }

  // ── Build forward adjacency: asset → [assets that depend on it] ───────────
  const forward = new Map<string, string[]>()
  for (const row of rows) {
    if (!forward.has(row.asset_id)) forward.set(row.asset_id, [])
    for (const dep of row.depends_on) {
      if (!forward.has(dep)) forward.set(dep, [])
      forward.get(dep)!.push(row.asset_id)
    }
  }

  // ── BFS from asset_id to find all transitively downstream assets ──────────
  const visited = new Set<string>([asset_id])
  const queue = [asset_id]
  while (queue.length > 0) {
    const current = queue.shift()!
    for (const next of forward.get(current) ?? []) {
      if (!visited.has(next)) {
        visited.add(next)
        queue.push(next)
      }
    }
  }
  visited.delete(asset_id) // exclude the asset being rebuilt itself

  // ── Build response ordered by sort_order ─────────────────────────────────
  const meta = new Map(rows.map((r) => [r.asset_id, r]))
  const downstream = [...visited]
    .map((id) => ({
      asset_id: id,
      display_name: meta.get(id)?.display_name ?? id,
      layer: meta.get(id)?.layer ?? '',
      sort_order: meta.get(id)?.sort_order ?? 999,
    }))
    .sort((a, b) => a.sort_order - b.sort_order)

  return NextResponse.json({
    asset_id,
    chart_id,
    downstream,
    total_affected: downstream.length,
  })
}
