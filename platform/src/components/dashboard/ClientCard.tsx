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
      className="brand-card group flex min-h-11 rounded-xl p-4 transition-[border-color,transform] duration-200 hover:-translate-y-px hover:border-[rgba(212,175,55,0.38)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#d4af37] focus-visible:ring-offset-2 focus-visible:ring-offset-black motion-reduce:transition-none motion-reduce:hover:translate-y-0"
    >
      <div className="min-w-0 flex-1">
        <h2 className="bt-heading truncate text-[#fce29a]">{chart.name}</h2>
        <p className="bt-label mt-1 truncate text-[rgba(212,175,55,0.48)]">
          {formatDate(chart.birth_date)} · {chart.birth_place}
        </p>
        <DirectoryReadiness readiness={chart.readiness} chartName={chart.name} />
      </div>
    </Link>
  )
}
