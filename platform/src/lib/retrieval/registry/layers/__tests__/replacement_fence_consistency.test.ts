import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import { getSourceQueryAvailabilityContract } from '../../knowledge/source_query_availability'

// Every replacement fence must distinguish a producer that can still mutate (or may
// already have mutated) the served asset from an orphan queued row that a terminal
// run never dispatched. The DB behaviour is proven against real PostgreSQL in
// get_dashas.pagination.db.test.ts; this guard keeps the sibling fences from
// drifting back to the bare `state IN ('queued', 'building')` disjunct (RC-2).
const layersDir = path.resolve(__dirname, '..')
const chartScopedFences = [
  'L1_ganita/get_dashas.ts',
  'L2_bodha/query_mechanisms.ts',
  'reading_checklist.ts',
]

function source(relative: string): string {
  return readFileSync(path.join(layersDir, relative), 'utf8')
}

describe('replacement fence consistency', () => {
  it.each(chartScopedFences)('%s never fences a never-dispatched queued row in a terminal run', (file) => {
    const sql = source(file)
    expect(sql).not.toMatch(/OR\s+fenced_asset\.state IN \('queued', 'building'\)/)
    expect(sql).toContain("fenced_run.state IN ('planned', 'running', 'paused')")
    expect(sql).toContain("NOT (fenced_asset.state = 'queued' AND fenced_asset.started_at IS NULL)")
  })

  it('applies the same orphan rule to the global bg_texts handler and its availability probe', () => {
    const contract = getSourceQueryAvailabilityContract('source-query:query-classical-texts:v1')!
    for (const sql of [source('L0_brahmagyan/query_classical_texts.ts'), contract.sql]) {
      expect(sql).not.toMatch(/OR asset\.state IN \('queued', 'building'\)\)/)
      expect(sql).toContain("run.state IN ('planned', 'running', 'paused')")
      expect(sql).toContain("NOT (asset.state = 'queued' AND asset.started_at IS NULL)")
      expect(sql).toContain('>= (SELECT MAX(observed_at) FROM eligible_receipts)')
    }
  })
})
