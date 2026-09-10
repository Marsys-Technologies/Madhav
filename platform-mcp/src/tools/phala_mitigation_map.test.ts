/**
 * phala_mitigation_map.test.ts — F-5 (L4_W1_ANALYSIS_BATCH_C.md §3.5, §N.8).
 *
 * `all_cited` used to compute over `!classical_citation && !source_citation` --
 * but `source_citation` is an internal, always-populated provenance string,
 * never a classical grounding signal. Since it can never be falsy, `uncited`
 * was structurally always empty regardless of `classical_citation`'s honesty.
 * Fixed to key on `classical_citation` alone.
 */
import { describe, it, expect } from 'vitest'
import { filterUncited } from './phala_mitigation_map.js'

describe('filterUncited (F-5)', () => {
  it('flags a row with no classical_citation, even though source_citation is populated', () => {
    const rows = [
      { classical_citation: null, source_citation: 'ph_pratikara/obs-1/light' },
    ]
    expect(filterUncited(rows)).toHaveLength(1)
  })

  it('does not flag a row with a real classical_citation', () => {
    const rows = [
      { classical_citation: 'BPHS Ch.93 (Chandra dana)', source_citation: 'ph_pratikara/obs-1/light' },
    ]
    expect(filterUncited(rows)).toHaveLength(0)
  })

  it('flags an empty-string classical_citation the same as null', () => {
    const rows = [
      { classical_citation: '', source_citation: 'ph_pratikara/obs-1/light' },
    ]
    expect(filterUncited(rows)).toHaveLength(1)
  })

  it('source_citation being present must never rescue a missing classical_citation', () => {
    // The exact defect: source_citation is unconditionally non-empty on every
    // real row, so the old `&& !source_citation` clause could never be true.
    const rows = [
      { classical_citation: null, source_citation: 'ph_pratikara/obs-1/light' },
      { classical_citation: undefined, source_citation: 'ph_pratikara/obs-2/moderate' },
    ]
    expect(filterUncited(rows)).toHaveLength(2)
  })

  it('mixed set: only the uncited rows are returned', () => {
    const rows = [
      { classical_citation: 'BPHS Ch.88 (Shani upaya)', source_citation: 'ph_pratikara/obs-1/light' },
      { classical_citation: null, source_citation: 'ph_pratikara/obs-2/moderate' },
      { classical_citation: 'Phaladeepika remedial section', source_citation: 'ph_pratikara/obs-3/light' },
    ]
    const uncited = filterUncited(rows)
    expect(uncited).toHaveLength(1)
    expect(uncited[0]?.['source_citation']).toBe('ph_pratikara/obs-2/moderate')
  })

  it('empty input yields no uncited rows', () => {
    expect(filterUncited([])).toEqual([])
  })
})
