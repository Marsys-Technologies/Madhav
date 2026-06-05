'use client'

/**
 * ChartCreatedToast — Dismissible banner shown after a new chart is created.
 *
 * Reads ?chart_created=[chartId] from the URL (set by the new-chart form on
 * successful submission). Renders a dismissible success banner with a link
 * to open the cockpit for the newly created chart.
 *
 * Automatically hides itself after 12 seconds or when dismissed by the user.
 * Uses useSearchParams so it works in the Next.js App Router without SSR.
 */

import { useSearchParams, useRouter, usePathname } from 'next/navigation'
import { useEffect, useState, useCallback } from 'react'

export function ChartCreatedToast() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()

  const chartId = searchParams.get('chart_created')
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (chartId) setVisible(true)
  }, [chartId])

  // Auto-dismiss after 12 seconds
  useEffect(() => {
    if (!visible) return
    const timer = setTimeout(() => setVisible(false), 12_000)
    return () => clearTimeout(timer)
  }, [visible])

  const dismiss = useCallback(() => {
    setVisible(false)
    // Remove the ?chart_created param from the URL without a page reload
    const params = new URLSearchParams(searchParams.toString())
    params.delete('chart_created')
    const newUrl = params.size > 0 ? `${pathname}?${params.toString()}` : pathname
    router.replace(newUrl, { scroll: false })
  }, [pathname, router, searchParams])

  if (!visible || !chartId) return null

  return (
    <div
      role="status"
      aria-live="polite"
      aria-atomic="true"
      data-testid="chart-created-toast"
      className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 w-full max-w-md"
    >
      <div className="flex items-center gap-3 rounded-xl bg-emerald-950 border border-emerald-700 px-4 py-3 shadow-2xl text-emerald-100">
        {/* Icon */}
        <span
          className="flex-shrink-0 h-8 w-8 rounded-full bg-emerald-700 flex items-center justify-center text-emerald-100 text-base"
          aria-hidden="true"
        >
          ✓
        </span>

        {/* Message */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium">
            Chart created — ready to build.
          </p>
          <p className="text-xs text-emerald-400 mt-0.5 truncate">
            Chart ID: {chartId}
          </p>
        </div>

        {/* Open cockpit link */}
        <a
          href={`/clients/${chartId}/build`}
          className="flex-shrink-0 rounded-lg bg-emerald-700 hover:bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors"
          onClick={dismiss}
          aria-label="Open cockpit for new chart"
        >
          Open cockpit →
        </a>

        {/* Dismiss button */}
        <button
          onClick={dismiss}
          className="flex-shrink-0 rounded p-1 text-emerald-400 hover:text-emerald-100 hover:bg-emerald-800 transition-colors"
          aria-label="Dismiss notification"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  )
}
