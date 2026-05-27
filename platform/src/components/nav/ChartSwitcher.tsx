'use client'

import { useState, useMemo } from 'react'
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
 *   - /clients/<old>/build/<conversationId> → /clients/<new>/build
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
  const modules = ['consult', 'build', 'consume']
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

  const sorted = useMemo(() => {
    return [...charts].sort((a, b) => {
      const an = (a.name ?? a.id).toLowerCase()
      const bn = (b.name ?? b.id).toLowerCase()
      return an.localeCompare(bn)
    })
  }, [charts])

  const current = charts.find((c) => c.id === currentChartId)
  const label = current?.name ?? currentChartId.slice(0, 8)

  function handleSelect(newId: string) {
    setOpen(false)
    if (newId === currentChartId) return
    try {
      localStorage.setItem(LAST_CHART_STORAGE_KEY, newId)
    } catch {
      /* localStorage unavailable; ignore */
    }
    const href = computeSwitchHref(pathname, newId)
    router.push(href)
  }

  return (
    <div className="relative inline-block text-left" data-testid="chart-switcher">
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        data-testid="chart-switcher-trigger"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center gap-2 rounded-md border border-[rgba(212,175,55,0.28)] bg-[rgba(212,175,55,0.06)] px-3 py-1.5 text-xs font-medium text-[var(--brand-gold)] hover:bg-[rgba(212,175,55,0.12)]"
      >
        <span className="truncate max-w-[180px]">{label}</span>
        <span aria-hidden className="opacity-50">▾</span>
      </button>

      {open && (
        <ul
          role="listbox"
          aria-label="Chart switcher"
          data-testid="chart-switcher-list"
          className="absolute z-50 mt-1 max-h-72 w-64 overflow-auto rounded-md border border-[rgba(212,175,55,0.28)] bg-[rgba(20,15,5,0.96)] py-1 text-xs shadow-xl"
        >
          {sorted.length === 0 && (
            <li className="px-3 py-2 opacity-50">No charts</li>
          )}
          {sorted.map((c) => {
            const isCurrent = c.id === currentChartId
            return (
              <li key={c.id}>
                <button
                  type="button"
                  role="option"
                  aria-selected={isCurrent}
                  data-testid="chart-switcher-option"
                  data-chart-id={c.id}
                  onClick={() => handleSelect(c.id)}
                  className={
                    'flex w-full items-center justify-between gap-2 px-3 py-1.5 text-left transition-colors ' +
                    (isCurrent
                      ? 'bg-[rgba(212,175,55,0.14)] text-[var(--brand-gold)]'
                      : 'text-[rgba(212,175,55,0.75)] hover:bg-[rgba(212,175,55,0.08)] hover:text-[var(--brand-gold)]')
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
