'use client'

import type { StagePart } from '@/lib/streams/data_parts'

interface StageStepperProps {
  stages: StagePart[]
}

const STAGE_LABELS: Record<string, string> = {
  classify: 'Classify',
  compose_bundle: 'Compose',
  plan_per_tool: 'Plan',
  tool_fetch: 'Fetch',
  synthesis: 'Synthesise',
  audit: 'Audit',
  'panel:member:1': 'M1',
  'panel:member:2': 'M2',
  'panel:member:3': 'M3',
  'panel:adjudicator': 'Adjudicate',
}

export function StageStepper({ stages }: StageStepperProps) {
  if (stages.length === 0) return null

  return (
    <div
      className="flex flex-wrap items-center gap-x-1 gap-y-1 py-1"
      data-testid="v2-stage-stepper"
    >
      {stages.map((s, i) => (
        <span key={`${s.stage}-${i}`} className="flex items-center gap-1">
          {i > 0 && <span className="text-zinc-700 text-[10px]">›</span>}
          <span
            className={`flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium leading-none ${
              s.status === 'running'
                ? 'bg-indigo-900/40 text-indigo-300 border border-indigo-500/30 animate-pulse'
                : s.status === 'done'
                  ? 'bg-zinc-800/60 text-zinc-400 border border-zinc-700/40'
                  : 'bg-red-900/30 text-red-400 border border-red-500/30'
            }`}
            data-testid={`v2-stage-${s.stage}`}
          >
            {s.status === 'running' && (
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-indigo-400" aria-hidden="true" />
            )}
            {s.status === 'done' && (
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-zinc-500" aria-hidden="true" />
            )}
            {s.status === 'error' && (
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-red-500" aria-hidden="true" />
            )}
            {STAGE_LABELS[s.stage] ?? s.stage}
            {s.ms !== undefined && s.status === 'done' && (
              <span className="opacity-50">{s.ms}ms</span>
            )}
          </span>
        </span>
      ))}
    </div>
  )
}
