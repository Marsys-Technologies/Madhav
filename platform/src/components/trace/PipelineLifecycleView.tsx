'use client'

/**
 * PipelineLifecycleView — Gate II realignment (2026-05-12).
 *
 * Renders the new query pipeline shape per the Gate II brief:
 *   Planner → Retrieval (grouped, with one row per fired tool) → Synthesis → Audit,
 *   followed by a collapsible Checkpoints group with "N of 3 ran" header.
 *
 * Stage shape is stable across flag combinations (D1). Per-step latency does NOT
 * appear on lifecycle node headers (D2); details are surfaced in the step-detail
 * panel. The grouped retrieval node lists every tool that fired under
 * `parallel_group === 'tool_fetch'`; skipped tools (from the planner) render dimmed.
 *
 * All stage names are sourced from `lib/trace/types.ts` (PipelineStage / mapStepToStage),
 * not hard-coded string literals.
 */

import { useMemo, useState } from 'react'
import { Check, AlertCircle, MinusCircle, ChevronDown, ChevronRight } from 'lucide-react'
import type { PipelineStage, TraceStep } from '@/lib/trace/types'
import { mapStepToStage } from '@/lib/trace/types'

interface Props {
  steps: TraceStep[]
  manifestTools: string[]
}

type RowStatus = 'done' | 'error' | 'skipped' | 'pending'

function StatusIcon({ status }: { status: RowStatus }) {
  if (status === 'error') return <AlertCircle size={12} className="text-amber-400" aria-label="error" />
  if (status === 'skipped' || status === 'pending') return <MinusCircle size={12} className="text-muted-foreground" aria-label={status} />
  return <Check size={12} className="text-[var(--brand-gold)]" aria-label="done" />
}

function StageCard({
  index,
  title,
  status,
  children,
  testid,
}: {
  index: number | string
  title: string
  status: RowStatus
  children?: React.ReactNode
  testid?: string
}) {
  const dimmed = status === 'skipped' || status === 'pending'
  return (
    <div
      data-testid={testid}
      data-stage-status={status}
      className={`rounded border p-3 ${dimmed ? 'border-[rgba(212,175,55,0.06)] bg-[oklch(0.10_0.005_70)] opacity-60' : 'border-[rgba(212,175,55,0.12)] bg-[oklch(0.11_0.010_70)]'}`}
    >
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-mono text-muted-foreground/70 w-4">{index}.</span>
        <span className="text-[11px] font-semibold uppercase tracking-wider text-[#fce29a]">{title}</span>
        <StatusIcon status={status} />
      </div>
      {children && <div className="mt-2 pl-6 text-[11px]">{children}</div>}
    </div>
  )
}

function Connector() {
  return <div className="bg-[rgba(212,175,55,0.20)] w-px h-4 mx-auto" />
}

function deriveStageStatus(stageSteps: TraceStep[]): RowStatus {
  if (stageSteps.length === 0) return 'skipped'
  if (stageSteps.some(s => s.status === 'error')) return 'error'
  if (stageSteps.every(s => s.status === 'done')) return 'done'
  return 'pending'
}

const CHECKPOINT_STAGES: Array<{ stage: PipelineStage; label: string }> = [
  { stage: 'checkpoint_4_5', label: 'Checkpoint 4.5' },
  { stage: 'checkpoint_5_5', label: 'Checkpoint 5.5' },
  { stage: 'checkpoint_8_5', label: 'Checkpoint 8.5' },
]

export function PipelineLifecycleView({ steps, manifestTools }: Props) {
  const stageGroups = useMemo(() => {
    const groups: Record<PipelineStage, TraceStep[]> = {
      planner: [],
      retrieval: [],
      synthesis: [],
      audit: [],
      checkpoint_4_5: [],
      checkpoint_5_5: [],
      checkpoint_8_5: [],
    }
    for (const s of steps) {
      const stage = mapStepToStage(s)
      if (!stage) continue
      groups[stage].push(s)
    }
    return groups
  }, [steps])

  // Planner stage data — emitter writes step_name='classify' for the planner LLM call.
  // Also surfaces the `compose_bundle` deterministic sub-step's result line.
  const plannerLlmStep = stageGroups.planner.find(s => s.step_name === 'classify')
  const composeBundleStep = stageGroups.planner.find(s => s.step_name === 'compose_bundle')
  const plannerPayload = plannerLlmStep?.payload as
    | { query_plan?: { tools_authorized?: string[]; planning_rationale?: string }; tool_calls?: Array<{ tool_name?: string }> }
    | undefined
  const planned: string[] = useMemo(() => {
    const fromCalls = plannerPayload?.tool_calls?.map(c => c.tool_name).filter(Boolean) as string[] | undefined
    if (fromCalls && fromCalls.length > 0) return fromCalls
    return plannerPayload?.query_plan?.tools_authorized ?? []
  }, [plannerPayload])
  const planningRationale = plannerPayload?.query_plan?.planning_rationale ?? null

  // Retrieval grouped — one row per fired tool (D5). Tools the planner picked but
  // that did not fire (or fired but errored) are surfaced too.
  const retrievalFired = stageGroups.retrieval
  const firedNames = new Set(retrievalFired.map(s => s.step_name))
  const plannerPickedButMissing = planned.filter(p => !firedNames.has(p))
  const manifestSkipped = manifestTools.filter(t => !planned.includes(t))

  // Synthesis stage data
  const synthStep = stageGroups.synthesis.find(s => s.step_name === 'synthesis' || s.step_name === 'synthesis_done')
  const contextAssemblyStep = stageGroups.synthesis.find(s => s.step_name === 'context_assembly')

  // Audit stage data — citation_warn / citation_error trace steps (audit_events JOIN
  // happens at the assembler boundary, not here).
  const citationGateStep = stageGroups.audit.find(s => s.step_name === 'citation_error' || s.step_name === 'citation_warn')

  // Checkpoints — collapsible group per D1.
  const [checkpointsExpanded, setCheckpointsExpanded] = useState(false)
  const checkpointRan = CHECKPOINT_STAGES.filter(c => stageGroups[c.stage].length > 0).length

  const plannerStatus = deriveStageStatus(stageGroups.planner)
  const retrievalStatus: RowStatus = retrievalFired.length === 0 ? 'skipped'
    : retrievalFired.some(s => s.status === 'error') ? 'error'
    : retrievalFired.some(s => s.status !== 'done') ? 'pending'
    : 'done'
  const synthStatus = deriveStageStatus(stageGroups.synthesis.filter(s => s.step_name !== 'context_assembly'))
  const auditStatus: RowStatus = citationGateStep
    ? (citationGateStep.step_name === 'citation_error' ? 'error' : 'done')
    : 'pending'

  return (
    <div className="space-y-1" data-testid="pipeline-lifecycle-view">
      <StageCard index={1} title="Planner" status={plannerStatus} testid="lifecycle-stage-planner">
        {plannerLlmStep ? (
          <>
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
                  Available, skipped ({manifestSkipped.length})
                </div>
                <ul className="space-y-0.5">
                  {manifestSkipped.length === 0 ? (
                    <li className="text-muted-foreground/70 italic">none</li>
                  ) : (
                    manifestSkipped.map(t => (
                      <li key={t} className="font-mono text-[11px] text-muted-foreground/70">
                        • {t}
                        <span className="ml-1 italic text-[10px]">not selected</span>
                      </li>
                    ))
                  )}
                </ul>
              </div>
            </div>
            {composeBundleStep && (
              <div className="mt-2 text-muted-foreground">
                Bundle: <span className="text-foreground">{(composeBundleStep.data_summary as { result?: string })?.result ?? '—'}</span>
              </div>
            )}
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
        ) : (
          <span className="text-muted-foreground italic">not invoked</span>
        )}
      </StageCard>
      <Connector />

      <StageCard index={2} title="Retrieval" status={retrievalStatus} testid="lifecycle-stage-retrieval">
        <div className="text-muted-foreground mb-1">
          {retrievalFired.length} tool{retrievalFired.length === 1 ? '' : 's'} fired
        </div>
        <ul className="space-y-0.5 font-mono text-[11px]" data-testid="retrieval-subrows">
          {retrievalFired.length === 0 && plannerPickedButMissing.length === 0 ? (
            <li className="text-muted-foreground/70 italic">no retrieval steps</li>
          ) : (
            <>
              {retrievalFired.map(s => {
                const ds = s.data_summary as { rows_returned?: number; chunks_returned?: number; token_estimate?: number; top_score?: number }
                const count = ds?.rows_returned ?? ds?.chunks_returned ?? null
                const dimmed = s.status !== 'done'
                return (
                  <li
                    key={s.step_seq + ':' + s.step_name}
                    className={dimmed ? 'text-muted-foreground/60' : 'text-foreground'}
                    data-testid={`retrieval-subrow-${s.step_name}`}
                    data-subrow-status={s.status}
                  >
                    • {s.step_name}
                    {count !== null && <span className="text-muted-foreground"> · {count} rows</span>}
                    {ds?.token_estimate != null && (
                      <span className="text-muted-foreground"> · ~{ds.token_estimate} tk</span>
                    )}
                    {typeof ds?.top_score === 'number' && (
                      <span className="text-muted-foreground"> · top {ds.top_score.toFixed(2)}</span>
                    )}
                  </li>
                )
              })}
              {plannerPickedButMissing.map(t => (
                <li
                  key={'missing:' + t}
                  className="text-muted-foreground/40 italic"
                  data-testid={`retrieval-subrow-${t}`}
                  data-subrow-status="missing"
                >
                  • {t} <span className="text-[10px]">(picked, not yet emitted)</span>
                </li>
              ))}
            </>
          )}
        </ul>
      </StageCard>
      <Connector />

      <StageCard index={3} title="Synthesis" status={synthStatus} testid="lifecycle-stage-synthesis">
        {synthStep ? (
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
            {contextAssemblyStep && (() => {
              const ds = contextAssemblyStep.data_summary as { short_circuited?: boolean; total_token_estimate?: number; threshold?: number; reason?: string }
              if (ds?.short_circuited) {
                return (
                  <div className="mt-1 text-[10px] text-muted-foreground/80">
                    context_assembly short-circuited at <span className="font-mono">{ds.total_token_estimate ?? 0}</span> /{' '}
                    <span className="font-mono">{ds.threshold ?? 0}</span> tk
                    {ds.reason ? ` (${ds.reason})` : ''}
                  </div>
                )
              }
              return null
            })()}
          </div>
        ) : (
          <span className="text-muted-foreground italic">not invoked</span>
        )}
      </StageCard>
      <Connector />

      <StageCard index={4} title="Audit" status={auditStatus} testid="lifecycle-stage-audit">
        {citationGateStep ? (
          <div className="text-muted-foreground">
            Citation gate:{' '}
            <span className={citationGateStep.step_name === 'citation_error' ? 'text-amber-400' : 'text-foreground'}>
              {citationGateStep.step_name === 'citation_error' ? 'ERROR' : 'WARN'}
            </span>
            <span className="ml-2 text-[10px]">
              {(citationGateStep.data_summary as { result?: string })?.result ?? ''}
            </span>
          </div>
        ) : (
          <span className="text-muted-foreground italic">
            Audit data lives in audit_events; full audit detail surfaced in step-detail panel
          </span>
        )}
      </StageCard>
      <Connector />

      <div
        className="rounded border border-[rgba(212,175,55,0.08)] bg-[oklch(0.10_0.005_70)]"
        data-testid="lifecycle-stage-checkpoints"
      >
        <button
          type="button"
          onClick={() => setCheckpointsExpanded(v => !v)}
          aria-expanded={checkpointsExpanded}
          className="w-full flex items-center gap-2 p-3 text-left hover:bg-[rgba(212,175,55,0.04)] rounded"
        >
          <span className="text-[10px] font-mono text-muted-foreground/70 w-4">5.</span>
          {checkpointsExpanded
            ? <ChevronDown size={12} className="text-muted-foreground" />
            : <ChevronRight size={12} className="text-muted-foreground" />}
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#fce29a]">
            Checkpoints
          </span>
          <span className="text-[10px] text-muted-foreground" data-testid="checkpoints-summary">
            · {checkpointRan} of {CHECKPOINT_STAGES.length} ran
          </span>
        </button>
        {checkpointsExpanded && (
          <ul className="px-3 pb-3 space-y-1.5 pl-10">
            {CHECKPOINT_STAGES.map(c => {
              const ran = stageGroups[c.stage].length > 0
              const stageStep = stageGroups[c.stage][0]
              const status: RowStatus = ran
                ? (stageStep?.status === 'error' ? 'error' : 'done')
                : 'skipped'
              return (
                <li
                  key={c.stage}
                  data-testid={`checkpoint-${c.stage}`}
                  data-checkpoint-status={status}
                  className={`flex items-center gap-2 text-[11px] ${ran ? '' : 'opacity-50'}`}
                >
                  <StatusIcon status={status} />
                  <span className="font-mono text-foreground">{c.label}</span>
                  {!ran && (
                    <span className="text-[10px] italic text-muted-foreground/70">disabled / skipped</span>
                  )}
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
