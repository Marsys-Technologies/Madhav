'use client'

import { cn } from '@/lib/utils'
import { StreamingMarkdown } from '@/components/chat/StreamingMarkdown'
import { StreamingDots } from '@/components/chat/StreamingDots'
import type { ChatLifecycleState } from '@/lib/hooks/useChatLifecycle'

interface Props {
  state: ChatLifecycleState
  finalText: string
  className?: string
}

/**
 * FinalAnswerSlot — stable DOM slot for the final answer text.
 *
 * Always present once the first STATUS event fires (stable slot from
 * submission). Content streams in via finalText accumulated by the
 * chat lifecycle reducer. Renders StreamingDots when composing but
 * finalText is still empty, StreamingMarkdown once text arrives.
 */
export function FinalAnswerSlot({ state, finalText, className }: Props) {
  const isComposing = state === 'composing'
  const isComplete = state === 'complete'
  const isVisible = isComposing || isComplete || finalText !== ''

  if (!isVisible) return null

  return (
    <div className={cn('mx-auto w-full max-w-4xl px-4 py-2', className)}>
      {finalText ? (
        <StreamingMarkdown isStreaming={isComposing}>
          {finalText}
        </StreamingMarkdown>
      ) : isComposing ? (
        <StreamingDots />
      ) : null}
    </div>
  )
}
