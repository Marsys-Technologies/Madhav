'use client'

import type { UIMessage } from 'ai'
import { StreamingMarkdown } from '@/components/chat/StreamingMarkdown'
import { StreamingDots } from '@/components/chat/StreamingDots'
import { AssistantMessage } from '@/components/chat/AssistantMessage'
import { MessageErrorBoundary } from '@/components/chat/MessageErrorBoundary'
import type { Rating } from '@/hooks/useFeedback'
import { cn } from '@/lib/utils'

interface Props {
  messages: UIMessage[]
  isStreaming: boolean
  onStop?: () => void
  onRegenerate?: () => void
  ratings?: Record<string, Rating>
  onRate?: (messageId: string, rating: Rating) => void
  className?: string
}

/**
 * Flag-ON message renderer for the pipeline-v2 path.
 *
 * Streaming tail: bare StreamingMarkdown with caret while the last assistant
 * message is in flight.
 *
 * Completed turns: rendered through AssistantMessage (avatar + actions bar)
 * wrapped in MessageErrorBoundary so a single broken message cannot crash the
 * whole conversation.
 */
export function StreamingAnswer({
  messages,
  isStreaming,
  onRegenerate,
  ratings,
  onRate,
  className,
}: Props) {

  if (messages.length === 0) return null

  if (process.env.NODE_ENV === 'development') {
    // Phase 1 debug: track part-to-message attribution for Q1→Q2 misattribution repro
    messages.forEach(m => {
      const preview = m.parts
        ?.map(p => `${p.type}:${('text' in p ? String((p as { text: unknown }).text).slice(0, 80) : '')}`)
        .join(' | ')
      console.debug('[StreamingAnswer] msg', m.id, m.role, '|', preview)
    })
  }

  return (
    <div role="log" aria-label="Conversation" aria-live="polite" className={cn('flex w-full flex-col', className)}>
      {messages.map((message, idx) => {
        const isLast = idx === messages.length - 1
        const textContent = extractText(message)

        if (message.role === 'user') {
          return (
            <div key={message.id} className="mx-auto w-full max-w-4xl flex justify-end px-4 py-2">
              <div
                className={cn(
                  'max-w-[75%] rounded-2xl border border-border/80 bg-muted/50 px-4 py-2.5',
                  'bt-body text-foreground'
                )}
              >
                {textContent}
              </div>
            </div>
          )
        }

        if (message.role === 'assistant') {
          const isCurrentlyStreaming = isLast && isStreaming

          if (isCurrentlyStreaming) {
            return (
              <div key={message.id} className="mx-auto w-full max-w-4xl px-4 py-2">
                {textContent ? (
                  <StreamingMarkdown isStreaming>
                    {textContent}
                  </StreamingMarkdown>
                ) : (
                  <StreamingDots />
                )}
              </div>
            )
          }

          return (
            <MessageErrorBoundary key={message.id} messageId={message.id}>
              <AssistantMessage
                message={message}
                isStreaming={false}
                isLast={isLast}
                onRegenerate={isLast ? onRegenerate : undefined}
                rating={ratings?.[message.id]}
                onRate={onRate ? (r) => onRate(message.id, r) : undefined}
              />
            </MessageErrorBoundary>
          )
        }

        return null
      })}
    </div>
  )
}

function extractText(message: UIMessage): string {
  if (!message.parts) return ''
  return message.parts
    .filter((p): p is { type: 'text'; text: string } => p.type === 'text')
    .map(p => p.text)
    .join('')
}
