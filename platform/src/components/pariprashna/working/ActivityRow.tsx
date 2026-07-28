import type { ActivityRow as ActivityRowT } from '../state/types'

/**
 * A single ledger row. `status` may patch the glyph in place (running →
 * done); the row's own geometry never changes (§6.5, §8.2).
 */
export function ActivityRow({ row }: { row: ActivityRowT }) {
  const isTool = row.kind === 'tool'
  return (
    <div className="flex items-center gap-2.5 py-1.5" style={{ fontSize: '12.5px', color: 'var(--pp-ink-dim)' }}>
      <span
        aria-hidden
        data-pp-pulse={row.status === 'running' ? true : undefined}
        className="w-3.5 flex-none text-center font-mono"
        style={{ fontSize: isTool ? '10px' : '12px', color: row.status === 'done' ? 'var(--pp-gold)' : 'var(--pp-gold-tertiary)' }}
      >
        {row.status === 'done' ? '✓' : isTool ? '▸' : '○'}
      </span>
      <span className="flex-1 min-w-0 truncate">
        {row.label}
        {row.detail && (
          <span className="italic ml-1.5" style={{ color: 'var(--pp-gold-tertiary)', fontSize: '11px' }}>
            — {row.detail}
          </span>
        )}
      </span>
      {row.status === 'done' && row.ms && (
        <span className="font-mono flex-none" style={{ fontSize: '10.5px', color: 'var(--pp-gold-tertiary)' }}>
          {row.ms}
        </span>
      )}
    </div>
  )
}
