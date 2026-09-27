/**
 * source_query_availability — chart-context staleness (Jātaka Phase-A2, item 2).
 *
 * `source-query:query-calibration:v1`'s representative probe mirrors
 * query_calibration.ts's real JOIN mimamsa_predictions shape (documented via
 * its own `source_refs`), so it must mirror the staleness exclusion too — an
 * out-of-sync probe would validate a shape the real handler no longer runs.
 * The probe is LIMIT 0, so this is a documentation-accuracy guard, not an
 * observable-row-count assertion.
 */
import { describe, expect, it } from 'vitest'
import { getSourceQueryAvailabilityContract } from '../source_query_availability'

describe('query-calibration availability probe mirrors the real staleness exclusion', () => {
  it('the mimamsa_predictions JOIN excludes chart-context-stale rows', () => {
    const contract = getSourceQueryAvailabilityContract('source-query:query-calibration:v1')
    expect(contract).toBeDefined()
    expect(contract!.sql).toMatch(/LEFT JOIN mimamsa_predictions p[\s\S]*?chart_context_stale_at\s+IS\s+NULL/)
  })
})
