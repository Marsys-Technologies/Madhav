'use client'

/**
 * PlanningIndicator — TRACE-0 (W2-TRACE-A).
 *
 * Visual signal for the LLM-first planner step. Three render states:
 *
 *   1. isPlanning && !toolsSelected   → pulsing skeleton bar + "Analyzing…"
 *   2. isPlanning && toolsSelected     → planning_done arrived; show selected
 *                                        tools; collapse 1.5s later
 *   3. !isPlanning                     → renders nothing (collapsed)
 *
 * UI-only: receives state via props. Hydration is the parent's job
 * (planning_start sets isPlanning=true; planning_done sets toolsSelected;
 * the 1.5s collapse is tracked here so the parent doesn't need to time it).
 */

import { useEffect, useState } from 'react'

interface PlanningIndicatorProps {
  isPlanning: boolean
  plannerModelId?: string
  toolsSelected?: string[]
}

export function PlanningIndicator({
  isPlanning,
  plannerModelId,
  toolsSelected,
}: PlanningIndicatorProps) {
  const hasTools = Boolean(toolsSelected && toolsSelected.length > 0)

  if (!isPlanning && !hasTools) return null

  // Done state — tools materialised, briefly visible before collapse.
  if (hasTools) {
    return <CompletedPlanningIndicator toolsSelected={toolsSelected!} plannerModelId={plannerModelId} />
  }

  // Planning state — pulsing skeleton bar.
  return (
    <div className="px-4 py-2 border-b border-[rgba(212,175,55,0.10)] bg-[rgba(13,10,5,0.5)] flex items-center gap-2">
      <span className="inline-block h-1.5 w-1.5 rounded-full bg-[rgba(244,209,96,0.95)] animate-pulse" />
      <span className="text-[10px] font-bold uppercase tracking-[0.16em] text-[rgba(244,209,96,0.85)]">
        Analyzing your question…
      </span>
      <div className="flex-1 h-6 rounded bg-[rgba(212,175,55,0.08)] animate-pulse" />
      {plannerModelId && (
        <span className="text-[10px] text-[rgba(212,175,55,0.5)]">{plannerModelId}</span>
      )}
    </div>
  )
}

function CompletedPlanningIndicator({
  toolsSelected,
  plannerModelId,
}: {
  toolsSelected: string[]
  plannerModelId?: string
}) {
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => setVisible(false), 1500)
    return () => clearTimeout(timer)
  }, [])

  if (!visible) return null

  return (
      <div className="px-4 py-2 border-b border-[rgba(212,175,55,0.10)] bg-[rgba(13,10,5,0.5)] flex items-center gap-2">
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-[rgba(120,210,160,0.95)]" />
        <span className="text-[10px] font-bold uppercase tracking-[0.16em] text-[rgba(120,210,160,0.85)]">
          Plan ready
        </span>
        <div className="flex flex-wrap items-center gap-1">
          {toolsSelected!.map((name) => (
            <span
              key={name}
              className="text-[10px] px-1.5 py-0.5 rounded border border-[rgba(212,175,55,0.25)] bg-[rgba(212,175,55,0.08)] text-[rgba(244,209,96,0.9)]"
            >
              {name}
            </span>
          ))}
        </div>
        {plannerModelId && (
          <span className="ml-auto text-[10px] text-[rgba(212,175,55,0.5)]">{plannerModelId}</span>
        )}
      </div>
  )
}
