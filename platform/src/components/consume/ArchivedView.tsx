'use client'

import { useEffect, useState } from 'react'
import { ArrowLeft } from 'lucide-react'

interface ArchivedConversation {
  id: string
  title: string | null
  created_at: string
}

interface Props {
  chartId: string
  activeId: string | null
  onSelect: (id: string) => void
  onBack: () => void
  onUnarchive: (id: string) => void
}

export function ArchivedView({ chartId, activeId, onSelect, onBack, onUnarchive }: Props) {
  const [conversations, setConversations] = useState<ArchivedConversation[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    /* eslint-disable-next-line react-hooks/set-state-in-effect -- initial load in archived view */
    setLoading(true)
    fetch(`/api/conversations?chartId=${encodeURIComponent(chartId)}&module=consume&archived=true`)
      .then(r => (r.ok ? r.json() : null))
      .then((data: { conversations: ArchivedConversation[] } | null) => {
        if (data?.conversations) setConversations(data.conversations)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [chartId])

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-1.5 px-3 py-2 border-b border-zinc-800">
        <button
          type="button"
          onClick={onBack}
          aria-label="Back to conversations"
          className="flex items-center gap-1 text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <ArrowLeft className="size-3" aria-hidden />
          Archived
        </button>
      </div>

      <div className="flex-1 overflow-y-auto py-1">
        {loading && <p className="px-3 py-2 text-xs text-zinc-500">Loading…</p>}

        {!loading && conversations.length === 0 && (
          <p className="px-3 py-4 text-xs text-zinc-600 text-center">No archived conversations</p>
        )}

        {conversations.map(conv => (
          <div key={conv.id} className="group/arc relative">
            <button
              type="button"
              onClick={() => onSelect(conv.id)}
              className={`w-full text-left px-3 py-2 pr-14 text-xs rounded-md transition-colors truncate ${
                conv.id === activeId
                  ? 'bg-indigo-600/20 text-indigo-300'
                  : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
              }`}
            >
              {conv.title ?? 'Untitled'}
            </button>
            <button
              type="button"
              onClick={() => onUnarchive(conv.id)}
              className="absolute right-2 top-1/2 -translate-y-1/2 invisible group-hover/arc:visible text-[10px] text-zinc-500 hover:text-zinc-200 px-1 py-0.5 rounded hover:bg-zinc-700 transition-colors"
            >
              Restore
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
