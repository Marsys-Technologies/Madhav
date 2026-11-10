'use client'

import { useEffect, useId, useMemo, useRef, useState, type KeyboardEvent } from 'react'
import { useRouter, usePathname } from 'next/navigation'

/**
 * ChartSwitcher (Unit 3.consult_nav, Commit 2).
 *
 * Persists chart selection in two places:
 *   1. localStorage[`marsys.last_chart_id`] — survives refresh + new tabs.
 *   2. URL — the chart_id is already in the path (`/clients/[id]/...`),
 *      so a switch performs router.push() to the same suffix under the
 *      new chart_id, preserving the user's current page (Profile/Build/
 *      Consult/Panchang).
 *
 * "No silent context switch mid-conversation":
 *   - If the user is currently on a Consult conversation
 *     (/clients/[id]/consult/[conversationId]), switching the chart
 *     navigates to the root /clients/[newId]/consult — it does NOT carry
 *     the conversationId across to the new chart (which would be a silent
 *     context switch). This is explicit, deterministic, and asserted by
 *     the unit test.
 *
 * Tier/depth selectors are not present here (tier excision is concurrent).
 */

export interface ChartSwitcherEntry {
  id: string
  name: string | null
}

export interface ChartSwitcherProps {
  currentChartId: string
  charts: ChartSwitcherEntry[]
}

export const LAST_CHART_STORAGE_KEY = 'marsys.last_chart_id'

/**
 * Pure helper exported for unit testing: given the current pathname and
 * the chart we're switching to, compute the destination URL.
 *
 * Rules:
 *   - /clients/<old>/<suffix>  → /clients/<new>/<suffix>
 *   - /clients/<old>/consult/<conversationId> → /clients/<new>/consult
 *     (no silent conversation carry-over)
 *   - /clients/<old>/nirmana/<conversationId> → /clients/<new>/nirmana
 *   - /clients/<old>/consume/<conversationId> → /clients/<new>/consume
 *   - anything else → /clients/<new>
 */
export function computeSwitchHref(currentPath: string, newChartId: string): string {
  const match = currentPath.match(/^\/clients\/([^/]+)(?:\/(.*))?$/)
  if (!match) return `/clients/${newChartId}`
  const suffix = match[2] ?? ''
  if (suffix === '') return `/clients/${newChartId}`
  // Strip a trailing /<conversationId> from build/consult/consume modules
  // to avoid mid-conversation context switches.
  const modules = ['consult', 'nirmana', 'consume']
  for (const mod of modules) {
    if (suffix === mod) return `/clients/${newChartId}/${mod}`
    if (suffix.startsWith(`${mod}/`)) return `/clients/${newChartId}/${mod}`
  }
  return `/clients/${newChartId}/${suffix}`
}

export function ChartSwitcher({ currentChartId, charts }: ChartSwitcherProps) {
  const router = useRouter()
  const pathname = usePathname() || ''
  const [open, setOpen] = useState(false)
  const listId = useId()
  const trigger = useRef<HTMLButtonElement>(null)
  const list = useRef<HTMLUListElement>(null)

  const sorted = useMemo(() => {
    return [...charts].sort((a, b) => {
      const an = (a.name ?? a.id).toLowerCase()
      const bn = (b.name ?? b.id).toLowerCase()
      return an.localeCompare(bn)
    })
  }, [charts])

  const current = charts.find((c) => c.id === currentChartId)
  const label = current?.name ?? currentChartId.slice(0, 8)

  useEffect(() => {
    if (!open) return
    const option = list.current?.querySelector<HTMLElement>('[aria-selected="true"]')
      ?? list.current?.querySelector<HTMLElement>('[role="option"]')
    option?.focus()
  }, [open])

  function handleOptionsKey(event: KeyboardEvent<HTMLUListElement>) {
    if (event.key === 'Escape') {
      event.preventDefault()
      trigger.current?.focus()
      setOpen(false)
      return
    }
    if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) return
    const options = Array.from(list.current?.querySelectorAll<HTMLElement>('[role="option"]') ?? [])
    if (!options.length) return
    event.preventDefault()
    const index = options.indexOf(document.activeElement as HTMLElement)
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? options.length - 1
      : (index + (event.key === 'ArrowDown' ? 1 : -1) + options.length) % options.length
    options[next]?.focus()
  }

  function handleSelect(newId: string) {
    setOpen(false)
    if (newId === currentChartId) {
      trigger.current?.focus()
      return
    }
    try {
      localStorage.setItem(LAST_CHART_STORAGE_KEY, newId)
    } catch {
      /* localStorage unavailable; ignore */
    }
    const href = computeSwitchHref(pathname, newId)
    router.push(href)
  }

  return (
    <div className="relative inline-block max-w-full text-left" data-testid="chart-switcher"
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false)
      }}>
      <button
        ref={trigger}
        type="button"
        aria-label={`Switch chart: ${label}`}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? listId : undefined}
        data-testid="chart-switcher-trigger"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex min-h-11 max-w-full items-center gap-2 rounded-md border border-[var(--folio-boundary)] bg-[var(--folio-panel)] px-3 text-sm font-medium text-[var(--folio-action)] hover:bg-[var(--folio-selected)] focus-visible:outline-2 focus-visible:outline-[var(--folio-focus)]"
      >
        <span className="truncate max-w-[180px]">{label}</span>
        <span aria-hidden className="opacity-50">▾</span>
      </button>

      {open && (
        <ul
          id={listId}
          ref={list}
          onKeyDown={handleOptionsKey}
          role="listbox"
          aria-label="Chart switcher"
          data-testid="chart-switcher-list"
          className="absolute z-50 mt-1 max-h-72 w-64 max-w-[calc(100vw-2rem)] overflow-auto rounded-md border border-[var(--folio-boundary)] bg-[var(--folio-panel)] py-1 text-sm shadow-lg"
        >
          {sorted.length === 0 && (
            <li className="px-3 py-2 text-[var(--folio-muted)]">No charts</li>
          )}
          {sorted.map((c) => {
            const isCurrent = c.id === currentChartId
            return (
              <li key={c.id} role="presentation">
                <button
                  type="button"
                  role="option"
                  tabIndex={-1}
                  aria-selected={isCurrent}
                  data-testid="chart-switcher-option"
                  data-chart-id={c.id}
                  onClick={() => handleSelect(c.id)}
                  className={
                    'flex min-h-11 w-full items-center justify-between gap-2 px-3 py-1.5 text-left focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[var(--folio-focus)] ' +
                    (isCurrent
                      ? 'bg-[var(--folio-selected)] font-semibold text-[var(--folio-action)]'
                      : 'text-[var(--folio-ink)] hover:bg-[var(--folio-selected)]')
                  }
                >
                  <span className="truncate">{c.name ?? c.id.slice(0, 8)}</span>
                  {isCurrent && <span aria-hidden>•</span>}
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
