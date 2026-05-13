import 'server-only'
import { NextResponse } from 'next/server'
import { res } from '@/lib/errors'
import { guardAiopsRoute } from '@/app/api/admin/aiops/_guard'
import { stackSchema, VALID_STACKS } from '@/app/api/admin/aiops/_parse'
import { query } from '@/lib/db/client'
import { invalidateRuntimeConfigCache } from '@/lib/models/runtime_config'

export const dynamic = 'force-dynamic'

// PUT /api/admin/aiops/stack
// Body: { active_stack: ModelStack }
export async function PUT(req: Request) {
  const guard = await guardAiopsRoute()
  if (guard instanceof NextResponse) return guard

  let raw: unknown
  try { raw = await req.json() } catch { return res.badRequest('Request body must be valid JSON.') }

  const parsed = stackSchema.safeParse((raw as Record<string, unknown>)?.active_stack)
  if (!parsed.success) {
    return res.badRequest(`active_stack must be one of: ${VALID_STACKS.join(', ')}`)
  }
  const newStack = parsed.data

  try {
    await query(
      `INSERT INTO llm_stack_config (scope, active_stack, updated_at, updated_by)
       VALUES ('global', $1, NOW(), $2)
       ON CONFLICT (scope) DO UPDATE SET active_stack = $1, updated_at = NOW(), updated_by = $2`,
      [newStack, guard.user.uid],
    )

    await query(
      `INSERT INTO llm_config_audit (occurred_at, actor_user_id, action, scope, stack, before_value, after_value)
       VALUES (NOW(), $1, 'set_active_stack', 'global', $2, NULL, $3::jsonb)`,
      [guard.user.uid, newStack, JSON.stringify({ active_stack: newStack })],
    )

    invalidateRuntimeConfigCache()

    return NextResponse.json({ active_stack: newStack })
  } catch (err) {
    console.error('[aiops/stack] PUT error:', err)
    return res.internal('Failed to update active stack.')
  }
}
