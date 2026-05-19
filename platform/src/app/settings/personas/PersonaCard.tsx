'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { PersonaForm } from './PersonaForm'
import type { Persona, PersonaUpdate } from '@/types/personas'

interface PersonaCardProps {
  persona: Persona
  isLast: boolean
  onUpdate: (id: string, data: PersonaUpdate) => Promise<void>
  onDelete: (id: string) => Promise<void>
}

export function PersonaCard({ persona, isLast, onUpdate, onDelete }: PersonaCardProps) {
  const [editing, setEditing] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [deleting, setDeleting] = useState(false)

  if (editing) {
    return (
      <div className="rounded-xl border border-zinc-700 bg-zinc-900/60 p-5">
        <PersonaForm
          initial={persona}
          onSave={async data => {
            await onUpdate(persona.id, data as PersonaUpdate)
            setEditing(false)
          }}
          onCancel={() => setEditing(false)}
        />
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5 space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-sm text-zinc-100">{persona.name}</h3>
            {persona.is_default && (
              <span className="rounded bg-indigo-900/40 px-1.5 py-0.5 text-[10px] font-medium text-indigo-300 border border-indigo-700/30">
                default
              </span>
            )}
            {persona.default_style && (
              <span className="rounded bg-zinc-700/50 px-1.5 py-0.5 text-[10px] text-zinc-400">
                {persona.default_style}
              </span>
            )}
            {persona.default_stack && (
              <span className="rounded bg-zinc-700/50 px-1.5 py-0.5 text-[10px] text-zinc-400">
                {persona.default_stack}
              </span>
            )}
          </div>
          <p className="mt-1.5 text-xs text-zinc-500 line-clamp-2 leading-relaxed">
            {persona.system_prompt.slice(0, 120)}{persona.system_prompt.length > 120 ? '…' : ''}
          </p>
        </div>
        <div className="flex gap-1.5 shrink-0">
          <Button size="sm" variant="outline" onClick={() => setEditing(true)}>Edit</Button>
          {confirming ? (
            <div className="flex gap-1">
              <Button
                size="sm"
                variant="destructive"
                disabled={isLast || deleting}
                onClick={async () => {
                  setDeleting(true)
                  try { await onDelete(persona.id) } finally { setDeleting(false); setConfirming(false) }
                }}
              >
                {deleting ? '…' : 'Confirm'}
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setConfirming(false)}>Cancel</Button>
            </div>
          ) : (
            <Button
              size="sm"
              variant="ghost"
              disabled={isLast}
              title={isLast ? 'Cannot delete last persona' : 'Delete'}
              onClick={() => setConfirming(true)}
              className="text-zinc-500 hover:text-red-400"
            >
              Delete
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
