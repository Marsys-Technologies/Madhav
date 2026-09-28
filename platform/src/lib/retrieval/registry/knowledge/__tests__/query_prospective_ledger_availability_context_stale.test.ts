/**
 * source_query_availability — chart-context staleness (Jātaka Phase-A3,
 * independent-review Important finding #6).
 *
 * `source-query:query-prospective-ledger:v1`'s representative probe mirrors
 * query_prospective_ledger.ts's real SELECT shape (documented via its own
 * `source_refs`), so it must mirror the staleness exclusion the real handler
 * applies by default (migration 1123 / Jātaka Phase-A3 item 2) too — an
 * out-of-sync probe would validate a shape the real handler no longer runs.
 * The probe is LIMIT 0, so this is a documentation-accuracy guard, not an
 * observable-row-count assertion.
 */
import { describe, expect, it } from 'vitest'
import { getSourceQueryAvailabilityContract } from '../source_query_availability'

describe('query-prospective-ledger availability probe mirrors the real staleness exclusion', () => {
  it('the brahma_prospective_ledger SELECT excludes chart-context-stale rows', () => {
    const contract = getSourceQueryAvailabilityContract('source-query:query-prospective-ledger:v1')
    expect(contract).toBeDefined()
    expect(contract!.sql).toMatch(/FROM brahma_prospective_ledger p[\s\S]*?chart_context_stale_at\s+IS\s+NULL/)
  })
})
