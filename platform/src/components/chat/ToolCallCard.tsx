'use client'

/**
 * ToolCallCard — C-S5 R11.C
 *
 * Inline tool call card with:
 *   - Icon + verb label (from tool_verbs.ts): "Looked up panchang" / "Looking up panchang…"
 *   - Progressive input reveal during streaming (state=input-streaming → partial JSON shown)
 *   - Marsys gold accent (NOT coral)
 *   - Gated by MARSYS_FLAG_R11C_TOOL_CARDS (default true)
 *
 * Kept as ToolCallCard — do NOT rename or create InlineToolCard.tsx.
 */

import { useState, memo } from 'react'
import { ChevronDown, CircleCheck, CircleAlert, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { getToolVerb } from './tool_verbs'

export interface ToolCallCardProps {
  toolName: string
  state: 'input-streaming' | 'input-available' | 'output-available' | 'output-error' | string
  input?: unknown
  output?: unknown
  errorText?: string
}

function formatJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

function ToolCallCardImpl({ toolName, state, input, output, errorText }: ToolCallCardProps) {
  const [open, setOpen] = useState(false)
  const isRunning = state === 'input-streaming' || state === 'input-available'
  const isError = state === 'output-error'

  // C-S5: verb label from mapping (e.g., "Looked up panchang" / "Looking up panchang…")
  const verbEntry = getToolVerb(toolName)
  const verbLabel = isError
    ? `Error — ${verbEntry.done}`
    : isRunning
    ? verbEntry.running
    : verbEntry.done

  return (
    <div className={cn(
      'my-3 overflow-hidden rounded-xl border border-border/60 bg-muted/30 border-l-2 transition-colors duration-150',
      open ? 'border-l-[var(--brand-gold)]' : 'border-l-transparent'
    )}>
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs transition-colors hover:bg-muted/50"
        data-tool-name={toolName}
        data-tool-state={state}
      >
        {isRunning ? (
          <Loader2 className="size-3.5 animate-spin text-[var(--brand-gold)]/70" aria-label="Running" />
        ) : isError ? (
          <CircleAlert className="size-3.5 text-destructive" aria-label="Error" />
        ) : (
          <CircleCheck className="size-3.5 text-[var(--brand-gold)]/70" aria-label="Done" />
        )}
        <span
          className={cn(
            'font-sans text-xs',
            isRunning ? 'text-muted-foreground' : isError ? 'text-destructive/80' : 'text-muted-foreground/80',
          )}
          data-testid="tool-card-verb-label"
        >
          {verbLabel}
        </span>
        <ChevronDown
          className={cn(
            'ml-auto size-3.5 text-muted-foreground transition-transform duration-150',
            open && 'rotate-180'
          )}
        />
      </button>
      {open && (
        <div className="border-t border-border/60 bg-background/50 px-3 py-2 text-xs">
          {input !== undefined && (
            <div className="mb-2">
              <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">Input</p>
              <pre className="overflow-x-auto rounded bg-muted/40 p-2 font-mono text-[11px] leading-relaxed text-foreground/80">
                {formatJson(input)}
              </pre>
            </div>
          )}
          {output !== undefined && (
            <div>
              <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">Output</p>
              <pre className="max-h-60 overflow-auto rounded bg-muted/40 p-2 font-mono text-[11px] leading-relaxed text-foreground/80">
                {formatJson(output)}
              </pre>
            </div>
          )}
          {errorText && (
            <div>
              <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-destructive">Error</p>
              <pre className="overflow-x-auto rounded bg-destructive/10 p-2 font-mono text-[11px] text-destructive">
                {errorText}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export const ToolCallCard = memo(ToolCallCardImpl)
