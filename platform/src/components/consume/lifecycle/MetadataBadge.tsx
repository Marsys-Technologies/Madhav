'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { getModelMeta, PROVIDER_LABEL } from '@/lib/models/registry'
import type { ChatLifecycleSnapshot } from '@/lib/hooks/useChatLifecycle'

interface Props {
  modelMeta: ChatLifecycleSnapshot['modelMeta']
  className?: string
}

/**
 * MetadataBadge — per-message model + cost + latency capsule.
 *
 * CO.1: structural stub. Renders when modelMeta is populated (after 'finish').
 * CO.2 evolves this into the full per-message metadata badge with expanded
 * token breakdown replacing the lastAssistantMeta toolbar span (Bug 3.1).
 *
 * Positioned at the end of the assistant message. Compact by default;
 * click to expand full token breakdown.
 */
export function MetadataBadge({ modelMeta, className }: Props) {
  const [expanded, setExpanded] = useState(false)

  if (!modelMeta) return null

  const meta = getModelMeta(modelMeta.modelId)
  const providerLabel = meta ? PROVIDER_LABEL[meta.provider] : ''
  const modelLabel = meta?.label ?? modelMeta.modelId
  const costStr = modelMeta.cost !== undefined ? `$${modelMeta.cost.toFixed(4)}` : null
  const latencyStr = modelMeta.latencyMs !== undefined
    ? `${(modelMeta.latencyMs / 1000).toFixed(1)}s`
    : null

  const usage = modelMeta.usage as {
    inputTokens?: number
    outputTokens?: number
    reasoningTokens?: number
    cacheReadTokens?: number
    cacheWriteTokens?: number
  } | undefined

  return (
    <div className={cn('mx-auto w-full max-w-4xl px-4 pb-2', className)}>
      <button
        type="button"
        onClick={() => setExpanded(o => !o)}
        className="inline-flex flex-wrap items-center gap-1.5 text-left"
        aria-expanded={expanded}
        aria-label="Model metadata — click to expand"
      >
        <span className="rounded-full border border-border/50 bg-muted/30 px-2.5 py-0.5 text-[11px] text-muted-foreground hover:border-[var(--brand-gold)]/40 hover:text-foreground transition-colors">
          {modelLabel}
        </span>
        {providerLabel && (
          <span className="rounded-full border border-border/50 bg-muted/30 px-2.5 py-0.5 text-[11px] text-muted-foreground hover:border-[var(--brand-gold)]/40 hover:text-foreground transition-colors">
            {providerLabel}
          </span>
        )}
        {costStr && (
          <span className="rounded-full border border-border/50 bg-muted/30 px-2.5 py-0.5 text-[11px] font-mono text-muted-foreground">
            {costStr}
          </span>
        )}
        {latencyStr && (
          <span className="rounded-full border border-border/50 bg-muted/30 px-2.5 py-0.5 text-[11px] font-mono text-muted-foreground">
            {latencyStr}
          </span>
        )}
      </button>

      {expanded && usage && (
        <div className="mt-1.5 rounded-md border border-border/40 bg-muted/20 px-3 py-2">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-[10px] font-mono">
            {usage.inputTokens !== undefined && (
              <>
                <dt className="text-muted-foreground/60">Input tokens</dt>
                <dd className="text-muted-foreground">{usage.inputTokens.toLocaleString()}</dd>
              </>
            )}
            {usage.outputTokens !== undefined && (
              <>
                <dt className="text-muted-foreground/60">Output tokens</dt>
                <dd className="text-muted-foreground">{usage.outputTokens.toLocaleString()}</dd>
              </>
            )}
            {usage.reasoningTokens !== undefined && usage.reasoningTokens > 0 && (
              <>
                <dt className="text-muted-foreground/60">Reasoning tokens</dt>
                <dd className="text-muted-foreground">{usage.reasoningTokens.toLocaleString()}</dd>
              </>
            )}
            {usage.cacheReadTokens !== undefined && usage.cacheReadTokens > 0 && (
              <>
                <dt className="text-muted-foreground/60">Cache read</dt>
                <dd className="text-muted-foreground">{usage.cacheReadTokens.toLocaleString()}</dd>
              </>
            )}
            {usage.cacheWriteTokens !== undefined && usage.cacheWriteTokens > 0 && (
              <>
                <dt className="text-muted-foreground/60">Cache write</dt>
                <dd className="text-muted-foreground">{usage.cacheWriteTokens.toLocaleString()}</dd>
              </>
            )}
          </dl>
        </div>
      )}
    </div>
  )
}
