import { redirect } from 'next/navigation'
import { query } from '@/lib/db/client'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { configService } from '@/lib/config/index'
import { getReviewData } from '@/lib/pariprashna/samiksha/review'
import { countBadge } from '@/lib/pariprashna/samiksha/badge'
import { SamiksaReview } from '@/components/pariprashna/samiksha/SamiksaReview'
import type { ReviewViewModel, ReviewActions } from '@/components/pariprashna/samiksha/types'
import {
  confirmCandidateAction,
  editCandidateAction,
  dismissCandidateAction,
  resolvePredictionAction,
  batchResolveAction,
} from './actions'

/**
 * SAMĪKṢĀ review tab — PB-3 (SAMĪKṢĀ) lane L-3. Server component: gate → auth → assemble the
 * review data (review.ts) + badge (badge.ts) server-side, then hand a serialisable view-model
 * to the client `<SamiksaReview>`. Flagged behind PARIPRASHNA_ENABLED (the same surface family;
 * no new flag is introduced — feature_flags.ts is out of this lane's scope). All mutation is via
 * the imported server actions, bound to this chart id by thin inline server-action adapters.
 */
export default async function SamiksaPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params

  if (!configService.getFlag('PARIPRASHNA_ENABLED')) {
    redirect(`/clients/${id}/consult`)
  }

  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')
  if (access.permission === 'deny') redirect('/dashboard')

  const chartResult = await query<{ name: string | null }>('SELECT name FROM charts WHERE id=$1', [id])
  const chart = chartResult.rows[0] ?? null
  if (!chart) redirect('/dashboard')

  const [review, badgeCount] = await Promise.all([getReviewData(id), countBadge(id)])

  const vm: ReviewViewModel = {
    chartId: id,
    chartName: chart.name ?? 'This chart',
    awaiting: review.awaiting,
    open: review.open,
    resolvable: review.resolvable,
    coverage: review.coverage,
    turnAnchors: review.turnAnchors,
    badgeCount,
    nowIso: new Date().toISOString(),
  }

  // Inline server-action adapters — inject the chart id, match the client action signatures.
  const actions: ReviewActions = {
    confirm: async (input) => {
      'use server'
      await confirmCandidateAction({ chartId: id, ...input })
    },
    dismiss: async (input) => {
      'use server'
      await dismissCandidateAction({ chartId: id, ...input })
    },
    edit: async (input) => {
      'use server'
      await editCandidateAction({ chartId: id, ...input })
    },
    resolve: async (input) => {
      'use server'
      await resolvePredictionAction({ chartId: id, ...input })
    },
    batchResolve: async (items) => {
      'use server'
      await batchResolveAction({ chartId: id, items })
    },
  }

  return <SamiksaReview vm={vm} actions={actions} />
}
