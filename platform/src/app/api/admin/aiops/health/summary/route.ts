import 'server-only'
import { NextResponse } from 'next/server'
import { res } from '@/lib/errors'
import { query } from '@/lib/db/client'
import type {
  LlmModelHealthRow,
  LlmStackRoutingOverrideRow,
  AiopsModelHealthStatus,
} from '@/lib/db/schema/aiops'
import { STACK_ROUTING, type ModelStack, type CallType } from '@/lib/models/registry'
import { guardAiopsRoute } from '@/app/api/admin/aiops/_guard'

export const dynamic = 'force-dynamic'

interface HealthCounts {
  green: number
  red:   number
  amber: number
  dim:   number
  total: number
}

const STACKS: ModelStack[] = ['gemini', 'nim', 'deepseek', 'gpt', 'anthropic', 'marsys']

function bucketFor(status: AiopsModelHealthStatus | null | undefined): keyof Omit<HealthCounts, 'total'> {
  switch (status) {
    case 'pass':         return 'green'
    case 'fail':
    case 'timeout':      return 'red'
    case 'stale':        return 'amber'
    case 'never_probed':
    default:             return 'dim'
  }
}

export async function GET() {
  const guard = await guardAiopsRoute()
  if (guard instanceof NextResponse) return guard

  // 1. Gather routing overrides per stack
  let overrides: LlmStackRoutingOverrideRow[] = []
  let healthRows: LlmModelHealthRow[] = []
  try {
    const [ovr, hr] = await Promise.all([
      query<LlmStackRoutingOverrideRow>(`SELECT * FROM llm_stack_routing_override WHERE scope = 'global'`),
      query<LlmModelHealthRow>(`SELECT * FROM llm_model_health`),
    ])
    overrides = ovr.rows
    healthRows = hr.rows
  } catch {
    return res.dbError()
  }

  const healthByModel = new Map<string, AiopsModelHealthStatus>()
  for (const h of healthRows) healthByModel.set(h.model_id, h.status)

  // 2. For each stack, build the effective model set (primary + fallback across all call types)
  const summary: Record<string, HealthCounts> = {}
  for (const stack of STACKS) {
    const modelIds = new Set<string>()
    const baseline = STACK_ROUTING[stack] ?? {}
    for (const ct of Object.keys(baseline) as CallType[]) {
      const r = baseline[ct]
      if (r?.primary)  modelIds.add(r.primary)
      if (r?.fallback) modelIds.add(r.fallback)
    }
    for (const ovr of overrides) {
      if (ovr.stack !== stack) continue
      if (ovr.primary_model)  modelIds.add(ovr.primary_model)
      if (ovr.fallback_model) modelIds.add(ovr.fallback_model)
    }

    const counts: HealthCounts = { green: 0, red: 0, amber: 0, dim: 0, total: modelIds.size }
    for (const id of modelIds) {
      const status = healthByModel.get(id)
      counts[bucketFor(status)] += 1
    }
    summary[stack] = counts
  }

  return Response.json(summary, {
    headers: { 'cache-control': 'private, max-age=15' },
  })
}
