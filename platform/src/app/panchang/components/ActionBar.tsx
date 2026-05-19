'use client'

/**
 * ActionBar — three-button action bar for the /panchang page.
 *
 * Buttons per §4.2 mockup:
 *   1. 🔎 Find Muhurat — shell (Muhurat Finder full impl deferred to 4C-6)
 *   2. 📅 Export to Calendar — shell (deferred to 4C-7)
 *   3. 💬 Ask Madhav about this day — navigates to /clients/:id/consume with pre-loaded prompt
 *
 * Sticky bottom on mobile; inline on desktop.
 *
 * Phase: 4C-4-S4 (Item 1)
 */

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Search, CalendarDays, MessageCircle, X } from 'lucide-react'

// Native's chart client ID — used for Ask-Madhav deep link.
// Phase 4C-8 will enhance this with full context-block deep-linking.
const NATIVE_CLIENT_ID = 'abhisek_mohanty_primary'

interface ActionBarProps {
  /** ISO date string for the currently displayed Panchang day (YYYY-MM-DD) */
  date: string
}

/**
 * Coming-soon modal — shown for unimplemented actions (Muhurat Finder, Calendar Export).
 */
function ComingSoonModal({
  title,
  phase,
  onClose,
}: {
  title: string
  phase: string
  onClose: () => void
}) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`${title} — coming soon`}
      className="fixed inset-0 z-50 flex items-center justify-center"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" aria-hidden="true" />

      {/* Panel */}
      <div
        className="relative z-10 mx-4 max-w-sm w-full rounded-2xl border border-[rgba(212,175,55,0.20)] bg-[rgba(28,28,26,0.95)] p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          aria-label="Close"
          className="absolute right-4 top-4 flex h-7 w-7 items-center justify-center rounded-full text-[rgba(212,175,55,0.40)] transition-colors hover:bg-[rgba(212,175,55,0.10)] hover:text-[var(--brand-gold)]"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>

        <p className="font-serif text-xl" style={{ color: 'var(--brand-gold)' }}>
          {title}
        </p>

        <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
          This feature is coming in <span style={{ color: 'var(--brand-gold)' }}>{phase}</span>.
          The full implementation includes deeper astrological logic for finding auspicious windows
          tailored to your chart.
        </p>

        <button
          onClick={onClose}
          className="mt-5 w-full rounded-lg border border-[rgba(212,175,55,0.20)] bg-[rgba(212,175,55,0.06)] py-2.5 text-sm font-medium transition-colors hover:bg-[rgba(212,175,55,0.12)]"
          style={{ color: 'var(--brand-gold)' }}
        >
          Got it
        </button>
      </div>
    </div>
  )
}

export function ActionBar({ date }: ActionBarProps) {
  const router = useRouter()
  const [modal, setModal] = useState<'muhurat' | 'export' | null>(null)

  function handleAskMadhav() {
    const prompt = encodeURIComponent(
      `Tell me about today's Panchang (${date}) and what it means for me.`,
    )
    router.push(`/clients/${NATIVE_CLIENT_ID}/consume?prompt=${prompt}`)
  }

  return (
    <>
      {/* Coming-soon modals */}
      {modal === 'muhurat' && (
        <ComingSoonModal
          title="🔎 Muhurat Finder"
          phase="Phase 4C-6"
          onClose={() => setModal(null)}
        />
      )}
      {modal === 'export' && (
        <ComingSoonModal
          title="📅 Export to Calendar"
          phase="Phase 4C-7"
          onClose={() => setModal(null)}
        />
      )}

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
          {/* Find Muhurat — shell, coming in 4C-6 */}
          <button
            onClick={() => setModal('muhurat')}
            aria-label="Find Muhurat (coming in Phase 4C-6)"
            title="Muhurat Finder — Phase 4C-6"
            className="
              flex flex-1 items-center justify-center gap-2
              rounded-xl border border-[rgba(212,175,55,0.20)] bg-[rgba(212,175,55,0.05)]
              px-4 py-3 text-sm font-medium
              transition-colors hover:bg-[rgba(212,175,55,0.10)]
              focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-gold)]
            "
            style={{ color: 'rgba(212,175,55,0.65)' }}
          >
            <Search className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span>Find Muhurat</span>
            <span
              className="ml-auto rounded-full border border-[rgba(212,175,55,0.15)] bg-[rgba(212,175,55,0.08)] px-2 py-0.5 text-xs"
              style={{ color: 'rgba(212,175,55,0.40)' }}
              aria-hidden="true"
            >
              4C-6
            </span>
          </button>

          {/* Export to Calendar — shell, coming in 4C-7 */}
          <button
            onClick={() => setModal('export')}
            aria-label="Export to Calendar (coming in Phase 4C-7)"
            title="Calendar Export — Phase 4C-7"
            className="
              flex flex-1 items-center justify-center gap-2
              rounded-xl border border-[rgba(212,175,55,0.20)] bg-[rgba(212,175,55,0.05)]
              px-4 py-3 text-sm font-medium
              transition-colors hover:bg-[rgba(212,175,55,0.10)]
              focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-gold)]
            "
            style={{ color: 'rgba(212,175,55,0.65)' }}
          >
            <CalendarDays className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span>Export to Calendar</span>
            <span
              className="ml-auto rounded-full border border-[rgba(212,175,55,0.15)] bg-[rgba(212,175,55,0.08)] px-2 py-0.5 text-xs"
              style={{ color: 'rgba(212,175,55,0.40)' }}
              aria-hidden="true"
            >
              4C-7
            </span>
          </button>

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
