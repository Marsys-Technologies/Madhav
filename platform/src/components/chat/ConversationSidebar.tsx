'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect, useMemo, useRef, useState } from 'react'
import {
  MoreHorizontal,
  PenSquare,
  Trash2,
  Plus,
  PanelLeft,
  ArrowLeft,
  Search,
  X,
  Pin,
  PinOff,
} from 'lucide-react'
import { useSidebarState } from '@/lib/hooks/useSidebarState'
import {
  isToday,
  isYesterday,
  differenceInDays,
  parseISO,
  format,
} from 'date-fns'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { ThemeToggle } from './ThemeToggle'

interface ConversationRow {
  id: string
  title: string | null
  created_at: string
}

interface Props {
  chartId: string
  chartName: string
  conversations: ConversationRow[]
  currentConversationId?: string
  onRenamed?: (id: string, title: string) => void
  onDeleted?: (id: string) => void
  onClose?: () => void
  onNavigate?: () => void
  /** Hide the bottom MARSYS-JIS + ThemeToggle footer (used by ConsumeRail). */
  hideFooter?: boolean
  /**
   * Simple/slide-over mode: renders as w-full h-full with no auto-expand
   * rail behaviour. Hides the dashboard link and pin controls.
   */
  simple?: boolean
}

function groupByDate(conversations: ConversationRow[]) {
  const groups = new Map<string, ConversationRow[]>()
  const now = new Date()
  for (const c of conversations) {
    const d = parseISO(c.created_at)
    let bucket: string
    if (isToday(d)) bucket = 'Today'
    else if (isYesterday(d)) bucket = 'Yesterday'
    else {
      const days = differenceInDays(now, d)
      if (days < 7) bucket = 'Previous 7 days'
      else if (days < 30) bucket = 'Previous 30 days'
      else bucket = format(d, 'MMMM yyyy')
    }
    if (!groups.has(bucket)) groups.set(bucket, [])
    groups.get(bucket)!.push(c)
  }
  return Array.from(groups.entries())
}

export function ConversationSidebar({
  chartId,
  chartName,
  conversations,
  currentConversationId,
  onRenamed,
  onDeleted,
  onClose,
  onNavigate,
  hideFooter = false,
  simple = false,
}: Props) {
  const router = useRouter()
  const sidebar = useSidebarState()
  const [query, setQuery] = useState('')
  const [renameTarget, setRenameTarget] = useState<{ id: string; current: string } | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; title: string } | null>(null)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return conversations
    return conversations.filter(c => (c.title ?? 'new chat').toLowerCase().includes(q))
  }, [conversations, query])

  const groups = useMemo(() => groupByDate(filtered), [filtered])
  const searching = query.trim().length > 0

  function handleRename(id: string) {
    const current = conversations.find(c => c.id === id)
    setRenameTarget({ id, current: current?.title ?? '' })
    setRenameValue(current?.title ?? '')
  }

  function handleDelete(id: string) {
    const current = conversations.find(c => c.id === id)
    setDeleteTarget({ id, title: current?.title ?? 'New chat' })
  }

  async function confirmRename() {
    if (!renameTarget) return
    const { id } = renameTarget
    const title = renameValue.trim()
    setRenameTarget(null)
    if (!title || title === renameTarget.current) return
    const res = await fetch(`/api/conversations/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    })
    if (res.ok) onRenamed?.(id, title)
  }

  async function confirmDelete() {
    if (!deleteTarget) return
    const { id, title } = deleteTarget
    setDeleteTarget(null)
    const res = await fetch(`/api/conversations/${id}`, { method: 'DELETE' })
    if (res.ok) {
      onDeleted?.(id)
      if (id === currentConversationId) {
        router.push(`/clients/${chartId}/consume`)
      }
      toast('Conversation deleted', { description: title, duration: 10000 })
    }
  }

  // simple mode: flat full-size container, no auto-expand rail
  const outerCn = simple
    ? 'flex h-full flex-col bg-sidebar text-sidebar-foreground'
    : cn(
        'flex h-full flex-col bg-sidebar text-sidebar-foreground',
        'transition-[width] duration-[250ms] ease-out overflow-hidden',
        sidebar.isMobile
          ? sidebar.state === 'mobile-open'
            ? 'fixed inset-0 z-50 w-full'
            : 'hidden'
          : sidebar.isExpanded
            ? 'w-64'
            : 'w-14',
      )

  const showExpanded = simple || sidebar.isExpanded || sidebar.isMobile

  return (
    <div
      className={outerCn}
      onMouseEnter={simple ? undefined : sidebar.onMouseEnter}
      onMouseLeave={simple ? undefined : sidebar.onMouseLeave}
      data-sidebar-state={simple ? 'simple' : sidebar.state}
    >
      <div className="flex items-center justify-between gap-2 px-3 pt-3 pb-2">
        {/* Dashboard link — hidden in simple mode (back arrow is in ConsumeShell header) */}
        {!simple && (
          <Link
            href="/dashboard"
            className={cn(
              'inline-flex items-center gap-1.5 rounded-md px-1.5 py-1 text-xs text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-foreground',
              !sidebar.isExpanded && !sidebar.isMobile && 'justify-center',
            )}
          >
            <ArrowLeft className="size-3.5 shrink-0" />
            {(sidebar.isExpanded || sidebar.isMobile) && <span>Dashboard</span>}
          </Link>
        )}

        <div className={cn('flex items-center gap-1', simple && 'ml-auto')}>
          {/* Pin button — desktop only, non-simple mode */}
          {!simple && !sidebar.isMobile && (
            <button
              type="button"
              onClick={sidebar.onPinToggle}
              aria-label={sidebar.state === 'pinned-expanded' ? 'Unpin sidebar' : 'Pin sidebar'}
              aria-pressed={sidebar.state === 'pinned-expanded'}
              className="inline-flex size-6 items-center justify-center rounded-md text-muted-foreground/50 hover:bg-sidebar-accent hover:text-foreground"
            >
              {sidebar.state === 'pinned-expanded'
                ? <PinOff className="size-3" />
                : <Pin className="size-3" />
              }
            </button>
          )}
          {/* Close button — simple mode always shows it; non-simple mobile-only */}
          {(simple || onClose || sidebar.isMobile) && (
            <button
              type="button"
              onClick={simple ? onClose : (sidebar.isMobile ? sidebar.onMobileToggle : onClose)}
              aria-label="Close sidebar"
              className={cn(
                'inline-flex size-7 items-center justify-center rounded-md text-muted-foreground hover:bg-sidebar-accent hover:text-foreground',
                !simple && 'md:hidden'
              )}
            >
              <X className="size-4" />
            </button>
          )}
        </div>
      </div>

      {showExpanded && (
        <div className="px-4 pb-3 pt-1">
          <p className="text-[9px] font-semibold uppercase tracking-[0.22em] text-[rgba(var(--brand-gold-rgb),0.38)]">
            Chart
          </p>
          <p className="mt-0.5 truncate font-serif text-[15px] font-medium leading-tight text-[color-mix(in_oklch,var(--brand-gold-cream)_85%,transparent)]">
            {chartName}
          </p>
          <div className="mt-2 h-px bg-[rgba(var(--brand-gold-rgb),0.12)]" />
        </div>
      )}

      <div className="px-3 pb-2 pt-1">
        <button
          type="button"
          onClick={() => router.push(`/clients/${chartId}/consume`)}
          className={cn(
            'w-full inline-flex items-center gap-2 rounded-lg',
            'border border-[var(--brand-gold-hairline)] bg-[var(--brand-charcoal)]/50',
            'px-3 py-2.5 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--brand-cream)]',
            'transition hover:border-[var(--brand-gold)] hover:bg-[var(--brand-charcoal)]/70 hover:text-[var(--brand-gold-light)]',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-gold)]',
            showExpanded ? 'justify-center' : 'justify-center px-2',
          )}
        >
          <Plus className="size-4 shrink-0" />
          {showExpanded && <span>New conversation</span>}
        </button>
      </div>

      {showExpanded && (
      <div className="px-3 pb-2">
        <div className="relative">
          <Search
            className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground"
            aria-hidden
          />
          <input
            type="search"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search conversations…"
            aria-label="Search conversations"
            className="w-full rounded-md border border-border/60 bg-background/50 py-2 pl-8 pr-7 text-sm text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/30"
          />
          {searching && (
            <button
              type="button"
              onClick={() => setQuery('')}
              aria-label="Clear search"
              className="absolute right-1.5 top-1/2 inline-flex size-5 -translate-y-1/2 items-center justify-center rounded text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <X className="size-3" />
            </button>
          )}
        </div>
      </div>
      )}

      <ScrollArea className="flex-1">
        <div className="px-2 pb-4">
          {conversations.length === 0 && (
            <p className="px-3 py-6 text-center text-xs text-muted-foreground">
              No conversations yet.
            </p>
          )}
          {conversations.length > 0 && filtered.length === 0 && (
            <p className="px-3 py-6 text-center text-xs text-muted-foreground">
              No conversations match &ldquo;{query}&rdquo;.
            </p>
          )}
          {groups.map(([label, rows]) => (
            <div key={label} className="mt-3 first:mt-0">
              <p className="px-2 pb-1 text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
                {label}
              </p>
              <ul className="space-y-0.5">
                {rows.map(c => (
                  <ConversationRowItem
                    key={c.id}
                    row={c}
                    chartId={chartId}
                    active={c.id === currentConversationId}
                    onRename={() => handleRename(c.id)}
                    onDelete={() => handleDelete(c.id)}
                    onNavigate={onNavigate}
                  />
                ))}
              </ul>
            </div>
          ))}
        </div>
      </ScrollArea>

      {!hideFooter && (
        <div className="mt-auto border-t border-sidebar-border px-3 py-3 flex justify-center">
          <ThemeToggle />
        </div>
      )}

      {/* Rename dialog */}
      <Dialog open={renameTarget !== null} onOpenChange={(o) => !o && setRenameTarget(null)}>
        <DialogContent className="border-[var(--brand-gold-hairline)] bg-[var(--brand-charcoal)]/95 backdrop-blur-md">
          <DialogHeader>
            <DialogTitle className="font-serif text-[var(--brand-cream)]">Rename conversation</DialogTitle>
            <DialogDescription className="text-[var(--brand-cream)]/60">
              Choose a new title for this conversation.
            </DialogDescription>
          </DialogHeader>
          <Input
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') confirmRename() }}
            autoFocus
            className="border-[var(--brand-gold-hairline)] bg-[var(--brand-charcoal-deep)] text-[var(--brand-cream)] focus-visible:ring-[var(--brand-gold)]"
          />
          <DialogFooter>
            <Button variant="ghost" onClick={() => setRenameTarget(null)}>Cancel</Button>
            <Button
              onClick={confirmRename}
              className="bg-[var(--brand-gold)] text-[var(--brand-charcoal)] hover:bg-[var(--brand-gold-light)]"
            >
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation dialog */}
      <Dialog open={deleteTarget !== null} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <DialogContent className="border-destructive/40 bg-[var(--brand-charcoal)]/95 backdrop-blur-md">
          <DialogHeader>
            <DialogTitle className="font-serif text-[var(--brand-cream)]">Delete conversation?</DialogTitle>
            <DialogDescription className="text-[var(--brand-cream)]/60">
              This will permanently delete &ldquo;<span className="text-[var(--brand-cream)]">{deleteTarget?.title}</span>&rdquo;.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setDeleteTarget(null)}>Cancel</Button>
            <Button variant="destructive" onClick={confirmDelete}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function ConversationRowItem({
  row,
  chartId,
  active,
  onRename,
  onDelete,
  onNavigate,
}: {
  row: ConversationRow
  chartId: string
  active: boolean
  onRename: () => void
  onDelete: () => void
  onNavigate?: () => void
}) {
  const linkRef = useRef<HTMLAnchorElement>(null)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (active) linkRef.current?.scrollIntoView({ block: 'nearest' })
  }, [active])

  const title = row.title ?? 'New chat'

  return (
    <li className="group/row relative">
      <Link
        ref={linkRef}
        href={`/clients/${chartId}/consume/${row.id}`}
        onClick={onNavigate}
        className={cn(
          'block truncate rounded-lg px-3 py-1.5 pr-8 text-sm transition-colors',
          active
            ? 'bg-sidebar-accent text-foreground'
            : 'text-muted-foreground hover:bg-sidebar-accent/60 hover:text-foreground'
        )}
      >
        {title}
      </Link>
      <div
        className={cn(
          'absolute right-1 top-1/2 -translate-y-1/2 transition-opacity',
          open ? 'opacity-100' : 'opacity-0 group-hover/row:opacity-100 focus-within:opacity-100'
        )}
      >
        <DropdownMenu open={open} onOpenChange={setOpen}>
          <DropdownMenuTrigger
            aria-label="Conversation actions"
            className="inline-flex size-6 items-center justify-center rounded-md text-muted-foreground hover:bg-background hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/30"
          >
            <MoreHorizontal className="size-3.5" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" sideOffset={2}>
            <DropdownMenuItem onClick={onRename}>
              <PenSquare className="size-3.5" />
              Rename
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem variant="destructive" onClick={onDelete}>
              <Trash2 className="size-3.5" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </li>
  )
}
