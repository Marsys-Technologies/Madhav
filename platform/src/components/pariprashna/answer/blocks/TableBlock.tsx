import type { TableBlockContent } from '../../state/types'

/**
 * Commit-only (§5.6): the server buffers a table fully before emitting so
 * it renders complete, with committed column widths — never streamed
 * raggedly, never a caret landing inside it.
 */
export function TableBlock({ table }: { table: TableBlockContent }) {
  return (
    <div className="overflow-x-auto my-3">
      <table className="w-full font-sans" style={{ fontSize: '13px', lineHeight: 1.5 }}>
        <thead>
          <tr>
            {table.headers.map((h, i) => (
              <th
                key={i}
                className="text-left py-2 px-2"
                style={{
                  borderBottom: '1px solid var(--pp-rule)',
                  fontSize: '10px',
                  letterSpacing: '0.2em',
                  textTransform: 'uppercase',
                  color: 'var(--pp-gold-tertiary)',
                  fontWeight: 500,
                }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, ri) => (
            <tr key={ri}>
              {row.map((cell, ci) => (
                <td key={ci} className="py-2 px-2" style={{ borderBottom: '1px solid var(--pp-rule)', color: 'var(--pp-ink)' }}>
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
