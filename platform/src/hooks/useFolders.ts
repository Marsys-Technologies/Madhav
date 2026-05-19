'use client'

import { useCallback, useEffect, useState } from 'react'
import type { ConversationFolder } from '@/types/folders'

export function useFolders() {
  const [folders, setFolders] = useState<ConversationFolder[]>([])
  const [loading, setLoading] = useState(false)

  const reload = useCallback(() => {
    setLoading(true)
    fetch('/api/folders')
      .then(r => (r.ok ? r.json() : null))
      .then((data: { folders: ConversationFolder[] } | null) => {
        if (data?.folders) setFolders(data.folders)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    /* eslint-disable-next-line react-hooks/set-state-in-effect -- load folders on mount */
    reload()
  }, [reload])

  const createFolder = useCallback(async (name: string, color?: string) => {
    const r = await fetch('/api/folders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, color }),
    })
    if (r.ok) reload()
    return r.ok
  }, [reload])

  const renameFolder = useCallback(async (id: string, name: string) => {
    const r = await fetch(`/api/folders/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    })
    if (r.ok) reload()
    return r.ok
  }, [reload])

  const deleteFolder = useCallback(async (id: string) => {
    const r = await fetch(`/api/folders/${id}`, { method: 'DELETE' })
    if (r.ok) reload()
    return r.ok
  }, [reload])

  return { folders, loading, createFolder, renameFolder, deleteFolder, reload }
}
