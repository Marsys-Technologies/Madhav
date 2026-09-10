import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

/**
 * Nirmāṇa L1 ga_tajaka volume_explanation correction (migration 844, fifth in the 840-859
 * range).
 *
 * Closes F-E17 (L1_W1_ANALYSIS_BATCH_E.md): the prior text claimed varshas outside the
 * precomputed window are "computed on-demand by the retrieval tool via
 * ga_tajaka_writer.compute_varsha()" -- compute_varsha() has zero callers (confirmed live,
 * cycle 106). get_tajik.ts is a pure SELECT; its own empty_reason honestly discloses
 * out-of-window varshas as genuinely not computed. The tool was already honest; only the
 * registry lied.
 *
 * This is a textual contract test (no live DB) -- it exists so a future edit cannot silently
 * reintroduce the false "computed on-demand" claim.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/844_nirmana_l1_ga_tajaka_volume_explanation_fix.sql'),
  'utf8',
)

describe('migration 844 — ga_tajaka volume_explanation correction', () => {
  it('removes the false "computed on-demand" / compute_varsha claim from the SQL payload', () => {
    const sqlBody = migration.slice(migration.indexOf('BEGIN;'))
    expect(sqlBody).not.toMatch(/computed on-demand by the retrieval tool via ga_tajaka_writer\.compute_varsha/)
  })

  it('states the honest windowed-storage behavior instead', () => {
    const sqlBody = migration.slice(migration.indexOf('BEGIN;'))
    expect(sqlBody).toMatch(/NOT computed on-demand/)
    expect(sqlBody).toMatch(/empty_reason/)
  })

  it('touches ONLY volume_explanation -- no count_sql or target_floor column assignment', () => {
    const sqlBody = migration.slice(migration.indexOf('BEGIN;'))
    // "target_floor = 240" legitimately appears INSIDE the volume_explanation string value
    // being SET -- that's data, not a column assignment. Check for a real SET clause instead.
    expect(sqlBody).not.toMatch(/SET\s+count_sql\s*=/i)
    expect(sqlBody).not.toMatch(/SET\s+target_floor\s*=/i)
    expect(sqlBody).toMatch(/SET\s+volume_explanation\s*=/i)
  })

  it('cites F-E17 as the finding this closes', () => {
    expect(migration).toContain('F-E17')
  })

  it('documents this as the fifth migration in the 840-859 range', () => {
    expect(migration).toContain('840-859')
    expect(migration).toContain('#2101')
  })
})
