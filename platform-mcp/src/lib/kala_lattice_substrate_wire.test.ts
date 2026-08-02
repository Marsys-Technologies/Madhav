/**
 * kala_lattice_substrate_wire.test.ts — REGRESSION for the ṢAḌ-DARŚANA W3
 * lattice-unwrap production defect (kala_elect_get serving 'not_adjudicated'
 * with "no parihara_rules section" against a fully-populated production DB).
 *
 * Root cause: `fetchLatticeSubstrate` read `envelope.result.rows` /
 * `.parihara_rules` / `.factor_census` directly, but the primitives route
 * returns a legacy ToolBundle whose real payload is a JSON string at
 * `envelope.result.results[0].content` (tool_name_bridge.ts
 * `toToolBundleResults` branch 3). Worse, `lattice_available` was set
 * unconditionally on HTTP 200 (§N.8 violation) — silently downgrading ELECT to
 * the legacy ph_muhurta path.
 *
 * These tests drive `fetchLatticeSubstrate` (and the ritual-resonance /
 * upaya substrate fetchers) against BYTE-FAITHFUL wire fixtures — the mock
 * shape mismatch is exactly why the defect shipped with green tests.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../types.js'

const mockCallPlatformPrimitive = vi.fn()
vi.mock('../client.js', async () => {
  const actual = await vi.importActual('../client.js')
  return { ...actual, callPlatformPrimitive: (...args: unknown[]) => mockCallPlatformPrimitive(...args) }
})

import { fetchLatticeSubstrate } from './kala_lattice_query.js'
import { fetchActivityRules, fetchStructuralSubstrate } from './kala_ritual_resonance.js'

const PRINCIPAL: Principal = {
  user_uid: 'test-user',
  key_id: 'test-key',
  role: 'super_admin',
} as unknown as Principal

/** Byte-faithful production envelope: capability {content, is_error:false} →
 *  capabilityResultToToolBundle → toToolBundleResults branch 3. */
function wireEnvelope(payload: Record<string, unknown>) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-1',
      result: {
        tool_bundle_id: 'tb-1',
        tool_name: 'x',
        results: [{ content: JSON.stringify(payload) }],
        result_hash: 'sha256:x',
        duration_ms: 3,
      },
    },
  }
}

const LATTICE_ROW = {
  factor_family: 'vara',
  factor_key: 'ravivara',
  start_utc: '2026-08-02T00:00:00Z',
  end_utc: '2026-08-03T00:00:00Z',
  detail: { factor_id: 1 },
  source_citation: 'muhurta_chintamani 2.1',
  corpus_status: 'computed_cited',
}

const PARIHARA_PAYLOAD = {
  sections_returned: ['parihara_rules', 'factor_census'],
  parihara_rules: {
    rows: [{
      dosha_canonical_id: 'rahu_kalam',
      dosha_name_en: 'Rahu Kalam',
      dosha_category: 'kala_dosha',
      cancellation_index: 1,
      cancellation_condition_text: 'Abhijit muhurta cancels',
      net_standing: 'cancellable',
      scope: 'muhurta',
      source_text_id: 'bphs_jaimini',
      source_chapter: 213,
      source_citation: 'PG213',
    }],
    count: 1,
  },
  factor_census: {
    rows: [{
      factor_family: 'vara',
      factor_name: 'vara',
      disposition: 'computed',
      citation_or_gap_note: 'computed from panchang_engine',
      evidence_pointer: 'bg_muhurta_lattice',
      school_tag: null,
    }],
    count: 1,
  },
}

beforeEach(() => {
  mockCallPlatformPrimitive.mockReset()
})

describe('fetchLatticeSubstrate — production wire shape (the missing test)', () => {
  it('parses lattice rows + parihāra + census out of the ToolBundle wrapper; all three availability flags are REAL', async () => {
    mockCallPlatformPrimitive.mockImplementation(async (tool: string) => {
      if (tool === 'query_muhurta_lattice') return wireEnvelope({ rows: [LATTICE_ROW], count: 1 })
      if (tool === 'query_parihara_graph') return wireEnvelope(PARIHARA_PAYLOAD)
      throw new Error(`unexpected tool ${tool}`)
    })

    const s = await fetchLatticeSubstrate(
      { start_utc: '2026-08-02T00:00:00Z', end_utc: '2026-08-03T00:00:00Z' },
      PRINCIPAL,
    )

    expect(s.lattice_available).toBe(true)
    expect(s.lattice_rows).toHaveLength(1)
    expect(s.lattice_rows[0]?.factor_key).toBe('ravivara')
    expect(s.parihara_available).toBe(true)
    expect(s.parihara_rules).toHaveLength(1)
    expect(s.parihara_rules[0]?.dosha_canonical_id).toBe('rahu_kalam')
    expect(s.census_available).toBe(true)
    expect(s.census_rows).toHaveLength(1)
    expect(s.unavailable_reason).toBeNull()
  })

  it('honestly-empty lattice rows keep lattice_available=true (empty horizon ≠ unavailable)', async () => {
    mockCallPlatformPrimitive.mockImplementation(async (tool: string) => {
      if (tool === 'query_muhurta_lattice') return wireEnvelope({ rows: [], count: 0, empty_reason: 'no rows overlap' })
      return wireEnvelope(PARIHARA_PAYLOAD)
    })
    const s = await fetchLatticeSubstrate({ start_utc: 'a', end_utc: 'b' }, PRINCIPAL)
    expect(s.lattice_available).toBe(true)
    expect(s.lattice_rows).toEqual([])
    expect(s.unavailable_reason).toBeNull()
  })

  it('a payload genuinely missing a section reports section-absent (distinct from wrapper failure)', async () => {
    mockCallPlatformPrimitive.mockImplementation(async (tool: string) => {
      if (tool === 'query_muhurta_lattice') return wireEnvelope({ rows: [] })
      // sections param limited the response — factor_census genuinely absent.
      return wireEnvelope({ sections_returned: ['parihara_rules'], parihara_rules: { rows: [], count: 0 } })
    })
    const s = await fetchLatticeSubstrate({ start_utc: 'a', end_utc: 'b' }, PRINCIPAL)
    expect(s.parihara_available).toBe(true)
    expect(s.census_available).toBe(false)
    expect(s.unavailable_reason).toContain('no factor_census section')
    expect(s.unavailable_reason).not.toContain('unwrap failed')
  })

  it('wrapper-shape drift (no results array) is UNAVAILABLE with the unwrap reason — never a silent empty', async () => {
    mockCallPlatformPrimitive.mockResolvedValue({
      status: 200,
      envelope: { ok: true, trace_id: 't', result: { tool_bundle_id: 'tb-1', tool_name: 'x' } },
    })
    const s = await fetchLatticeSubstrate({ start_utc: 'a', end_utc: 'b' }, PRINCIPAL)
    expect(s.lattice_available).toBe(false)
    expect(s.parihara_available).toBe(false)
    expect(s.census_available).toBe(false)
    expect(s.unavailable_reason).toContain('ToolBundle unwrap failed (results_missing)')
    expect(s.unavailable_reason).toContain('not as empty data')
  })

  it('non-JSON content is UNAVAILABLE with content_not_json — never parsed-as-nothing', async () => {
    mockCallPlatformPrimitive.mockResolvedValue({
      status: 200,
      envelope: { ok: true, trace_id: 't', result: { results: [{ content: '<!doctype html>' }] } },
    })
    const s = await fetchLatticeSubstrate({ start_utc: 'a', end_utc: 'b' }, PRINCIPAL)
    expect(s.lattice_available).toBe(false)
    expect(s.parihara_available).toBe(false)
    expect(s.unavailable_reason).toContain('content_not_json')
  })

  it('non-200 status keeps the status reason (unchanged behaviour)', async () => {
    mockCallPlatformPrimitive.mockResolvedValue({ status: 503, envelope: { ok: false } })
    const s = await fetchLatticeSubstrate({ start_utc: 'a', end_utc: 'b' }, PRINCIPAL)
    expect(s.lattice_available).toBe(false)
    expect(s.unavailable_reason).toContain('query_muhurta_lattice returned status 503')
  })
})

describe('fetchActivityRules — same wire discipline', () => {
  it('reads activity_rules through the ToolBundle wrapper', async () => {
    mockCallPlatformPrimitive.mockResolvedValue(wireEnvelope({
      sections_returned: ['activity_rules'],
      activity_rules: {
        rows: [{ activity_class: 'vivah', factor_type: 'vara', factor_id: 1, quality_score: 0.8, source_citation: 'MC 5.1' }],
        count: 1,
      },
    }))
    const r = await fetchActivityRules('vivah', PRINCIPAL)
    expect(r.available).toBe(true)
    expect(r.rows).toHaveLength(1)
    expect(r.unavailable_reason).toBeNull()
  })

  it('wrapper drift → honest unavailable with the unwrap reason', async () => {
    mockCallPlatformPrimitive.mockResolvedValue({
      status: 200,
      envelope: { ok: true, result: { results: [] } },
    })
    const r = await fetchActivityRules('vivah', PRINCIPAL)
    expect(r.available).toBe(false)
    expect(r.unavailable_reason).toContain('results_empty')
  })

  it('payload without the section → section-absent reason (distinct)', async () => {
    mockCallPlatformPrimitive.mockResolvedValue(wireEnvelope({ sections_returned: [] }))
    const r = await fetchActivityRules('vivah', PRINCIPAL)
    expect(r.available).toBe(false)
    expect(r.unavailable_reason).toContain('no activity_rules section')
  })
})

describe('fetchStructuralSubstrate — whitelisted names + wire unwrap', () => {
  it('calls the WHITELISTED primitive names (bare capability names 400 on the route)', async () => {
    mockCallPlatformPrimitive.mockResolvedValue(wireEnvelope({ rows: [] }))
    await fetchStructuralSubstrate('482012f1-710e-4a25-994a-93821f5871aa', PRINCIPAL)
    const toolsCalled = mockCallPlatformPrimitive.mock.calls.map((c) => c[0])
    expect(toolsCalled).toContain('query_remedies')
    expect(toolsCalled).toContain('bodha_rm_resonances_get')
    expect(toolsCalled).not.toContain('query_remedy_corpus')
    expect(toolsCalled).not.toContain('query_rm_resonances')
  })

  it('unwraps both legs from the ToolBundle wrapper', async () => {
    mockCallPlatformPrimitive.mockImplementation(async (tool: string) => {
      if (tool === 'query_remedies') return wireEnvelope({ rows: [{ remedy_id: 'r1', planet: 'saturn' }] })
      if (tool === 'bodha_rm_resonances_get') return wireEnvelope({ rows: [{ graha: 'Saturn', resonance_score: 0.7 }] })
      throw new Error(`unexpected tool ${tool}`)
    })
    const s = await fetchStructuralSubstrate('482012f1-710e-4a25-994a-93821f5871aa', PRINCIPAL)
    expect(s.remedy_available).toBe(true)
    expect(s.remedy_rows).toHaveLength(1)
    expect(s.resonance_available).toBe(true)
    expect(s.resonance_rows).toHaveLength(1)
  })

  it('wrapper drift on one leg names that leg in missing_legs with the unwrap reason', async () => {
    mockCallPlatformPrimitive.mockImplementation(async (tool: string) => {
      if (tool === 'query_remedies') {
        return { status: 200, envelope: { ok: true, result: { tool_bundle_id: 'tb', tool_name: 'x' } } }
      }
      return wireEnvelope({ rows: [] })
    })
    const s = await fetchStructuralSubstrate('482012f1-710e-4a25-994a-93821f5871aa', PRINCIPAL)
    expect(s.remedy_available).toBe(false)
    expect(s.missing_legs.some((l) => l.includes('brahma_remedy_corpus') && l.includes('results_missing'))).toBe(true)
    expect(s.resonance_available).toBe(true)
  })
})
