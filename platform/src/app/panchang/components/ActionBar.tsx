'use client'

/**
 * ActionBar — three-button action bar for the /panchang page.
 *
 * Buttons per §4.2 mockup:
 *   1. 🔎 Find Muhurat — opens MuhuratFinderModal (wired in 4C-6-S3)
 *   2. 📅 Export to Calendar — dropdown with three options (wired in 4C-7)
 *   3. 💬 Ask Madhav about this day — navigates to /clients/:id/consume with pre-loaded prompt
 *
 * Sticky bottom on mobile; inline on desktop.
 *
 * Phase: 4C-4-S4 (Item 1); 4C-6-S3 (Item 5 — Find Muhurat wired);
 *        4C-7 (Item 8 — Calendar Export wired)
 */

import { useState, useRef, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Search, CalendarDays, MessageCircle, X, Link, Settings } from 'lucide-react'
import { MuhuratFinderModal } from './MuhuratFinderModal'
import { resolveLocation, resolveChartId } from './PanchangHeader'

// Native's chart client ID — used for Ask-Madhav deep link.
// Phase 4C-8 will enhance this with full context-block deep-linking.
const NATIVE_CLIENT_ID = 'abhisek_mohanty_primary'

interface ActionBarProps {
  /** ISO date string for the currently displayed Panchang day (YYYY-MM-DD) */
  date: string
}

// ── Calendar export sub-components ────────────────────────────────────────────

/**
 * Toast notification — shown briefly after copying feed URL to clipboard.
 */
function Toast({ message, onDismiss }: { message: string; onDismiss: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 3500)
    return () => clearTimeout(t)
  }, [onDismiss])
  return (
    <div
      role="status"
      aria-live="polite"
      className="
        fixed bottom-20 left-1/2 -translate-x-1/2 z-[60]
        rounded-xl border border-[rgba(212,175,55,0.30)] bg-[rgba(28,28,26,0.96)]
        px-4 py-2.5 text-sm font-medium shadow-2xl backdrop-blur-md
      "
      style={{ color: 'var(--brand-gold)' }}
    >
      {message}
    </div>
  )
}

/**
 * Manage subscriptions modal — lists active tokens + revoke button.
 */
function ManageSubscriptionsModal({ onClose }: { onClose: () => void }) {
  // Full token listing requires GET /api/panchang/feed/tokens — deferred to 4C-8.
  // For now, management panel shows revoke-all with an explanatory note.
  const loading = false
  const [revoking, setRevoking] = useState<string | null>(null)
  const [toast, setToast] = useState<string | null>(null)

  async function handleRevokeAll() {
    setRevoking('all')
    try {
      const r = await fetch('/api/panchang/feed/revoke', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const data = (await r.json()) as { revoked: number }
      setToast(`Revoked ${data.revoked} subscription(s). Existing URLs are now invalid.`)
    } catch {
      setToast('Failed to revoke. Please try again.')
    } finally {
      setRevoking(null)
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Manage feed subscriptions"
      className="fixed inset-0 z-50 flex items-center justify-center"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" aria-hidden="true" />
      <div
        className="relative z-10 mx-4 max-w-sm w-full rounded-2xl border border-[rgba(212,175,55,0.20)] bg-[rgba(28,28,26,0.95)] p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          aria-label="Close manage subscriptions"
          className="absolute right-4 top-4 flex h-7 w-7 items-center justify-center rounded-full text-[rgba(212,175,55,0.40)] transition-colors hover:bg-[rgba(212,175,55,0.10)] hover:text-[var(--brand-gold)]"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>

        <p className="font-serif text-xl mb-1" style={{ color: 'var(--brand-gold)' }}>
          Manage Feed Subscriptions
        </p>
        <p className="text-xs text-muted-foreground mb-4">
          Subscribable iCal feed URLs are HMAC-signed and expire after 90 days.
        </p>

        {loading ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : (
          <>
            <p className="text-sm text-muted-foreground mb-4">
              To invalidate all existing feed URLs, click Revoke All below. You can then generate
              a new URL from the Export to Calendar menu.
            </p>

            <button
              onClick={handleRevokeAll}
              disabled={revoking === 'all'}
              className="w-full rounded-lg border border-[rgba(220,80,60,0.30)] bg-[rgba(220,80,60,0.08)] py-2.5 text-sm font-medium transition-colors hover:bg-[rgba(220,80,60,0.15)] disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ color: 'rgba(220,100,80,0.90)' }}
            >
              {revoking === 'all' ? 'Revoking...' : 'Revoke All Active Subscriptions'}
            </button>
          </>
        )}

        {toast && (
          <p className="mt-3 text-xs text-center" style={{ color: 'var(--brand-gold)' }}>
            {toast}
          </p>
        )}
      </div>
    </div>
  )
}

/**
 * Calendar export dropdown — three options:
 *   1. Download today's Panchang as .ics
 *   2. Get subscribable feed URL → copy to clipboard
 *   3. Manage feed subscriptions
 */
function CalendarExportDropdown({
  date,
  location,
  chartId,
  onClose,
  onToast,
}: {
  date: string
  location: { lat: number; lon: number; label: string }
  chartId: string | null
  onClose: () => void
  onToast: (msg: string) => void
}) {
  const [subscribing, setSubscribing] = useState(false)
  const [showManage, setShowManage] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [onClose])

  function handleDownload() {
    const params = new URLSearchParams({
      d: date,
      loc: location.label,
      lat: String(location.lat),
      lon: String(location.lon),
      ...(chartId ? { chart_id: chartId } : {}),
    })
    window.location.href = `/api/panchang/ics?${params.toString()}`
    onClose()
  }

  async function handleSubscribe() {
    setSubscribing(true)
    try {
      const r = await fetch('/api/panchang/feed/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location: location.label.toLowerCase().split(',')[0].trim(),
          personalise: !!chartId,
          chart_id: chartId ?? undefined,
        }),
      })
      if (!r.ok) {
        onToast('Failed to generate feed URL. Please try again.')
        return
      }
      const data = await r.json() as { feed_url: string }
      await navigator.clipboard.writeText(data.feed_url)
      onToast('Feed URL copied! Paste into Google / Apple Calendar to subscribe.')
    } catch {
      onToast('Could not copy to clipboard. Check browser permissions.')
    } finally {
      setSubscribing(false)
      onClose()
    }
  }

  if (showManage) {
    return <ManageSubscriptionsModal onClose={() => { setShowManage(false); onClose() }} />
  }

  return (
    <div
      ref={dropdownRef}
      role="menu"
      aria-label="Calendar export options"
      className="absolute bottom-full mb-2 right-0 z-50 w-72 rounded-xl border border-[rgba(212,175,55,0.20)] bg-[rgba(28,28,26,0.97)] shadow-2xl backdrop-blur-md overflow-hidden"
    >
      {/* Option 1: Download today's .ics */}
      <button
        role="menuitem"
        onClick={handleDownload}
        className="flex w-full items-center gap-3 px-4 py-3 text-sm transition-colors hover:bg-[rgba(212,175,55,0.08)] border-b border-[rgba(212,175,55,0.08)]"
        style={{ color: 'var(--brand-gold)' }}
      >
        <CalendarDays className="h-4 w-4 shrink-0" aria-hidden="true" />
        <span className="text-left">
          <span className="block font-medium">Download today&apos;s Panchang</span>
          <span className="block text-xs mt-0.5" style={{ color: 'rgba(212,175,55,0.55)' }}>
            Save as .ics file
          </span>
        </span>
      </button>

      {/* Option 2: Get subscribable feed URL */}
      <button
        role="menuitem"
        onClick={handleSubscribe}
        disabled={subscribing}
        className="flex w-full items-center gap-3 px-4 py-3 text-sm transition-colors hover:bg-[rgba(212,175,55,0.08)] border-b border-[rgba(212,175,55,0.08)] disabled:opacity-60 disabled:cursor-not-allowed"
        style={{ color: 'var(--brand-gold)' }}
      >
        <Link className="h-4 w-4 shrink-0" aria-hidden="true" />
        <span className="text-left">
          <span className="block font-medium">
            {subscribing ? 'Generating URL...' : 'Get subscribable feed URL'}
          </span>
          <span className="block text-xs mt-0.5" style={{ color: 'rgba(212,175,55,0.55)' }}>
            Copy URL for Google / Apple Calendar
          </span>
        </span>
      </button>

      {/* Option 3: Manage subscriptions */}
      <button
        role="menuitem"
        onClick={() => setShowManage(true)}
        className="flex w-full items-center gap-3 px-4 py-3 text-sm transition-colors hover:bg-[rgba(212,175,55,0.08)]"
        style={{ color: 'rgba(212,175,55,0.70)' }}
      >
        <Settings className="h-4 w-4 shrink-0" aria-hidden="true" />
        <span className="text-left">
          <span className="block font-medium">Manage feed subscriptions</span>
          <span className="block text-xs mt-0.5" style={{ color: 'rgba(212,175,55,0.45)' }}>
            View and revoke active URLs
          </span>
        </span>
      </button>
    </div>
  )
}

export function ActionBar({ date }: ActionBarProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [muhuratOpen, setMuhuratOpen] = useState(false)
  const [exportDropdownOpen, setExportDropdownOpen] = useState(false)
  const [toast, setToast] = useState<string | null>(null)
  const exportBtnRef = useRef<HTMLDivElement>(null)

  // Resolve current location + chart from URL (mirrors PanchangClientView / PanchangHeader)
  const location = resolveLocation(searchParams)
  const chartId = resolveChartId(searchParams)

  function handleAskMadhav() {
    const prompt = encodeURIComponent(
      `Tell me about today's Panchang (${date}) and what it means for me.`,
    )
    router.push(`/clients/${NATIVE_CLIENT_ID}/consume?prompt=${prompt}`)
  }

  return (
    <>
      {/* Muhurat Finder modal — live (4C-6-S3) */}
      {muhuratOpen && (
        <MuhuratFinderModal
          onClose={() => setMuhuratOpen(false)}
          lat={location.lat}
          lon={location.lon}
          tzOffsetMinutes={330}
          chartId={chartId}
        />
      )}

      {/* Toast notification */}
      {toast && <Toast message={toast} onDismiss={() => setToast(null)} />}

      {/* Action bar
          Mobile: sticky bottom, full-width, safe-area padded.
          Desktop (md+): inline row below the panels — centered, max-w-4xl. */}
      <div
        className="
          sticky bottom-0 z-30
          border-t border-[rgba(212,175,55,0.10)]
          bg-[rgba(18,18,16,0.92)] backdrop-blur-md
          px-4 py-3
          pb-[calc(0.75rem+env(safe-area-inset-bottom))]
          md:relative md:bottom-auto md:border-t-0 md:bg-transparent md:backdrop-blur-none md:pb-6
        "
        aria-label="Panchang actions"
        role="group"
      >
        <div className="mx-auto flex max-w-4xl flex-col gap-2 sm:flex-row sm:gap-3">
          {/* Find Muhurat — live in 4C-6-S3 */}
          <button
            onClick={() => setMuhuratOpen(true)}
            aria-label="Find Muhurat — opens Muhurat Finder"
            title="Muhurat Finder"
            className="
              flex flex-1 items-center justify-center gap-2
              rounded-xl border border-[rgba(212,175,55,0.35)] bg-[rgba(212,175,55,0.10)]
              px-4 py-3 text-sm font-semibold
              transition-colors hover:bg-[rgba(212,175,55,0.18)] hover:border-[rgba(212,175,55,0.50)]
              focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-gold)]
            "
            style={{ color: 'var(--brand-gold)' }}
          >
            <Search className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span>Find Muhurat</span>
          </button>

          {/* Export to Calendar — dropdown (4C-7) */}
          <div ref={exportBtnRef} className="relative flex-1">
            <button
              onClick={() => setExportDropdownOpen((v) => !v)}
              aria-label="Export to Calendar — opens export options"
              aria-expanded={exportDropdownOpen}
              aria-haspopup="menu"
              title="Calendar Export"
              className="
                flex w-full items-center justify-center gap-2
                rounded-xl border border-[rgba(212,175,55,0.35)] bg-[rgba(212,175,55,0.10)]
                px-4 py-3 text-sm font-semibold
                transition-colors hover:bg-[rgba(212,175,55,0.18)] hover:border-[rgba(212,175,55,0.50)]
                focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-gold)]
              "
              style={{ color: 'var(--brand-gold)' }}
            >
              <CalendarDays className="h-4 w-4 shrink-0" aria-hidden="true" />
              <span>Export to Calendar</span>
            </button>

            {/* Dropdown — positioned above the button on mobile, below on desktop */}
            {exportDropdownOpen && (
              <CalendarExportDropdown
                date={date}
                location={{
                  lat: location.lat,
                  lon: location.lon,
                  label: location.label ? `${location.label}, IN` : 'Bhubaneswar, IN',
                }}
                chartId={chartId}
                onClose={() => setExportDropdownOpen(false)}
                onToast={(msg) => setToast(msg)}
              />
            )}
          </div>

          {/* Ask Madhav — functional; routes to /clients/:id/consume with pre-loaded prompt */}
          <button
            onClick={handleAskMadhav}
            aria-label="Ask Madhav about this day"
            title="Opens chat with pre-loaded Panchang prompt"
            className="
              flex flex-1 items-center justify-center gap-2
              rounded-xl border border-[rgba(212,175,55,0.35)] bg-[rgba(212,175,55,0.10)]
              px-4 py-3 text-sm font-semibold
              transition-colors hover:bg-[rgba(212,175,55,0.18)] hover:border-[rgba(212,175,55,0.50)]
              focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-gold)]
            "
            style={{ color: 'var(--brand-gold)' }}
          >
            <MessageCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span>Ask Madhav about this day</span>
          </button>
        </div>
      </div>
    </>
  )
}
