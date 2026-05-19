'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import type { UIMessage } from 'ai'
import type { ConversationBranch } from '@/types/branches'

export type { ConversationBranch }

// Branching: when a user edits a message, the pre-edit message list is
// archived under the edited message id. The user can navigate back through
// archived versions. Branch metadata is persisted to conversation_branches via
// the REST API (AC.9/AC.10 of R8-S1); in-memory state is the source of truth
// for rendering so the UI is never blocked by network.

interface ViewingBranch {
  editId: string
  index: number // 0 = oldest archived branch at this edit point
}

export function useBranches(conversationId: string | undefined) {
  const [branches, setBranches] = useState<Record<string, UIMessage[][]>>({})
  const [viewing, setViewing] = useState<ViewingBranch | null>(null)

  // Hydrate from the server on mount / conversation change (AC.9).
  // Failures are silently swallowed — persistence is additive and must not
  // break the UI if the API is unavailable.
  useEffect(() => {
    if (!conversationId) return
    let cancelled = false
    fetch(`/api/conversations/${conversationId}/branches`)
      .then(r => (r.ok ? r.json() : null))
      .then((data: { branches: ConversationBranch[] } | null) => {
        if (cancelled || !data?.branches?.length) return
        // Rebuild in-memory branch map from persisted metadata.
        // snapshot_jsonb carries the archived UIMessage[], if present.
        setBranches(prev => {
          const next = { ...prev }
          for (const b of data.branches) {
            const snapshot = Array.isArray(b.snapshotJsonb?.messages)
              ? (b.snapshotJsonb.messages as UIMessage[])
              : []
            if (!snapshot.length) continue
            const existing = next[b.editedMessageId] ?? []
            if (!existing.length) next[b.editedMessageId] = [snapshot]
          }
          return next
        })
      })
      .catch(() => {
        // network error — silently ignore
      })
    return () => { cancelled = true }
  }, [conversationId])

  // Clear all branch state whenever we switch conversations.
  useEffect(() => {
    /* eslint-disable react-hooks/set-state-in-effect -- reset branch UI when switching chats */
    setBranches({})
    setViewing(null)
    /* eslint-enable react-hooks/set-state-in-effect */
  }, [conversationId])

  const archiveBranch = useCallback((editId: string, snapshot: UIMessage[]) => {
    // Update in-memory state immediately — does NOT wait for network (AC.10).
    setBranches(b => {
      const existing = b[editId] ?? []
      return { ...b, [editId]: [...existing, snapshot] }
    })
    setViewing(null)

    // Fire-and-forget persistence — failures are intentionally swallowed.
    if (conversationId) {
      fetch(`/api/conversations/${conversationId}/branches`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          edited_message_id: editId,
          snapshot_jsonb: { messages: snapshot },
        }),
      }).catch(() => {
        // persistence failure — branch still available in-memory this session
      })
    }
  }, [conversationId])

  // editId → [oldest … newest-archived, live]. Total count is archived + 1.
  const stats = useMemo(() => {
    const s: Record<string, { total: number; current: number }> = {}
    for (const [editId, arr] of Object.entries(branches)) {
      const total = arr.length + 1
      let current = total - 1 // live
      if (viewing && viewing.editId === editId) current = viewing.index
      s[editId] = { total, current }
    }
    return s
  }, [branches, viewing])

  const goToBranch = useCallback(
    (editId: string, index: number) => {
      const versions = branches[editId]
      if (!versions) return
      const total = versions.length + 1
      if (index < 0 || index >= total) return
      if (index === total - 1) {
        setViewing(null)
      } else {
        setViewing({ editId, index })
      }
    },
    [branches]
  )

  const stepBranch = useCallback(
    (editId: string, delta: -1 | 1) => {
      const s = stats[editId]
      if (!s) return
      goToBranch(editId, s.current + delta)
    },
    [stats, goToBranch]
  )

  // When viewing an archived branch, expose that snapshot; otherwise null so
  // the caller falls back to live messages.
  const viewingMessages = useMemo<UIMessage[] | null>(() => {
    if (!viewing) return null
    return branches[viewing.editId]?.[viewing.index] ?? null
  }, [viewing, branches])

  return {
    branches,
    stats,
    viewing,
    isViewingArchived: viewingMessages !== null,
    viewingMessages,
    archiveBranch,
    goToBranch,
    stepBranch,
    returnToLive: () => setViewing(null),
  }
}
