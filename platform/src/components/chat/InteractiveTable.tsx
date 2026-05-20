'use client'

import { useState, useCallback } from 'react'

interface InteractiveTableProps {
  headers: string[]
  rows: string[][]
}

type SortDir = 'asc' | 'desc' | null

function parseForSort(val: string): number | string {
  const trimmed = val.trim()
  const num = Number(trimmed)
  return isNaN(num) || trimmed === '' ? trimmed.toLowerCase() : num
}

function sortRows(rows: string[][], colIdx: number, dir: 'asc' | 'desc'): string[][] {
  return [...rows].sort((a, b) => {
    const av = parseForSort(a[colIdx] ?? '')
    const bv = parseForSort(b[colIdx] ?? '')
    let cmp = 0
    if (typeof av === 'number' && typeof bv === 'number') {
      cmp = av - bv
    } else {
      cmp = String(av) < String(bv) ? -1 : String(av) > String(bv) ? 1 : 0
    }
    return dir === 'asc' ? cmp : -cmp
  })
}

function toCSV(headers: string[], rows: string[][]): string {
  const escape = (v: string) => `"${v.replace(/"/g, '""')}"`
  const lines = [headers.map(escape).join(','), ...rows.map((r) => r.map(escape).join(','))]
  return lines.join('\r\n')
}

export function InteractiveTable({ headers, rows }: InteractiveTableProps) {
  const [sortCol, setSortCol] = useState<number | null>(null)
  const [sortDir, setSortDir] = useState<SortDir>(null)

  const displayRows =
    sortCol !== null && sortDir !== null ? sortRows(rows, sortCol, sortDir) : rows

  const handleHeaderClick = useCallback(
    (colIdx: number) => {
      if (sortCol !== colIdx) {
        setSortCol(colIdx)
        setSortDir('asc')
      } else if (sortDir === 'asc') {
        setSortDir('desc')
      } else {
        setSortCol(null)
        setSortDir(null)
      }
    },
    [sortCol, sortDir],
  )

  const handleDownload = useCallback(() => {
    const csv = toCSV(headers, rows)
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `marsys-table-${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }, [headers, rows])

  return (
    <div className="my-4" data-testid="v2-interactive-table">
      <div className="mb-1 flex justify-end">
        <button
          type="button"
          onClick={handleDownload}
          data-testid="v2-table-download-csv"
          className="rounded px-2 py-0.5 text-xs text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
          aria-label="Download table as CSV"
        >
          ↓ CSV
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="border-b border-border">
            <tr>
              {headers.map((h, i) => (
                <th
                  key={i}
                  onClick={() => handleHeaderClick(i)}
                  data-testid={`v2-table-header-${i}`}
                  className="cursor-pointer select-none px-3 py-2 text-left font-semibold text-foreground hover:bg-muted/40 transition-colors"
                  aria-sort={
                    sortCol === i
                      ? sortDir === 'asc'
                        ? 'ascending'
                        : 'descending'
                      : 'none'
                  }
                >
                  {h}
                  {sortCol === i && (
                    <span className="ml-1 text-[10px]" data-testid="v2-table-sort-indicator">
                      {sortDir === 'asc' ? '▲' : '▼'}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayRows.map((row, ri) => (
              <tr key={ri} className="border-b border-border/60 last:border-0">
                {row.map((cell, ci) => (
                  <td key={ci} className="px-3 py-2 align-top">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
