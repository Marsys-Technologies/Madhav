/**
 * register_gochara_contact_ledger.test.ts — WP7 P-4 acceptance.
 *
 * Mocks global fetch (the platform DB proxy) — no live DB. Dispatches on SQL
 * substrings exactly as the sibling gochara suites do. Coverage:
 *   1. Layers are disjoint by construction: the confirmed page and the
 *      context layer arrive from separate queries with the confirmed
 *      predicate / its negation in the SQL.
 *   2. hard_floor is trim-proof: a confirmed set larger than the page limit
 *      returns not_computed + floor_overflow — never a truncated floor.
 *   3. moon_on_demand: searched_horizon is the moon partition's own
 *      completed_horizon quoted exactly (H-3) with unsearched_reason present;
 *      a missing moon partition is stated, never served as 0 contacts.
 *   4. Chart with no authority row returns status='unpublished' with a full
 *      coverage object — no contact/coverage SQL is even issued.
 *   5. Keyset pagination: a full page yields next_cursor; the following call
 *      carries the (t_exact, contact_id) cursor clause.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.stubGlobal('fetch', vi.fn())

import { queryContactLedger } from './register_gochara_contact_ledger'

const mockFetch = globalThis.fetch as unknown as ReturnType<typeof vi.fn>
const principal = { user_uid: 'test-uid', key_id: 'mcp_test_key' }
const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

function jsonRes(rows: Record<string, unknown>[]) {
  return { ok: true, status: 200, json: async () => ({ rows }), text: async () => JSON.stringify({ rows }) }
}

function sqlOf(call: number): string {
  const init = mockFetch.mock.calls[call][1] as { body: string }
  return (JSON.parse(init.body) as { sql: string }).sql
}

function episodeRow(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    contact_id: 'sha256:' + 'ab'.repeat(32),
    independence_group: 'ig-1',
    body: 'Saturn',
    relation: 'conjunction',
    aspect_deg: null,
    target_type: 'karaka',
    target_ref: 'sun',
    target_resolution_state: 'resolved',
    t_in: '2027-01-01T00:00:00Z',
    t_exact: '2027-01-15T00:00:00Z',
    t_out: '2027-02-01T00:00:00Z',
    branch: 'direct',
    orb_max_deg: 5,
    completeness_state: 'qualified',
    epistemic_class: 'computed',
    operator_role: 'primary',
    claim_grain: 'contact',
    comparable_with: 'self',
    convention_id: 'conv-1',
    classical_citation: null,
    uncited_extension: false,
    truncated_at_horizon: null,
    ...overrides,
  }
}

const MOON_COVERAGE_ROW = {
  partition_kind: 'moon_on_demand',
  partition_key: 'moon:interval:2027-01-01/2027-02-01',
  requested_horizon: '[2027-01-01, 2027-02-01)',
  completed_horizon: '[2027-01-01, 2027-01-20)',
  resolution: 0.5,
  relations_searched: ['conjunction'],
  targets_requested: 3,
  targets_resolved: 2,
  targets_unresolved: 1,
  target_resolution_state_counts: { resolved: 2, unqualified: 1 },
  unavailable_inputs: { moon_arc: 'not_persisted' },
  unsearched_reason: 'ephemeris_window_exceeded',
}

describe('queryContactLedger — WP7 P-4', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('serves confirmed floor and context layer disjoint by construction', async () => {
    mockFetch
      .mockResolvedValueOnce(jsonRes([{ authoritative_generation: '4.0' }])) // authority
      .mockResolvedValueOnce(jsonRes([{ manifest_id: 'm-1', convention_id: 'conv-1', content_digest: 'sha256:x', status: 'published' }])) // manifest
      .mockResolvedValueOnce(jsonRes([{ n: '1' }])) // confirmed count
      .mockResolvedValueOnce(jsonRes([episodeRow()])) // confirmed page
      .mockResolvedValueOnce(jsonRes([episodeRow({ contact_id: 'sha256:' + 'cd'.repeat(32), completeness_state: 'unqualified', target_resolution_state: 'unqualified' })])) // context
      .mockResolvedValueOnce(jsonRes([])) // coverage

    const result = await queryContactLedger(
      { chart_id: CHART, include_context: true, page: { limit: 50 } },
      principal
    )

    expect(result.status).toBe('ok')
    expect(result.hard_floor.count).toBe(1)
    expect(result.hard_floor.confirmed).toHaveLength(1)
    expect(result.context_layer?.catalog_only).toHaveLength(1)
    expect(result.context_layer?.unqualified_count).toBe(1)
    // the confirmed predicate and its negation live in the SQL itself
    expect(sqlOf(3)).toContain("completeness_state IN ('confirmed', 'qualified')")
    expect(sqlOf(3)).toContain("target_resolution_state = 'resolved'")
    expect(sqlOf(4)).toContain('NOT (')
    // disjoint ids
    expect(result.hard_floor.confirmed[0].contact_id).not.toBe(
      result.context_layer?.catalog_only[0].contact_id
    )
  })

  it('page size smaller than the confirmed set → not_computed + floor_overflow, never a truncated floor', async () => {
    mockFetch
      .mockResolvedValueOnce(jsonRes([{ authoritative_generation: '4.0' }]))
      .mockResolvedValueOnce(jsonRes([{ manifest_id: 'm-1', convention_id: 'conv-1', content_digest: 'sha256:x', status: 'published' }]))
      .mockResolvedValueOnce(jsonRes([{ n: '7' }])) // confirmed count > limit 3

    const result = await queryContactLedger(
      { chart_id: CHART, page: { limit: 3 } },
      principal
    )

    expect(result.status).toBe('not_computed')
    expect(result.floor_overflow).toBe(true)
    expect(result.hard_floor.count).toBe(7) // true count still reported
    expect(result.hard_floor.confirmed).toEqual([]) // nothing truncated served
    expect(mockFetch).toHaveBeenCalledTimes(3) // no page query was issued
  })

  it('moon_on_demand: searched_horizon quotes the moon partition exactly (H-3) with unsearched_reason', async () => {
    mockFetch
      .mockResolvedValueOnce(jsonRes([{ authoritative_generation: '4.0' }]))
      .mockResolvedValueOnce(jsonRes([])) // no manifest row
      .mockResolvedValueOnce(jsonRes([{ n: '0' }]))
      .mockResolvedValueOnce(jsonRes([])) // confirmed page
      .mockResolvedValueOnce(jsonRes([MOON_COVERAGE_ROW])) // coverage

    const result = await queryContactLedger(
      { chart_id: CHART, moon: 'on_demand', horizon: { start: '2027-01-01', end: '2027-02-01' }, page: { limit: 50 } },
      principal
    )

    expect(result.status).toBe('ok')
    expect(result.manifest).toBeNull()
    expect(result.coverage.searched_horizon).toBe('[2027-01-01, 2027-01-20)')
    const moon = result.coverage.partitions.find((p) => p.partition_kind === 'moon_on_demand')
    expect(moon?.requested_horizon).toBe('[2027-01-01, 2027-02-01)')
    expect(moon?.unsearched_reason).toBe('ephemeris_window_exceeded')
    expect(result.coverage.unavailable_inputs).toEqual({ moon_arc: 'not_persisted' })
  })

  it('chart with no authority row → unpublished full coverage object, no contact/coverage SQL issued', async () => {
    mockFetch.mockResolvedValueOnce(jsonRes([])) // authority: absent

    const result = await queryContactLedger({ chart_id: CHART }, principal)

    expect(result.status).toBe('unpublished')
    expect(result.generation).toBeNull()
    expect(result.manifest).toBeNull()
    expect(result.coverage.partitions).toEqual([])
    expect(result.coverage.note).toContain('unpublished')
    expect(mockFetch).toHaveBeenCalledTimes(1)
  })

  it('keyset pagination: full page yields next_cursor consumed by the following call', async () => {
    const page1 = [
      episodeRow({ contact_id: 'sha256:' + '01'.repeat(32), t_exact: '2027-01-10T00:00:00Z' }),
      episodeRow({ contact_id: 'sha256:' + '02'.repeat(32), t_exact: '2027-01-12T00:00:00Z' }),
      episodeRow({ contact_id: 'sha256:' + '03'.repeat(32), t_exact: '2027-01-14T00:00:00Z' }), // the +1 lookahead row
    ]
    mockFetch
      .mockResolvedValueOnce(jsonRes([{ authoritative_generation: '4.0' }]))
      .mockResolvedValueOnce(jsonRes([]))
      .mockResolvedValueOnce(jsonRes([{ n: '2' }]))
      .mockResolvedValueOnce(jsonRes(page1))
      .mockResolvedValueOnce(jsonRes([])) // coverage

    const first = await queryContactLedger({ chart_id: CHART, page: { limit: 2 } }, principal)
    expect(first.hard_floor.confirmed).toHaveLength(2)
    expect(first.page.next_cursor).toBe('2027-01-12T00:00:00Z|sha256:' + '02'.repeat(32))

    mockFetch
      .mockResolvedValueOnce(jsonRes([{ authoritative_generation: '4.0' }]))
      .mockResolvedValueOnce(jsonRes([]))
      .mockResolvedValueOnce(jsonRes([{ n: '2' }]))
      .mockResolvedValueOnce(jsonRes([episodeRow({ contact_id: 'sha256:' + '03'.repeat(32) })]))
      .mockResolvedValueOnce(jsonRes([]))

    const second = await queryContactLedger(
      { chart_id: CHART, page: { limit: 2, cursor: first.page.next_cursor! } },
      principal
    )
    const pageSql = sqlOf(8) // second call: authority(5), manifest(6), count(7), page(8)
    expect(pageSql).toContain('(t_exact, contact_id) >')
    expect(second.page.next_cursor).toBeNull()
  })

  it('refuses a TEST SLICE candidate by name — explicit generation 5.0, no contact or coverage SQL issued', async () => {
    mockFetch.mockResolvedValueOnce(
      jsonRes([{ manifest_id: 'm-slice', convention_id: 'conv-1', content_digest: 'sha256:x', status: 'candidate',
                 stored_scope: 'test_slice', has_test_slice: true }])
    )
    const res = await queryContactLedger({ chart_id: CHART, generation: '5.0' }, principal)
    expect(res.status).toBe('not_computed')
    expect(res.refusal).toBe('test_slice_candidate')
    expect(res.hard_floor).toEqual({ confirmed: [], count: 0 })
    expect(res.coverage.partitions).toEqual([])
    expect(res.coverage.note).toMatch(/TEST SLICE/)
    expect(mockFetch).toHaveBeenCalledTimes(1)                    // the manifest read only
    expect(sqlOf(0)).toContain('kala_gochara_publication')
  })

  it('refuses on EITHER marker: the test_slice component alone, or the scope word alone', async () => {
    for (const row of [
      { stored_scope: 'stored_non_moon', has_test_slice: true },
      { stored_scope: 'test_slice', has_test_slice: false },
    ]) {
      mockFetch.mockReset()
      mockFetch.mockResolvedValueOnce(
        jsonRes([{ manifest_id: 'm-s', convention_id: 'conv-1', content_digest: 'sha256:x', status: 'candidate', ...row }])
      )
      const res = await queryContactLedger({ chart_id: CHART, generation: '5.0' }, principal)
      expect(res.refusal).toBe('test_slice_candidate')
      expect(mockFetch).toHaveBeenCalledTimes(1)
    }
  })

  const MANIFEST = (status: string, extra: Record<string, unknown> = {}) =>
    jsonRes([{ manifest_id: 'm-d', convention_id: 'conv-1', content_digest: 'sha256:x', status,
               stored_scope: 'stored_non_moon', has_test_slice: false, ...extra }])

  function serveData() {
    mockFetch
      .mockResolvedValueOnce(jsonRes([{ n: '1' }]))                        // confirmed count
      .mockResolvedValueOnce(jsonRes([episodeRow()]))                      // confirmed page
      .mockResolvedValueOnce(jsonRes([]))                                  // coverage partitions
  }

  const SEALED = (sealed: boolean) => jsonRes([{ sealed }])

  it('a governed (5.x) generation that is PUBLISHED and SEALED is served', async () => {
    mockFetch.mockResolvedValueOnce(MANIFEST('published')).mockResolvedValueOnce(SEALED(true))
    serveData()
    const res = await queryContactLedger({ chart_id: CHART, generation: '5.0' }, principal)
    expect(res.refusal).toBeUndefined()
    expect(res.diagnostic).toBeUndefined()
    expect(res.status).toBe('ok')
    expect(res.hard_floor.count).toBe(1)
    expect(sqlOf(1)).toBe('SELECT EXISTS (SELECT 1 FROM ka_gochara_generation_seal WHERE chart_id = $1::uuid AND generation = $2) AS sealed')
  })

  it('an interrupted slice-to-full rebuild (new UNSTAMPED candidate manifest, old chain) is NOT served as ok — no contact or coverage SQL', async () => {
    // between the manifest substep and the snapshot substep the manifest already carries the new vector (no slice stamp), so the
    // slice guard passes; the status rule is what stops it
    mockFetch.mockResolvedValueOnce(MANIFEST('candidate')).mockResolvedValueOnce(SEALED(false))
    const res = await queryContactLedger({ chart_id: CHART, generation: '5.0' }, principal)
    expect(res.status).toBe('not_computed')
    expect(res.refusal).toBe('candidate_not_served')
    expect(res.hard_floor).toEqual({ confirmed: [], count: 0 })
    expect(res.coverage.partitions).toEqual([])
    expect(res.coverage.note).toMatch(/not published and sealed/)
    expect(mockFetch).toHaveBeenCalledTimes(2)                            // the manifest read and the seal lookup only
  })

  it('published but NOT sealed is refused too', async () => {
    mockFetch.mockResolvedValueOnce(MANIFEST('published')).mockResolvedValueOnce(SEALED(false))
    const res = await queryContactLedger({ chart_id: CHART, generation: '5.0' }, principal)
    expect(res.refusal).toBe('candidate_not_served')
    expect(mockFetch).toHaveBeenCalledTimes(2)
  })

  it('a governed generation with NO manifest is refused', async () => {
    mockFetch.mockResolvedValueOnce(jsonRes([])).mockResolvedValueOnce(SEALED(false))      // no manifest row at all
    const none = await queryContactLedger({ chart_id: CHART, generation: '5.0' }, principal)
    expect(none.refusal).toBe('candidate_not_served')
    expect(none.manifest).toBeNull()
  })

  it('a FAILED seal lookup never serves: refused, and the response says the lookup failed', async () => {
    mockFetch.mockResolvedValueOnce(MANIFEST('published'))
      .mockResolvedValueOnce({ ok: false, status: 400, json: async () => ({}), text: async () => 'Rejected by whitelist' })
    const res = await queryContactLedger({ chart_id: CHART, generation: '5.0' }, principal)
    expect(res.refusal).toBe('candidate_not_served')
    expect(res.coverage.note).toMatch(/seal lookup failed/)
  })

  it('(b) a SUPERSEDED generation that WAS sealed is refused, and a diagnostic read reports sealed TRUE (seal history is independent of status)', async () => {
    mockFetch.mockResolvedValueOnce(MANIFEST('superseded')).mockResolvedValueOnce(SEALED(true))
    const refused = await queryContactLedger({ chart_id: CHART, generation: '5.0' }, principal)
    expect(refused.refusal).toBe('candidate_not_served')
    expect(refused.coverage.note).toMatch(/manifest superseded, sealed/)
    mockFetch.mockReset()
    mockFetch.mockResolvedValueOnce(MANIFEST('withdrawn')).mockResolvedValueOnce(SEALED(true))
    serveData()
    const diag = await queryContactLedger({ chart_id: CHART, generation: '5.0', diagnostic: true }, principal)
    expect(diag.status).toBe('ok')
    expect(diag.diagnostic).toMatchObject({ manifest_status: 'withdrawn', sealed: true })
  })

  it('diagnostic=true reads an unsealed governed generation, LABELLED as diagnostic', async () => {
    mockFetch.mockResolvedValueOnce(MANIFEST('candidate')).mockResolvedValueOnce(SEALED(false))
    serveData()
    const res = await queryContactLedger({ chart_id: CHART, generation: '5.0', diagnostic: true }, principal)
    expect(res.status).toBe('ok')
    expect(res.refusal).toBeUndefined()
    expect(res.diagnostic).toMatchObject({ served_unpublished_generation: true, manifest_status: 'candidate', sealed: false })
    expect(res.diagnostic?.note).toMatch(/NOT a coverage statement/)
  })

  it('a diagnostic read whose seal lookup FAILED reports sealed null, never false', async () => {
    mockFetch.mockResolvedValueOnce(MANIFEST('candidate'))
      .mockResolvedValueOnce({ ok: false, status: 400, json: async () => ({}), text: async () => 'Rejected' })
    serveData()
    const res = await queryContactLedger({ chart_id: CHART, generation: '5.0', diagnostic: true }, principal)
    expect(res.diagnostic).toMatchObject({ sealed: null, seal_lookup_failed: true })
  })

  it('diagnostic=true never serves a TEST SLICE', async () => {
    mockFetch.mockResolvedValueOnce(MANIFEST('candidate', { stored_scope: 'test_slice', has_test_slice: true }))
    const res = await queryContactLedger({ chart_id: CHART, generation: '5.0', diagnostic: true }, principal)
    expect(res.refusal).toBe('test_slice_candidate')
    expect(mockFetch).toHaveBeenCalledTimes(1)
  })

  it('legacy generations are unchanged: 4.0 reads need no seal and issue no seal query', async () => {
    mockFetch
      .mockResolvedValueOnce(MANIFEST('published'))
    serveData()
    const res = await queryContactLedger({ chart_id: CHART, generation: '4.0' }, principal)
    expect(res.status).toBe('ok')
    expect(mockFetch).toHaveBeenCalledTimes(4)                            // manifest + count + page + coverage
    for (let i = 0; i < 4; i++) expect(sqlOf(i)).not.toContain('ka_gochara_generation_seal')
  })
})
