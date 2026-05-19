'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, Folder, MoreHorizontal, Pencil, Trash2 } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'

interface FolderMember {
  id: string
  title: string | null
  active: boolean
}

interface Props {
  folderId: string
  folderName: string
  folderColor: string
  members: FolderMember[]
  onSelect: (id: string) => void
  onRename: (id: string, currentName: string) => void
  onDelete: (id: string) => void
  onMemberRemove: (conversationId: string) => void
}

export function FolderGroup({
  folderId,
  folderName,
  folderColor,
  members,
  onSelect,
  onRename,
  onDelete,
}: Props) {
  const [open, setOpen] = useState(true)

  return (
    <div>
      <div className="flex items-center justify-between px-2 pt-2 pb-0.5 group/folder">
        <button
          type="button"
          onClick={() => setOpen(o => !o)}
          className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wide text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          {open ? (
            <ChevronDown className="size-2.5" aria-hidden />
          ) : (
            <ChevronRight className="size-2.5" aria-hidden />
          )}
          <Folder className="size-2.5" style={{ color: folderColor }} aria-hidden />
          <span className="truncate max-w-[100px]">{folderName}</span>
        </button>

        <DropdownMenu>
          <DropdownMenuTrigger
            aria-label={`Folder actions for ${folderName}`}
            className="invisible group-hover/folder:visible inline-flex h-5 w-5 items-center justify-center rounded text-zinc-500 hover:text-zinc-200 hover:bg-zinc-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/30"
          >
            <MoreHorizontal className="h-3 w-3" aria-hidden />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onRename(folderId, folderName)}>
              <Pencil className="h-3.5 w-3.5" aria-hidden />
              Rename
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem variant="destructive" onClick={() => onDelete(folderId)}>
              <Trash2 className="h-3.5 w-3.5" aria-hidden />
              Delete folder
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {open && members.map(m => (
        <button
          key={m.id}
          type="button"
          onClick={() => onSelect(m.id)}
          className={`w-full text-left px-4 py-1.5 text-xs rounded-md transition-colors truncate ${
            m.active
              ? 'bg-indigo-600/20 text-indigo-300'
              : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
          }`}
        >
          {m.title ?? 'Untitled'}
        </button>
      ))}

      {open && members.length === 0 && (
        <p className="px-4 py-1 text-[10px] text-zinc-600 italic">Empty folder</p>
      )}
    </div>
  )
}
