import 'server-only'
import { NextResponse } from 'next/server'
import { guardPerformanceRoute } from '../_guard'
import { getConflictSummary } from '@/lib/performance/conflict_summary'

// ─────────────────────────────────────────────────────────────────────────────
// Route
// ─────────────────────────────────────────────────────────────────────────────

export async function GET(): Promise<NextResponse> {
  const auth = await guardPerformanceRoute()
  if (auth instanceof NextResponse) return auth

  try {
    const repoRoot = process.cwd()
    const report = getConflictSummary(repoRoot)
    return NextResponse.json(report)
  } catch (err) {
    console.error('[api/performance/conflict-summary] failed', err)
    return NextResponse.json({ error: 'conflict_summary_failed' }, { status: 500 })
  }
}
