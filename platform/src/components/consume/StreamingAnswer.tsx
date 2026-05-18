'use client'

import { useMemo, useEffect } from 'react'
import type { UIMessage } from 'ai'
import { isReasoningUIPart } from 'ai'
import { StreamingMarkdown } from '@/components/chat/StreamingMarkdown'
import { AssistantMessage } from '@/components/chat/AssistantMessage'
import { MessageErrorBoundary } from '@/components/chat/MessageErrorBoundary'
import type { Rating } from '@/hooks/useFeedback'
import { cn } from '@/lib/utils'
import { parseMarkers } from '@/lib/consume/marker_parser'
import { getReasoningMode } from '@/lib/models/registry'
import type {
  ReasoningStepEvent,
  SanskritTerm,
  CorrectionEvent,
  OutOfDomainEvent,
} from '@/types/sse_events'

interface Props {
  messages: UIMessage[]
  isStreaming: boolean
  onStop?: () => void
  onRegenerate?: () => void
  ratings?: Record<string, Rating>
  onRate?: (messageId: string, rating: Rating) => void
  className?: string
  /** Gate III — surface parsed markers from the in-flight assistant message. */
  onMarkers?: (markers: {
    reasoning: ReasoningStepEvent[]
    sanskrit: SanskritTerm[]
    correction: CorrectionEvent | null
    outOfDomain: OutOfDomainEvent | null
    messageId: string | null
  }) => void
}

/**
 * Flag-ON message renderer for the pipeline-v2 path.
 *
 * Gate III adds marker-aware rendering:
 *   - Streamed assistant text is run through `parseMarkers` so ‹reasoning›,
 *     ‹correction›, ‹sanskrit›, and ‹out_of_domain› spans are extracted.
 *   - Markers bubble up via `onMarkers` so ConsumeChat can drive
 *     CorrectionNotice, ReasoningSlot, etc.
 *   - The visible streamed prose has markers stripped (Sanskrit display
 *     text is kept; reasoning/correction/out_of_domain are removed).
 */
export function StreamingAnswer({
  messages,
  isStreaming,
  onRegenerate,
  ratings,
  onRate,
  className,
  onMarkers,
}: Props) {
  // Find the last assistant message + parse its markers once per render.
  // Hooks are declared unconditionally so they run on every render regardless
  // of the empty-message early-return.
  const lastAssistantIdx = (() => {
    for (let i = messages.length - 1; i >= 0; i--) if (messages[i].role === 'assistant') return i
    return -1
  })()
  const lastAssistant = lastAssistantIdx >= 0 ? messages[lastAssistantIdx] : null
  const lastAssistantText = lastAssistant ? extractText(lastAssistant) : ''
  const parsed = useMemo(() => parseMarkers(lastAssistantText), [lastAssistantText])

  // Derive reasoning mode from the synthesis model that produced this message.
  // The model ID is stored in message metadata by the route handler.
  const lastAssistantModelId = (lastAssistant?.metadata as Record<string, unknown> | undefined)
    ?.model as string | undefined
  const reasoningMode = getReasoningMode(lastAssistantModelId ?? '')

  // For 'native' models (Gemini 2.5), reasoning arrives as SDK-level
  // type:'reasoning' UIMessage parts rather than ‹reasoning› text markers.
  // Each reasoning part may contain a multi-line thought block; split by line
  // so the card renders individual steps (matching the ‹reasoning› granularity).
  //
  // Two-level memo: the first derives a stable string from parts content.
  // String deps are compared by value, so nativeReasoningSteps only recomputes
  // when text changes — not when the parts array gets a new reference on each
  // render (which would otherwise cause an infinite loop via the useEffect below).
  const nativeReasoningText = useMemo(() => {
    if (reasoningMode !== 'native' || !lastAssistant?.parts) return ''
    return lastAssistant.parts.filter(isReasoningUIPart).map(p => p.text).join('\x00')
  }, [reasoningMode, lastAssistant?.parts])

  const nativeReasoningSteps = useMemo((): ReasoningStepEvent[] => {
    if (!nativeReasoningText) return []
    const now = Date.now()
    return nativeReasoningText
      .split('\x00')
      .flatMap(block =>
        block
          .split('\n')
          .map((line: string) => line.trim())
          .filter((line: string) => line.length > 0)
          .map((line: string) => ({
            type: 'reasoning_step' as const,
            phase: 'synthesis' as const,
            text: line,
            timestamp: now,
          }))
      )
  }, [nativeReasoningText])

  // Surface markers to parent on every change.
  // For 'native' models, substitute the SDK-extracted reasoning steps in place
  // of the empty marker-parsed array (the gate was stripped from their prompt).
  // For 'markers' models, use the marker-parsed array as before.
  //
  // Use nativeReasoningSteps.length (a primitive) instead of nativeReasoningSteps
  // (an array) as the dep. The array is a new reference on every streaming token;
  // using it would fire this effect on every token, feeding rapid state updates
  // into ConsumeChat.handleMarkers and triggering the re-render cascade.
  const nativeStepsLen = nativeReasoningSteps.length
  useEffect(() => {
    if (!onMarkers) return
    onMarkers({
      reasoning: reasoningMode === 'native' ? nativeReasoningSteps : parsed.reasoning,
      sanskrit: parsed.sanskrit,
      correction: parsed.correction,
      outOfDomain: parsed.outOfDomain,
      messageId: lastAssistant?.id ?? null,
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [parsed, lastAssistant?.id, nativeStepsLen, reasoningMode, onMarkers])

  if (messages.length === 0) return null

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
                  'max-w-[75%] rounded-2xl px-4 py-2.5',
                  'bt-body text-foreground/90',
                  'bg-[rgba(255,255,255,0.06)] backdrop-blur-sm ring-1 ring-white/5',
                )}
              >
                {textContent}
              </div>
            </div>
          )
        }

        if (message.role === 'assistant') {
          const isCurrentlyStreaming = isLast && isStreaming
          const visible = idx === lastAssistantIdx ? parsed.visibleText : parseMarkers(textContent).visibleText

          if (isCurrentlyStreaming) {
            // When there's no visible text yet, return an invisible placeholder.
            if (!visible) return <div key={message.id} aria-hidden />
            return (
              <div key={message.id} className="mx-auto w-full max-w-4xl px-4 py-2">
                <StreamingMarkdown isStreaming>{visible}</StreamingMarkdown>
              </div>
            )
          }

          return (
            <MessageErrorBoundary key={message.id} messageId={message.id}>
              <AssistantMessage
                message={maskedMessage(message, visible)}
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

/**
 * Returns a shallow-cloned message whose text parts are the marker-stripped
 * `visible` string. Used for finalized turns so AssistantMessage doesn't
 * render raw ‹marker› tags.
 */
function maskedMessage(message: UIMessage, visible: string): UIMessage {
  if (!message.parts) return message
  const parts = message.parts.map(p => {
    if (p.type === 'text') return { ...p, text: visible }
    return p
  })
  return { ...message, parts } as UIMessage
}
