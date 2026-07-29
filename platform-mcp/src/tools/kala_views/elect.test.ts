/**
 * elect.test.ts — ṢAḌ-DARŚANA v2 W0.4 kala_elect_get facade.
 * Covers: the argument-shaped reading composed from muhurta_finder windows, honest
 * coverage for the not-yet-built W3/W4 election-doctrine items, and the Mode-3 role
 * (ELECT answers an undertaking-shaped call — the routing redirect itself is a separate
 * lane's `kala_ritual_get`, not tested here).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockHandleMuhurtaFinder = vi.fn()

vi.mock('../muhurta_finder.js', async () => {
  const actual = await vi.importActual<typeof import('../muhurta_finder.js')>('../muhurta_finder.js')
  return {
    ...actual,
    handleMuhurtaFinder: (...args: unknown[]) => mockHandleMuhurtaFinder(...args),
  }
})

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const PRINCIPAL = { user_uid: 'u1', key_id: 'k1', role: 'guest' as const }

function muhurtaResult(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    ok: true,
    chart_id: CHART_ID,
    action_type: 'business',
    query_window: { start: '2026-08-01', end: '2026-10-30' },
    windows: [
      {
        start: '2026-08-05T00:00:00Z',
        end: '2026-08-07T00:00:00Z',
        score: 0.82,
        factors: {
          panchanga_quality: 0.7, dasha_quality: 0.8, transit_quality: 0.6, signal_activation: 0.5,
          panchanga_details: { tithi_name: 'Tritiya', vara_lord: 'Guru', moon_nakshatra: 'Pushya', yoga: 'Siddha', inauspicious_windows: [] },
          dasha_details: { md_lord: 'Mercury', ad_lord: 'Venus' },
          avoid_notes: [],
        },
        source_citation: 'BPHS ch.46',
        hard_flag: false,
        disqualified: false,
        rank_penalty_reason: [],
      },
      {
        start: '2026-08-12T00:00:00Z',
        end: '2026-08-14T00:00:00Z',
        score: 0.55,
        factors: {
          panchanga_quality: 0.4, dasha_quality: 0.5, transit_quality: 0.5, signal_activation: 0.4,
          panchanga_details: { tithi_name: 'Dashami', vara_lord: 'Shani', moon_nakshatra: 'Ashwini', yoga: 'Vyatipata', inauspicious_windows: [] },
          dasha_details: { md_lord: 'Mercury', ad_lord: 'Venus' },
          avoid_notes: [],
        },
        source_citation: 'BPHS ch.46',
        hard_flag: true,
        disqualified: true,
        rank_penalty_reason: ['Vadha-tara for native star'],
        tara_bala: {
          janma_nakshatra: 'Purva Bhadrapada', day_nakshatra: 'Ashwini', count_from_janma: 3, tara_index: 3,
          tara_name: 'Vipat', favorable: false, adverse: true, severity: 'severe', citation: 'Muhurta Chintamani',
        },
      },
    ],
    window_count: 2,
    provenance_envelope: {
      source: 'phala.muhurta', asset: 'PH-4-4', algorithm: 'x', min_score_applied: 0,
      chart_id: CHART_ID, action_type: 'business', queried_at: '2026-07-29T00:00:00Z',
      l1_ground_truth: 'FORENSIC', b3_citation_compliant: true,
    },
    lane_f: {
      tara_bala_status: 'applied' as const,
      hora_status: 'applied' as const,
      hora_sunrise_assumption: 'x',
      ranking_note: 'x',
      target_graha_status: 'not_requested' as const,
    },
    ...overrides,
  }
}

describe('handleKalaElectGet', () => {
  beforeEach(() => {
    mockHandleMuhurtaFinder.mockReset()
  })

  it('composes an argument reading with a live top candidate and a hard-vetoed dissent row', async () => {
    mockHandleMuhurtaFinder.mockResolvedValue({
      structuredContent: { object: muhurtaResult() },
      content: [{ type: 'text', text: '{}' }],
    })

    const { handleKalaElectGet } = await import('./elect.js')
    const { response, error } = await handleKalaElectGet(
      { chart_id: CHART_ID, undertaking: 'business', limit: 5 },
      PRINCIPAL,
    )

    expect(error).toBeUndefined()
    expect(response).toBeDefined()
    expect(response!.tool).toBe('kala_elect_get')
    expect(response!.candidate_count).toBe(2)
    expect(response!.reading.thesis).toContain('2026-08-05')
    // The disqualified window surfaces as dissent, not silently dropped.
    expect(response!.reading.dissent.length).toBeGreaterThan(0)
    expect(response!.reading.dissent[0]!.source).toContain('tara_bala')
    expect(response!.reading.verdict.tier).toBe('structural_prior')
    expect(response!.reading.falsifier?.resolves_by).toBe('2026-08-07')
    // ELECT is itself the intervention plane — self-pointer is null, not omitted.
    expect(response!.tri_plane.intervention_ref).toBeNull()
    // Honest W0 gap coverage present.
    const conceptNames = response!.coverage.map((c) => c.concept)
    expect(conceptNames).toContain('contender_lattice_parihara_adjudication')
    expect(conceptNames).toContain('ritual_pairing')
  })

  it('reports an honest gap when every candidate is disqualified', async () => {
    const allVetoed = muhurtaResult()
    ;(allVetoed.windows as Record<string, unknown>[])[0]!['disqualified'] = true
    mockHandleMuhurtaFinder.mockResolvedValue({
      structuredContent: { object: allVetoed },
      content: [{ type: 'text', text: '{}' }],
    })

    const { handleKalaElectGet } = await import('./elect.js')
    const { response } = await handleKalaElectGet({ chart_id: CHART_ID, undertaking: 'business' }, PRINCIPAL)

    expect(response!.gap_report).not.toBeNull()
    expect(response!.reading.thesis).toContain('hard veto')
  })

  it('reports an honest empty when no windows are computed', async () => {
    mockHandleMuhurtaFinder.mockResolvedValue({
      structuredContent: { object: muhurtaResult({ windows: [], window_count: 0, empty_reason: 'date_range outside populated panchanga horizon' }) },
      content: [{ type: 'text', text: '{}' }],
    })

    const { handleKalaElectGet } = await import('./elect.js')
    const { response } = await handleKalaElectGet({ chart_id: CHART_ID, undertaking: 'business' }, PRINCIPAL)

    expect(response!.candidate_count).toBe(0)
    expect(response!.gap_report).toContain('outside populated panchanga horizon')
    expect(response!.reading.falsifier).toBeNull()
  })

  it('propagates an honest error on AUTHZ_DENIED (no structuredContent on that branch)', async () => {
    mockHandleMuhurtaFinder.mockResolvedValue({
      content: [{ type: 'text', text: 'AUTHZ_DENIED: not authorized to access this chart' }],
      isError: true,
    })

    const { handleKalaElectGet } = await import('./elect.js')
    const { response, error } = await handleKalaElectGet({ chart_id: CHART_ID, undertaking: 'business' }, PRINCIPAL)

    expect(response).toBeUndefined()
    expect(error?.message).toContain('AUTHZ_DENIED')
  })
})
