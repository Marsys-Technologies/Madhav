'use client'

import { cn } from '@/lib/utils'
import type { SlashCommand } from '@/lib/chat-commands'

interface Props {
  commands: SlashCommand[]
  activeIndex: number
  onSelect: (cmd: SlashCommand) => void
}

export function SlashCommandMenu({ commands, activeIndex, onSelect }: Props) {
  if (commands.length === 0) return null

  return (
    <div
      role="listbox"
      aria-label="Slash commands"
      className="absolute bottom-full left-0 right-0 mb-1 mx-4 z-50 max-h-[210px] overflow-y-auto rounded-xl border border-zinc-700 bg-zinc-900 py-1 shadow-xl"
    >
      {commands.map((cmd, idx) => (
        <button
          key={cmd.id}
          type="button"
          role="option"
          aria-selected={idx === activeIndex}
          onMouseDown={e => {
            // mousedown fires before blur — prevent textarea blur
            e.preventDefault()
            onSelect(cmd)
          }}
          className={cn(
            'flex w-full items-start gap-2 px-3 py-1.5 text-left text-sm transition-colors',
            idx === activeIndex
              ? 'bg-zinc-800 text-amber-400'
              : 'text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100'
          )}
        >
          <span className="shrink-0 font-mono text-[11px] text-zinc-400 pt-0.5">/{cmd.name}</span>
          <span className="text-xs text-zinc-400 truncate">{cmd.description}</span>
        </button>
      ))}
    </div>
  )
}
