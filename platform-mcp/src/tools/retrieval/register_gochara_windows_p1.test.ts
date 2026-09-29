/**
 * register_gochara_windows_p1.test.ts — WP7 packet P-1 acceptance tests.
 *
 * Covers the packet §5 tests at the mocked-fetch level (a live disposable-DB
 * integration pass is owned by the WP6 harness):
 *   Test 1 — manifest-driven provenance + republish stability: a '4.0' authority
 *            chart's citation names ka_gochara + manifest_id + convention_id;
 *            the same assertion holds after a simulated republish as '4.1'.
 *   Test 2 — coverage equals the manifest: kala_gochara_coverage rows drive the
 *            served coverage object; the substep axis is demoted to
 *            sweep_execution.
 *   Test 3 — unpublished honesty (P-1d): windows but NO authority row →
 *            coverage.status 'unpublished', empty_reason 'unpublished', and no
 *            generation=v1 provenance anywhere.
 *   Test 4 — legacy regression: explicit 'v1' / '3.0' / g3_* authority with no
 *            manifest rows → citation strings byte-identical to the pre-P-1
 *            output.
 */
import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from 'vitest'
import {
  computeGocharaActivation,
  computeGocharaCoverage,
} from './register_gochara_windows.js'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const PRINCIPAL = { user_uid: 'test', key_id: 'test', role: 'super_admin' as const }

function fakeJsonResponse(rows: unknown[]): Response {
  return {
    ok: true,
    json: () => Promise.resolve({ rows }),
    text: () => Promise.resolve(JSON.stringify({ rows })),
  } as unknown as Response
}

function manifestRow(generation: string) {
  return {
    manifest_id: `manifest-${generation}`,
    chart_id: CHART,
    generation,
    writer_asset_id: 'ka_gochara',
    convention_id: 'sha256:conv123',
    input_generation_vector: {},
    ephemeris_backend: {},
    horizon: '[2026-01-01,2027-01-01)',
    row_counts: { contacts: 1, coverage: 2, windows: 1 },
    content_digest: 'sha256:digest',
    status: 'published',
  }
}

function windowRow(generation: string) {
  return {
    id: 42,
    chart_id: CHART,
    event_class: 'marriage',
    temporal_shape: 'point',
    window_start: '2026-06-01',
    window_end: '2026-06-01',
    peak_date: '2026-06-01',
    milestone_id: null,
    is_irreversibility_milestone: false,
    signed_intensity: 0.5,
    raw_intensity: 0.5,
    valence: 'favourable',
    is_adverse: false,
    active_sentences: [],
    contributing_systems: [],
    suppression_state: null,
    peak_basis: 'gochara_lambda_v3_argmax',
    calibration_state: 'structural_prior',
    source: 'test',
    computed_at: '2026-01-01T00:00:00Z',
    continuity_state: null,
    generation,
    era_slice_key: null,
    term_breakdown: null,
    resolution: 'day',
    parent_window_id: null,
    shape_conformance: null,
  }
}

function coverageRows() {
  return [
    {
      partition_kind: 'event_class',
      partition_key: 'marriage',
      requested_horizon: '[2026-01-01,2027-01-01)',
      completed_horizon: '[2026-01-01,2027-01-01)',
      resolution: 'day',
      relations_searched: ['conjunction'],
      targets_requested: 3,
      targets_resolved: 3,
      targets_unresolved: 0,
      target_resolution_state_counts: {},
      unavailable_inputs: [],
      unsearched_reason: null,
    },
    {
      partition_kind: 'body_target',
      partition_key: 'Jupiter:natal_Sun',
      requested_horizon: '[2026-01-01,2027-01-01)',
      completed_horizon: '[2026-01-01,2027-01-01)',
      resolution: 'day',
      relations_searched: ['conjunction'],
      targets_requested: 1,
      targets_resolved: 1,
      targets_unresolved: 0,
      target_resolution_state_counts: {},
      unavailable_inputs: [],
      unsearched_reason: null,
    },
  ]
}

/** SQL-dispatching fetch mock for a manifest-generation ('4.x') chart. */
function mockManifestGenerationFetch(fetchSpy: Mock, generation: string) {
  fetchSpy.mockImplementation((_url: string, init: RequestInit) => {
    const { sql } = JSON.parse(init.body as string) as { sql: string }
    if (sql.includes('FROM kala_gochara_windows')) {
      return Promise.resolve(fakeJsonResponse([windowRow(generation)]))
    }
          if (sql.includes('FROM kala_gochara_windows')) {
        return Promise.resolve(fakeJsonResponse([windowRow('v1')]))
      }
if (sql.includes('FROM kala_gochara_authority')) {
      return Promise.resolve(fakeJsonResponse([{ authoritative_generation: generation }]))
    }
    if (sql.includes('FROM kala_gochara_publication')) {
      return Promise.resolve(fakeJsonResponse([manifestRow(generation)]))
    }
    if (sql.includes('FROM kala_gochara_coverage')) {
      return Promise.resolve(fakeJsonResponse(coverageRows()))
    }
    if (sql.includes('gochara_resonance_map')) {
      return Promise.resolve(fakeJsonResponse([{ event_class: 'marriage', domain: 'marriage' }]))
    }
    if (sql.includes('brahma_event_ontology')) {
      return Promise.resolve(fakeJsonResponse([{ domain: 'marriage' }]))
    }
    if (sql.includes('FROM build_substep_progress')) {
      return Promise.resolve(fakeJsonResponse([{ substeps_committed: 7, swept_event_classes: ['marriage'] }]))
    }
    return Promise.resolve(fakeJsonResponse([]))
  })
}

describe('WP7 P-1 — manifest-driven provenance & coverage', () => {
  let fetchSpy: Mock

  beforeEach(() => {
    fetchSpy = vi.fn()
    vi.spyOn(globalThis, 'fetch').mockImplementation(fetchSpy)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("Test 1 — '4.0' authority names ka_gochara + manifest_id + convention_id (never the v1 branch)", async () => {
    mockManifestGenerationFetch(fetchSpy, '4.0')
    const result = await computeGocharaActivation(CHART, '2026-06-01', PRINCIPAL) as {
      provenance_envelope: { source_citation: string }
    }
    const citation = result.provenance_envelope.source_citation
    expect(citation).toContain('ka_gochara writer')
    expect(citation).toContain('manifest_id=manifest-4.0')
    expect(citation).toContain('convention_id=sha256:conv123')
    expect(citation).toContain('generation=4.0')
    expect(citation).not.toContain('ka_gochara_sweep')
    expect(citation).not.toContain('generation=v1')
  })

  it("Test 1b — after a republish as '4.1' the same assertions hold (no hardcoded '4.0')", async () => {
    mockManifestGenerationFetch(fetchSpy, '4.1')
    const result = await computeGocharaActivation(CHART, '2026-06-01', PRINCIPAL) as {
      provenance_envelope: { source_citation: string }
    }
    const citation = result.provenance_envelope.source_citation
    expect(citation).toContain('ka_gochara writer')
    expect(citation).toContain('manifest_id=manifest-4.1')
    expect(citation).toContain('generation=4.1')
    expect(citation).not.toContain('generation=v1')
  })

  it('Test 2 — coverage object is derived from the kala_gochara_coverage rows; substep axis demoted to sweep_execution', async () => {
    mockManifestGenerationFetch(fetchSpy, '4.0')
    const { coverage } = await computeGocharaCoverage(CHART, PRINCIPAL)

    // The manifest block carries per-class horizon + resolution counts.
    expect(coverage.coverage_manifest).toBeTruthy()
    expect(coverage.coverage_manifest!.source).toContain('kala_gochara_coverage')
    const marriage = coverage.coverage_manifest!.event_classes['marriage']
    expect(marriage.requested_horizon).toBe('[2026-01-01,2027-01-01)')
    expect(marriage.completed_horizon).toBe('[2026-01-01,2027-01-01)')
    expect(marriage.targets_resolved).toBe(3)
    expect(marriage.targets_unresolved).toBe(0)
    // Both partitions are carried verbatim.
    expect(coverage.coverage_manifest!.partitions).toHaveLength(2)
    expect(coverage.coverage_manifest!.partitions.map((p) => p.partition_kind).sort())
      .toEqual(['body_target', 'event_class'])
    // Class set derives from the manifest.
    expect(coverage.event_classes_covered).toEqual(['marriage'])
    // Substep axis is present but labelled sweep_execution — not the coverage source.
    expect(coverage.sweep_execution).toBeTruthy()
    expect(coverage.sweep_execution!.substeps_committed).toBe(7)
    expect(coverage.sweep_execution!.source).toContain('ka_gochara')
  })

  it("Test 3 — windows but NO authority row → unpublished everywhere, no generation=v1 provenance (P-1d)", async () => {
    fetchSpy.mockImplementation((_url: string, init: RequestInit) => {
      const { sql } = JSON.parse(init.body as string) as { sql: string }
      if (sql.includes('FROM kala_gochara_authority')) return Promise.resolve(fakeJsonResponse([]))
      if (sql.includes('FROM kala_gochara_publication')) return Promise.resolve(fakeJsonResponse([]))
      if (sql.includes('gochara_resonance_map')) {
        return Promise.resolve(fakeJsonResponse([{ event_class: 'marriage', domain: 'marriage' }]))
      }
      if (sql.includes('brahma_event_ontology')) {
        return Promise.resolve(fakeJsonResponse([{ domain: 'marriage' }]))
      }
      // windows exist (legacy rows) — but with no authority row the filter
      // matches nothing, which is the correct unpublished behaviour.
      if (sql.includes('FROM kala_gochara_windows')) return Promise.resolve(fakeJsonResponse([]))
      return Promise.resolve(fakeJsonResponse([]))
    })

    const { coverage } = await computeGocharaCoverage(CHART, PRINCIPAL)
    expect(coverage.status).toBe('unpublished')
    expect(coverage.sweep_completeness.materialized_through).toBeNull()
    expect(coverage.event_classes_covered).toEqual([])
    expect(coverage.note).toContain('unpublished')

    const result = await computeGocharaActivation(CHART, '2026-06-01', PRINCIPAL) as {
      provenance_envelope: { source_citation: string; empty_reason: string | null }
    }
    expect(result.provenance_envelope.empty_reason).toBe('unpublished')
    expect(result.provenance_envelope.source_citation).toContain('unpublished')
    expect(JSON.stringify(result)).not.toContain('generation=v1')
    expect(JSON.stringify(result)).not.toContain('ka_gochara_sweep writer')
  })

  it("Test 4 — explicit 'v1' authority with no manifest → legacy citation byte-identical", async () => {
    fetchSpy.mockImplementation((_url: string, init: RequestInit) => {
      const { sql } = JSON.parse(init.body as string) as { sql: string }
      if (sql.includes('FROM kala_gochara_authority')) {
        return Promise.resolve(fakeJsonResponse([{ authoritative_generation: 'v1' }]))
      }
      if (sql.includes('FROM kala_gochara_publication')) return Promise.resolve(fakeJsonResponse([]))
      if (sql.includes('gochara_resonance_map')) {
        return Promise.resolve(fakeJsonResponse([{ event_class: 'marriage', domain: 'marriage' }]))
      }
      if (sql.includes('brahma_event_ontology')) {
        return Promise.resolve(fakeJsonResponse([{ domain: 'marriage' }]))
      }
      if (sql.includes('build_substep_progress')) {
        return Promise.resolve(fakeJsonResponse([{ substeps_committed: 3, swept_event_classes: ['marriage'] }]))
      }
      return Promise.resolve(fakeJsonResponse([]))
    })

    const result = await computeGocharaActivation(CHART, '2026-06-01', PRINCIPAL) as {
      provenance_envelope: { source_citation: string }
    }
    expect(result.provenance_envelope.source_citation).toBe(
      'kala_gochara_windows (L3 Kāla, D-5 Lane G-4 ka_gochara_sweep writer) — ' +
      'lambda_e via services/gochara_intensity (G-3), consuming gochara_resonance_map ' +
      '(G-1) + gochara_grammar (G-2); generation=v1'
    )
  })

  it("Test 4b — explicit '3.0' authority with no manifest → legacy v3 citation byte-identical", async () => {
    fetchSpy.mockImplementation((_url: string, init: RequestInit) => {
      const { sql } = JSON.parse(init.body as string) as { sql: string }
            if (sql.includes('FROM kala_gochara_windows')) {
        return Promise.resolve(fakeJsonResponse([windowRow('3.0')]))
      }
if (sql.includes('FROM kala_gochara_authority')) {
        return Promise.resolve(fakeJsonResponse([{ authoritative_generation: '3.0' }]))
      }
      if (sql.includes('FROM kala_gochara_publication')) return Promise.resolve(fakeJsonResponse([]))
      if (sql.includes('gochara_resonance_map')) {
        return Promise.resolve(fakeJsonResponse([{ event_class: 'marriage', domain: 'marriage' }]))
      }
      if (sql.includes('brahma_event_ontology')) {
        return Promise.resolve(fakeJsonResponse([{ domain: 'marriage' }]))
      }
      if (sql.includes('build_substep_progress')) {
        return Promise.resolve(fakeJsonResponse([{ substeps_committed: 3, swept_event_classes: ['marriage'] }]))
      }
      return Promise.resolve(fakeJsonResponse([]))
    })

    const result = await computeGocharaActivation(CHART, '2026-06-01', PRINCIPAL) as {
      provenance_envelope: { source_citation: string }
    }
    expect(result.provenance_envelope.source_citation).toBe(
      'kala_gochara_windows (L3 Kāla, W6.4 cutover ka_gochara materializer) — ' +
      'lambda_v3 via services/gochara_v3, consuming gochara_resonance_map (G-1); ' +
      'generation=3.0'
    )
  })
})
