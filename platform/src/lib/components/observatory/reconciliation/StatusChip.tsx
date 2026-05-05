// Brand-styled status chip for reconciliation status.
// Server-renderable; pure presentation.

import { cn } from '@/lib/utils'
import type { ReconciliationStatus } from '@/lib/observatory/reconciliation/types'

const PROVIDER_LABEL: Record<string, string> = {
  anthropic: 'Anthropic',
  openai: 'OpenAI',
  gemini: 'Gemini',
  deepseek: 'DeepSeek',
  nim: 'NIM',
}

export function providerLabel(provider: string): string {
  return PROVIDER_LABEL[provider] ?? provider
}

const STATUS_LABEL: Record<string, string> = {
  matched: 'Reconciled',
  variance_within_tolerance: 'Within tolerance',
  variance_alert: 'Alert',
  missing_authoritative: 'No data',
  error: 'Error',
  ok: 'OK',
  warning: 'Warning',
  critical: 'Critical',
  pending: 'Pending',
  in_progress: 'In progress',
}

const STATUS_STYLES: Record<string, string> = {
  ok:                        'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
  matched:                   'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
  warning:                   'bg-amber-500/10 border-amber-500/20 text-amber-400',
  variance_within_tolerance: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
  critical:                  'bg-red-500/10 border-red-500/20 text-red-400',
  variance_alert:            'bg-red-500/10 border-red-500/20 text-red-400',
  error:                     'bg-red-500/10 border-red-500/20 text-red-400',
  pending:                   'bg-[rgba(212,175,55,0.06)] border-[rgba(212,175,55,0.12)] text-[rgba(212,175,55,0.50)]',
  missing_authoritative:     'bg-[rgba(212,175,55,0.06)] border-[rgba(212,175,55,0.12)] text-[rgba(212,175,55,0.50)]',
  in_progress:               'bg-sky-500/10 border-sky-500/20 text-sky-400',
}

export interface StatusChipProps {
  provider: string
  status: ReconciliationStatus | string
  variancePct: number | null
  href?: string
}

export function StatusChip({ provider, status }: StatusChipProps) {
  const style = STATUS_STYLES[status ?? ''] ?? STATUS_STYLES['pending']
  const label = STATUS_LABEL[status ?? ''] ?? String(status ?? '—')
  return (
    <span
      data-testid={`reconciliation-chip-${provider}`}
      data-status={status}
      className={cn(
        'inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium',
        style,
      )}
    >
      {label}
    </span>
  )
}
