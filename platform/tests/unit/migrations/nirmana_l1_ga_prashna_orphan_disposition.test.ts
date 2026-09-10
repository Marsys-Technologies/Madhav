import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

/**
 * Nirmāṇa L1 ga_prashna_judgment orphan disposition contract (migration 651).
 *
 * C13 (D-NATIVE-05): "No-FK referrers get dispositions, not cascades: either
 * a real FK with an intended delete rule, or documented orphan-tolerance WITH
 * A DETECTOR." F-E21/F-E22 (L1_W1_ANALYSIS_BATCH_E.md) found 5 rows in
 * ga_prashna_judgment citing a chart_id absent from `charts` -- unlike
 * phala_anchors.signal_id (migration 683, genuine orphan-tolerance), a
 * prashna judgment with no backing chart has no legitimate lifecycle, so the
 * disposition here is the OTHER C13 option: a real FK.
 *
 * This is a textual contract test (no live DB) -- it exists so a future edit
 * to this migration cannot silently widen the delete beyond the one named
 * chart_id, or drop either safety guard, without a test failing to say so.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/651_nirmana_l1_ga_prashna_orphan_disposition.sql'),
  'utf8',
)

const ORPHANED_CHART_ID = 'b35046d8-4131-4e0e-8548-3136678fc2bb'

describe('migration 651 — ga_prashna_judgment orphan disposition', () => {
  it('deletes only the one named chart_id, never a blanket condition', () => {
    expect(migration).toContain(`DELETE FROM ga_prashna_judgment`)
    expect(migration).toMatch(
      new RegExp(`DELETE FROM ga_prashna_judgment[\\s\\S]{0,80}chart_id = '${ORPHANED_CHART_ID}'`),
    )
    // The literal defect class this guards against: a delete with no WHERE,
    // or one scoped by a live subquery that could match rows nobody reviewed.
    expect(migration).not.toMatch(/DELETE FROM ga_prashna_judgment\s*;/i)
  })

  it('refuses to proceed if the exact expected row count has drifted', () => {
    expect(migration).toContain('deleted_count <> 5')
    expect(migration).toMatch(/expected to delete exactly 5 orphaned/i)
  })

  it('refuses to add the FK if any OTHER orphan exists beyond the named set', () => {
    expect(migration).toMatch(/remaining_orphans\s*>\s*0/)
    expect(migration).toContain(
      'NOT EXISTS (SELECT 1 FROM charts c WHERE c.id = j.chart_id)',
    )
  })

  it('halts instead of deleting if the chart now exists (re-review, do not proceed blind)', () => {
    expect(migration).toMatch(
      new RegExp(`EXISTS \\(SELECT 1 FROM charts WHERE id = '${ORPHANED_CHART_ID}'\\)`),
    )
  })

  it('adds a real FK with ON DELETE CASCADE, matching the chart_fact_identity convention', () => {
    expect(migration).toContain('ADD CONSTRAINT ga_prashna_judgment_chart_id_fkey')
    expect(migration).toMatch(
      /FOREIGN KEY \(chart_id\) REFERENCES charts\(id\) ON DELETE CASCADE/,
    )
  })

  it('documents the disposition on the constraint itself, not only in a comment above it', () => {
    expect(migration).toContain('COMMENT ON CONSTRAINT ga_prashna_judgment_chart_id_fkey')
    expect(migration).toMatch(/C13 disposition/)
  })
})
