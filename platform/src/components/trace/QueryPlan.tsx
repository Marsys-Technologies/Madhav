'use client'

/**
 * QueryPlan — TRACE-2 (W2-TRACE-A).
 *
 * Renders the planner's output as expandable tool cards. One card per
 * planned tool call, ordered as the planner emitted them. Each card shows
 * tool_name + priority badge + reason + token_budget; params expand on
 * click into a JSON block.
 *
 * Hydration: `plan` is null until planning_done arrives; show the skeleton
 * while isLoading=true. UI-only — no fetching.
 */

import { useState } from 'react'
import type { PipelinePlan } from '@/lib/pipeline/types'

interface QueryPlanProps {
  plan: PipelinePlan | null
  isLoading: boolean
}

const PRIORITY_STYLE: Record<1 | 2 | 3, { label: string; className: string }> = {
  1: {
    label: 'P1',
    className:
      'bg-[rgba(220,90,60,0.14)] text-[rgba(240,150,120,0.95)] border-[rgba(230,110,80,0.4)]',
  },
  2: {
    label: 'P2',
    className:
      'bg-[rgba(212,175,55,0.14)] text-[rgba(244,209,96,0.95)] border-[rgba(212,175,55,0.4)]',
  },
  3: {
    label: 'P3',
    className:
      'bg-[rgba(80,150,200,0.14)] text-[rgba(140,190,240,0.95)] border-[rgba(80,150,200,0.4)]',
  },
}

function RowSkeleton() {
  return (
    <div className="h-9 rounded border border-[rgba(212,175,55,0.10)] bg-[rgba(212,175,55,0.04)] animate-pulse" />
  )
}

function ToolCard({
  toolCall,
}: {
  toolCall: PipelinePlan['tool_calls'][number]
}) {
  const [expanded, setExpanded] = useState(false)
  const priority = PRIORITY_STYLE[toolCall.priority]
  const hasParams = Object.keys(toolCall.params).length > 0

  return (
    <div className="rounded border border-[rgba(212,175,55,0.15)] bg-[rgba(13,10,5,0.5)]">
      <button
        type="button"
        onClick={() => hasParams && setExpanded((e) => !e)}
        className={`w-full text-left flex items-center gap-2 px-3 py-2 ${
          hasParams ? 'hover:bg-[rgba(212,175,55,0.04)]' : 'cursor-default'
        }`}
      >
        <span
          className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${priority.className}`}
        >
          {priority.label}
        </span>
        <span className="text-[11px] font-semibold text-[rgba(252,226,154,0.95)]">
          {toolCall.tool_name}
        </span>
        <span className="flex-1 text-[10px] text-[rgba(212,175,55,0.6)] italic truncate">
          {toolCall.reason}
        </span>
        <span className="text-[10px] text-[rgba(212,175,55,0.5)] flex-shrink-0">
          {toolCall.token_budget} tok
        </span>
        {hasParams && (
          <span className="text-[10px] text-[rgba(212,175,55,0.4)] flex-shrink-0">
            {expanded ? '▾' : '▸'}
          </span>
        )}
      </button>

      {expanded && hasParams && (
        <pre className="px-3 pb-2 text-[10px] text-[rgba(212,175,55,0.7)] whitespace-pre-wrap break-all">
          {JSON.stringify(toolCall.params, null, 2)}
        </pre>
      )}
    </div>
  )
}

export function QueryPlan({ plan, isLoading }: QueryPlanProps) {
  if (isLoading) {
    return (
      <div className="px-4 py-3 space-y-2">
        <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-[rgba(212,175,55,0.6)]">
          Query Plan
        </div>
        {Array.from({ length: 5 }).map((_, i) => (
          <RowSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (!plan) {
    return (
      <div className="px-4 py-3 text-[10px] italic text-[rgba(212,175,55,0.4)]">
        No plan available.
      </div>
    )
  }

  return (
    <div className="px-4 py-3 space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-bold uppercase tracking-[0.16em] text-[rgba(212,175,55,0.6)]">
          Query Plan
        </span>
        <span className="text-[10px] text-[rgba(244,209,96,0.7)]">
          {plan.query_class}
        </span>
        <span className="ml-auto text-[10px] text-[rgba(212,175,55,0.5)]">
          {plan.tool_calls.length} tools
        </span>
      </div>

      {plan.query_intent_summary && (
        <div className="text-[11px] italic text-[rgba(252,226,154,0.75)]">
          {plan.query_intent_summary}
        </div>
      )}

      <div className="space-y-1.5">
        {plan.tool_calls.map((tc, i) => (
          <ToolCard key={`${tc.tool_name}-${i}`} toolCall={tc} />
        ))}
      </div>
    </div>
  )
}
