'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import type { Persona, PersonaCreate, PersonaUpdate } from '@/types/personas'

export function usePersonas() {
  const [personas, setPersonas] = useState<Persona[]>([])
  const [loading, setLoading] = useState(true)
  const [error,setError]=useState<string|null>(null)
  const request=useRef<AbortController|null>(null)

  const reload = useCallback(() => {
    request.current?.abort()
    const controller=new AbortController();request.current=controller
    setLoading(true)
    setError(null)
    fetch('/api/personas',{cache:'no-store',signal:controller.signal})
      .then(r => {if(!r.ok)throw Error('load');return r.json()})
      .then(data => {
        if (!Array.isArray(data?.personas))throw Error('load')
        if (!controller.signal.aborted)setPersonas(data.personas as Persona[])
      })
      .catch(() => {if(!controller.signal.aborted)setError('Personas could not be loaded.')})
      .finally(() => {if(!controller.signal.aborted)setLoading(false)})
  }, [])

  useEffect(() => {
    const initialFetch = setTimeout(reload, 0)
    window.addEventListener('madhav:personas',reload)
    return () => {clearTimeout(initialFetch);request.current?.abort();window.removeEventListener('madhav:personas',reload)}
  }, [reload])

  const create = useCallback(async (payload: PersonaCreate): Promise<Persona | null> => {
    try {
      const r = await fetch('/api/personas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!r.ok) return null
      const data = await r.json()
      window.dispatchEvent(new Event('madhav:personas'))
      return data.persona as Persona
    } catch { return null }
  }, [])

  const update = useCallback(async (id: string, payload: PersonaUpdate): Promise<Persona | null> => {
    try {
      const r = await fetch(`/api/personas/${encodeURIComponent(id)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!r.ok) return null
      const data = await r.json()
      window.dispatchEvent(new Event('madhav:personas'))
      return data.persona as Persona
    } catch { return null }
  }, [])

  const remove = useCallback(async (id: string): Promise<{ ok: boolean; lastPersona?: boolean }> => {
    try {
      const r = await fetch(`/api/personas/${encodeURIComponent(id)}`, { method: 'DELETE' })
      if (r.status === 409) return { ok: false, lastPersona: true }
      if (!r.ok) return { ok: false }
      window.dispatchEvent(new Event('madhav:personas'))
      return { ok: true }
    } catch { return { ok: false } }
  }, [])

  return { personas, loading, error, reload, create, update, remove }
}
