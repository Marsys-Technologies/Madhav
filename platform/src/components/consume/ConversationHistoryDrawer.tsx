'use client'

/**
 * ConversationHistoryDrawer — Gate III §10.
 *
 * A search-augmented overlay drawer that lists every prior consume
 * conversation for the current chart. Co-exists with the existing left
 * ConversationSidebar (which is locked design) and provides search +
 * relative-time formatting on top.
 *
 * Triggered by ConversationHistoryButton in the chat header.
 */

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { X, Search } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface ConversationListItem {
  id: string
  title: string | null
  created_at: string
  updated_at?: string | null
}

interface Props {
  chartId: string
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Pre-loaded server-rendered list (passed through from ConsumeChat). */
  initialConversations: ConversationListItem[]
  /** When provided, the matching conversation is highlighted. */
  currentConversationId?: string
}

function relativeTime(iso: string): string {
  const ms = Date.now() - new Date(iso).getTime()
  if (ms < 60_000) return 'just now'
  const minutes = Math.floor(ms / 60_000)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days}d ago`
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export function ConversationHistoryDrawer({
  chartId,
  open,
  onOpenChange,
  initialConversations,
  currentConversationId,
}: Props) {
  const [query, setQuery] = useState('')

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onOpenChange(false) }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onOpenChange])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return initialConversations
    return initialConversations.filter(c => (c.title ?? '').toLowerCase().includes(q))
  }, [initialConversations, query])

  if (!open) return null

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
        aria-label="Conversation history"
        className="fixed inset-y-0 left-0 z-50 flex w-full max-w-sm flex-col border-r border-border bg-background shadow-2xl"
      >
        <header className="flex items-center justify-between border-b border-border px-4 py-3">
          <h2 className="text-sm font-semibold">Conversations</h2>
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            aria-label="Close"
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </header>

        <div className="border-b border-border px-3 py-2">
          <label className="flex items-center gap-2 rounded-md border border-border/60 bg-muted/30 px-2 py-1">
            <Search className="h-3.5 w-3.5 text-muted-foreground" />
            <input
              aria-label="Search conversations"
              type="search"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search titles…"
              className="flex-1 bg-transparent text-xs outline-none placeholder:text-muted-foreground/70"
            />
          </label>
        </div>

        <div className="flex-1 overflow-y-auto">
          {filtered.length === 0 ? (
            <p className="px-4 py-6 text-center text-xs text-muted-foreground">
              {initialConversations.length === 0 ? 'No prior conversations yet.' : 'No conversations match.'}
            </p>
          ) : (
            <ul role="list" className="py-1">
              {filtered.map(c => {
                const active = c.id === currentConversationId
                return (
                  <li key={c.id}>
                    <Link
                      href={`/clients/${chartId}/consume/${c.id}`}
                      onClick={() => onOpenChange(false)}
                      className={cn(
                        'flex items-center justify-between gap-3 px-4 py-2 text-xs transition-colors',
                        active ? 'bg-muted text-foreground' : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground',
                      )}
                    >
                      <span className="min-w-0 flex-1 truncate">
                        {c.title ?? 'Untitled conversation'}
                      </span>
                      <span className="shrink-0 text-[10px] text-muted-foreground/70">
                        {relativeTime(c.updated_at ?? c.created_at)}
                      </span>
                    </Link>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      </aside>
    </>
  )
}
