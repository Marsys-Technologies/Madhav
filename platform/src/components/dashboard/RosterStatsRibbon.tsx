interface RosterStatsRibbonProps {
  total: number
  inActiveBuild: number
  consumedToday: number
  predictionsOverdue: number
  onFilterShortcut?: (key: string, value: string) => void
}

export function RosterStatsRibbon({
  total,
  inActiveBuild,
  consumedToday,
  predictionsOverdue,
  onFilterShortcut,
}: RosterStatsRibbonProps) {
  const segments: { label: string; value: number; filterKey?: string; filterVal?: string }[] = [
    { label: 'charts', value: total },
    { label: 'in active build', value: inActiveBuild, filterKey: 'buildMax', filterVal: '99' },
    { label: 'consumed today', value: consumedToday },
    ...(predictionsOverdue > 0
      ? [{ label: 'predictions overdue', value: predictionsOverdue }]
      : []),
  ]

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 rounded-lg border border-[var(--folio-divider)] bg-[var(--folio-panel)] px-4 py-2.5 text-sm">
      {segments.map((seg) => (
        <span key={seg.label} className="flex items-center gap-1.5">
          {seg.filterKey && onFilterShortcut ? (
            <button
              onClick={() => onFilterShortcut(seg.filterKey!, seg.filterVal!)}
              aria-label={`Filter by ${seg.label}`}
              className="min-h-11 font-semibold tabular-nums text-[var(--folio-action)] underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-[var(--folio-focus)]"
            >
              {seg.value}
            </button>
          ) : (
            <span className="font-semibold tabular-nums text-[var(--folio-ink)]">{seg.value}</span>
          )}
          <span className="text-[var(--folio-muted)]">{seg.label}</span>
        </span>
      ))}
    </div>
  )
}
