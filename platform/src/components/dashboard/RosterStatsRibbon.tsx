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
    <dl data-roster-stats aria-label="Chart directory summary">
      {segments.map((seg) => (
        <div key={seg.label}>
          <dt>{seg.label}</dt>
          <dd>
            {seg.filterKey && onFilterShortcut ? (
              <button
                type="button"
                onClick={() => onFilterShortcut(seg.filterKey!, seg.filterVal!)}
                aria-label={`Filter by ${seg.label}, ${seg.value}`}
                className="min-h-11 min-w-11 underline decoration-[var(--folio-boundary)] decoration-1 underline-offset-4 focus-visible:outline-2 focus-visible:outline-[var(--folio-focus)]"
              >
                {seg.value}
              </button>
            ) : seg.value}
          </dd>
        </div>
      ))}
    </dl>
  )
}
