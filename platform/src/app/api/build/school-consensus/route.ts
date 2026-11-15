/**
 * POST /api/build/school-consensus
 * Task C (U4): Runs the 7-school triangulation engine for a chart and persists
 * the convergence results to school_analysis_runs + convergence_scores + school_disagreements.
 *
 * Auth: super_admin only (write path touches the four school consensus tables).
 * Idempotency: delete-then-insert per chart_id (§N.3 L4+).
 *
 * Body: { chart_id: string, ayanamsha_id?: string }
 *   ayanamsha_id: omitted = lahiri_chitrapaksha (primary, N-339); short ids are normalised
 *   by the PR-1 helper; unknown ids and "all" are HTTP 400 (the engines read one ayanamsha).
 * Returns: { ok: true, domains: 5, analysis_rows: 35, convergence_rows: 5 }
 */
import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { runAndPersistSchoolConsensus } from '@/lib/schools/consensusCommand'
import { PRIMARY_AYANAMSHA, resolveAyanamshaArg } from '@/lib/retrieval/chart_facts_helpers'

async function requireSuperAdmin(): Promise<boolean> {
  const user = await getServerUser()
  if (!user) return false
  const { rows } = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id = $1',
    [user.uid],
  )
  return rows[0]?.role === 'super_admin'
}

export async function POST(req: NextRequest) {
  const ok = await requireSuperAdmin()
  if (!ok) return NextResponse.json({ error: 'Forbidden' }, { status: 403 })

  const body = await req.json().catch(() => null)
  if (!body?.chart_id) {
    return NextResponse.json({ error: 'chart_id required' }, { status: 400 })
  }

  const { chart_id, ayanamsha_id: rawAyanamsha } = body as {
    chart_id: string
    ayanamsha_id?: string
  }

  // Normalise at the boundary: omitted -> Lahiri (stored long id), aliases -> stored id.
  const resolved = resolveAyanamshaArg(rawAyanamsha)
  if (!resolved.ok) {
    return NextResponse.json(
      { error: resolved.message, code: 'invalid_ayanamsha_id', stored_ids: resolved.stored_ids },
      { status: 400 },
    )
  }
  if (resolved.ayanamsha_id === null) {
    return NextResponse.json(
      { error: 'school consensus runs on one ayanamsha; "all" is not valid here', code: 'invalid_ayanamsha_id' },
      { status: 400 },
    )
  }
  const ayanamsha_id: string = resolved.ayanamsha_id ?? PRIMARY_AYANAMSHA

  const { domains, analysisRows, convergenceRows, disagreementRows } =
    await runAndPersistSchoolConsensus({ chartId: chart_id, ayanamshaId: ayanamsha_id })

  return NextResponse.json({
    ok: true,
    chart_id,
    domains,
    analysis_rows: analysisRows,
    convergence_rows: convergenceRows,
    disagreement_rows: disagreementRows,
  })
}
