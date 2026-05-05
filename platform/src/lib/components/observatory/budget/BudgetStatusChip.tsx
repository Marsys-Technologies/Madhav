// Pill badge for a budget rule's evaluation status. Server-renderable.

import { cn } from '@/lib/utils'
import type { BudgetStatus } from '@/lib/observatory/budget/types'

const CHIP_STYLES: Record<string, string> = {
  ok:       'bg-emerald-500/10 border-emerald-500/25 text-emerald-400',
  warning:  'bg-amber-500/10 border-amber-500/25 text-amber-400',
  alert:    'bg-red-500/10 border-red-500/25 text-red-400',
  exceeded: 'bg-red-600/15 border-red-600/35 text-red-300',
}

const CHIP_ICONS: Record<string, string> = {
  ok:       '✓',
  warning:  '!',
  alert:    '!!',
  exceeded: '⚠',
}

const CHIP_LABELS: Record<string, string> = {
  ok:       'OK',
  warning:  'Warning',
  alert:    'Alert',
  exceeded: 'Exceeded',
}

export interface BudgetStatusChipProps {
  status: BudgetStatus
  pct_used: number
}

export function BudgetStatusChip({ status, pct_used }: BudgetStatusChipProps) {
  const style =
    CHIP_STYLES[status] ??
    'bg-[rgba(212,175,55,0.08)] border-[rgba(212,175,55,0.15)] text-[rgba(212,175,55,0.60)]'
  const icon = CHIP_ICONS[status] ?? '?'
  return (
    <div
      data-testid={`budget-status-chip-${status}`}
      data-status={status}
      className={cn(
        'flex items-center gap-1 rounded-full border px-2.5 py-1 text-[10px] font-semibold',
        style,
      )}
    >
      <span>{icon}</span>
      <span>{CHIP_LABELS[status] ?? status}</span>
      <span className="tabular-nums opacity-70">· {pct_used.toFixed(0)}%</span>
    </div>
  )
}
