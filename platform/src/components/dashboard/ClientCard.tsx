import Link from 'next/link'
import { ArrowUpRight } from 'lucide-react'
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
      data-roster-card
      className="focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[var(--folio-focus)] focus-visible:ring-offset-[var(--folio-canvas)]"
    >
      <div data-roster-card-identity>
        <h2>{chart.name}</h2>
        <p>
          {formatDate(chart.birth_date)} · {chart.birth_place}
        </p>
      </div>
      <ArrowUpRight aria-hidden="true" focusable="false" size={17} />
      <DirectoryReadiness readiness={chart.readiness} chartName={chart.name} />
    </Link>
  )
}
