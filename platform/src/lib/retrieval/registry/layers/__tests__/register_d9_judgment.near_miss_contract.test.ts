/**
 * The complete judgment receipt cannot retain a permanent hardcoded gap for notably-absent
 * yogas (NMB-CAND-v1, OSR-009 / OSR-012).  The implementation must instead consume the
 * serve-time formation band; ordinary L1 non-firings are not a substitute.
 *
 * Source-level tripwire (kept from the salvaged worktree test) plus wiring assertions.
 */
import { readFile } from 'node:fs/promises'
import { describe, expect, it } from 'vitest'

const SOURCE = new URL('../register_d9_judgment.ts', import.meta.url)
const CHECKLIST = new URL('../reading_checklist.ts', import.meta.url)

describe('judgment_query notably-absent yoga contract', () => {
  it('does not hardcode notably_absent_yogas as not computed', async () => {
    const source = await readFile(SOURCE, 'utf8')
    expect(source).not.toMatch(
      /unit:\s*'notably_absent_yogas',[\s\S]{0,400}?state:\s*'not_computed'/,
    )
  })

  it('reads the band through the served-generation fetcher and never emits not_computed for the unit', async () => {
    const source = await readFile(SOURCE, 'utf8')
    expect(source).toContain('fetchNotablyAbsentYogas(chart_id, ayanamsha_id, generation)')
    const unit = source.slice(source.indexOf("unit: 'notably_absent_yogas'"), source.indexOf("unit: 'dasha_levels'"))
    expect(unit).not.toContain('not_computed')
  })

  it('fences the band on ga_yoga + ga_positions and NOT on bo_laksana (nothing is stored)', async () => {
    const source = await readFile(CHECKLIST, 'utf8')
    expect(source).toMatch(/NEAR_MISS_REQUIRED_ASSETS = \['ga_yoga', 'ga_positions'\] as const/)
    const block = source.slice(source.indexOf('NMB-CAND-v1 (OSR-009 / OSR-012)'), source.indexOf('export interface KpCuspLink'))
    expect(block).not.toContain("'bo_laksana'")
    expect(block).not.toMatch(/bodha_msr_signals/)
  })
})
