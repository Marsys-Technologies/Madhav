import Link from 'next/link'
import { STACK_ROUTING, type ModelStack, type CallType } from '@/lib/models/registry'
import { StackPickerCards } from '@/lib/components/aiops/StackPickerCards'
import { InteractiveCallTypeRow } from '@/lib/components/aiops/InteractiveCallTypeRow'
import { StackSmokeButton } from '@/lib/components/aiops/StackSmokeButton'
import { DirtyRowsProvider } from '@/lib/components/aiops/DirtyRowsContext'
import { STACK_DISPLAY } from '@/lib/components/aiops/displayNames'
import { query } from '@/lib/db/client'
import type { LlmStackConfigRow, LlmStackRoutingOverrideRow } from '@/lib/db/schema/aiops'

export const dynamic = 'force-dynamic'

const VALID_STACKS: ModelStack[] = ['gemini', 'nim', 'deepseek', 'gpt', 'anthropic', 'marsys']

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

export default async function AiopsControlPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>
}) {
  const { active_stack, routingIdx } = await fetchState()
  const params = await searchParams
  const urlStack = typeof params.stack === 'string' && VALID_STACKS.includes(params.stack as ModelStack)
    ? (params.stack as ModelStack)
    : null
  const fromObservatory = params.from === 'observatory'
  const displayStack = urlStack ?? active_stack

  return (
    <div className="aiops-shell p-6">
      <DirtyRowsProvider>
        <header className="mb-6">
          <h1 className="bt-display" style={{ color: 'var(--brand-gold-cream)' }}>AIOps Control Panel</h1>
        </header>

        {fromObservatory && (
          <div className="mb-6 flex items-center gap-2 rounded border border-border bg-card px-3 py-2 text-xs text-muted-foreground">
            Came from Observatory —{' '}
            <Link href="/observatory" className="underline hover:text-foreground">back to /observatory</Link>
          </div>
        )}

        <div className="max-w-[1080px] space-y-8">

          {/* ── Section 1: Stack Configuration ── */}
          <section className="rounded-lg border border-border">
            <div className="border-b border-border px-5 py-4">
              <h2 className="bt-heading" style={{ color: 'var(--brand-gold-cream)' }}>
                Stack Configuration
              </h2>
              <p className="mt-1 text-xs text-muted-foreground">
                Select a stack to view and edit its pipeline routing. Live queries always use the stack chosen in the composer.
              </p>
            </div>

            <div className="px-5 py-5">
              <StackPickerCards viewingStack={displayStack} />

              <div className="mt-6">
                <p className="bt-label bt-label-upper mb-3">
                  Pipeline —{' '}
                  <span style={{ color: 'var(--brand-gold)' }}>{STACK_DISPLAY[displayStack]}</span>
                </p>
                <div className="rounded-lg border border-border bg-card px-4">
                  {PIPELINE_CALL_TYPES.map(ct => {
                    const { primary, fallback } = getRouting(displayStack, ct, routingIdx)
                    return (
                      <InteractiveCallTypeRow
                        key={`${displayStack}:${ct}`}
                        stack={displayStack}
                        callType={ct}
                        initialPrimary={primary}
                        initialFallback={fallback}
                      />
                    )
                  })}
                </div>
                <StackSmokeButton stack={displayStack} />
              </div>
            </div>
          </section>

          {/* ── Section 2: System Configuration ── */}
          <section className="rounded-lg border border-border">
            <div className="border-b border-border px-5 py-4">
              <h2 className="bt-heading" style={{ color: 'var(--brand-gold-cream)' }}>
                System Configuration
              </h2>
              <p className="mt-1 text-xs text-muted-foreground">
                Cross-stack quality and verification models — shared across all stacks.
              </p>
            </div>

            <div className="px-5 py-5">
              <div className="rounded-lg border border-border bg-card px-4">
                {QUALITY_CALL_TYPES.map(ct => {
                  const { primary, fallback } = getRouting('marsys', ct, routingIdx)
                  return (
                    <InteractiveCallTypeRow
                      key={ct}
                      stack="marsys"
                      callType={ct}
                      initialPrimary={primary}
                      initialFallback={fallback}
                    />
                  )
                })}
              </div>
            </div>
          </section>

        </div>
      </DirtyRowsProvider>
    </div>
  )
}
