import { NextResponse } from 'next/server'
import { query } from '@/lib/db/client'
import { guardPerformanceRoute } from '../../_guard'

export async function GET(_request: Request, ctx: { params: Promise<{ id: string }> }) {
  const auth = await guardPerformanceRoute()
  if (auth instanceof NextResponse) return auth

  const { id } = await ctx.params
  try {
    const run = (
      await query(`SELECT * FROM eval_runs WHERE id = $1`, [id])
    ).rows[0]
    if (!run) return NextResponse.json({ error: 'not_found' }, { status: 404 })

    const summary = (
      await query<{
        n: string
        correct: string
        wrong: string
        ambiguous: string
        success: string
        failure: string
        verdict_pass: string
        verdict_warn: string
        verdict_fail: string
      }>(
        `SELECT
          COUNT(*) AS n,
          COUNT(*) FILTER (WHERE plan_accuracy_label = 'correct')   AS correct,
          COUNT(*) FILTER (WHERE plan_accuracy_label = 'wrong')     AS wrong,
          COUNT(*) FILTER (WHERE plan_accuracy_label = 'ambiguous') AS ambiguous,
          COUNT(*) FILTER (WHERE synthesis_status = 'success')      AS success,
          COUNT(*) FILTER (WHERE synthesis_status = 'failure')      AS failure,
          COUNT(*) FILTER (WHERE validator_verdict = 'pass')        AS verdict_pass,
          COUNT(*) FILTER (WHERE validator_verdict = 'warn')        AS verdict_warn,
          COUNT(*) FILTER (WHERE validator_verdict = 'fail')        AS verdict_fail
        FROM performance_queries WHERE eval_run_id = $1`,
        [id]
      )
    ).rows[0]

    return NextResponse.json({
      run,
      queries_summary: {
        n: Number(summary.n),
        by_plan_accuracy: {
          correct: Number(summary.correct),
          wrong: Number(summary.wrong),
          ambiguous: Number(summary.ambiguous),
        },
        by_synthesis_status: {
          success: Number(summary.success),
          failure: Number(summary.failure),
        },
        by_validator_verdict: {
          pass: Number(summary.verdict_pass),
          warn: Number(summary.verdict_warn),
          fail: Number(summary.verdict_fail),
        },
      },
    })
  } catch (err) {
    console.error('[api/performance/eval-runs/[id]] failed', err)
    return NextResponse.json({ error: 'eval_run_detail_failed' }, { status: 500 })
  }
}
