'use client'

import { useState } from 'react'
import { usePersonas } from '@/hooks/usePersonas'
import { PersonaCard } from './PersonaCard'
import { PersonaForm } from './PersonaForm'
import { Button } from '@/components/ui/button'

export default function PersonasSettingsPage() {
  const { personas, loading, create, update, remove } = usePersonas()
  const [creating, setCreating] = useState(false)

  return (
    <main className="max-w-2xl mx-auto px-4 py-10 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-zinc-100">Personas</h1>
          <p className="text-sm text-zinc-500 mt-0.5">
            Named system prompt variants you can quick-switch in the model picker.
          </p>
        </div>
        {!creating && (
          <Button onClick={() => setCreating(true)} size="sm">
            New Persona
          </Button>
        )}
      </div>

      {creating && (
        <div className="rounded-xl border border-zinc-700 bg-zinc-900/60 p-5">
          <h2 className="text-sm font-semibold text-zinc-200 mb-4">New Persona</h2>
          <PersonaForm
            onSave={async data => {
              await create(data as Parameters<typeof create>[0])
              setCreating(false)
            }}
            onCancel={() => setCreating(false)}
          />
        </div>
      )}

      {loading && personas.length === 0 && (
        <p className="text-sm text-zinc-500">Loading…</p>
      )}

      {!loading && personas.length === 0 && !creating && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 px-6 py-10 text-center">
          <p className="text-sm text-zinc-600">No personas yet.</p>
          <Button className="mt-3" size="sm" onClick={() => setCreating(true)}>
            Create your first persona
          </Button>
        </div>
      )}

      <div className="space-y-3">
        {personas.map(p => (
          <PersonaCard
            key={p.id}
            persona={p}
            isLast={personas.length === 1}
            onUpdate={async (id, data) => { await update(id, data) }}
            onDelete={async (id) => { await remove(id) }}
          />
        ))}
      </div>
    </main>
  )
}
