'use client'

import { useState, useRef, useEffect } from 'react'
import { cn } from '@/lib/utils'
import type { SanskritTerm } from '@/types/sse_events'

interface Props {
  term: SanskritTerm
  className?: string
  children?: React.ReactNode
}

/**
 * SanskritTermSpan — Gate III §8.
 *
 * Hover/focus-revealed tooltip for an inline Sanskrit term. Keyboard
 * accessible. Underlines the term with a dotted indicator so the native
 * sees the affordance.
 */
export function SanskritTermSpan({ term, className, children }: Props) {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLSpanElement | null>(null)

  // Close tooltip when focus leaves the span.
  useEffect(() => {
    if (!open) return
    const onDocClick = (e: MouseEvent) => {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDocClick)
    return () => document.removeEventListener('mousedown', onDocClick)
  }, [open])

  return (
    <span
      ref={containerRef}
      className={cn('relative inline-block', className)}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
    >
      <span
        tabIndex={0}
        role="button"
        aria-describedby={`sanskrit-tt-${term.term}`}
        className="cursor-help underline decoration-dotted decoration-muted-foreground/40 underline-offset-2"
      >
        {children ?? term.term}
      </span>
      {open && (
        <span
          id={`sanskrit-tt-${term.term}`}
          role="tooltip"
          className={cn(
            'absolute bottom-full left-1/2 z-50 mb-1 -translate-x-1/2 whitespace-normal',
            'min-w-[200px] max-w-[320px] rounded-md border border-border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-lg',
          )}
        >
          <span className="block font-medium">{term.term}</span>
          {term.transliteration && (
            <span className="mt-0.5 block font-mono text-[10px] text-muted-foreground">
              {term.transliteration}
            </span>
          )}
          {term.definition && (
            <span className="mt-1 block text-[11px] leading-tight text-foreground/90">
              {term.definition}
            </span>
          )}
        </span>
      )}
    </span>
  )
}
