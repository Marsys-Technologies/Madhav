/** Explicit density floor for stage envelopes, including additive public NOW. */
import type { TrimmableSection } from '../../lib/response_budget.js'
type Data = Record<string, unknown>
const object = (value: unknown): Data | null => value && typeof value === 'object' && !Array.isArray(value) ? value as Data : null
const views = new Set(['now','ahead','priority','elect','story','ritual','explain'])
export function stageDensityBudgetSections(content: Data): TrimmableSection<Data>[] {
  const nested = object(object(content.published_now)?.snapshot)
  const stage = nested ?? content
  if (!views.has(String(stage.view)) || !Array.isArray(stage.rows)) return []
  const path = nested ? 'published_now.snapshot.rows' : 'rows'
  const rows = stage.rows as Data[]
  // Stage composition orders confirmed first. Protect every confirmed row on
  // this page, even when the irreducible base still exceeds the requested cap.
  const minKeep = rows.filter(row => row.density === 'confirmed').length
  return [{ path, label: path, minKeep, hardFloor: true,
    getArray: () => stage.rows as Data[],
    setArray: (_content, kept) => {
      stage.rows = kept
      const density = object(stage.density)
      if (density) {
        for (const key of ['confirmed','testimony','catalog_only','unknown','context_only']) density[key] = 0
        for (const value of kept) {
          const row = object(value)!
          const key = row.density === null ? 'unknown' : String(row.density)
          density[key] = Number(density[key]) + 1
          if (row.qualification === 'context_only') density.context_only = Number(density.context_only) + 1
        }
        stage.catalog_only_rows_in_page = Number(density.catalog_only) + Number(density.unknown)
      }
      const pagination = object(stage.pagination)
      if (pagination) { pagination.returned = kept.length; pagination.more_available = true }
    },
    recover: { instrument: `${stage.view}_read`, hint: 'Use the source drill and page selectors for the full stored stage page.' },
  }]
}
