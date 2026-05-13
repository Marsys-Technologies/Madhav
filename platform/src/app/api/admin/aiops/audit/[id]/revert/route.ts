import 'server-only'
import { NextResponse } from 'next/server'
import { res } from '@/lib/errors'
import { guardAiopsRoute } from '@/app/api/admin/aiops/_guard'
import { query } from '@/lib/db/client'
import { invalidateRuntimeConfigCache } from '@/lib/models/runtime_config'
import type { LlmConfigAuditRow } from '@/lib/db/schema/aiops'

export const dynamic = 'force-dynamic'

export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const guard = await guardAiopsRoute()
  if (guard instanceof NextResponse) return guard

  const { id } = await params
  const auditId = parseInt(id, 10)
  if (isNaN(auditId)) return res.badRequest('Invalid audit id')

  let auditRow: LlmConfigAuditRow
  try {
    const result = await query<LlmConfigAuditRow>(
      `SELECT * FROM llm_config_audit WHERE id = $1`,
      [auditId],
    )
    if (result.rows.length === 0) return res.notFound('audit entry')
    auditRow = result.rows[0]
  } catch {
    return res.dbError()
  }

  const { action, stack, call_type, param_name, before_value } = auditRow

  try {
    if (action === 'set_stack') {
      const beforeStack = (before_value as { active_stack?: string } | null)?.active_stack
      if (!beforeStack) return res.badRequest('No before_value to revert to')
      await query(
        `INSERT INTO llm_stack_config (scope, active_stack, updated_at, updated_by)
         VALUES ('global', $1, NOW(), $2)
         ON CONFLICT (scope) DO UPDATE SET active_stack = $1, updated_at = NOW(), updated_by = $2`,
        [beforeStack, guard.user.uid],
      )
      invalidateRuntimeConfigCache()

    } else if (action === 'set_routing' || action === 'reset_routing') {
      if (!stack || !call_type) return res.badRequest('Missing stack/call_type for routing revert')
      const before = before_value as { primary?: string; fallback?: string } | null
      if (before?.primary) {
        await query(
          `INSERT INTO llm_stack_routing_override (scope, stack, call_type, primary_model, fallback_model, updated_at, updated_by)
           VALUES ('global', $1, $2, $3, $4, NOW(), $5)
           ON CONFLICT (scope, stack, call_type) DO UPDATE SET primary_model=$3, fallback_model=$4, updated_at=NOW(), updated_by=$5`,
          [stack, call_type, before.primary, before.fallback ?? '', guard.user.uid],
        )
      } else {
        await query(
          `DELETE FROM llm_stack_routing_override WHERE scope='global' AND stack=$1 AND call_type=$2`,
          [stack, call_type],
        )
      }
      invalidateRuntimeConfigCache()

    } else if (action === 'set_param' || action === 'reset_param') {
      if (!stack || !call_type || !param_name) return res.badRequest('Missing fields for param revert')
      const beforeParam = (before_value as { param_value?: unknown } | null)?.param_value
      if (beforeParam !== undefined && beforeParam !== null) {
        await query(
          `INSERT INTO llm_param_override (scope, stack, call_type, param_name, param_value, updated_at, updated_by)
           VALUES ('global', $1, $2, $3, $4::jsonb, NOW(), $5)
           ON CONFLICT (scope, stack, call_type, param_name) DO UPDATE SET param_value=$4::jsonb, updated_at=NOW(), updated_by=$5`,
          [stack, call_type, param_name, JSON.stringify(beforeParam), guard.user.uid],
        )
      } else {
        await query(
          `DELETE FROM llm_param_override WHERE scope='global' AND stack=$1 AND call_type=$2 AND param_name=$3`,
          [stack, call_type, param_name],
        )
      }
      invalidateRuntimeConfigCache()

    } else {
      return res.badRequest(`Action '${action}' is not revertible`)
    }

    await query(
      `INSERT INTO llm_config_audit (occurred_at, actor_user_id, action, scope, stack, call_type, param_name, notes)
       VALUES (NOW(), $1, 'revert', 'global', $2, $3, $4, $5)`,
      [guard.user.uid, stack, call_type, param_name, `reverted audit id ${auditId}`],
    )

    return NextResponse.json({ reverted: auditId })
  } catch (err) {
    console.error('[aiops/audit/revert] error:', err)
    return res.internal('Revert failed.')
  }
}
