import 'server-only'
import { NextResponse } from 'next/server'
import { res } from '@/lib/errors'
import { guardAiopsRoute } from '@/app/api/admin/aiops/_guard'
import { stackSchema, callTypeSchema, routingOverrideBodySchema } from '@/app/api/admin/aiops/_parse'
import { STACK_ROUTING } from '@/lib/models/registry'
import { query } from '@/lib/db/client'
import { invalidateRuntimeConfigCache } from '@/lib/models/runtime_config'

export const dynamic = 'force-dynamic'

type Params = { stack: string; call_type: string }

// PUT /api/admin/aiops/routing/[stack]/[call_type]
export async function PUT(req: Request, { params }: { params: Params }) {
  const guard = await guardAiopsRoute()
  if (guard instanceof NextResponse) return guard

  const stackParsed = stackSchema.safeParse(params.stack)
  if (!stackParsed.success) return res.badRequest(`Unknown stack: ${params.stack}`)
  const ctParsed = callTypeSchema.safeParse(params.call_type)
  if (!ctParsed.success) return res.badRequest(`Unknown call_type: ${params.call_type}`)

  const stack = stackParsed.data
  const callType = ctParsed.data

  let raw: unknown
  try { raw = await req.json() } catch { return res.badRequest('Request body must be valid JSON.') }

  const bodyParsed = routingOverrideBodySchema.safeParse(raw)
  if (!bodyParsed.success) {
    return res.badRequest(`Body must include primary_model and fallback_model strings.`)
  }
  const { primary_model, fallback_model } = bodyParsed.data

  try {
    const before = STACK_ROUTING[stack]?.[callType] ?? { primary: '', fallback: '' }

    await query(
      `INSERT INTO llm_stack_routing_override
         (scope, stack, call_type, primary_model, fallback_model, updated_at, updated_by)
       VALUES ('global', $1, $2, $3, $4, NOW(), $5)
       ON CONFLICT (scope, stack, call_type)
         DO UPDATE SET primary_model=$3, fallback_model=$4, updated_at=NOW(), updated_by=$5`,
      [stack, callType, primary_model, fallback_model, guard.user.uid],
    )

    await query(
      `INSERT INTO llm_config_audit
         (occurred_at, actor_user_id, action, scope, stack, call_type, before_value, after_value)
       VALUES (NOW(), $1, 'set_routing', 'global', $2, $3, $4::jsonb, $5::jsonb)`,
      [
        guard.user.uid,
        stack,
        callType,
        JSON.stringify(before),
        JSON.stringify({ primary_model, fallback_model }),
      ],
    )

    invalidateRuntimeConfigCache()

    return NextResponse.json({ stack, call_type: callType, primary_model, fallback_model })
  } catch (err) {
    console.error('[aiops/routing] PUT error:', err)
    return res.internal('Failed to update routing override.')
  }
}

// DELETE /api/admin/aiops/routing/[stack]/[call_type]
export async function DELETE(_req: Request, { params }: { params: Params }) {
  const guard = await guardAiopsRoute()
  if (guard instanceof NextResponse) return guard

  const stackParsed = stackSchema.safeParse(params.stack)
  if (!stackParsed.success) return res.badRequest(`Unknown stack: ${params.stack}`)
  const ctParsed = callTypeSchema.safeParse(params.call_type)
  if (!ctParsed.success) return res.badRequest(`Unknown call_type: ${params.call_type}`)

  const stack = stackParsed.data
  const callType = ctParsed.data

  try {
    await query(
      `DELETE FROM llm_stack_routing_override WHERE scope='global' AND stack=$1 AND call_type=$2`,
      [stack, callType],
    )

    await query(
      `INSERT INTO llm_config_audit
         (occurred_at, actor_user_id, action, scope, stack, call_type, notes)
       VALUES (NOW(), $1, 'reset_routing', 'global', $2, $3, 'Reset to registry default')`,
      [guard.user.uid, stack, callType],
    )

    invalidateRuntimeConfigCache()

    const registryDefault = STACK_ROUTING[stack]?.[callType] ?? { primary: '', fallback: '' }
    return NextResponse.json({ stack, call_type: callType, effective: registryDefault, source: 'registry' })
  } catch (err) {
    console.error('[aiops/routing] DELETE error:', err)
    return res.internal('Failed to reset routing override.')
  }
}
