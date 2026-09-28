'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect, useId, useRef, useState } from 'react'
import { DeleteChartDialog } from '@/components/dialogs/DeleteChartDialog'

/**
 * Understated secondary controls for one chart: Edit chart details, Sharing,
 * Audit, and a separated destructive Delete. Permission-aware: view-only
 * grantees never receive Edit or Delete, Audit is super-admin only, and
 * Sharing follows the existing sharing authorisation (`canShare`).
 *
 * A disclosure (button + list of links), not an ARIA `menu`: Escape and an
 * outside click close it and focus returns to the trigger.
 */
export interface ChartActionsMenuProps {
  chartId: string
  chartName: string
  canBuild: boolean
  isSuperAdmin: boolean
  canShare: boolean
}

const ITEM =
  'jw-touch flex min-h-11 w-full items-center px-4 text-left text-sm text-[var(--jw-ink)] hover:bg-[var(--jw-tint)] focus-visible:bg-[var(--jw-tint)] focus-visible:outline-none'

export function ChartActionsMenu({ chartId, chartName, canBuild, isSuperAdmin, canShare }: ChartActionsMenuProps) {
  const [open, setOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const listId = useId()
  const router = useRouter()

  useEffect(() => {
    if (!open) return
    function onPointerDown(event: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onPointerDown)
    return () => document.removeEventListener('mousedown', onPointerDown)
  }, [open])

  if (!canBuild && !canShare && !isSuperAdmin) return null

  function close() {
    setOpen(false)
    triggerRef.current?.focus()
  }

  return (
    <div
      ref={rootRef}
      className="relative"
      onKeyDown={(event) => {
        if (event.key === 'Escape' && open) {
          event.stopPropagation()
          close()
        }
      }}
    >
      <button
        ref={triggerRef}
        type="button"
        aria-expanded={open}
        aria-controls={listId}
        onClick={() => setOpen((value) => !value)}
        className="jw-control jw-touch inline-flex min-h-11 items-center gap-2 border border-[var(--jw-rule)] px-3 text-xs uppercase tracking-[0.18em] text-[var(--jw-ink-dim)] hover:border-[var(--jw-rule-strong)] hover:text-[var(--jw-ink)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--jw-gold)]"
      >
        <span>Chart actions</span>
        <span aria-hidden="true">⋯</span>
      </button>

      {open && (
        <ul
          id={listId}
          className="absolute right-0 top-full z-30 mt-2 min-w-56 overflow-hidden rounded-md border border-[var(--jw-rule-strong)] bg-[var(--jw-raise)] py-1 shadow-lg"
        >
          {canBuild && (
            <li>
              <Link href={`/clients/${chartId}/edit`} className={ITEM} onClick={() => setOpen(false)}>
                Edit chart details
              </Link>
            </li>
          )}
          {canShare && (
            <li>
              <Link href="#sharing" className={ITEM} onClick={() => setOpen(false)}>
                Sharing
              </Link>
            </li>
          )}
          {isSuperAdmin && (
            <li>
              <Link href={`/cockpit/audit?chart=${chartId}`} className={ITEM} onClick={() => setOpen(false)}>
                Audit log
              </Link>
            </li>
          )}
          {canBuild && (
            <li className="mt-1 border-t border-[var(--jw-rule)] pt-1">
              <button
                type="button"
                className={`${ITEM} text-[var(--jw-danger)]`}
                onClick={() => {
                  setOpen(false)
                  setDeleteOpen(true)
                }}
              >
                Delete chart
              </button>
            </li>
          )}
        </ul>
      )}

      {canBuild && (
        <DeleteChartDialog
          chartId={chartId}
          chartName={chartName}
          open={deleteOpen}
          onClose={() => {
            setDeleteOpen(false)
            triggerRef.current?.focus()
          }}
          onDeleted={() => {
            setDeleteOpen(false)
            router.push('/dashboard')
            router.refresh()
          }}
        />
      )}
    </div>
  )
}
