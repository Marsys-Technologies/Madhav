import { NextResponse } from 'next/server'
import { query } from '@/lib/db/client'
import { guardPerformanceRoute } from '../_guard'

export async function GET(request: Request) {
  const auth = await guardPerformanceRoute()
  if (auth instanceof NextResponse) return auth

  const url = new URL(request.url)
  const page = Math.max(1, Number(url.searchParams.get('page') ?? '1') || 1)
  const pageSize = Math.min(100, Math.max(1, Number(url.searchParams.get('page_size') ?? '20') || 20))
  const offset = (page - 1) * pageSize

  try {
    const totalRow = (
      await query<{ total: string }>(`SELECT COUNT(*) AS total FROM eval_runs`)
    ).rows[0]
    const rows = (
      await query(
        `SELECT * FROM eval_runs ORDER BY created_at DESC LIMIT $1 OFFSET $2`,
        [pageSize, offset]
      )
    ).rows
    return NextResponse.json({ page, page_size: pageSize, total: Number(totalRow.total), rows })
  } catch (err) {
    console.error('[api/performance/eval-runs] failed', err)
    return NextResponse.json({ error: 'eval_runs_list_failed' }, { status: 500 })
  }
}
