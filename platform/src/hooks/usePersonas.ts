'use client'

import { useCallback, useEffect, useState } from 'react'
import type { Persona, PersonaCreate, PersonaUpdate } from '@/types/personas'

export function usePersonas() {
  const [personas, setPersonas] = useState<Persona[]>([])
  const [loading, setLoading] = useState(false)

  const reload = useCallback(() => {
    setLoading(true)
    fetch('/api/personas')
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data?.personas)) setPersonas(data.personas as Persona[])
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { reload() }, [reload])

  const create = useCallback(async (payload: PersonaCreate): Promise<Persona | null> => {
    try {
      const r = await fetch('/api/personas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!r.ok) return null
      const data = await r.json()
      reload()
      return data.persona as Persona
    } catch { return null }
  }, [reload])

  const update = useCallback(async (id: string, payload: PersonaUpdate): Promise<Persona | null> => {
    try {
      const r = await fetch(`/api/personas/${encodeURIComponent(id)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!r.ok) return null
      const data = await r.json()
      reload()
      return data.persona as Persona
    } catch { return null }
  }, [reload])

  const remove = useCallback(async (id: string): Promise<{ ok: boolean; lastPersona?: boolean }> => {
    try {
      const r = await fetch(`/api/personas/${encodeURIComponent(id)}`, { method: 'DELETE' })
      if (r.status === 409) return { ok: false, lastPersona: true }
      if (!r.ok) return { ok: false }
      reload()
      return { ok: true }
    } catch { return { ok: false } }
  }, [reload])

  return { personas, loading, reload, create, update, remove }
}
