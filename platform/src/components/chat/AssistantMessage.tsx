'use client'

import type { UIMessage } from 'ai'
import { useCallback, useMemo } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { AssistantSigil } from '@/components/brand/AssistantSigil'
import { StreamingMarkdown } from './StreamingMarkdown'
import { ToolCallCard } from './ToolCallCard'
import { StreamingDots } from './StreamingDots'
import { MessageActions } from './MessageActions'
import { DisclosureTierBadge } from '@/components/disclosure/DisclosureTierBadge'
import type { Rating } from '@/hooks/useFeedback'
import type { AudienceTier } from '@/lib/prompts/types'

function extractText(message: UIMessage): string {
  return message.parts
    .filter(p => p.type === 'text')
    .map(p => (p as { type: 'text'; text: string }).text)
    .join('')
}

interface ToolPart {
  type: string
  state: string
  toolCallId: string
  input?: unknown
  output?: unknown
  errorText?: string
}

function isToolPart(part: unknown): part is ToolPart {
  if (!part || typeof part !== 'object') return false
  const p = part as { type?: unknown }
  return typeof p.type === 'string' && (p.type.startsWith('tool-') || p.type === 'dynamic-tool')
}

function getToolName(part: ToolPart): string {
  if (part.type === 'dynamic-tool') {
    const dyn = part as unknown as { toolName?: string }
    return dyn.toolName ?? 'tool'
  }
  return part.type.replace(/^tool-/, '')
}

interface Props {
  message: UIMessage
  isStreaming: boolean
  isLast: boolean
  onRegenerate?: () => void
  onRegenerateWithModel?: (modelId: string) => void
  rating?: Rating
  onRate?: (rating: Rating) => void
}

export function AssistantMessage({ message, isStreaming, isLast, onRegenerate, onRegenerateWithModel, rating, onRate }: Props) {
  const reduce = useReducedMotion()
  const text = extractText(message)

  const timestamp = useMemo(() => {
    const meta = (message.metadata ?? {}) as Record<string, unknown>
    const raw = meta.created_at ?? (message as unknown as { created_at?: unknown }).created_at
    return typeof raw === 'string' || typeof raw === 'number' ? new Date(raw) : null
  }, [message])

  const hasAnyContent = message.parts.some(p => {
    if (p.type === 'text') return (p as { text: string }).text.length > 0
    if (isToolPart(p)) return true
    if (p.type === 'reasoning') return true
    return false
  })
  const meta = (message.metadata ?? {}) as Record<string, unknown>
  const wasTruncated = !isStreaming && meta.truncated === true
  // Prefer server's canonical names; fall back to legacy *_id keys for
  // messages persisted during the R2 era before the key alignment.
  const modelLabel = (meta.model ?? meta.model_id) as string | undefined
  const styleLabel = (meta.style ?? meta.style_id) as string | undefined
  const tier = meta.disclosure_tier as string | undefined
  const methodologyBlock = meta.methodology_block as string | null | undefined

  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text)
    } catch { }
  }, [text])

  return (
    <motion.div
      initial={reduce ? false : { opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18, ease: 'easeOut' }}
      className="group/message mx-auto w-full max-w-4xl px-4"
    >
      <div className="flex gap-4">
        <div className="flex size-8 shrink-0 items-center justify-center rounded-full border border-[rgba(var(--brand-gold-rgb),0.35)] bg-muted text-[var(--brand-gold)] shadow-sm">
          <AssistantSigil size={18} />
        </div>
        <div className="min-w-0 flex-1 pt-0.5">
          {!hasAnyContent && isStreaming && isLast && (
            <div className="py-2">
              <StreamingDots />
            </div>
          )}
          {message.parts.map((part, idx) => {
            if (part.type === 'text') {
              const isLastTextPart = idx === message.parts.length - 1
              const streamingThisPart = isStreaming && isLast && isLastTextPart
              return (
                <div key={idx}>
                  <StreamingMarkdown isStreaming={streamingThisPart}>{(part as { text: string }).text}</StreamingMarkdown>
                </div>
              )
            }
            if (isToolPart(part)) {
              return (
                <ToolCallCard
                  key={part.toolCallId || idx}
                  toolName={getToolName(part)}
                  state={part.state}
                  input={part.input}
                  output={part.output}
                  errorText={part.errorText}
                />
              )
            }
            if (part.type === 'reasoning') {
              const reasoning = (part as { text: string }).text
              if (!reasoning) return null
              return (
                <details key={idx} className="my-3 rounded-xl border border-border/60 bg-muted/20 px-3 py-2 text-xs">
                  <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                    Reasoning
                  </summary>
                  <p className="mt-2 whitespace-pre-wrap text-muted-foreground">{reasoning}</p>
                </details>
              )
            }
            return null
          })}
          {wasTruncated && (
            <div className="mt-3 rounded-md border px-3 py-2 text-xs" style={{ borderColor: 'color-mix(in oklch, var(--status-warn) 30%, transparent)', backgroundColor: 'var(--status-warn-bg)', color: 'var(--status-warn)' }}>
              <p className="font-medium">Response was truncated.</p>
              <p className="mt-0.5 opacity-80">
                The model hit its output length cap. Ask it to continue to get the rest.
              </p>
            </div>
          )}

          {/* Per-message metadata strip — model, style, disclosure tier, timestamp */}
          {!isStreaming && hasAnyContent && (
            <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-[var(--brand-cream)]/40">
              {modelLabel ? (
                <span className="rounded border border-[var(--brand-gold-hairline)]/60 px-1.5 py-0.5">
                  {modelLabel}
                </span>
              ) : null}
              {styleLabel ? (
                <span className="rounded border border-[var(--brand-gold-hairline)]/60 px-1.5 py-0.5">
                  {styleLabel}
                </span>
              ) : null}
              {tier ? (
                <DisclosureTierBadge
                  tier={tier as AudienceTier}
                  compact
                  methodologyBlock={methodologyBlock ?? null}
                  defaultExpanded={false}
                />
              ) : null}
              {timestamp ? (
                <time dateTime={timestamp.toISOString()} className="font-sans normal-case tracking-normal">
                  {timestamp.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                </time>
              ) : null}
            </div>
          )}

          {!isStreaming && hasAnyContent && (
            <div className="mt-1 -ml-1.5 opacity-0 transition-opacity duration-150 group-hover/message:opacity-100 focus-within:opacity-100">
              <MessageActions
                onCopy={copy}
                onRegenerate={isLast ? onRegenerate : undefined}
                onRegenerateWithModel={isLast ? onRegenerateWithModel : undefined}
                rating={rating}
                onRate={onRate}
                timestamp={timestamp ?? undefined}
              />
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
