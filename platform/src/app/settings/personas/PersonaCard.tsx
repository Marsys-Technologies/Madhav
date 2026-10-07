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
  const [error,setError]=useState<string|null>(null)

  if (editing) {
    return (
      <div className="j5-panel">
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
    <div className="j5-panel j5-persona-card space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-sm text-zinc-100">{persona.name}</h3>
            {persona.is_default && (
              <span className="rounded bg-[#20190d] px-1.5 py-0.5 text-[10px] font-medium text-[#ecc56a] border border-[#604720]">
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
        <div className="j5-actions">
          {!persona.is_default && <Button className="j1-btn j1-btn-secondary" onClick={async()=>{try{setError(null);await onUpdate(persona.id,{is_default:true})}catch{setError('Default persona could not be saved. Try again.')}}}>Make default</Button>}
          <Button size="sm" variant="outline" onClick={() => setEditing(true)}>Edit</Button>
          {confirming ? (
            <div className="flex gap-1">
              <Button
                size="sm"
                variant="destructive"
                disabled={isLast || deleting}
                onClick={async () => {
                  setDeleting(true)
                  try { await onDelete(persona.id) } catch {setError('Persona could not be deleted. Try again.')} finally { setDeleting(false); setConfirming(false) }
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
      {error && <p className="j1-error" role="alert">{error}</p>}
    </div>
  )
}
