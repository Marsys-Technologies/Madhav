'use client'

/**
 * EmptyState — Gemini-style welcome.
 *
 * Shown when there are no messages and no conversationId loaded.
 * Minimal: just a centered greeting. The composer below handles input.
 */

import { cn } from '@/lib/utils'

interface Props {
  chartId: string
  chartName: string
  // Kept for API compatibility with ConsumeChat; unused in this minimal layout.
  onPick?: (text: string) => void
  className?: string
}

export function EmptyState({ chartName, className }: Props) {
  const firstName = chartName?.split(/\s+/)[0] ?? ''
  return (
    <div
      className={cn(
        'mx-auto flex h-full w-full max-w-2xl flex-col items-center justify-center px-4',
        className
      )}
    >
      <p className="text-center text-3xl font-normal leading-snug text-foreground/90">
        {firstName ? `Hi ${firstName},` : 'Hi,'}
        <br />
        What&rsquo;s on your mind?
      </p>
    </div>
  )
}
