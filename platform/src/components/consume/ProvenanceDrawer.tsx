'use client'

import { useEffect, useState } from 'react'
import { X, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ProvenanceEvent } from '@/types/sse_events'

export type ProvenanceTab = 'astrological' | 'technical'

interface Props {
  provenance: ProvenanceEvent | null
  open: boolean
  onOpenChange: (open: boolean) => void
  initialTab?: ProvenanceTab
}

/**
 * ProvenanceDrawer — Gate III §9.
 *
 * Right-side slide-in panel with two tabs (Astrological / Technical) that
 * expose the structured provenance assembled by `provenance_assembler.ts`.
 * Internal asset labels are pre-translated server-side; the drawer NEVER
 * shows raw internal IDs in the Astrological tab.
 */
export function ProvenanceDrawer({ provenance, open, onOpenChange, initialTab = 'astrological' }: Props) {
  const [tab, setTab] = useState<ProvenanceTab>(initialTab)
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  useEffect(() => {
    // Reset tab to the caller's `initialTab` whenever the drawer opens.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (open) setTab(initialTab)
  }, [open, initialTab])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onOpenChange(false) }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onOpenChange])

  if (!open || !provenance) return null

  const toggleExpand = (key: string) => {
    setExpanded(prev => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key); else next.add(key)
      return next
    })
  }

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-black/40"
        onClick={() => onOpenChange(false)}
        aria-hidden="true"
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Answer sources and models"
        className={cn(
          'fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col',
          'border-l border-border bg-background shadow-2xl',
        )}
      >
        <header className="flex items-center justify-between border-b border-border px-4 py-3">
          <h2 className="text-sm font-semibold">Sources &amp; models</h2>
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            aria-label="Close"
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </header>
        <nav role="tablist" className="flex border-b border-border">
          {(['astrological', 'technical'] as ProvenanceTab[]).map(name => (
            <button
              key={name}
              role="tab"
              type="button"
              aria-selected={tab === name}
              onClick={() => setTab(name)}
              className={cn(
                'flex-1 px-3 py-2 text-xs font-medium capitalize',
                tab === name
                  ? 'border-b-2 border-[var(--brand-gold)] text-foreground'
                  : 'text-muted-foreground hover:text-foreground',
              )}
            >
              {name}
            </button>
          ))}
        </nav>
        <div className="flex-1 overflow-y-auto px-4 py-3">
          {tab === 'astrological' ? (
            <>
              <section className="mb-4">
                <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Models
                </h3>
                <ul className="space-y-1">
                  {provenance.models.map((m, i) => (
                    <li key={i} className="flex items-center justify-between rounded border border-border/40 px-2 py-1 text-xs">
                      <span className="text-foreground">{m.role}</span>
                      <span className="font-mono text-[10px] text-muted-foreground">{m.model_id}</span>
                    </li>
                  ))}
                </ul>
              </section>
              <section>
                <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Sources
                </h3>
                {provenance.sources.astrological.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No sources retrieved for this answer.</p>
                ) : (
                  <ul className="space-y-1">
                    {provenance.sources.astrological.map(group => {
                      const key = group.asset
                      const isOpen = expanded.has(key)
                      return (
                        <li key={key} className="rounded border border-border/40">
                          <button
                            type="button"
                            onClick={() => toggleExpand(key)}
                            className="flex w-full items-center justify-between px-2 py-1 text-left text-xs"
                            aria-expanded={isOpen}
                          >
                            <span className="text-foreground">{group.label}</span>
                            <span className="flex items-center gap-1 text-muted-foreground">
                              <span>{group.items.length}</span>
                              <ChevronRight className={cn('h-3.5 w-3.5 transition-transform', isOpen && 'rotate-90')} />
                            </span>
                          </button>
                          {isOpen && (
                            <ul className="border-t border-border/30 px-2 py-1">
                              {group.items.length === 0 ? (
                                <li className="py-0.5 text-[11px] text-muted-foreground/70">(referenced; no granular items)</li>
                              ) : (
                                group.items.map(item => (
                                  <li key={item.id} className="py-0.5 text-[11px]">
                                    <span className="text-foreground/90">{item.label}</span>{' '}
                                    <span className="ml-1 font-mono text-[9px] text-muted-foreground/60">{item.id}</span>
                                  </li>
                                ))
                              )}
                            </ul>
                          )}
                        </li>
                      )
                    })}
                  </ul>
                )}
              </section>
            </>
          ) : (
            <ul className="space-y-1">
              {provenance.sources.technical.length === 0 ? (
                <li className="text-xs text-muted-foreground">No technical telemetry captured.</li>
              ) : (
                provenance.sources.technical.map((tag, i) => (
                  <li key={i} className="flex items-center justify-between rounded border border-border/40 px-2 py-1 text-xs">
                    <span className="text-muted-foreground">{tag.label}</span>
                    <span className="font-mono text-foreground">{tag.value}</span>
                  </li>
                ))
              )}
            </ul>
          )}
        </div>
      </aside>
    </>
  )
}
