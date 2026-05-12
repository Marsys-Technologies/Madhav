'use client'

import { History } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Props {
  onClick: () => void
  count?: number
  active?: boolean
  className?: string
}

export function ConversationHistoryButton({ onClick, count, active, className }: Props) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Open conversation history"
      title="Conversation history"
      className={cn(
        'inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-medium transition-colors',
        active
          ? 'border-[var(--brand-gold)]/60 bg-[var(--brand-gold)]/10 text-[var(--brand-gold)]'
          : 'border-border text-muted-foreground hover:border-[var(--brand-gold)]/40 hover:text-foreground',
        className,
      )}
    >
      <History className="h-3 w-3" />
      <span>History</span>
      {typeof count === 'number' && count > 0 && (
        <span className="ml-1 rounded-full bg-muted px-1 font-mono text-[10px]">{count}</span>
      )}
    </button>
  )
}
