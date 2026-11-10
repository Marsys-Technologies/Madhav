'use client'

import Link from 'next/link'
import { SamiksaBadge } from './SamiksaBadge'
import { AwaitingSection } from './AwaitingSection'
import { OpenTimeline } from './OpenTimeline'
import { ResolveSection } from './ResolveSection'
import type { ReviewViewModel, ReviewActions } from './types'

/**
 * SAMĪKṢĀ review surface — PB-3 (SAMĪKṢĀ) lane L-3.
 *
 * The `/clients/[id]/samiksha` tab body: three sections (Awaiting confirmation · Open · Resolve)
 * + the non-alarming `--pp-gold-dim` badge. Client component; all mutation goes through the
 * injected `actions` (server actions in production, stubs in tests). Pure presentation otherwise
 * — the data (`vm`) is assembled server-side by review.ts so this component never queries.
 */
export function SamiksaReview({ vm, actions }: { vm: ReviewViewModel; actions: ReviewActions | null }) {
  return (
    <main
      className="samiksa-review"
      style={{ maxWidth: '760px', margin: '0 auto', padding: '32px 24px 96px' }}
    >
      <header style={{ marginBottom: '28px' }}>
        <div className="flex items-center" style={{ gap: '10px' }}>
          <h1
            style={{
              fontFamily: 'var(--pp-font-serif, Georgia, serif)',
              fontSize: '24px',
              color: 'var(--pp-ink, #EBE3D2)',
              margin: 0,
            }}
          >
            Samīkṣā — prediction review
          </h1>
          <SamiksaBadge count={vm.badgeCount} />
        </div>
        <p style={{ fontSize: '12px', color: 'var(--pp-ink-dim, rgba(235,227,210,0.64))', marginTop: '6px' }}>
          {vm.chartName}{actions === null && ' · Read-only'} · predictions detected in conversation, tracked through their window, and resolved.
        </p>
        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-sm">
          <Link href={`/clients/${vm.chartId}`} className="underline">
            Back to chart
          </Link>
          <Link href={`/clients/${vm.chartId}/timeline`} className="underline">
            Life Events
          </Link>
        </div>
      </header>

      <div style={{ display: 'grid', gap: '40px' }}>
        <AwaitingSection
          rows={vm.awaiting}
          turnAnchors={vm.turnAnchors}
          actions={actions}
        />
        <OpenTimeline rows={vm.open} turnAnchors={vm.turnAnchors} nowIso={vm.nowIso} />
        <ResolveSection
          rows={vm.resolvable}
          turnAnchors={vm.turnAnchors}
          coverage={vm.coverage}
          actions={actions}
        />
      </div>
    </main>
  )
}
