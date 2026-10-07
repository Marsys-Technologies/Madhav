'use client'

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
export function SamiksaReview({ vm, actions }: { vm: ReviewViewModel; actions: ReviewActions }) {
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
          {vm.chartName} · predictions detected in conversation, tracked through their window, and resolved.
        </p>
      </header>

      <div style={{ display: 'grid', gap: '40px' }}>
        <AwaitingSection
          rows={vm.awaiting}
          turnAnchors={vm.turnAnchors}
          onConfirm={actions.confirm}
          onDismiss={actions.dismiss}
          onEdit={actions.edit}
        />
        <OpenTimeline rows={vm.open} turnAnchors={vm.turnAnchors} nowIso={vm.nowIso} />
        <ResolveSection
          rows={vm.resolvable}
          turnAnchors={vm.turnAnchors}
          coverage={vm.coverage}
          onResolve={actions.resolve}
          onBatchResolve={actions.batchResolve}
        />
      </div>
    </main>
  )
}
