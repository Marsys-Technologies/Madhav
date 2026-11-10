import Link from 'next/link'
import type { ChartWithMeta } from '@/lib/roster/types'
import { formatDate } from '@/lib/utils/date'
import { DirectoryReadiness } from './DirectoryReadiness'

// RasiChartMini intentionally not rendered on cards (parked — not deleted).

interface Props {
  chart: ChartWithMeta
}

/**
 * Jātaka directory card — one semantic link to the chart workspace.
 *
 * Only the name, a quiet birth line and the shared readiness live here.
 * Nirmāṇa, Paripraśna, edit and delete belong to `/clients/[id]`, which keeps
 * the card free of nested interactive targets.
 */
export function ClientCard({ chart }: Props) {
  return (
    <Link
      href={`/clients/${chart.id}`}
      aria-label={`Open ${chart.name} Jātaka — ${chart.readiness.label}`}
      className="group flex min-h-11 rounded-xl border border-[var(--folio-divider)] bg-[var(--folio-panel)] p-4 hover:border-[var(--folio-action)] focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[var(--folio-focus)] focus-visible:ring-offset-[var(--folio-canvas)]"
    >
      <div className="min-w-0 flex-1">
        <h2 className="break-words font-[family-name:var(--folio-font-heading)] text-lg font-semibold text-[var(--folio-ink)]">{chart.name}</h2>
        <p className="mt-1 break-words text-sm text-[var(--folio-muted)]">
          {formatDate(chart.birth_date)} · {chart.birth_place}
        </p>
        <DirectoryReadiness readiness={chart.readiness} chartName={chart.name} />
      </div>
    </Link>
  )
}
