'use client'

/**
 * ConversationSidebarV2 — callback-based conversation sidebar for ConsumeChatV2.
 *
 * Drop-in replacement for the inline ConversationSidebar in ConsumeChatV2.tsx.
 * Adds Today / Yesterday / Older date grouping via date-fns while preserving
 * the exact same props interface as the inline component.
 *
 * Part of Chat V2 Chrome Parity Phase C — item C.11.
 * R9-S1: Added flag-gated Projects section above conversation list.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { isToday, isYesterday, parseISO } from 'date-fns'
import { Archive, FolderPlus, MoreHorizontal, PenSquare, Pin, PinOff, Search, Trash2 } from 'lucide-react'
import { Logo } from '@/components/brand/Logo'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import { FolderGroup } from './FolderGroup'
import { ArchivedView } from './ArchivedView'
import { useFolders } from '@/hooks/useFolders'
import { useProjects } from '@/hooks/useProjects'
import { ProjectsSection } from '@/components/sidebar/ProjectsSection'
import { NewProjectModal } from '@/components/modals/NewProjectModal'

// ─── Types ────────────────────────────────────────────────────────────────────

interface ConversationSummary {
  id: string
  title: string | null
  created_at: string
  updated_at: string | null
  archived_at: string | null
  pinned?: boolean
  folder_id?: string | null
}

interface SearchResult {
  id: string
  title: string
  snippet: string
}

export interface ConversationSidebarV2Props {
  chartId: string
  activeId: string | null
  onSelect: (id: string) => void
  onNew: () => void
  collapsed: boolean
  onToggle: () => void
  /** E.1: increments each time the server signals a title was set; triggers reload. */
  reloadTrigger?: number
  /** N3: rename conversation via PATCH /api/conversations/[id] */
  onRename?: (id: string, currentTitle: string) => Promise<void> | void
  /** N3: delete (archive) conversation via DELETE /api/conversations/[id] */
  onDelete?: (id: string) => Promise<void> | void
  /** R9-S1: Show Projects section above conversations. Controlled by MARSYS_FLAG_R9_PROJECTS. */
  showProjects?: boolean
}

// ─── Date grouping ────────────────────────────────────────────────────────────

type DateGroup = 'Today' | 'Yesterday' | 'Older'

function getDateGroup(created_at: string): DateGroup {
  const d = parseISO(created_at)
  if (isToday(d)) return 'Today'
  if (isYesterday(d)) return 'Yesterday'
  return 'Older'
}

function groupConversations(
  conversations: ConversationSummary[],
): Array<{ label: DateGroup; items: ConversationSummary[] }> {
  const buckets: Record<DateGroup, ConversationSummary[]> = {
    Today: [],
    Yesterday: [],
    Older: [],
  }
  for (const c of conversations) {
    buckets[getDateGroup(c.created_at)].push(c)
  }
  const ORDER: DateGroup[] = ['Today', 'Yesterday', 'Older']
  return ORDER.filter((label) => buckets[label].length > 0).map((label) => ({
    label,
    items: buckets[label],
  }))
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function SectionHeader({ label }: { label: DateGroup }) {
  return (
    <p className="px-3 pt-3 pb-0.5 text-[9px] font-semibold uppercase tracking-[0.20em] text-[rgba(var(--brand-gold-rgb),0.38)] select-none">
      {label}
    </p>
  )
}

function SearchResultItem({
  result,
  active,
  onSelect,
}: {
  result: SearchResult
  active: boolean
  onSelect: (id: string) => void
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(result.id)}
      className={`w-full text-left px-3 py-2 text-xs rounded-md transition-colors ${
        active
          ? 'bg-indigo-600/20 text-indigo-300'
          : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
      }`}
    >
      <div className="truncate">{result.title}</div>
      {result.snippet && (
        <div className="mt-0.5 truncate text-[10px] text-zinc-600">{result.snippet}</div>
      )}
    </button>
  )
}

function ConversationItem({
  conv,
  active,
  onSelect,
  onRename,
  onDelete,
  onPin,
  onArchive,
  onMoveToFolder,
  folders,
}: {
  conv: ConversationSummary
  active: boolean
  onSelect: (id: string) => void
  onRename?: (id: string, currentTitle: string) => Promise<void> | void
  onDelete?: (id: string) => Promise<void> | void
  onPin?: (id: string, pinned: boolean) => void
  onArchive?: (id: string, archived: boolean) => void
  onMoveToFolder?: (id: string, folderId: string | null) => void
  folders?: Array<{ id: string; name: string }>
}) {
  const [hovered, setHovered] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div
      className="relative group"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <button
        type="button"
        onClick={() => onSelect(conv.id)}
        className={`w-full text-left px-3 py-2 pr-7 text-xs rounded-md transition-colors truncate ${
          active
            ? 'bg-indigo-600/20 text-indigo-300'
            : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
        }`}
        data-testid={`v2-conversation-item-${conv.id}`}
      >
        {conv.pinned && <span className="mr-1 text-amber-500" aria-label="Pinned">📌</span>}
        {conv.title ?? 'Untitled'}
      </button>

      {(hovered || menuOpen) && (
        <DropdownMenu open={menuOpen} onOpenChange={setMenuOpen}>
          <DropdownMenuTrigger
            aria-label="Conversation actions"
            data-testid={`v2-conversation-menu-${conv.id}`}
            className="absolute right-1.5 top-1/2 -translate-y-1/2 inline-flex h-5 w-5 items-center justify-center rounded text-zinc-500 hover:text-zinc-200 hover:bg-zinc-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/30"
          >
            <MoreHorizontal className="h-3.5 w-3.5" aria-hidden />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" sideOffset={2}>
            <DropdownMenuItem
              onClick={() => onRename?.(conv.id, conv.title ?? 'Untitled')}
              data-testid={`v2-conversation-rename-${conv.id}`}
            >
              <PenSquare className="h-3.5 w-3.5" aria-hidden />
              Rename
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onPin?.(conv.id, !conv.pinned)}>
              {conv.pinned ? (
                <><PinOff className="h-3.5 w-3.5" aria-hidden /> Unpin</>
              ) : (
                <><Pin className="h-3.5 w-3.5" aria-hidden /> Pin</>
              )}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onArchive?.(conv.id, !conv.archived_at)}>
              <Archive className="h-3.5 w-3.5" aria-hidden />
              {conv.archived_at ? 'Unarchive' : 'Archive'}
            </DropdownMenuItem>
            {onMoveToFolder && folders && folders.length > 0 && (
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>
                  <FolderPlus className="h-3.5 w-3.5 mr-1" aria-hidden />
                  Move to folder
                </DropdownMenuSubTrigger>
                <DropdownMenuSubContent>
                  {folders.map(f => (
                    <DropdownMenuItem key={f.id} onClick={() => onMoveToFolder(conv.id, f.id)}>
                      {f.name}
                    </DropdownMenuItem>
                  ))}
                  {conv.folder_id && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => onMoveToFolder(conv.id, null)}>
                        Remove from folder
                      </DropdownMenuItem>
                    </>
                  )}
                </DropdownMenuSubContent>
              </DropdownMenuSub>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem
              variant="destructive"
              onClick={() => onDelete?.(conv.id)}
              data-testid={`v2-conversation-delete-${conv.id}`}
            >
              <Trash2 className="h-3.5 w-3.5" aria-hidden />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </div>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────

export function ConversationSidebarV2({
  chartId,
  activeId,
  onSelect,
  onNew,
  collapsed,
  onToggle,
  reloadTrigger,
  onRename,
  onDelete,
  showProjects = false,
}: ConversationSidebarV2Props) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[] | null>(null)
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchError, setSearchError] = useState(false)
  const [showArchived, setShowArchived] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const { folders, createFolder, renameFolder, deleteFolder } = useFolders()

  // R9-S1: Project filter state — null means "all conversations"
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null)
  const [newProjectOpen, setNewProjectOpen] = useState(false)
  const { projects, createProject } = useProjects()

  const reload = useCallback(() => {
    setLoading(true)
    fetch(`/api/conversations?chartId=${encodeURIComponent(chartId)}&module=consume`)
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data?.conversations)) {
          setConversations(data.conversations as ConversationSummary[])
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [chartId])

  useEffect(() => {
    /* eslint-disable-next-line react-hooks/set-state-in-effect -- initial load on mount */
    reload()
  }, [reload])

  // E.1: reload when server signals a title was set (fires once on the first turn).
  useEffect(() => {
    /* eslint-disable-next-line react-hooks/set-state-in-effect -- triggered reload on title change */
    if (reloadTrigger !== undefined && reloadTrigger > 0) reload()
  }, [reloadTrigger, reload])

  // Debounced FTS search — fires after 300ms of no keystroke, only when query >= 2 chars.
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)

    if (searchQuery.length < 2) {
      /* eslint-disable react-hooks/set-state-in-effect -- reset search state on short query */
      setSearchResults(null)
      setSearchError(false)
      /* eslint-enable react-hooks/set-state-in-effect */
      return
    }

    debounceRef.current = setTimeout(() => {
      setSearchLoading(true)
      setSearchError(false)
      fetch(`/api/conversations/search?q=${encodeURIComponent(searchQuery)}&limit=20`)
        .then(r => {
          if (!r.ok) throw new Error('search failed')
          return r.json()
        })
        .then((data: { conversations: SearchResult[] }) => {
          setSearchResults(data.conversations)
        })
        .catch(() => {
          setSearchError(true)
          setSearchResults(null)
        })
        .finally(() => setSearchLoading(false))
    }, 300)

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [searchQuery])


  // Local title filter for short queries (fallback to client-side when search not active).
  const localFiltered = useMemo(() => {
    if (searchQuery.length === 0 || searchQuery.length >= 2) return null
    const lower = searchQuery.toLowerCase()
    return conversations.filter(c => (c.title ?? '').toLowerCase().includes(lower))
  }, [conversations, searchQuery])

  // Mutation helpers — optimistic update + background sync
  const pinConversation = useCallback((id: string, pinned: boolean) => {
    setConversations(prev => prev.map(c => c.id === id ? { ...c, pinned } : c))
    fetch(`/api/conversations/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pinned }),
    }).catch(() => { reload() })
  }, [reload])

  const archiveConversation = useCallback((id: string, archived: boolean) => {
    setConversations(prev =>
      prev.map(c => c.id === id ? { ...c, archived_at: archived ? new Date().toISOString() : null } : c)
    )
    fetch(`/api/conversations/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ archived }),
    }).catch(() => { reload() })
  }, [reload])

  const moveToFolder = useCallback((id: string, folderId: string | null) => {
    setConversations(prev => prev.map(c => c.id === id ? { ...c, folder_id: folderId } : c))
    fetch(`/api/conversations/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder_id: folderId }),
    }).catch(() => { reload() })
  }, [reload])

  const handleNewFolder = useCallback(() => {
    const name = window.prompt('Folder name:')
    if (name?.trim()) createFolder(name.trim())
  }, [createFolder])

  const handleRenameFolder = useCallback((id: string, currentName: string) => {
    const name = window.prompt('New name:', currentName)
    if (name?.trim()) renameFolder(id, name.trim())
  }, [renameFolder])

  // R9-S1: Fetch project conversation IDs for the active project filter
  const [projectConversationIds, setProjectConversationIds] = useState<Set<string>>(new Set())
  useEffect(() => {
    if (!showProjects || !activeProjectId) {
      setProjectConversationIds(new Set())
      return
    }
    fetch(`/api/projects/${encodeURIComponent(activeProjectId)}`)
      .then(r => r.json())
      .then(data => {
        const ids: string[] = data?.project?.conversation_ids ?? []
        setProjectConversationIds(new Set(ids))
      })
      .catch(() => setProjectConversationIds(new Set()))
  }, [showProjects, activeProjectId])

  // R9-S1: Filter conversations by project when a project is selected
  const filteredConversations = useMemo(() => {
    if (!showProjects || activeProjectId === null) return conversations
    return conversations.filter(c => projectConversationIds.has(c.id))
  }, [conversations, showProjects, activeProjectId, projectConversationIds])

  // Derived groupings — apply project filter via filteredConversations
  const pinnedConversations = useMemo(
    () => filteredConversations.filter(c => c.pinned && !c.archived_at),
    [filteredConversations]
  )

  const unfolderedUnpinned = useMemo(
    () => filteredConversations.filter(c => !c.pinned && !c.folder_id && !c.archived_at),
    [filteredConversations]
  )

  // ── Collapsed strip ────────────────────────────────────────────────────────

  if (collapsed) {
    return null
  }

  // ── Archived view ──────────────────────────────────────────────────────────
  if (showArchived) {
    return (
      <aside
        className="flex flex-col w-56 shrink-0 border-r border-[rgba(var(--brand-gold-rgb),0.15)] bg-[rgba(var(--brand-charcoal-rgb),0.55)] backdrop-blur-md"
        data-testid="v2-conversation-sidebar"
      >
        <ArchivedView
          chartId={chartId}
          activeId={activeId}
          onSelect={onSelect}
          onBack={() => setShowArchived(false)}
          onUnarchive={(id) => { archiveConversation(id, false); setShowArchived(false) }}
        />
        <div className="flex items-center justify-center px-3 py-3 border-t border-zinc-800 mt-auto">
          <Logo size="sm" className="opacity-40" />
        </div>
      </aside>
    )
  }

  // ── Expanded sidebar ───────────────────────────────────────────────────────

  return (
    <aside
      className="flex flex-col w-56 shrink-0 border-r border-[rgba(var(--brand-gold-rgb),0.15)] bg-[rgba(var(--brand-charcoal-rgb),0.55)] backdrop-blur-md"
      data-testid="v2-conversation-sidebar"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-zinc-800">
        <span className="text-[9px] font-semibold uppercase tracking-[0.20em] text-[rgba(var(--brand-gold-rgb),0.38)]">
          Conversations
        </span>
        <div className="flex gap-1">
          <button
            type="button"
            onClick={onToggle}
            title="Collapse sidebar"
            className="flex h-6 w-6 items-center justify-center rounded text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
            data-testid="v2-sidebar-collapse"
          >
            {/* ChevronLeft icon */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 16 16"
              fill="none"
              className="h-3.5 w-3.5"
              aria-hidden
            >
              <path
                d="M10 3L5 8l5 5"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
          <button
            type="button"
            onClick={onNew}
            title="New conversation"
            className="flex h-6 w-6 items-center justify-center rounded text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
            data-testid="v2-new-conversation"
          >
            {/* Plus icon */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 16 16"
              fill="none"
              className="h-3.5 w-3.5"
              aria-hidden
            >
              <path
                d="M8 2v12M2 8h12"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* R9-S1: Projects section — only when showProjects=true */}
      {showProjects && (
        <>
          <ProjectsSection
            projects={projects}
            activeProjectId={activeProjectId}
            onSelectProject={setActiveProjectId}
            onNewProject={() => setNewProjectOpen(true)}
          />
          <NewProjectModal
            open={newProjectOpen}
            onClose={() => setNewProjectOpen(false)}
            onCreated={async (name, addition) => {
              await createProject(name, addition)
            }}
          />
        </>
      )}

      {/* Search input */}
      <div className="px-2 pt-2 pb-1">
        <div className="relative flex items-center">
          <Search className="absolute left-2 h-3 w-3 text-zinc-600 pointer-events-none" aria-hidden />
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search…"
            aria-label="Search conversations"
            className="w-full rounded-md border border-zinc-800 bg-zinc-900 py-1 pl-6 pr-2 text-xs text-zinc-300 placeholder-zinc-600 outline-none focus:border-zinc-700 focus:ring-0"
          />
        </div>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto py-1">
        {/* FTS search results mode */}
        {searchQuery.length >= 2 && (
          <>
            {searchLoading && (
              <p className="px-3 py-2 text-xs text-zinc-500">Searching…</p>
            )}
            {searchError && !searchLoading && (
              <p className="px-3 py-2 text-xs text-zinc-500">Search unavailable</p>
            )}
            {!searchLoading && !searchError && searchResults !== null && searchResults.length === 0 && (
              <p className="px-3 py-4 text-xs text-zinc-600 text-center">No results</p>
            )}
            {!searchLoading && !searchError && searchResults !== null && searchResults.length > 0 && (
              <div className="px-1">
                {searchResults.map(result => (
                  <SearchResultItem
                    key={result.id}
                    result={result}
                    active={result.id === activeId}
                    onSelect={onSelect}
                  />
                ))}
              </div>
            )}
          </>
        )}

        {/* Local title filter mode (1 char) */}
        {localFiltered !== null && (
          <>
            {localFiltered.length === 0 && (
              <p className="px-3 py-4 text-xs text-zinc-600 text-center">No results</p>
            )}
            {localFiltered.map(conv => (
              <ConversationItem
                key={conv.id}
                conv={conv}
                active={conv.id === activeId}
                onSelect={onSelect}
                onRename={onRename}
                onDelete={onDelete}
              />
            ))}
          </>
        )}

        {/* Normal mode (no search): Pinned → Folders → Date buckets */}
        {searchQuery.length === 0 && (
          <>
            {loading && conversations.length === 0 && (
              <p className="px-3 py-2 text-xs text-zinc-500">Loading…</p>
            )}

            {!loading && filteredConversations.length === 0 && (
              <p className="px-3 py-4 text-xs text-zinc-600 text-center">
                {activeProjectId ? 'No conversations in this project' : 'No conversations yet'}
              </p>
            )}

            {/* Pinned section */}
            {pinnedConversations.length > 0 && (
              <div>
                <p className="px-3 pt-3 pb-0.5 text-[9px] font-semibold uppercase tracking-[0.20em] text-amber-600/60 select-none">
                  Pinned
                </p>
                {pinnedConversations.map(conv => (
                  <ConversationItem
                    key={conv.id}
                    conv={conv}
                    active={conv.id === activeId}
                    onSelect={onSelect}
                    onRename={onRename}
                    onDelete={onDelete}
                    onPin={pinConversation}
                    onArchive={archiveConversation}
                    onMoveToFolder={moveToFolder}
                    folders={folders}
                  />
                ))}
              </div>
            )}

            {/* Folder sections */}
            {folders.map(folder => {
              const members = conversations.filter(
                c => c.folder_id === folder.id && !c.archived_at
              )
              return (
                <FolderGroup
                  key={folder.id}
                  folderId={folder.id}
                  folderName={folder.name}
                  folderColor={folder.color}
                  members={members.map(c => ({ id: c.id, title: c.title, active: c.id === activeId }))}
                  onSelect={onSelect}
                  onRename={handleRenameFolder}
                  onDelete={deleteFolder}
                  onMemberRemove={(cid) => moveToFolder(cid, null)}
                />
              )
            })}

            {/* Date bucket groups (unfoldered, unpinned, unarchived) */}
            {groupConversations(unfolderedUnpinned).map(({ label, items }) => (
              <div key={label}>
                <SectionHeader label={label} />
                {items.map((conv) => (
                  <ConversationItem
                    key={conv.id}
                    conv={conv}
                    active={conv.id === activeId}
                    onSelect={onSelect}
                    onRename={onRename}
                    onDelete={onDelete}
                    onPin={pinConversation}
                    onArchive={archiveConversation}
                    onMoveToFolder={moveToFolder}
                    folders={folders}
                  />
                ))}
              </div>
            ))}

          </>
        )}
      </div>

      {/* Archived link + New folder button */}
      <div className="flex items-center justify-between px-3 py-1.5 border-t border-zinc-800">
        <button
          type="button"
          onClick={() => setShowArchived(true)}
          className="text-[10px] text-zinc-600 hover:text-zinc-400 transition-colors"
        >
          Archived
        </button>
        <button
          type="button"
          onClick={handleNewFolder}
          title="New folder"
          className="text-[10px] text-zinc-600 hover:text-zinc-400 transition-colors"
        >
          + Folder
        </button>
      </div>

      {/* L4: Brand anchor — low-volume Logo at bottom of expanded sidebar */}
      <div className="flex items-center justify-center px-3 py-3 border-t border-zinc-800 mt-auto">
        <Logo size="sm" className="opacity-40" />
      </div>
    </aside>
  )
}
