'use client'

import type { UIMessage } from 'ai'
import { UserMessage } from './UserMessage'
import { AssistantMessage } from './AssistantMessage'
import { MessageErrorBoundary } from './MessageErrorBoundary'
import type { Rating } from '@/hooks/useFeedback'

interface BranchStat {
  total: number
  current: number
}

interface Props {
  messages: UIMessage[]
  isStreaming: boolean
  onRegenerate?: () => void
  onEditUserMessage?: (id: string, text: string) => void
  ratings?: Record<string, Rating>
  onRate?: (messageId: string, rating: Rating) => void
  branchStats?: Record<string, BranchStat>
  onStepBranch?: (messageId: string, delta: -1 | 1) => void
}

function extractMessageText(message: UIMessage): string {
  return message.parts
    .filter((p): p is { type: 'text'; text: string } => p.type === 'text')
    .map(p => p.text)
    .join('')
}

export function MessageList({
  messages,
  isStreaming,
  onRegenerate,
  onEditUserMessage,
  ratings,
  onRate,
  branchStats,
  onStepBranch,
}: Props) {
  return (
    <div className="flex flex-col gap-6 py-6">
      {messages.map((message, i) => {
        const isLast = i === messages.length - 1

        if (message.role !== 'user' && message.role !== 'assistant') return null

        return (
          <div
            key={message.id}
            data-message-index={i}
            tabIndex={-1}
            onKeyDown={e => {
              if (e.ctrlKey || e.metaKey || e.altKey) return
              const text = extractMessageText(message)
              if (e.key === 'c') {
                navigator.clipboard.writeText(text).catch(() => {})
              } else if (e.key === 'e' && message.role === 'user') {
                onEditUserMessage?.(message.id, text)
              } else if (e.key === 'r' && message.role === 'assistant') {
                onRegenerate?.()
              }
            }}
            className="focus:outline-none"
          >
            {message.role === 'user' ? (
              <MessageErrorBoundary key={message.id} messageId={message.id}>
                <UserMessage
                  message={message}
                  onEditSubmit={onEditUserMessage}
                  branchTotal={branchStats?.[message.id]?.total}
                  branchCurrent={branchStats?.[message.id]?.current}
                  onStepBranch={onStepBranch ? d => onStepBranch(message.id, d) : undefined}
                />
              </MessageErrorBoundary>
            ) : (
              <MessageErrorBoundary key={message.id} messageId={message.id}>
                <AssistantMessage
                  message={message}
                  isStreaming={isStreaming && isLast}
                  isLast={isLast}
                  onRegenerate={onRegenerate}
                  rating={ratings?.[message.id] ?? null}
                  onRate={onRate ? r => onRate(message.id, r) : undefined}
                />
              </MessageErrorBoundary>
            )}
          </div>
        )
      })}
    </div>
  )
}
