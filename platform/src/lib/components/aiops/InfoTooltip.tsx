'use client'

import { useState } from 'react'

interface InfoTooltipProps {
  /** Tooltip body text. */
  text: string
  /** Optional accessible label for the trigger (defaults to "More info"). */
  ariaLabel?: string
  /** Tooltip horizontal alignment relative to the trigger. */
  align?: 'left' | 'center' | 'right'
}

export function InfoTooltip({ text, ariaLabel, align = 'left' }: InfoTooltipProps) {
  const [open, setOpen] = useState(false)

  const justify =
    align === 'right'
      ? 'right-0'
      : align === 'center'
        ? 'left-1/2 -translate-x-1/2'
        : 'left-0'

  return (
    <span
      className="relative inline-flex items-center align-middle"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        aria-label={ariaLabel ?? 'More info'}
        aria-expanded={open}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onClick={(e) => { e.preventDefault(); setOpen(o => !o) }}
        className="inline-flex size-3.5 items-center justify-center rounded-full border border-[rgba(var(--brand-gold-rgb),0.32)] text-[9px] font-semibold leading-none text-[var(--brand-gold)] transition-colors hover:bg-[rgba(var(--brand-gold-rgb),0.10)] focus:outline-none focus-visible:ring-1 focus-visible:ring-[var(--brand-gold)]"
      >
        i
      </button>
      {open && (
        <span
          role="tooltip"
          className={[
            'absolute top-full z-50 mt-1.5 w-56 rounded border border-[rgba(var(--brand-gold-rgb),0.22)] bg-popover px-2 py-1.5 text-[10px] leading-relaxed text-popover-foreground shadow-lg',
            justify,
          ].join(' ')}
        >
          {text}
        </span>
      )}
    </span>
  )
}
