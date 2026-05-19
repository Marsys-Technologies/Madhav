'use client'

import { useCallback, useEffect, useState } from 'react'
import type { Project } from '@/types/projects'

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(false)

  const reload = useCallback(() => {
    setLoading(true)
    fetch('/api/projects')
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data?.projects)) setProjects(data.projects as Project[])
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { reload() }, [reload])

  const createProject = useCallback(
    async (name: string, systemPromptAddition?: string): Promise<Project | null> => {
      try {
        const r = await fetch('/api/projects', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, system_prompt_addition: systemPromptAddition ?? null }),
        })
        if (!r.ok) return null
        const data = await r.json()
        reload()
        return data.project as Project
      } catch {
        return null
      }
    },
    [reload],
  )

  return { projects, loading, reload, createProject }
}
