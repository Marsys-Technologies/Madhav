import * as React from 'react'
import { cn } from '@/lib/utils'

interface SectionLabelProps {
  children: React.ReactNode
  /** Add the Devanagari double-danda accent. Use for the first/most-prominent section per page. */
  accent?: boolean
  className?: string
}

export function SectionLabel({ children, accent, className }: SectionLabelProps) {
  return (
    <p
      className={cn(
        'mb-3 inline-flex items-center gap-2 bt-label bt-label-upper text-[rgba(212,175,55,0.55)]',
        className,
      )}
    >
      {accent ? (
        <span aria-hidden="true" className="text-[var(--brand-gold)] opacity-60">॥</span>
      ) : null}
      <span>{children}</span>
    </p>
  )
}
