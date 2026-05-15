'use client'

import { useMemo, useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ProvenanceEvent } from '@/types/sse_events'
import { ProvenanceDrawer, type ProvenanceTab } from './ProvenanceDrawer'

interface Props {
  provenance: ProvenanceEvent | null
  className?: string
}

/**
 * PostAnswerProvenance — Gate III §9.
 *
 * Collapsed "Details" toggle by default. Click to expand inline pill cluster:
 * [N models] · [N sources] · [N signals] · [Technical].
 * Click any pill → opens ProvenanceDrawer focused on the matching tab.
 */
export function PostAnswerProvenance({ provenance, className }: Props) {
  const [expanded, setExpanded] = useState(false)
  const [openTab, setOpenTab] = useState<ProvenanceTab | null>(null)

  const counts = useMemo(() => {
    if (!provenance) return { models: 0, sources: 0, signals: 0 }
    const sources = provenance.sources.astrological.length
    const signals = provenance.sources.astrological.reduce((s, a) => s + a.items.length, 0)
    return { models: provenance.models.length, sources, signals }
  }, [provenance])

  if (!provenance) return null
  if (counts.models === 0 && counts.sources === 0 && counts.signals === 0) return null

  const pillClass =
    'inline-flex items-center gap-1 rounded-full border border-border/60 bg-muted/30 px-2.5 py-0.5 text-[11px] text-muted-foreground hover:border-[var(--brand-gold)]/60 hover:text-foreground transition-colors'

  return (
    <>
      <span className={cn('inline-flex items-center gap-1.5 flex-wrap', className)}>
        <button
          type="button"
          onClick={() => setExpanded(e => !e)}
          className={pillClass}
          aria-expanded={expanded}
          aria-label="Toggle provenance details"
        >
          <span>Details</span>
          {expanded ? (
            <ChevronUp className="h-3 w-3" />
          ) : (
            <ChevronDown className="h-3 w-3" />
          )}
        </button>
        {expanded && (
          <>
            <button
              type="button"
              onClick={() => setOpenTab('astrological')}
              className={pillClass}
              aria-label="Open provenance — models"
            >
              <span className="font-mono">{counts.models}</span>
              <span>models</span>
            </button>
            <button
              type="button"
              onClick={() => setOpenTab('astrological')}
              className={pillClass}
              aria-label="Open provenance — sources"
            >
              <span className="font-mono">{counts.sources}</span>
              <span>sources</span>
            </button>
            <button
              type="button"
              onClick={() => setOpenTab('astrological')}
              className={pillClass}
              aria-label="Open provenance — signals"
            >
              <span className="font-mono">{counts.signals}</span>
              <span>signals</span>
            </button>
            <button
              type="button"
              onClick={() => setOpenTab('technical')}
              className={cn(pillClass, 'opacity-70')}
              aria-label="Open technical telemetry"
            >
              <span>Technical</span>
            </button>
          </>
        )}
      </span>
      <ProvenanceDrawer
        provenance={provenance}
        open={openTab !== null}
        onOpenChange={o => setOpenTab(o ? (openTab ?? 'astrological') : null)}
        initialTab={openTab ?? 'astrological'}
      />
    </>
  )
}
