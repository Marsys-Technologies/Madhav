import 'server-only'
import { NextResponse } from 'next/server'
import { res } from '@/lib/errors'
import { guardAiopsRoute } from '@/app/api/admin/aiops/_guard'
import { query } from '@/lib/db/client'
import type { LlmConfigAuditRow } from '@/lib/db/schema/aiops'

export const dynamic = 'force-dynamic'

// GET /api/admin/aiops/audit?limit=20
export async function GET(req: Request) {
  const guard = await guardAiopsRoute()
  if (guard instanceof NextResponse) return guard

  const url = new URL(req.url)
  const limitRaw = url.searchParams.get('limit') ?? '20'
  const limit = Math.min(Math.max(parseInt(limitRaw, 10) || 20, 1), 100)

  try {
    const result = await query<LlmConfigAuditRow>(
      `SELECT id, occurred_at, actor_user_id, action, scope, stack, call_type, param_name,
              before_value, after_value, notes
       FROM llm_config_audit
       ORDER BY occurred_at DESC
       LIMIT $1`,
      [limit],
    )
    return NextResponse.json({ rows: result.rows, count: result.rows.length })
  } catch (err) {
    console.error('[aiops/audit] GET error:', err)
    return res.internal('Failed to fetch audit log.')
  }
}
