'use client'

/**
 * StepDetail — Gate II W4 (2026-05-12).
 *
 * Dispatcher for the per-stage detail panel. Reads from the new AssembledTrace
 * shape. Stage IDs (per the lifecycle graph):
 *   - 'planner'
 *   - 'retrieval'
 *   - 'retrieval:<tool_name>'
 *   - 'synthesis'
 *   - 'audit'
 *   - 'checkpoint_4_5' | 'checkpoint_5_5' | 'checkpoint_8_5'
 *
 * The dispatcher imports its variants from `step_detail/*Detail.tsx`. No
 * registry entries for the deleted Classify / ContextAssembly / Fetch*
 * variants remain (D7).
 */

import type { AssembledTrace, PipelineStage } from '@/lib/trace/types'
import { PlannerDetail } from './step_detail/PlannerDetail'
import { RetrievalDetail } from './step_detail/RetrievalDetail'
import { SynthesisDetail } from './step_detail/SynthesisDetail'
import { AuditDetail } from './step_detail/AuditDetail'
import { CheckpointDetail } from './step_detail/CheckpointDetail'

type StepVariant = 'planner' | 'retrieval' | 'synthesis' | 'audit' | 'checkpoint'

const VARIANT_LABELS: Record<StepVariant, string> = {
  planner: 'Planner',
  retrieval: 'Retrieval',
  synthesis: 'Synthesis',
  audit: 'Audit',
  checkpoint: 'Checkpoint',
}

const BADGE_COLORS: Record<StepVariant, string> = {
  planner: 'bg-[rgba(212,175,55,0.1)] text-[#d4af37]',
  retrieval: 'bg-violet-400/10 text-violet-400',
  synthesis: 'bg-pink-400/10 text-pink-400',
  audit: 'bg-blue-400/10 text-blue-400',
  checkpoint: 'bg-emerald-400/10 text-emerald-400',
}

function StepTypeBadge({ variant }: { variant: StepVariant }) {
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold uppercase tracking-wide ${BADGE_COLORS[variant]}`}>
      {VARIANT_LABELS[variant]}
    </span>
  )
}

function resolveVariant(stepId: string): { variant: StepVariant; subId: string | null } {
  if (stepId === 'planner') return { variant: 'planner', subId: null }
  if (stepId === 'planner:classify') return { variant: 'planner', subId: 'classify' }
  if (stepId === 'planner:compose_bundle') return { variant: 'planner', subId: 'compose_bundle' }
  if (stepId === 'planner:plan_per_tool') return { variant: 'planner', subId: 'plan_per_tool' }
  if (stepId === 'synthesis') return { variant: 'synthesis', subId: null }
  if (stepId === 'audit') return { variant: 'audit', subId: null }
  if (stepId === 'retrieval') return { variant: 'retrieval', subId: null }
  if (stepId.startsWith('retrieval:')) return { variant: 'retrieval', subId: stepId.slice('retrieval:'.length) }
  if (stepId.startsWith('checkpoint_')) return { variant: 'checkpoint', subId: stepId }
  // Fallback for unknown stage ids — render synthesis with a console warning.
  if (typeof console !== 'undefined') {
    console.warn(`[StepDetail] unknown stage id "${stepId}" — falling back to synthesis`)
  }
  return { variant: 'synthesis', subId: null }
}

function extractStepData(assembled: AssembledTrace, stepId: string): unknown {
  if (stepId === 'planner' || stepId === 'planner:classify') return assembled.grouped.planner
  if (stepId === 'planner:compose_bundle') return assembled.grouped.planner?.compose_bundle ?? null
  if (stepId === 'planner:plan_per_tool') return assembled.grouped.planner?.plan_per_tool ?? null
  if (stepId === 'retrieval') return assembled.grouped.retrieval
  if (stepId === 'synthesis') return assembled.grouped.synthesis
  if (stepId === 'audit') return assembled.grouped.audit
  if (stepId.startsWith('retrieval:')) {
    const name = stepId.slice('retrieval:'.length)
    return assembled.grouped.retrieval.find(r => r.tool_name === name) ?? null
  }
  if (stepId.startsWith('checkpoint_')) {
    return assembled.grouped.checkpoints.find(c => c.stage === (stepId as PipelineStage)) ?? null
  }
  return null
}

interface StepDetailProps {
  assembled: AssembledTrace
  selectedStepId: string
}

export function StepDetail({ assembled, selectedStepId }: StepDetailProps) {
  const { variant, subId } = resolveVariant(selectedStepId)

  function handleCopyJson() {
    const data = extractStepData(assembled, selectedStepId)
    void navigator.clipboard.writeText(JSON.stringify(data, null, 2))
  }

  return (
    <div className="flex flex-col h-full" data-testid="step-detail">
      <div className="sticky top-0 z-10 bg-[oklch(0.10_0.012_70)] border-b border-[rgba(212,175,55,0.1)] px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StepTypeBadge variant={variant} />
          <span className="text-sm font-medium text-zinc-200">
            {subId ?? selectedStepId}
          </span>
        </div>
        <button
          onClick={handleCopyJson}
          className="text-xs text-zinc-500 hover:text-zinc-300"
          data-testid="copy-step-json"
        >
          Copy JSON
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {variant === 'planner' && <PlannerDetail planner={assembled.grouped.planner} focusedSub={subId} />}
        {variant === 'retrieval' && (
          <RetrievalDetail retrieval={assembled.grouped.retrieval} focusedTool={subId} />
        )}
        {variant === 'synthesis' && <SynthesisDetail synthesis={assembled.grouped.synthesis} />}
        {variant === 'audit' && <AuditDetail audit={assembled.grouped.audit} />}
        {variant === 'checkpoint' && (
          <CheckpointDetail
            checkpoint={
              assembled.grouped.checkpoints.find(c => c.stage === subId) ?? null
            }
          />
        )}
      </div>
    </div>
  )
}
