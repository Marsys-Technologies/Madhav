import { NextResponse } from 'next/server'
import { query } from '@/lib/db/client'
import { guardPerformanceRoute, parseSource, parseTimeWindow } from '../_guard'

export async function GET(request: Request) {
  const auth = await guardPerformanceRoute()
  if (auth instanceof NextResponse) return auth

  const url = new URL(request.url)
  const win = parseTimeWindow(url)
  if ('error' in win) return NextResponse.json({ error: win.error }, { status: 400 })
  const source = parseSource(url)

  const evalRunId = url.searchParams.get('eval_run_id')
  const queryClasses = url.searchParams.getAll('query_class')
  const validatorVerdicts = url.searchParams.getAll('validator_verdict')
  const planLabels = url.searchParams.getAll('plan_accuracy_label')
  const b10 = url.searchParams.get('b10_violation')
  const b11 = url.searchParams.get('b11_violation')

  const page = Math.max(1, Number(url.searchParams.get('page') ?? '1') || 1)
  const pageSize = Math.min(
    200,
    Math.max(1, Number(url.searchParams.get('page_size') ?? '50') || 50)
  )

  const params: unknown[] = [win.start, win.end]
  const clauses: string[] = [`pq.created_at BETWEEN $1 AND $2`]

  if (source !== 'all') {
    params.push(source)
    clauses.push(`pq.source = $${params.length}`)
  }
  if (evalRunId) {
    params.push(evalRunId)
    clauses.push(`pq.eval_run_id = $${params.length}`)
  }
  if (queryClasses.length > 0) {
    params.push(queryClasses)
    clauses.push(`pq.query_class = ANY($${params.length})`)
  }
  if (validatorVerdicts.length > 0) {
    params.push(validatorVerdicts)
    clauses.push(`pq.validator_verdict = ANY($${params.length})`)
  }
  if (planLabels.length > 0) {
    params.push(planLabels)
    clauses.push(`pq.plan_accuracy_label = ANY($${params.length})`)
  }
  if (b10 === 'true' || b10 === 'false') {
    params.push(b10 === 'true')
    clauses.push(`pq.b10_violation = $${params.length}`)
  }
  if (b11 === 'true' || b11 === 'false') {
    params.push(b11 === 'true')
    clauses.push(`pq.b11_violation = $${params.length}`)
  }

  const whereSql = clauses.join(' AND ')

  try {
    const totalRow = (
      await query<{ total: string }>(
        `SELECT COUNT(*) AS total FROM performance_queries pq WHERE ${whereSql}`,
        params
      )
    ).rows[0]
    const total = Number(totalRow.total)

    const offset = (page - 1) * pageSize
    const rowsParams = [...params, pageSize, offset]
    const rows = (
      await query(
        `SELECT
          pq.*,
          (
            SELECT json_build_object(
              'verdict', pjv.planner_verdict,
              'reasoning', pjv.planner_reasoning,
              'model', pjv.judge_model,
              'created_at', pjv.created_at
            )
            FROM performance_judge_verdict pjv
            WHERE pjv.performance_query_id = pq.id
            ORDER BY pjv.created_at DESC
            LIMIT 1
          ) AS judge_verdict_summary
        FROM performance_queries pq
        WHERE ${whereSql}
        ORDER BY pq.created_at DESC
        LIMIT $${params.length + 1} OFFSET $${params.length + 2}`,
        rowsParams
      )
    ).rows

    return NextResponse.json({ page, page_size: pageSize, total, rows })
  } catch (err) {
    console.error('[api/performance/queries] failed', err)
    return NextResponse.json({ error: 'query_log_failed' }, { status: 500 })
  }
}
