/**
 * Shared review-surface fixture — PB-3 lane L-3 tests. A plausible, populated view-model for
 * rendering the full `<SamiksaReview>` (badge render + axe). Not DB-backed; the DB integration
 * tests seed real rows separately.
 */
import type { LedgerRow } from '@/lib/pariprashna/samiksha/schema'
import type { ReviewViewModel, ReviewActions } from '@/components/pariprashna/samiksha/types'

function row(partial: Partial<LedgerRow> & Pick<LedgerRow, 'id' | 'claim_text' | 'lifecycle_status'>): LedgerRow {
  return {
    chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
    message_part_id: null,
    domain: 'career',
    window: '[2026-07-01,2027-01-01)',
    confidence: '[0.55,0.7)',
    direction: 'positive',
    technique_refs: [],
    grounding_fact_ids: [],
    created_from_channel: 'pariprashna',
    build_id: null,
    priors_version: null,
    formula_versions: null,
    ranking_config: null,
    now_context_date: null,
    stamp_copied_at: null,
    outcome: null,
    outcome_value: null,
    outcome_note: null,
    outcome_recorded_at: null,
    confirmed_at: null,
    dismissed_reason: null,
    created_at: '2026-07-01T00:00:00Z',
    updated_at: '2026-07-01T00:00:00Z',
    ...partial,
  }
}

export function makeFixtureVm(): ReviewViewModel {
  const detected1 = row({ id: '00000000-0000-4000-8000-000000000001', claim_text: 'A leadership role emerges by end of 2026.', lifecycle_status: 'detected', confidence: null, message_part_id: 'aaaaaaaa-0000-4000-8000-000000000001' })
  const detected2 = row({ id: '00000000-0000-4000-8000-000000000002', claim_text: 'A short relocation window opens mid-year.', lifecycle_status: 'detected' })
  const open1 = row({ id: '00000000-0000-4000-8000-000000000003', claim_text: 'Financial pressure eases through the Jupiter transit.', lifecycle_status: 'open', domain: 'wealth' })
  const closed1 = row({ id: '00000000-0000-4000-8000-000000000004', claim_text: 'A health check flags a minor, correctable issue.', lifecycle_status: 'window_closed', domain: 'health', window: '[2025-01-01,2025-07-01)' })

  return {
    chartId: '482012f1-710e-4a25-994a-93821f5871aa',
    chartName: 'Abhisek Mohanty',
    awaiting: [detected1, detected2],
    open: [open1],
    resolvable: [closed1],
    coverage: { resolvedCount: 3, unverifiableCount: 1, lapsedCount: 2, openCount: 1, awaitingCount: 2, coverageFraction: 4 / 6 },
    turnAnchors: {
      'aaaaaaaa-0000-4000-8000-000000000001': {
        chartId: '482012f1-710e-4a25-994a-93821f5871aa',
        conversationId: 'c0ffee00-0000-4000-8000-000000000001',
        turnOrdinal: 3,
      },
    },
    badgeCount: 3, // 2 detected + 1 window_closed
    nowIso: '2026-07-01T12:00:00Z',
  }
}

export const noopActions: ReviewActions = {
  confirm: () => {},
  dismiss: () => {},
  edit: () => {},
  resolve: () => {},
  batchResolve: () => {},
}
