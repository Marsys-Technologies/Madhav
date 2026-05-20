'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { cn } from '@/lib/utils'
import { Search } from 'lucide-react'
import type { Command } from '@/lib/chat-commands'

export type { Command }

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  commands: Command[]
}

export function CommandPalette({ open, onOpenChange, commands }: Props) {
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return commands
    return commands.filter(c => {
      const haystack = [c.label, c.hint ?? '', c.keywords ?? ''].join(' ').toLowerCase()
      return haystack.includes(q)
    })
  }, [commands, query])

  useEffect(() => {
    if (!open) {
      /* Reset dialog-local state when closed; syncing UI to dialog open prop */
      /* eslint-disable react-hooks/set-state-in-effect -- intentional reset when dialog closes */
      setQuery('')
      setSelected(0)
      /* eslint-enable react-hooks/set-state-in-effect */
      return
    }
    // Give the Dialog a tick to mount, then steal focus to the input.
    const id = setTimeout(() => inputRef.current?.focus(), 20)
    return () => clearTimeout(id)
  }, [open])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSelected(0)
  }, [query])

  function handleKey(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelected(s => Math.min(s + 1, Math.max(filtered.length - 1, 0)))
      return
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelected(s => Math.max(s - 1, 0))
      return
    }
    if (e.key === 'Enter') {
      e.preventDefault()
      const cmd = filtered[selected]
      if (cmd) {
        onOpenChange(false)
        cmd.run()
      }
    }
  }

  // Group commands by section for display.
  const groups = useMemo(() => {
    const bySection = new Map<string, Command[]>()
    for (const c of filtered) {
      const s = c.section ?? 'Commands'
      if (!bySection.has(s)) bySection.set(s, [])
      bySection.get(s)!.push(c)
    }
    return Array.from(bySection.entries())
  }, [filtered])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg gap-0 overflow-hidden p-0">
        <DialogTitle className="sr-only">Command palette</DialogTitle>
        <div className="flex items-center gap-2 border-b border-border px-3">
          <Search className="size-4 shrink-0 text-muted-foreground" />
          <input
            ref={inputRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Search commands…"
            className="h-11 w-full bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
            aria-label="Search commands"
            role="combobox"
            aria-expanded={filtered.length > 0}
            aria-controls="command-palette-listbox"
            aria-activedescendant={filtered[selected] ? `cmd-${filtered[selected].id}` : undefined}
          />
        </div>
        <div id="command-palette-listbox" role="listbox" aria-label="Commands" className="max-h-80 overflow-y-auto py-1">
          {filtered.length === 0 && (
            <p className="px-3 py-6 text-center text-xs text-muted-foreground">
              No matching commands.
            </p>
          )}
          {groups.map(([section, items]) => (
            <div key={section} className="py-0.5">
              <p className="px-3 pt-2 pb-1 text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
                {section}
              </p>
              {items.map(cmd => {
                const idx = filtered.indexOf(cmd)
                const isActive = idx === selected
                return (
                  <button
                    key={cmd.id}
                    id={`cmd-${cmd.id}`}
                    type="button"
                    role="option"
                    aria-selected={isActive}
                    onMouseEnter={() => setSelected(idx)}
                    onClick={() => {
                      onOpenChange(false)
                      cmd.run()
                    }}
                    className={cn(
                      'flex w-full items-center gap-2.5 px-3 py-1.5 text-left text-sm transition-colors',
                      isActive
                        ? 'bg-muted text-foreground'
                        : 'text-foreground hover:bg-muted/60'
                    )}
                  >
                    <cmd.icon className="size-4 shrink-0 text-muted-foreground" />
                    <span className="flex-1 truncate">{cmd.label}</span>
                    {cmd.hint && (
                      <span className="text-[11px] text-muted-foreground">{cmd.hint}</span>
                    )}
                  </button>
                )
              })}
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  )
}
