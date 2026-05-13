import { STACK_ROUTING, type ModelStack, type CallType } from '@/lib/models/registry'
import { StackPickerCards } from '@/lib/components/aiops/StackPickerCards'
import { CallTypeRow } from '@/lib/components/aiops/CallTypeRow'
import { EmptyRightRail } from '@/lib/components/aiops/EmptyRightRail'
import { query } from '@/lib/db/client'
import type { LlmStackConfigRow, LlmStackRoutingOverrideRow } from '@/lib/db/schema/aiops'

export const dynamic = 'force-dynamic'

const PIPELINE_CALL_TYPES: CallType[] = [
  'synthesis', 'planner_deep', 'planner_fast', 'context_assembly', 'worker',
]

const QUALITY_CALL_TYPES: CallType[] = [
  'eval_judge', 'eval_generator', 'smoke_synth', 'checkpoint_4_5', 'checkpoint_5_5', 'checkpoint_8_5',
]

async function fetchState() {
  try {
    const [stackRows, routingRows] = await Promise.all([
      query<LlmStackConfigRow>(`SELECT * FROM llm_stack_config WHERE scope = 'global' LIMIT 1`),
      query<LlmStackRoutingOverrideRow>(`SELECT * FROM llm_stack_routing_override WHERE scope = 'global'`),
    ])
    const active_stack = (stackRows.rows[0]?.active_stack ?? 'gemini') as ModelStack

    const routingIdx: Record<string, Record<string, { primary: string; fallback: string }>> = {}
    for (const row of routingRows.rows) {
      if (!routingIdx[row.stack]) routingIdx[row.stack] = {}
      routingIdx[row.stack][row.call_type] = { primary: row.primary_model, fallback: row.fallback_model }
    }
    return { active_stack, routingIdx }
  } catch {
    return { active_stack: 'gemini' as ModelStack, routingIdx: {} }
  }
}

function getRouting(
  stack: ModelStack,
  callType: CallType,
  routingIdx: Record<string, Record<string, { primary: string; fallback: string }>>,
) {
  return routingIdx[stack]?.[callType] ?? STACK_ROUTING[stack]?.[callType] ?? { primary: '', fallback: '' }
}

export default async function AiopsControlPage() {
  const { active_stack, routingIdx } = await fetchState()

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold tracking-tight">AIOps Control Panel</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Read-only view — write side lands in CP.2.
      </p>

      <section className="mt-6">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Stack
        </h2>
        <StackPickerCards activeStack={active_stack} />
      </section>

      <div className="mt-8 flex gap-6">
        <div className="min-w-0 flex-1">
          <section>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Pipeline — {active_stack} stack
            </h2>
            <div className="rounded-lg border border-border bg-card px-4">
              {PIPELINE_CALL_TYPES.map(ct => {
                const { primary, fallback } = getRouting(active_stack, ct, routingIdx)
                return (
                  <CallTypeRow
                    key={ct}
                    callType={ct}
                    primaryModel={primary}
                    fallbackModel={fallback}
                  />
                )
              })}
            </div>
          </section>

          <section className="mt-6">
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Quality & Verification (cross-stack)
            </h2>
            <div className="rounded-lg border border-border bg-card px-4">
              {QUALITY_CALL_TYPES.map(ct => {
                const { primary, fallback } = getRouting(active_stack, ct, routingIdx)
                return (
                  <CallTypeRow
                    key={ct}
                    callType={ct}
                    primaryModel={primary}
                    fallbackModel={fallback}
                  />
                )
              })}
            </div>
          </section>
        </div>

        <aside className="w-64 shrink-0">
          <EmptyRightRail />
        </aside>
      </div>
    </div>
  )
}
