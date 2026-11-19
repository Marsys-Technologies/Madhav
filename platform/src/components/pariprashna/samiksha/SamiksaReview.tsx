'use client'

import Link from 'next/link'
import { SamiksaBadge } from './SamiksaBadge'
import { AwaitingSection } from './AwaitingSection'
import { OpenTimeline } from './OpenTimeline'
import { ResolveSection } from './ResolveSection'
import type { ReviewViewModel, ReviewActions } from './types'
import './samiksha.css'

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
    <section aria-labelledby="samiksa-review-title" className="samiksa-review">
      <header className="samiksa-review-heading">
        <div className="samiksa-review-title">
          <h1 id="samiksa-review-title">Samīkṣā — prediction review</h1>
          <SamiksaBadge count={vm.badgeCount} />
        </div>
        <p className="samiksa-review-description">
          {vm.chartName}{actions === null && ' · Read-only'} · predictions detected in conversation, tracked through their window, and resolved.
        </p>
        <div className="samiksa-review-links">
          <Link href={`/clients/${vm.chartId}`} className="underline">
            Back to chart
          </Link>
          <Link href={`/clients/${vm.chartId}/timeline`} className="underline">
            Life Events
          </Link>
        </div>
      </header>

      <div className="samiksa-review-sections">
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
    </section>
  )
}
