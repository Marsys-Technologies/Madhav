'use client'

import { ArrowDown } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Props {
  visible: boolean
  onClick: () => void
  /** X-S6: number of streaming batches received while scrolled away */
  unreadCount?: number
}

export function ScrollToBottomButton({ visible, onClick, unreadCount = 0 }: Props) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={unreadCount > 0 ? `Jump to latest — ${unreadCount} new` : 'Jump to latest'}
      data-testid="v2-scroll-to-bottom-discipline"
      className={cn(
        'pointer-events-auto absolute left-1/2 -translate-x-1/2 inline-flex items-center justify-center gap-1.5 rounded-full border border-border bg-background shadow-md transition-all duration-200',
        'hover:bg-muted focus-visible:ring-3 focus-visible:ring-ring/40 focus-visible:outline-none',
        unreadCount > 0 ? 'h-7 px-3 text-[11px] font-medium' : 'size-9',
        visible ? 'opacity-100 translate-y-0' : 'pointer-events-none opacity-0 translate-y-2'
      )}
      style={{ bottom: 'calc(var(--composer-h, 160px) + 12px)' }}
    >
      <ArrowDown className="size-3.5 text-muted-foreground" />
      {unreadCount > 0 && (
        <span className="text-muted-foreground" data-testid="v2-unread-count">
          {unreadCount} new
        </span>
      )}
    </button>
  )
}
