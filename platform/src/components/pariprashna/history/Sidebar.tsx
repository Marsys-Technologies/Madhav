'use client'

import { useMemo, useState } from 'react'
import { Sigil } from '@/components/brand/Sigil'
import type { ThreadSummary } from './types'
import { formatRelativeTime } from './relativeTime'
import { useSidebarCollapse } from './useSidebarCollapse'

export interface SidebarProps {
  threads: ThreadSummary[]
  onSelect: (id: string) => void
  /**
   * Local-only rename (no persistence backend in this lane's scope — see
   * `history/types.ts`'s header note). Optional: a caller that hasn't wired
   * persistence yet can omit it and the row simply stays read-only-editable
   * in this session.
   */
  onRename?: (id: string, title: string) => void
}

/** Groups already-sorted-by-recency threads by chart, chart groups ordered
 * by their own most-recent thread (§10.1 F-1: "grouped by chart then
 * recency"). */
function groupByChart(threads: ThreadSummary[]): { chartId: string; chartName: string; threads: ThreadSummary[] }[] {
  const byChart = new Map<string, ThreadSummary[]>()
  for (const t of threads) {
    const list = byChart.get(t.chartId) ?? []
    list.push(t)
    byChart.set(t.chartId, list)
  }
  const groups = Array.from(byChart.entries()).map(([chartId, list]) => ({
    chartId,
    chartName: list[0].chartName,
    threads: [...list].sort((a, b) => b.updatedAtMs - a.updatedAtMs),
  }))
  groups.sort((a, b) => b.threads[0].updatedAtMs - a.threads[0].updatedAtMs)
  return groups
}

function RenameableTitle({ thread, onRename }: { thread: ThreadSummary; onRename?: (id: string, title: string) => void }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(thread.title)

  if (!editing) {
    return (
      <span
        className="pp-band-label"
        style={{ fontFamily: 'var(--pp-font-sans)', fontSize: 13, color: thread.active ? 'var(--pp-ink)' : 'var(--pp-ink-dim)' }}
        // A real double-click fires two constituent `click` events before the
        // `dblclick` — both bubble to the row's onSelect unless stopped here
        // too, not just on the dblclick itself (caught by this component's
        // own test, tests/pariprashna/history/sidebar.test.tsx).
        onClick={(e) => e.stopPropagation()}
        onDoubleClick={(e) => {
          e.stopPropagation()
          setDraft(thread.title)
          setEditing(true)
        }}
        title={thread.title}
      >
        {thread.title}
      </span>
    )
  }

  function commit() {
    const trimmed = draft.trim()
    setEditing(false)
    if (trimmed && trimmed !== thread.title) onRename?.(thread.id, trimmed)
  }

  return (
    <input
      autoFocus
      value={draft}
      onChange={(e) => setDraft(e.target.value)}
      onClick={(e) => e.stopPropagation()}
      onBlur={commit}
      onKeyDown={(e) => {
        // Must stop propagation, not just preventDefault: the row itself
        // treats a bare Enter/Space as "activate this row" (keyboard parity
        // with its onClick) — without this, committing a rename by pressing
        // Enter also fires onSelect on the row underneath (caught by this
        // component's own test).
        e.stopPropagation()
        if (e.key === 'Enter') {
          e.preventDefault()
          commit()
        } else if (e.key === 'Escape') {
          e.preventDefault()
          setEditing(false)
        }
      }}
      style={{
        font: 'inherit',
        fontSize: 13,
        color: 'var(--pp-ink)',
        background: 'var(--pp-surface)',
        border: '1px solid var(--pp-rule-strong)',
        borderRadius: 4,
        padding: '1px 4px',
        width: '100%',
      }}
    />
  )
}

/**
 * The history sidebar (§10.1, §5.8.0 ruling 3, BRIEF_PB-4 Lane F-1):
 * threads grouped by chart then recency; a row = auto-generated title
 * (double-click to rename), chart glyph, relative time, active tick; a
 * streaming thread shows a quiet gold dot. Collapsible to icons, collapse
 * state remembered per user. Selection swaps in-shell state — this
 * component never navigates/reloads; the caller (`PariprashnaApp`) decides
 * what "select" means.
 *
 * Search (§10.1: "Search deferred if no server index exists — record,
 * don't stub-fake") is deliberately absent: no server-side thread index
 * exists yet (see `history/types.ts`), so this renders no search affordance
 * at all rather than a decorative box that filters nothing.
 *
 * Delete/archive (§10.1: "Delete is archival; hard delete native-only,
 * confirmed in the instrument's register") is out of this lane's scope —
 * it needs the same backend this lane doesn't have, so no delete affordance
 * is rendered rather than a fake one.
 */
export function Sidebar({ threads, onSelect, onRename }: SidebarProps) {
  const { collapsed, setCollapsed } = useSidebarCollapse()
  const groups = useMemo(() => groupByChart(threads), [threads])
  // Lazy initializer (matches `working/WorkingBand.tsx`'s `useElapsedSeconds`
  // pattern) — `Date.now()` runs once at mount, not on every render, which
  // is what `react-hooks/purity` requires of an otherwise-impure read.
  const [now] = useState(() => Date.now())

  return (
    <div
      data-testid="pp-sidebar"
      className="flex-none flex flex-col overflow-hidden rounded-[14px] transition-[width]"
      style={{
        width: collapsed ? 46 : 232,
        background: 'var(--pp-panel)',
        border: '1px solid var(--pp-rule)',
        transitionDuration: '280ms',
        transitionTimingFunction: 'var(--pp-ease)',
      }}
    >
      <div
        className="flex items-center gap-2.5 px-3.5"
        style={{
          paddingTop: 14,
          paddingBottom: 12,
          borderBottom: collapsed ? 'none' : '1px solid var(--pp-rule)',
          justifyContent: collapsed ? 'center' : undefined,
        }}
      >
        <button
          type="button"
          className="font-mono"
          style={{ background: 'none', border: 'none', color: 'var(--pp-gold-tertiary)', fontSize: 13, cursor: 'pointer', padding: '2px 4px' }}
          onClick={() => setCollapsed(!collapsed)}
          aria-label={collapsed ? 'Expand past readings' : 'Collapse past readings'}
          aria-expanded={!collapsed}
        >
          {collapsed ? '»' : '«'}
        </button>
        {!collapsed && (
          <span style={{ fontFamily: 'var(--pp-font-sans)', fontSize: 11, letterSpacing: '0.28em', textTransform: 'uppercase', color: 'var(--pp-gold)', whiteSpace: 'nowrap' }}>
            Past readings
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-2" role="list" aria-label="Past readings, grouped by chart">
        {groups.length === 0 &&
          (collapsed ? null : (
            <p className="pp-caveat px-1.5" style={{ fontSize: 12.5 }}>
              This reading will appear here once it starts.
            </p>
          ))}

        {groups.map((group) => (
          <div key={group.chartId} className="mb-3">
            {!collapsed && (
              <div
                className="flex items-center gap-1.5 px-1.5 mb-1"
                style={{ fontSize: 9, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--pp-gold-tertiary)' }}
              >
                <Sigil size={11} style={{ color: 'var(--pp-gold-tertiary)' }} />
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{group.chartName}</span>
              </div>
            )}
            {group.threads.map((thread) => (
              <div
                key={thread.id}
                role="listitem"
                tabIndex={0}
                onClick={() => onSelect(thread.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    onSelect(thread.id)
                  }
                }}
                aria-current={thread.active ? 'true' : undefined}
                data-testid="pp-sidebar-row"
                data-thread-id={thread.id}
                data-active={thread.active || undefined}
                data-streaming={thread.streaming || undefined}
                className="flex items-center gap-2 rounded-md cursor-pointer"
                style={{
                  padding: collapsed ? '8px 0' : '7px 8px',
                  justifyContent: collapsed ? 'center' : undefined,
                  background: thread.active ? 'var(--pp-tint)' : undefined,
                  borderLeft: thread.active ? '2px solid var(--pp-gold)' : '2px solid transparent',
                }}
              >
                {collapsed ? (
                  <span style={{ position: 'relative' }} title={thread.title}>
                    <Sigil size={16} style={{ color: thread.active ? 'var(--pp-gold)' : 'var(--pp-ink-dim)' }} />
                    {thread.streaming && (
                      <span
                        aria-hidden
                        data-pp-pulse
                        className="rounded-full"
                        style={{ position: 'absolute', top: -1, right: -1, width: 6, height: 6, background: 'var(--pp-gold)' }}
                      />
                    )}
                  </span>
                ) : (
                  <>
                    <span className="flex-1 min-w-0">
                      <RenameableTitle thread={thread} onRename={onRename} />
                    </span>
                    {thread.streaming && (
                      <span
                        aria-hidden
                        data-pp-pulse
                        data-testid="pp-sidebar-streaming-dot"
                        className="flex-none rounded-full"
                        style={{ width: 6, height: 6, background: 'var(--pp-gold)' }}
                      />
                    )}
                    <span className="flex-none font-mono" style={{ fontSize: 10, color: 'var(--pp-gold-tertiary)' }}>
                      {formatRelativeTime(thread.updatedAtMs, now)}
                    </span>
                  </>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
