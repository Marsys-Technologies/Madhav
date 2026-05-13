import 'server-only'
import { NextResponse } from 'next/server'
import { res } from '@/lib/errors'
import { guardAiopsRoute } from '@/app/api/admin/aiops/_guard'
import { stackSchema, VALID_CALL_TYPES } from '@/app/api/admin/aiops/_parse'
import { runProbe } from '@/lib/aiops/probe/runner'
import { query } from '@/lib/db/client'
import type { LlmStackRoutingOverrideRow } from '@/lib/db/schema/aiops'
import type { CallType } from '@/lib/models/registry'

export const dynamic = 'force-dynamic'

type Params = { stack: string }

// POST /api/admin/aiops/smoke/[stack]
// Runs probe for every (call_type × role) pair for the stack.
// For MARSYS: only probes call types that have DB overrides.
export async function POST(_req: Request, { params }: { params: Promise<Params> }) {
  const guard = await guardAiopsRoute()
  if (guard instanceof NextResponse) return guard

  const { stack: stackRaw } = await params
  const stackParsed = stackSchema.safeParse(stackRaw)
  if (!stackParsed.success) return res.badRequest(`Unknown stack: ${stackRaw}`)
  const stack = stackParsed.data

  // Determine which call types to probe
  let callTypesToProbe: CallType[] = [...VALID_CALL_TYPES]

  if (stack === 'marsys') {
    // Only probe call types with explicit DB overrides for MARSYS
    const dbRows = await query<LlmStackRoutingOverrideRow>(
      `SELECT DISTINCT call_type FROM llm_stack_routing_override WHERE scope='global' AND stack='marsys'`,
    )
    callTypesToProbe = dbRows.rows.map(r => r.call_type as CallType)
  }

  // Run all probes in parallel (primary + fallback for each call type)
  const probeJobs = callTypesToProbe.flatMap(callType =>
    (['primary', 'fallback'] as const).map(role => runProbe({ stack, callType, role })),
  )

  const results = await Promise.all(probeJobs)
  const passCount = results.filter(r => r.status === 'pass').length
  const failCount = results.filter(r => r.status !== 'pass').length

  return NextResponse.json({
    stack,
    results,
    all_pass: failCount === 0,
    summary: {
      total: results.length,
      pass:  passCount,
      fail:  failCount,
    },
  })
}
