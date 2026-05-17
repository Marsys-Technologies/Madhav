'use client'

/**
 * ConversationSidebarV2 — callback-based conversation sidebar for ConsumeChatV2.
 *
 * Drop-in replacement for the inline ConversationSidebar in ConsumeChatV2.tsx.
 * Adds Today / Yesterday / Older date grouping via date-fns while preserving
 * the exact same props interface as the inline component.
 *
 * Part of Chat V2 Chrome Parity Phase C — item C.11.
 */

import { useCallback, useEffect, useMemo, useState } from 'react'
import { isToday, isYesterday, parseISO } from 'date-fns'

// ─── Types ────────────────────────────────────────────────────────────────────

interface ConversationSummary {
  id: string
  title: string | null
  created_at: string
  updated_at: string | null
  archived_at: string | null
}

export interface ConversationSidebarV2Props {
  chartId: string
  activeId: string | null
  onSelect: (id: string) => void
  onNew: () => void
  collapsed: boolean
  onToggle: () => void
}

// ─── Date grouping ────────────────────────────────────────────────────────────

type DateGroup = 'Today' | 'Yesterday' | 'Older'

function getDateGroup(created_at: string): DateGroup {
  const d = parseISO(created_at)
  if (isToday(d)) return 'Today'
  if (isYesterday(d)) return 'Yesterday'
  return 'Older'
}

function groupConversations(
  conversations: ConversationSummary[],
): Array<{ label: DateGroup; items: ConversationSummary[] }> {
  const buckets: Record<DateGroup, ConversationSummary[]> = {
    Today: [],
    Yesterday: [],
    Older: [],
  }
  for (const c of conversations) {
    buckets[getDateGroup(c.created_at)].push(c)
  }
  const ORDER: DateGroup[] = ['Today', 'Yesterday', 'Older']
  return ORDER.filter((label) => buckets[label].length > 0).map((label) => ({
    label,
    items: buckets[label],
  }))
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function SectionHeader({ label }: { label: DateGroup }) {
  return (
    <p className="px-3 pt-3 pb-0.5 text-[10px] font-semibold uppercase tracking-widest text-zinc-500 select-none">
      {label}
    </p>
  )
}

function ConversationItem({
  conv,
  active,
  onSelect,
}: {
  conv: ConversationSummary
  active: boolean
  onSelect: (id: string) => void
}) {
  const [hovered, setHovered] = useState(false)

  return (
    <div
      className="relative group"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <button
        type="button"
        onClick={() => onSelect(conv.id)}
        className={`w-full text-left px-3 py-2 pr-7 text-xs rounded-md transition-colors truncate ${
          active
            ? 'bg-indigo-600/20 text-indigo-300'
            : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
        }`}
        data-testid={`v2-conversation-item-${conv.id}`}
      >
        {conv.title ?? 'Untitled'}
      </button>

      {/* Archive affordance — "…" menu icon, visible on hover */}
      <span
        aria-hidden
        className={`absolute right-1.5 top-1/2 -translate-y-1/2 flex items-center justify-center h-5 w-5 rounded transition-opacity text-zinc-500 hover:text-zinc-300 hover:bg-zinc-700 ${
          hovered ? 'opacity-100' : 'opacity-0'
        }`}
        title="More actions"
        data-testid={`v2-conversation-menu-${conv.id}`}
      >
        {/* Horizontal ellipsis */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 16 16"
          fill="currentColor"
          className="h-3.5 w-3.5"
          aria-hidden
        >
          <circle cx="3" cy="8" r="1.2" />
          <circle cx="8" cy="8" r="1.2" />
          <circle cx="13" cy="8" r="1.2" />
        </svg>
      </span>
    </div>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────

export function ConversationSidebarV2({
  chartId,
  activeId,
  onSelect,
  onNew,
  collapsed,
  onToggle,
}: ConversationSidebarV2Props) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [loading, setLoading] = useState(false)

  const reload = useCallback(() => {
    setLoading(true)
    fetch(`/api/conversations?chartId=${encodeURIComponent(chartId)}&module=consume`)
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data?.conversations)) {
          setConversations(data.conversations as ConversationSummary[])
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [chartId])

  useEffect(() => {
    reload()
  }, [reload])

  const groups = useMemo(() => groupConversations(conversations), [conversations])

  // ── Collapsed strip ────────────────────────────────────────────────────────

  if (collapsed) {
    return (
      <div className="flex flex-col items-center w-10 border-r border-zinc-800 bg-zinc-950 shrink-0">
        <button
          type="button"
          onClick={onToggle}
          title="Expand conversation list"
          className="mt-3 flex h-8 w-8 items-center justify-center rounded-md text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
          data-testid="v2-sidebar-expand"
        >
          {/* Hamburger / list icon */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 16 16"
            fill="none"
            className="h-4 w-4"
            aria-hidden
          >
            <path
              d="M2 4h12M2 8h7M2 12h9"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
        </button>
      </div>
    )
  }

  // ── Expanded sidebar ───────────────────────────────────────────────────────

  return (
    <aside
      className="flex flex-col w-56 shrink-0 border-r border-zinc-800 bg-zinc-950"
      data-testid="v2-conversation-sidebar-v2"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-zinc-800">
        <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wide">
          Conversations
        </span>
        <div className="flex gap-1">
          <button
            type="button"
            onClick={onNew}
            title="New conversation"
            className="flex h-6 w-6 items-center justify-center rounded text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
            data-testid="v2-new-conversation"
          >
            {/* Plus icon */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 16 16"
              fill="none"
              className="h-3.5 w-3.5"
              aria-hidden
            >
              <path
                d="M8 2v12M2 8h12"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </button>
          <button
            type="button"
            onClick={onToggle}
            title="Collapse"
            className="flex h-6 w-6 items-center justify-center rounded text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
            data-testid="v2-sidebar-collapse"
          >
            {/* Left-chevron icon */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 16 16"
              fill="none"
              className="h-3.5 w-3.5"
              aria-hidden
            >
              <path
                d="M10 3L5 8l5 5"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto py-1">
        {loading && conversations.length === 0 && (
          <p className="px-3 py-2 text-xs text-zinc-500">Loading…</p>
        )}

        {!loading && conversations.length === 0 && (
          <p className="px-3 py-4 text-xs text-zinc-600 text-center">No conversations yet</p>
        )}

        {groups.map(({ label, items }) => (
          <div key={label}>
            <SectionHeader label={label} />
            {items.map((conv) => (
              <ConversationItem
                key={conv.id}
                conv={conv}
                active={conv.id === activeId}
                onSelect={onSelect}
              />
            ))}
          </div>
        ))}
      </div>
    </aside>
  )
}
