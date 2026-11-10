'use client'

import { usePathname } from 'next/navigation'
import { ChartSwitcher } from './ChartSwitcher'

interface Props {
  currentChartId: string
  charts: { id: string; name: string | null }[]
}

export function ConditionalChartSwitcherBar({ currentChartId, charts }: Props) {
  const pathname = usePathname()
  // Cockpit build has no switcher bar — hero is the topmost element
  if (pathname?.includes('/nirmana')) return null
  return (
    <div className="border-b border-[var(--folio-divider)] bg-[var(--folio-canvas)] px-4 py-2">
      <ChartSwitcher currentChartId={currentChartId} charts={charts} />
    </div>
  )
}
