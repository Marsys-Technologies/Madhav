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
  if (pathname?.includes('/build')) return null
  return (
    <div className="border-b border-[rgba(212,175,55,0.14)] px-4 py-2 flex items-center justify-between">
      <ChartSwitcher currentChartId={currentChartId} charts={charts} />
    </div>
  )
}
