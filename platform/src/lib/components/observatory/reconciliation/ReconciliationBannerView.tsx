// Pure presentation half of ReconciliationBanner — accepts pre-loaded rows
// and renders the provider status card grid. Split out so unit tests don't
// need to stub the DB loader.

import { cn } from '@/lib/utils'
import { PROVIDER_COLORS } from '@/lib/components/observatory/charts/utils'
import type { ReconciliationHistoryRow } from '@/lib/observatory/reconciliation/types'

export type ReconciliationBannerRow = ReconciliationHistoryRow

export interface ReconciliationBannerViewProps {
  rows: ReconciliationBannerRow[]
  linkHref?: string
}

const STATUS_LABEL: Record<string, string> = {
  matched: 'Reconciled',
  variance_within_tolerance: 'Within tolerance',
  variance_alert: 'Alert',
  missing_authoritative: 'No data',
  error: 'Error',
}

function varianceClass(pct: number | null | undefined): string {
  if (pct == null) return 'text-[rgba(212,175,55,0.40)]'
  const abs = Math.abs(pct)
  if (abs <= 5) return 'text-emerald-400'
  if (abs <= 15) return 'text-amber-400'
  return 'text-red-400'
}

function chipClass(status: string | null | undefined): string {
  switch (status) {
    case 'ok':
    case 'matched':
      return 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
    case 'warning':
    case 'variance_within_tolerance':
      return 'bg-amber-500/10 border-amber-500/20 text-amber-400'
    case 'critical':
    case 'variance_alert':
    case 'error':
      return 'bg-red-500/10 border-red-500/20 text-red-400'
    case 'in_progress':
      return 'bg-sky-500/10 border-sky-500/20 text-sky-400'
    default:
      return 'bg-[rgba(212,175,55,0.06)] border-[rgba(212,175,55,0.12)] text-[rgba(212,175,55,0.40)]'
  }
}

const PROVIDER_DISPLAY: Record<string, string> = {
  anthropic: 'Anthropic',
  openai: 'OpenAI',
  gemini: 'Gemini',
  deepseek: 'DeepSeek',
  nim: 'NIM',
}

function ProviderStatusCard({ row }: { row: ReconciliationBannerRow }) {
  const dotColor =
    PROVIDER_COLORS[row.provider as keyof typeof PROVIDER_COLORS] ?? '#64748b'
  const varClass = varianceClass(row.variance_pct)
  const label = STATUS_LABEL[row.status] ?? row.status ?? 'no data'

  return (
    <div
      data-testid={`reconciliation-card-${row.provider}`}
      data-status={row.status}
      className="rounded-xl border border-[rgba(212,175,55,0.10)] bg-[oklch(0.11_0.010_70)] p-3"
    >
      <div className="flex items-center gap-2 mb-2">
        <span
          aria-hidden="true"
          className="h-2.5 w-2.5 rounded-full shrink-0"
          style={{ backgroundColor: dotColor }}
        />
        <span className="text-xs font-semibold text-[rgba(212,175,55,0.70)]">
          {PROVIDER_DISPLAY[row.provider] ?? row.provider}
        </span>
      </div>
      <div
        className={cn(
          'inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium',
          chipClass(row.status),
        )}
      >
        {label}
      </div>
      {row.variance_pct != null && (
        <div className={cn('mt-1.5 text-xs font-semibold tabular-nums', varClass)}>
          {row.variance_pct > 0 ? '+' : ''}
          {row.variance_pct.toFixed(2)}%
        </div>
      )}
      {row.period_start && (
        <div className="mt-1 text-[10px] text-[rgba(212,175,55,0.30)]">
          {row.period_start}
        </div>
      )}
    </div>
  )
}

export function ReconciliationBannerView({
  rows,
}: ReconciliationBannerViewProps) {
  if (!rows || rows.length === 0) return null

  const seen = new Set<string>()
  const dedup: ReconciliationBannerRow[] = []
  for (const row of rows) {
    if (seen.has(row.provider)) continue
    seen.add(row.provider)
    dedup.push(row)
  }

  return (
    <div
      data-testid="reconciliation-banner"
      role="region"
      aria-label="Reconciliation status by provider"
      className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5"
    >
      {dedup.map((row) => (
        <ProviderStatusCard key={row.reconciliation_id} row={row} />
      ))}
    </div>
  )
}
