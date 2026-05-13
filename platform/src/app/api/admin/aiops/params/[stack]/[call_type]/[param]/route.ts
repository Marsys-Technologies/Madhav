import 'server-only'
import { NextResponse } from 'next/server'
import { res } from '@/lib/errors'
import { guardAiopsRoute } from '@/app/api/admin/aiops/_guard'
import { stackSchema, callTypeSchema } from '@/app/api/admin/aiops/_parse'
import { query } from '@/lib/db/client'
import { invalidateRuntimeConfigCache } from '@/lib/models/runtime_config'
import { z } from 'zod'

export const dynamic = 'force-dynamic'

type Params = { stack: string; call_type: string; param: string }

const VALID_PARAMS = ['max_output_tokens', 'temperature', 'thinkingBudget', 'timeout_ms'] as const
type ParamName = typeof VALID_PARAMS[number]
const paramNameSchema = z.enum(VALID_PARAMS)

const paramValueSchema = z.union([z.number(), z.boolean(), z.string()])

// PUT /api/admin/aiops/params/[stack]/[call_type]/[param]
// Body: { param_value: number | boolean | string }
export async function PUT(req: Request, { params }: { params: Params }) {
  const guard = await guardAiopsRoute()
  if (guard instanceof NextResponse) return guard

  const stackParsed = stackSchema.safeParse(params.stack)
  if (!stackParsed.success) return res.badRequest(`Unknown stack: ${params.stack}`)
  const ctParsed = callTypeSchema.safeParse(params.call_type)
  if (!ctParsed.success) return res.badRequest(`Unknown call_type: ${params.call_type}`)
  const paramParsed = paramNameSchema.safeParse(params.param)
  if (!paramParsed.success) return res.badRequest(`Unknown param: ${params.param}. Must be one of: ${VALID_PARAMS.join(', ')}`)

  const stack = stackParsed.data
  const callType = ctParsed.data
  const paramName: ParamName = paramParsed.data

  let raw: unknown
  try { raw = await req.json() } catch { return res.badRequest('Request body must be valid JSON.') }

  const valueParsed = paramValueSchema.safeParse((raw as Record<string, unknown>)?.param_value)
  if (!valueParsed.success) return res.badRequest('param_value must be a number, boolean, or string.')
  const paramValue = valueParsed.data

  try {
    await query(
      `INSERT INTO llm_param_override (scope, stack, call_type, param_name, param_value)
       VALUES ('global', $1, $2, $3, $4::jsonb)
       ON CONFLICT (scope, stack, call_type, param_name)
         DO UPDATE SET param_value = $4::jsonb`,
      [stack, callType, paramName, JSON.stringify(paramValue)],
    )

    await query(
      `INSERT INTO llm_config_audit
         (occurred_at, actor_user_id, action, scope, stack, call_type, param_name, after_value)
       VALUES (NOW(), $1, 'set_param', 'global', $2, $3, $4, $5::jsonb)`,
      [guard.user.uid, stack, callType, paramName, JSON.stringify(paramValue)],
    )

    invalidateRuntimeConfigCache()

    return NextResponse.json({ stack, call_type: callType, param_name: paramName, param_value: paramValue })
  } catch (err) {
    console.error('[aiops/params] PUT error:', err)
    return res.internal('Failed to update param override.')
  }
}

// DELETE /api/admin/aiops/params/[stack]/[call_type]/[param]
export async function DELETE(_req: Request, { params }: { params: Params }) {
  const guard = await guardAiopsRoute()
  if (guard instanceof NextResponse) return guard

  const stackParsed = stackSchema.safeParse(params.stack)
  if (!stackParsed.success) return res.badRequest(`Unknown stack: ${params.stack}`)
  const ctParsed = callTypeSchema.safeParse(params.call_type)
  if (!ctParsed.success) return res.badRequest(`Unknown call_type: ${params.call_type}`)
  const paramParsed = paramNameSchema.safeParse(params.param)
  if (!paramParsed.success) return res.badRequest(`Unknown param: ${params.param}`)

  const stack = stackParsed.data
  const callType = ctParsed.data
  const paramName = paramParsed.data

  try {
    await query(
      `DELETE FROM llm_param_override
       WHERE scope='global' AND stack=$1 AND call_type=$2 AND param_name=$3`,
      [stack, callType, paramName],
    )

    await query(
      `INSERT INTO llm_config_audit
         (occurred_at, actor_user_id, action, scope, stack, call_type, param_name, notes)
       VALUES (NOW(), $1, 'reset_param', 'global', $2, $3, $4, 'Reset to default')`,
      [guard.user.uid, stack, callType, paramName],
    )

    invalidateRuntimeConfigCache()

    return NextResponse.json({ stack, call_type: callType, param_name: paramName, source: 'default' })
  } catch (err) {
    console.error('[aiops/params] DELETE error:', err)
    return res.internal('Failed to reset param override.')
  }
}
