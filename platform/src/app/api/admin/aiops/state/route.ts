import 'server-only'
import { NextResponse } from 'next/server'
import { guardAiopsRoute } from '@/app/api/admin/aiops/_guard'
import { STACK_ROUTING, type ModelStack, type CallType } from '@/lib/models/registry'
import { query } from '@/lib/db/client'
import type { LlmStackConfigRow, LlmStackRoutingOverrideRow, LlmParamOverrideRow, LlmModelHealthRow, LlmConfigAuditRow } from '@/lib/db/schema/aiops'

export const dynamic = 'force-dynamic'

export async function GET(_req: Request) {
  const guard = await guardAiopsRoute()
  if (guard instanceof NextResponse) return guard

  try {
    // Fetch all state from DB in parallel
    const [stackRows, routingRows, paramRows, healthRows, auditRows] = await Promise.all([
      query<LlmStackConfigRow>(`SELECT * FROM llm_stack_config WHERE scope = 'global' LIMIT 1`),
      query<LlmStackRoutingOverrideRow>(`SELECT * FROM llm_stack_routing_override WHERE scope = 'global'`),
      query<LlmParamOverrideRow>(`SELECT * FROM llm_param_override WHERE scope = 'global'`),
      query<LlmModelHealthRow>(`SELECT * FROM llm_model_health`),
      query<Pick<LlmConfigAuditRow, 'id' | 'occurred_at'>>(`SELECT id, occurred_at FROM llm_config_audit ORDER BY occurred_at DESC LIMIT 1`),
    ])

    const active_stack = (stackRows.rows[0]?.active_stack ?? 'gemini') as ModelStack

    // Build effective routing: registry defaults merged with DB overrides
    const stacks: ModelStack[] = ['nim', 'anthropic', 'gemini', 'gpt', 'deepseek', 'marsys']
    const callTypes: CallType[] = [
      'synthesis', 'planner_deep', 'planner_fast', 'context_assembly', 'worker',
      'eval_judge', 'eval_generator', 'smoke_synth', 'checkpoint_4_5', 'checkpoint_5_5', 'checkpoint_8_5',
    ]

    // Index DB routing overrides
    const routingIdx: Record<string, Record<string, { primary: string; fallback: string }>> = {}
    for (const row of routingRows.rows) {
      if (!routingIdx[row.stack]) routingIdx[row.stack] = {}
      routingIdx[row.stack][row.call_type] = { primary: row.primary_model, fallback: row.fallback_model }
    }

    const effective_routing: Record<string, Record<string, { primary: string; fallback: string }>> = {}
    for (const stack of stacks) {
      effective_routing[stack] = {}
      for (const ct of callTypes) {
        effective_routing[stack][ct] = routingIdx[stack]?.[ct] ?? STACK_ROUTING[stack]?.[ct] ?? { primary: '', fallback: '' }
      }
    }

    // Build effective params
    const effective_params: Record<string, Record<string, Record<string, unknown>>> = {}
    for (const row of paramRows.rows) {
      if (!effective_params[row.stack]) effective_params[row.stack] = {}
      if (!effective_params[row.stack][row.call_type]) effective_params[row.stack][row.call_type] = {}
      effective_params[row.stack][row.call_type][row.param_name] = row.param_value
    }

    // Build health summary
    const health_summary: Record<string, string> = {}
    for (const row of healthRows.rows) {
      health_summary[row.model_id] = row.status
    }

    const auditCount = await query<{ count: string }>(`SELECT COUNT(*)::text AS count FROM llm_config_audit`)
    const latestAudit = auditRows.rows[0]?.occurred_at ?? null

    return NextResponse.json({
      active_stack,
      effective_routing,
      effective_params,
      health_summary,
      audit_summary: {
        count:     parseInt(auditCount.rows[0]?.count ?? '0', 10),
        latest_at: latestAudit,
      },
    })
  } catch (err) {
    console.error('[aiops/state] GET error:', err)
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Failed to fetch AIOps state.' } },
      { status: 500 },
    )
  }
}
