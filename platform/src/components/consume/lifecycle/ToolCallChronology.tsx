'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp, Wrench } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ToolCallRecord, ChatLifecycleState } from '@/lib/hooks/useChatLifecycle'

interface Props {
  state: ChatLifecycleState
  toolCalls: ToolCallRecord[]
  /** Tier determines default expansion. super_admin/acharya see it expanded. */
  audienceTier?: 'super_admin' | 'acharya_reviewer' | 'client' | 'public_redacted'
  className?: string
}

/**
 * ToolCallChronology — collapsible list of tool_call + tool_result pairs.
 *
 * CO.1: structural stub. Renders tool calls when present.
 * CO.3 wires full tool_call / tool_result event stream and polish.
 *
 * Present only when at least one tool_call has been emitted. Collapses
 * on composing. Hidden for client tier by default.
 */
export function ToolCallChronology({
  state: _state,
  toolCalls,
  audienceTier = 'client',
  className,
}: Props) {
  const defaultExpanded = audienceTier === 'super_admin' || audienceTier === 'acharya_reviewer'
  const [expanded, setExpanded] = useState(defaultExpanded)

  if (toolCalls.length === 0) return null
  if (audienceTier === 'client' || audienceTier === 'public_redacted') return null

  return (
    <div className={cn('mx-auto w-full max-w-4xl px-4 py-1', className)}>
      <div className="rounded-md border border-border/40 bg-muted/20">
        <button
          type="button"
          onClick={() => setExpanded(e => !e)}
          className="flex w-full items-center gap-2 px-3 py-2 text-left"
          aria-expanded={expanded}
          aria-controls="tool-call-list"
        >
          <Wrench className="h-3 w-3 shrink-0 text-muted-foreground/60" />
          <span className="flex-1 text-[11px] text-muted-foreground">
            {toolCalls.length} tool call{toolCalls.length !== 1 ? 's' : ''}
          </span>
          <span className="shrink-0 text-muted-foreground/60">
            {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          </span>
        </button>

        {expanded && (
          <ul
            id="tool-call-list"
            className="divide-y divide-border/30 border-t border-border/30"
          >
            {toolCalls.map((tc, i) => (
              <ToolCallCard key={`${tc.callId}-${i}`} record={tc} />
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function ToolCallCard({ record }: { record: ToolCallRecord }) {
  const [open, setOpen] = useState(false)
  const argsStr = JSON.stringify(record.args, null, 2)
  const resultStr = record.result !== undefined ? JSON.stringify(record.result, null, 2) : null
  const resultPreview = resultStr ? resultStr.slice(0, 200) + (resultStr.length > 200 ? '…' : '') : null

  return (
    <li className="px-3 py-2">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="flex w-full items-center justify-between gap-2 text-left"
        aria-expanded={open}
      >
        <span className="font-mono text-[11px] text-muted-foreground">{record.name}</span>
        <span className="text-[10px] text-muted-foreground/50">
          {record.result !== undefined ? '✓' : '…'}
        </span>
      </button>
      {open && (
        <div className="mt-1.5 space-y-1">
          <pre className="overflow-x-auto rounded bg-muted/40 p-2 text-[10px] text-muted-foreground/80">
            {argsStr}
          </pre>
          {resultPreview && (
            <pre className="overflow-x-auto rounded bg-muted/30 p-2 text-[10px] text-muted-foreground/70">
              {resultPreview}
            </pre>
          )}
        </div>
      )}
    </li>
  )
}
