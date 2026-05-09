'use client'

/**
 * PipelineLifecycleView — P6 D.6.2.
 *
 * Vertical 5-stage flow over the pipeline: classify → plan → retrieve →
 * assemble → synthesize. Reads TraceStep[] (already what TracePanel feeds
 * everywhere) plus an explicit manifest tool list to compute "Available,
 * skipped" — the tools that exist but the planner did not select.
 *
 * Implementation note (P6 D.6.1 mapping table): we read what's actually
 * surfaced by the route in this codebase rather than the field names in the
 * brief. See the per-stage comments below.
 */

import { useMemo } from 'react'
import { Check, AlertCircle, MinusCircle } from 'lucide-react'
import type { TraceStep } from '@/lib/trace/types'

interface Props {
  steps: TraceStep[]
  manifestTools: string[]
}

function fmtMs(ms: number | null | undefined): string {
  if (ms == null) return '—'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

function StageIcon({ status }: { status: 'done' | 'error' | 'skipped' }) {
  if (status === 'error') {
    return <AlertCircle size={12} className="text-amber-400" aria-label="error" />
  }
  if (status === 'skipped') {
    return <MinusCircle size={12} className="text-muted-foreground" aria-label="skipped" />
  }
  return <Check size={12} className="text-[var(--brand-gold)]" aria-label="done" />
}

function StageCard({
  index,
  title,
  latencyMs,
  status,
  children,
}: {
  index: number
  title: string
  latencyMs?: number | null
  status: 'done' | 'error' | 'skipped'
  children?: React.ReactNode
}) {
  return (
    <div className="rounded border border-[rgba(212,175,55,0.12)] bg-[oklch(0.11_0.010_70)] p-3">
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-mono text-muted-foreground/70 w-4">{index}.</span>
        <span className="text-[11px] font-semibold uppercase tracking-wider text-[#fce29a]">{title}</span>
        <StageIcon status={status} />
        <span className="ml-auto text-[10px] text-muted-foreground">{fmtMs(latencyMs ?? null)}</span>
      </div>
      {children && <div className="mt-2 pl-6 text-[11px]">{children}</div>}
    </div>
  )
}

function Connector() {
  return <div className="bg-[rgba(212,175,55,0.20)] w-px h-4 mx-auto" />
}

export function PipelineLifecycleView({ steps, manifestTools }: Props) {
  // Field-name mapping (D.6.1):
  //   step_name === 'classify'         → classify stage
  //   step_name === 'plan'             → plan stage; payload.query_plan + payload.tool_calls
  //   step_type in {'sql','vector','gcs'} after plan, before context_assembly → retrieve
  //   step_name === 'context_assembly' → assemble stage (incl. short-circuit)
  //   step_name in {'synthesis_done','synthesis'} → synthesize stage
  const classifyStep = useMemo(() => steps.find(s => s.step_name === 'classify'), [steps])
  const planStep = useMemo(() => steps.find(s => s.step_name === 'plan'), [steps])
  const retrievalSteps = useMemo(
    () => steps.filter(s => s.step_type === 'sql' || s.step_type === 'vector' || s.step_type === 'gcs'),
    [steps],
  )
  const assembleStep = useMemo(() => steps.find(s => s.step_name === 'context_assembly'), [steps])
  const synthStep = useMemo(
    () => steps.find(s => s.step_name === 'synthesis_done' || s.step_name === 'synthesis'),
    [steps],
  )

  const planPayload = planStep?.payload as
    | { query_plan?: { tools_authorized?: string[]; planning_rationale?: string }; tool_calls?: Array<{ tool_id?: string; tool_name?: string }> }
    | undefined
  const planned: string[] = useMemo(() => {
    const fromCalls = planPayload?.tool_calls?.map(c => c.tool_id ?? c.tool_name).filter(Boolean) as string[] | undefined
    if (fromCalls && fromCalls.length > 0) return fromCalls
    return planPayload?.query_plan?.tools_authorized ?? []
  }, [planPayload])
  const planningRationale = planPayload?.query_plan?.planning_rationale ?? null

  const executed: string[] = useMemo(
    () => retrievalSteps.filter(s => s.status === 'done').map(s => s.step_name),
    [retrievalSteps],
  )
  const skipped: string[] = useMemo(
    () => manifestTools.filter(t => !planned.includes(t)),
    [manifestTools, planned],
  )

  const classifyStatus: 'done' | 'error' | 'skipped' =
    classifyStep?.status === 'done' ? 'done' : classifyStep?.status === 'error' ? 'error' : 'skipped'

  const assembleShortCircuited =
    !!assembleStep?.data_summary && (assembleStep.data_summary as { short_circuited?: boolean }).short_circuited === true
  const assembleStatus: 'done' | 'error' | 'skipped' =
    !assembleStep ? 'skipped' : assembleShortCircuited ? 'skipped' : assembleStep.status === 'error' ? 'error' : 'done'

  return (
    <div className="space-y-1">
      <StageCard
        index={1}
        title="Classify"
        latencyMs={classifyStep?.latency_ms ?? null}
        status={classifyStatus}
      >
        {classifyStep && (
          <div className="text-muted-foreground">
            class:{' '}
            <span className="text-foreground font-mono">
              {(classifyStep.data_summary as { query_class?: string })?.query_class ?? '—'}
            </span>
            <span className="ml-3">
              confidence:{' '}
              <span className="text-foreground">
                {((classifyStep.data_summary as { confidence?: number })?.confidence ?? 0).toFixed(2)}
              </span>
            </span>
          </div>
        )}
      </StageCard>
      <Connector />

      <StageCard
        index={2}
        title="Plan"
        latencyMs={planStep?.latency_ms ?? null}
        status={planStep ? (planStep.status === 'error' ? 'error' : 'done') : 'skipped'}
      >
        {planStep && (
          <>
            <div className="text-muted-foreground mb-1">
              Planner:{' '}
              <span className="text-foreground font-mono">
                {(planStep.data_summary as { model?: string })?.model ?? '—'}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground/80 mb-1">
                  Planned ({planned.length})
                </div>
                <ul className="space-y-0.5">
                  {planned.length === 0 ? (
                    <li className="text-muted-foreground/70 italic">none</li>
                  ) : (
                    planned.map(t => (
                      <li key={t} className="font-mono text-[11px] text-foreground">
                        • {t}
                      </li>
                    ))
                  )}
                </ul>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground/80 mb-1">
                  Available, skipped ({skipped.length})
                </div>
                <ul className="space-y-0.5">
                  {skipped.length === 0 ? (
                    <li className="text-muted-foreground/70 italic">none</li>
                  ) : (
                    skipped.map(t => (
                      <li key={t} className="font-mono text-[11px] text-muted-foreground/70">
                        • {t}
                        <span className="ml-1 italic text-[10px]">not selected</span>
                      </li>
                    ))
                  )}
                </ul>
              </div>
            </div>
            {planningRationale && (
              <details className="mt-2">
                <summary className="cursor-pointer text-[10px] text-muted-foreground/80 hover:text-foreground">
                  Show planner rationale
                </summary>
                <p className="mt-1 text-[11px] text-muted-foreground whitespace-pre-wrap">
                  {planningRationale}
                </p>
              </details>
            )}
          </>
        )}
      </StageCard>
      <Connector />

      <StageCard
        index={3}
        title="Retrieve"
        latencyMs={retrievalSteps.reduce((acc, s) => acc + (s.latency_ms ?? 0), 0)}
        status={retrievalSteps.length === 0 ? 'skipped' : 'done'}
      >
        <div className="text-muted-foreground mb-1">
          {executed.length} tool{executed.length === 1 ? '' : 's'} executed
        </div>
        <ul className="space-y-0.5 font-mono text-[11px]">
          {retrievalSteps.map(s => {
            const ds = s.data_summary as { rows_returned?: number; chunks_returned?: number; token_estimate?: number }
            const count = ds?.rows_returned ?? ds?.chunks_returned ?? null
            return (
              <li key={s.step_seq + ':' + s.step_name} className="text-foreground">
                • {s.step_name}
                {count !== null && <span className="text-muted-foreground"> · {count} rows</span>}
                {ds?.token_estimate != null && (
                  <span className="text-muted-foreground"> · ~{ds.token_estimate} tk</span>
                )}
              </li>
            )
          })}
        </ul>
      </StageCard>
      <Connector />

      <StageCard
        index={4}
        title="Assemble"
        latencyMs={assembleStep?.latency_ms ?? null}
        status={assembleStatus}
      >
        {!assembleStep ? (
          <span className="text-muted-foreground italic">not invoked</span>
        ) : assembleShortCircuited ? (
          <span className="text-muted-foreground">
            Skipped — token threshold met (
            <span className="font-mono">
              {(assembleStep.data_summary as { total_token_estimate?: number })?.total_token_estimate ?? 0}
            </span>
            {' < '}
            <span className="font-mono">
              {(assembleStep.data_summary as { threshold?: number })?.threshold ?? 2000}
            </span>
            )
          </span>
        ) : (
          <span className="text-muted-foreground">
            assembled — see token breakdown in Context Inspector
          </span>
        )}
      </StageCard>
      <Connector />

      <StageCard
        index={5}
        title="Synthesize"
        latencyMs={synthStep?.latency_ms ?? null}
        status={synthStep ? (synthStep.status === 'error' ? 'error' : 'done') : 'skipped'}
      >
        {synthStep && (
          <div className="text-muted-foreground">
            <span>
              Model:{' '}
              <span className="text-foreground font-mono">
                {(synthStep.data_summary as { model?: string })?.model ?? '—'}
              </span>
            </span>
            <span className="ml-3">
              tokens in/out:{' '}
              <span className="text-foreground">
                {(synthStep.data_summary as { input_tokens?: number })?.input_tokens ?? 0}
              </span>
              {' / '}
              <span className="text-foreground">
                {(synthStep.data_summary as { output_tokens?: number })?.output_tokens ?? 0}
              </span>
            </span>
          </div>
        )}
      </StageCard>
    </div>
  )
}
