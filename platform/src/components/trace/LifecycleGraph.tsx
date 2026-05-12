'use client'

/**
 * LifecycleGraph — Gate II.5 realignment (2026-05-13).
 *
 * Renders the grouped production pipeline shape per D9 + D10:
 *   Planning [classify + compose_bundle + plan_per_tool inline sub-rows]
 *   → Retrieval [21 inline sub-rows; unfired tools dimmed]
 *   → Synthesis → Audit
 *   → Checkpoints (collapsible group, D1)
 */

import { useMemo, useState } from 'react'
import type { AssembledTrace, PipelineStage, TraceStep } from '@/lib/trace/types'
import { ALL_21_RETRIEVAL_TOOLS, mapStepToStage } from '@/lib/trace/types'

interface LifecycleGraphProps {
  steps: TraceStep[]
  assembled: AssembledTrace
  selectedStepId: string
  onSelectStep: (stepId: string) => void
  searchFilter?: string
}

const CHECKPOINTS: PipelineStage[] = ['checkpoint_4_5', 'checkpoint_5_5', 'checkpoint_8_5']
const CHECKPOINT_LABEL: Record<string, string> = {
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

function ContainerHeader({
  title,
  selected,
  hasData,
  onSelect,
  testid,
  children,
}: {
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

function SubRow({
  label,
  dim: isDimmed,
  onClick,
  selected,
  testid,
  status,
}: {
  label: string
  dim: boolean
  onClick: () => void
  selected: boolean
  testid?: string
  status?: string
}) {
  return (
    <li
      data-testid={testid}
      data-subrow-status={status}
      onClick={onClick}
      className={`text-[11px] font-mono pl-2 cursor-pointer hover:underline ${
        isDimmed ? 'text-muted-foreground/50' : selected ? 'text-[#fce29a]' : 'text-foreground'
      }`}
    >
      • {label}
    </li>
  )
}

function Edge() {
  return <div className="my-1 w-px h-3 mx-auto bg-[rgba(212,175,55,0.20)]" />
}

export function LifecycleGraph({
  steps,
  assembled,
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

  const { planner, retrieval, synthesis, audit } = assembled.grouped

  // Planning: 3 inline sub-rows in emission order
  const planningSubRows: Array<{ id: string; label: string; hasData: boolean; status?: string }> = [
    {
      id: 'planner:classify',
      label: 'classify',
      hasData: planner !== null,
      status: planner?.status,
    },
    {
      id: 'planner:compose_bundle',
      label: 'compose_bundle',
      hasData: planner?.compose_bundle !== null && planner?.compose_bundle !== undefined,
      status: planner?.compose_bundle ? 'done' : undefined,
    },
    {
      id: 'planner:plan_per_tool',
      label: 'plan_per_tool',
      hasData: planner?.plan_per_tool !== null && planner?.plan_per_tool !== undefined,
      status: planner?.plan_per_tool ? 'done' : undefined,
    },
  ]

  // Retrieval: all 21 tools; dim unfired ones
  const firedTools = new Set(retrieval.map(r => r.tool_name))
  const synthStep = steps.find(
    s => s.step_name === 'synthesis' || s.step_name === 'synthesis_done',
  )

  return (
    <div className="p-3 space-y-0" data-testid="lifecycle-graph">

      {/* Planning container */}
      <div className={dim(matchesFilter('planning', searchFilter))}>
        <ContainerHeader
          title="Planning"
          selected={selectedStepId === 'planner'}
          hasData={planner !== null}
          onSelect={() => onSelectStep('planner')}
          testid="lifecycle-node-planner"
        >
          {planner
            ? `${planner.tool_calls.length} tools planned`
            : 'not invoked'}
        </ContainerHeader>
        <ul
          className="ml-4 mt-1 space-y-0.5"
          data-testid="planning-subrows"
          aria-label="Planning sub-steps"
        >
          {planningSubRows.map(row => (
            <SubRow
              key={row.id}
              label={row.label}
              dim={!row.hasData}
              onClick={() => onSelectStep(row.id)}
              selected={selectedStepId === row.id}
              testid={`planning-subrow-${row.label}`}
              status={row.status}
            />
          ))}
        </ul>
      </div>

      <Edge />

      {/* Retrieval container — all 21 tools, unfired dimmed */}
      <div className={dim(matchesFilter('retrieval', searchFilter))}>
        <ContainerHeader
          title="Retrieval"
          selected={selectedStepId === 'retrieval'}
          hasData={retrieval.length > 0}
          onSelect={() => onSelectStep('retrieval')}
          testid="lifecycle-node-retrieval"
        >
          {retrieval.length} of {ALL_21_RETRIEVAL_TOOLS.length} tools fired
        </ContainerHeader>
        <ul
          className="ml-4 mt-1 space-y-0.5"
          data-testid="retrieval-subrows-graph"
          aria-label="Retrieval tools"
        >
          {ALL_21_RETRIEVAL_TOOLS.map(toolName => {
            const run = retrieval.find(r => r.tool_name === toolName)
            const fired = firedTools.has(toolName)
            return (
              <SubRow
                key={toolName}
                label={toolName}
                dim={!fired}
                onClick={() => fired ? onSelectStep(`retrieval:${toolName}`) : undefined}
                selected={selectedStepId === `retrieval:${toolName}`}
                testid={`retrieval-subrow-${toolName}`}
                status={run?.status ?? 'skipped'}
              />
            )
          })}
        </ul>
      </div>

      <Edge />

      {/* Synthesis */}
      <div className={dim(matchesFilter('synthesis', searchFilter))}>
        <ContainerHeader
          title="Synthesis"
          selected={selectedStepId === 'synthesis'}
          hasData={synthesis !== null}
          onSelect={() => onSelectStep('synthesis')}
          testid="lifecycle-node-synthesis"
        >
          {synthesis?.mode === 'single_model'
            ? (synthesis.model ?? '—')
            : synthesis?.mode === 'panel'
              ? 'panel mode'
              : 'not invoked'}
        </ContainerHeader>
      </div>

      <Edge />

      {/* Audit */}
      <div className={dim(matchesFilter('audit', searchFilter))}>
        <ContainerHeader
          title="Audit"
          selected={selectedStepId === 'audit'}
          hasData={audit !== null && audit.placeholder_note === null}
          onSelect={() => onSelectStep('audit')}
          testid="lifecycle-node-audit"
        >
          {audit?.placeholder_note ? 'pending' : audit?.validator_verdict ?? 'not invoked'}
        </ContainerHeader>
      </div>

      <Edge />

      {/* Checkpoints — collapsible group (D1) */}
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
          <ul className="px-3 pb-3 space-y-1.5 pl-6" aria-label="Checkpoint stages">
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
