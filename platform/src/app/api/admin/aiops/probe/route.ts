import 'server-only'
import { NextResponse } from 'next/server'
import { res } from '@/lib/errors'
import { guardAiopsRoute } from '@/app/api/admin/aiops/_guard'
import { stackSchema, callTypeSchema } from '@/app/api/admin/aiops/_parse'
import { runProbe } from '@/lib/aiops/probe/runner'
import { z } from 'zod'

export const dynamic = 'force-dynamic'

const probeBodySchema = z.object({
  stack:          stackSchema,
  call_type:      callTypeSchema,
  role:           z.enum(['primary', 'fallback']),
  model_override: z.string().optional(),
})

// POST /api/admin/aiops/probe
// Returns ProbeResult as JSON (not streaming for CP.2; streaming optional)
export async function POST(req: Request) {
  const guard = await guardAiopsRoute()
  if (guard instanceof NextResponse) return guard

  let raw: unknown
  try { raw = await req.json() } catch { return res.badRequest('Request body must be valid JSON.') }

  const parsed = probeBodySchema.safeParse(raw)
  if (!parsed.success) {
    return res.badRequest(`Invalid probe request: ${parsed.error.issues.map(i => i.message).join('; ')}`)
  }

  const { stack, call_type: callType, role, model_override: modelOverride } = parsed.data

  const result = await runProbe({ stack, callType, role, modelOverride })
  return NextResponse.json(result)
}
