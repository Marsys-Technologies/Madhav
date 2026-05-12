'use client'

/**
 * LifecycleGraph — Gate II realignment (2026-05-12).
 *
 * Used by the admin trace page (TraceModal). Renders the canonical pipeline
 * shape per D5 + D1: Planner → Retrieval (grouped) → Synthesis → Audit,
 * followed by a collapsible Checkpoints group.
 *
 * Consumes the new trace step schema (TraceStep[] from lib/trace/types.ts).
 * Stage names come from PipelineStage / mapStepToStage — no hard-coded
 * stage literals.
 */

import { useMemo, useState } from 'react'
import type { PipelineStage, TraceStep } from '@/lib/trace/types'
import { mapStepToStage } from '@/lib/trace/types'

interface LifecycleGraphProps {
  steps: TraceStep[]
  selectedStepId: string
  onSelectStep: (stepId: string) => void
  searchFilter?: string
}

const CHECKPOINTS: PipelineStage[] = ['checkpoint_4_5', 'checkpoint_5_5', 'checkpoint_8_5']
const CHECKPOINT_LABEL: Record<PipelineStage, string> = {
  planner: 'Planner',
  retrieval: 'Retrieval',
  synthesis: 'Synthesis',
  audit: 'Audit',
  checkpoint_4_5: 'Checkpoint 4.5',
  checkpoint_5_5: 'Checkpoint 5.5',
  checkpoint_8_5: 'Checkpoint 8.5',
}

function matchesFilter(id: string, filter: string): boolean {
  if (!filter) return true
  return id.toLowerCase().includes(filter.toLowerCase())
}

function dim(matches: boolean): string {
  return matches ? '' : 'opacity-20 pointer-events-none'
}

function StageNode({
  id,
  title,
  selected,
  hasData,
  onSelect,
  testid,
  children,
}: {
  id: string
  title: string
  selected: boolean
  hasData: boolean
  onSelect: () => void
  testid?: string
  children?: React.ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      data-testid={testid}
      data-stage-id={id}
      data-stage-has-data={hasData}
      className={`w-full text-left rounded border p-3 transition-colors ${
        selected
          ? 'border-[var(--brand-gold)] bg-[rgba(212,175,55,0.10)]'
          : 'border-[rgba(212,175,55,0.12)] bg-[oklch(0.11_0.010_70)] hover:bg-[rgba(212,175,55,0.04)]'
      } ${hasData ? '' : 'opacity-60'}`}
    >
      <div className="text-[11px] font-semibold uppercase tracking-wider text-[#fce29a]">
        {title}
      </div>
      {children && <div className="mt-1 text-[11px] text-muted-foreground">{children}</div>}
    </button>
  )
}

function Edge() {
  return <div className="my-1 w-px h-3 mx-auto bg-[rgba(212,175,55,0.20)]" />
}

export function LifecycleGraph({
  steps,
  selectedStepId,
  onSelectStep,
  searchFilter = '',
}: LifecycleGraphProps) {
  const groups = useMemo(() => {
    const m: Record<PipelineStage, TraceStep[]> = {
      planner: [], retrieval: [], synthesis: [], audit: [],
      checkpoint_4_5: [], checkpoint_5_5: [], checkpoint_8_5: [],
    }
    for (const s of steps) {
      const stage = mapStepToStage(s)
      if (stage) m[stage].push(s)
    }
    return m
  }, [steps])

  const [checkpointsExpanded, setCheckpointsExpanded] = useState(false)
  const checkpointRan = CHECKPOINTS.filter(c => groups[c].length > 0).length

  const plannerStep = groups.planner.find(s => s.step_name === 'classify')
  const synthStep = groups.synthesis.find(s => s.step_name === 'synthesis' || s.step_name === 'synthesis_done')

  return (
    <div className="p-3 space-y-0" data-testid="lifecycle-graph">
      <div className={dim(matchesFilter('planner', searchFilter))}>
        <StageNode
          id="planner"
          title="Planner"
          selected={selectedStepId === 'planner'}
          hasData={!!plannerStep}
          onSelect={() => onSelectStep('planner')}
          testid="lifecycle-node-planner"
        >
          {plannerStep
            ? `${((plannerStep.payload as { tool_calls?: unknown[] })?.tool_calls?.length ?? 0)} tools planned`
            : 'not invoked'}
        </StageNode>
      </div>

      <Edge />

      <div className={dim(matchesFilter('retrieval', searchFilter))}>
        <StageNode
          id="retrieval"
          title="Retrieval"
          selected={selectedStepId === 'retrieval'}
          hasData={groups.retrieval.length > 0}
          onSelect={() => onSelectStep('retrieval')}
          testid="lifecycle-node-retrieval"
        >
          {groups.retrieval.length} sub-tools fired
        </StageNode>
        {groups.retrieval.length > 0 && (
          <ul className="ml-4 mt-1 space-y-0.5" data-testid="retrieval-subrows-graph">
            {groups.retrieval.map(s => {
              const dimmed = s.status !== 'done'
              return (
                <li
                  key={s.step_seq + ':' + s.step_name}
                  data-testid={`retrieval-subrow-${s.step_name}`}
                  data-subrow-status={s.status}
                  className={`text-[11px] font-mono pl-2 ${dimmed ? 'text-muted-foreground/60' : 'text-foreground'} cursor-pointer hover:underline`}
                  onClick={() => onSelectStep(`retrieval:${s.step_name}`)}
                >
                  • {s.step_name}
                </li>
              )
            })}
          </ul>
        )}
      </div>

      <Edge />

      <div className={dim(matchesFilter('synthesis', searchFilter))}>
        <StageNode
          id="synthesis"
          title="Synthesis"
          selected={selectedStepId === 'synthesis'}
          hasData={!!synthStep}
          onSelect={() => onSelectStep('synthesis')}
          testid="lifecycle-node-synthesis"
        >
          {synthStep ? (synthStep.data_summary as { model?: string })?.model ?? '—' : 'not invoked'}
        </StageNode>
      </div>

      <Edge />

      <div className={dim(matchesFilter('audit', searchFilter))}>
        <StageNode
          id="audit"
          title="Audit"
          selected={selectedStepId === 'audit'}
          hasData={groups.audit.length > 0}
          onSelect={() => onSelectStep('audit')}
          testid="lifecycle-node-audit"
        >
          {groups.audit.length > 0 ? 'citation gate fired' : 'audit_events JOIN (assembler)'}
        </StageNode>
      </div>

      <Edge />

      <div
        className="rounded border border-[rgba(212,175,55,0.08)] bg-[oklch(0.10_0.005_70)]"
        data-testid="lifecycle-node-checkpoints"
      >
        <button
          type="button"
          onClick={() => setCheckpointsExpanded(v => !v)}
          aria-expanded={checkpointsExpanded}
          className="w-full text-left p-3 hover:bg-[rgba(212,175,55,0.04)] rounded"
        >
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#fce29a]">
            Checkpoints
          </span>
          <span
            className="ml-2 text-[10px] text-muted-foreground"
            data-testid="checkpoints-summary"
          >
            · {checkpointRan} of {CHECKPOINTS.length} ran
          </span>
        </button>
        {checkpointsExpanded && (
          <ul className="px-3 pb-3 space-y-1.5 pl-6">
            {CHECKPOINTS.map(c => {
              const ran = groups[c].length > 0
              const label = CHECKPOINT_LABEL[c]
              return (
                <li
                  key={c}
                  data-testid={`checkpoint-${c}`}
                  data-checkpoint-status={ran ? (groups[c][0]?.status ?? 'done') : 'skipped'}
                  className={`text-[11px] font-mono ${ran ? 'text-foreground cursor-pointer hover:underline' : 'text-muted-foreground/50'}`}
                  onClick={() => ran && onSelectStep(c)}
                >
                  • {label}
                  {!ran && <span className="ml-1 italic text-[10px]">disabled / skipped</span>}
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
