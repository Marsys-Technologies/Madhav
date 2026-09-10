'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { Persona, PersonaCreate, PersonaUpdate } from '@/types/personas'

const STYLE_OPTIONS = ['acharya', 'brief', 'client']
// DD-2 (PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md §2): anthropic delisted —
// ANTHROPIC_API_KEY is unprovisioned in production; the stack fails silently.
// Re-enlist by adding 'anthropic' back once a key is provisioned and qualified.
const STACK_OPTIONS = ['google', 'nim', 'deepseek']

interface PersonaFormProps {
  initial?: Persona
  onSave: (data: PersonaCreate | PersonaUpdate) => Promise<void>
  onCancel: () => void
}

export function PersonaForm({ initial, onSave, onCancel }: PersonaFormProps) {
  const [name, setName] = useState(initial?.name ?? '')
  const [prompt, setPrompt] = useState(initial?.system_prompt ?? '')
  const [defaultStyle, setDefaultStyle] = useState(initial?.default_style ?? '')
  const [defaultStack, setDefaultStack] = useState(initial?.default_stack ?? '')
  const [isDefault, setIsDefault] = useState(initial?.is_default ?? false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) { setError('Name required'); return }
    if (name.trim().length > 50) { setError('Name max 50 chars'); return }
    if (!prompt.trim()) { setError('System prompt required'); return }
    if (prompt.trim().length > 4000) { setError('System prompt max 4000 chars'); return }

    setSaving(true)
    setError(null)
    try {
      await onSave({
        name: name.trim(),
        system_prompt: prompt.trim(),
        default_style: defaultStyle || null,
        default_stack: defaultStack || null,
        is_default: isDefault,
      })
    } catch {
      setError('Failed to save. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <p className="text-xs text-red-400">{error}</p>}

      <div className="space-y-1.5">
        <Label htmlFor="persona-name">Name <span className="text-zinc-500">(max 50)</span></Label>
        <Input
          id="persona-name"
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="e.g. Career Focus"
          maxLength={50}
          data-testid="persona-form-name"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="persona-prompt">System prompt <span className="text-zinc-500">(max 4000)</span></Label>
        <textarea
          id="persona-prompt"
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          placeholder="Custom instructions prepended to every query in this persona…"
          rows={6}
          maxLength={4000}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
          data-testid="persona-form-prompt"
        />
        <p className="text-[10px] text-zinc-500">{prompt.length}/4000</p>
      </div>

      <div className="flex gap-3">
        <div className="space-y-1.5 flex-1">
          <Label htmlFor="persona-style">Default style <span className="text-zinc-500">(optional)</span></Label>
          <select
            id="persona-style"
            value={defaultStyle}
            onChange={e => setDefaultStyle(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">— none —</option>
            {STYLE_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div className="space-y-1.5 flex-1">
          <Label htmlFor="persona-stack">Default stack <span className="text-zinc-500">(optional)</span></Label>
          <select
            id="persona-stack"
            value={defaultStack}
            onChange={e => setDefaultStack(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">— none —</option>
            {STACK_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>

      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={isDefault}
          onChange={e => setIsDefault(e.target.checked)}
          className="rounded border-input"
          data-testid="persona-form-default"
        />
        <span className="text-sm">Set as default persona</span>
      </label>

      <div className="flex gap-2 pt-2">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={saving}>Cancel</Button>
        <Button type="submit" disabled={saving}>{saving ? 'Saving…' : (initial ? 'Save changes' : 'Create')}</Button>
      </div>
    </form>
  )
}
