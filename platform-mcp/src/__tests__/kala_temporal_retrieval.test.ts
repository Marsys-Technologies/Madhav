/**
 * kala_temporal_retrieval.test.ts — BRAHMA-KA-3-COMPOSITE: kala.temporal_bundle tests
 *
 * CR-40/T-1 (D-1.6 Lane S-6, 2026-07-16) rewrite: the tool no longer calls a Python-sidecar
 * HTTP surface (those `/kala/*` routes were never mounted on the sidecar — confirmed by
 * inspecting `platform/python-sidecar/main.py`'s router list). It now proxies through
 * /api/retrieval/capability (callRegistryCapability), the same DB-primary path every other
 * BA-P1 tool uses. These tests mock `fetch` to simulate that proxy: (a) an "unreachable
 * registry" case (fetch always fails → every array empty, `sidecar_available: false`,
 * snapshot fields honestly null/unreachable — never a fabricated score); (b) a "live registry"
 * case (fetch returns real-shaped rows per capability URI → bundle reflects them,
 * `sidecar_available: true`).
 *
 * Contract gates:
 *   ✓ computeKalaTemporalBundle returns all 4 sub-assets
 *   ✓ unreachable registry → every array empty, snapshot present with honest nulls
 *   ✓ live registry → rows flow through, sidecar_available=true, snapshot composed from
 *     the MD/AD/PD dossier rows + kala_darshana confluence row
 *   ✓ registerKalaTemporalRetrievalTool(server, principal) registers 'kala_temporal_bundle'
 *   ✓ provenance_envelope.obstructions_not_date_filtered = true (kala_obstruction has no
 *     per-row date range — must never be silently mis-filtered)
 *
 * BRAHMA-KA-3-COMPOSITE / l3-kala
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

import {
  computeKalaTemporalBundle,
  registerKalaTemporalRetrievalTool,
  type KalaTemporalBundle,
} from '../tools/retrieval/kala_temporal.js'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Constants ─────────────────────────────────────────────────────────────────

const SOURCE_CITATION =
  'kala_avadhi / kala_convergence / kala_obstruction / kala_darshana (L3 Kāla, orchestrator-built) via Brahma retrieval registry'
const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'
const DATE_RANGE = { start: '2026-01-01', end: '2026-12-31' }
const TODAY = new Date().toISOString().slice(0, 10)
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }

const TIMELINE_ROW = {
  avadhi_id: 'a1', system_id: 'vimshottari', level_n: 2, lord_graha: 'Mercury',
  period_start: '2026-02-01', period_end: '2027-02-01', dossier: {}, quality: {},
}
const CONVERGENCE_ROW = {
  convergence_id: 1, window_start: '2026-06-01', window_end: '2026-08-01',
  peak_date: '2026-07-01', convergence_score: 72.5, confidence_score: 0.8,
  confidence_label: 'high', domain: 'career', constituent_factors: [], source_citation: 'x',
}
const OBSTRUCTION_ROW = {
  id: 1, convergence_id: 1, obstruction_type: 'sade_sati', severity: 'moderate',
  severity_score: 40, override_score: null, obstruction_detail: {}, source_citation: 'x',
}
const DARSHANA_ROW = {
  effective_score: 55.2, net_label: 'favorable', window_start: TODAY, window_end: TODAY,
  obstruction_summary: { note: 'minor' }, narrative: { text: 'ok' },
}

/**
 * Builds a fetch mock for /api/retrieval/capability that dispatches on the requested URI.
 *
 * CR-93/94-shaped mock (fixed alongside the fetchCapabilityRows double-unwrap bug this file
 * exists to catch): the real /api/retrieval/capability route responds
 * `{ ok: true, content: await capability.handler(args) }`, and every CapabilityDescriptor
 * handler (registry/types.ts contract) itself returns `{ content: <realPayload>, is_error }`.
 * So the true wire shape is DOUBLE-wrapped: `{ ok: true, content: { content: { rows }, is_error:
 * false } }` — not the single-wrapped `{ ok: true, content: { rows } }` this mock previously
 * simulated. The single-wrapped mock let the double-unwrap bug in kala_temporal.ts ship
 * undetected: the buggy `fetchCapabilityRows` read `content.rows` directly, which happened to
 * exist on this too-shallow mock, so every test here passed against inverted/fabricated
 * confirmation. Matching the real shape is what makes this suite an effective regression guard.
 */
function mockRegistryFetch(opts: { reachable: boolean }) {
  return vi.fn(async (_url: string, init?: RequestInit) => {
    if (!opts.reachable) {
      throw new Error('registry unreachable in test')
    }
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri: string; args: Record<string, unknown> }
    let rows: unknown[] = []
    if (body.uri === 'marsys://tool/L3/query_dasha_dossier') {
      const levelN = body.args['level_n']
      rows = levelN === undefined || levelN === 2 ? [TIMELINE_ROW] : levelN === 1
        ? [{ ...TIMELINE_ROW, level_n: 1, lord_graha: 'Venus' }]
        : levelN === 3
          ? [{ ...TIMELINE_ROW, level_n: 3, lord_graha: 'Saturn' }]
          : []
    } else if (body.uri === 'marsys://tool/L3/query_convergence_windows') {
      rows = [CONVERGENCE_ROW]
    } else if (body.uri === 'marsys://tool/L3/query_obstruction_periods') {
      rows = [OBSTRUCTION_ROW]
    } else if (body.uri === 'marsys://tool/L3/query_temporal_view') {
      rows = [DARSHANA_ROW]
    }
    return {
      ok: true,
      // Double-wrapped — matches the real /api/retrieval/capability + CapabilityDescriptor
      // handler contract (see doc-comment above).
      json: async () => ({ ok: true, content: { content: { rows }, is_error: false } }),
      text: async () => '',
    } as Response
  })
}

async function getBundle(reachable: boolean, includeSnapshot = true): Promise<KalaTemporalBundle> {
  vi.stubGlobal('fetch', mockRegistryFetch({ reachable }))
  return computeKalaTemporalBundle(TEST_CHART_ID, DATE_RANGE, includeSnapshot, TEST_PRINCIPAL)
}

beforeEach(() => {
  vi.unstubAllGlobals()
})

// ── Tests: source_citation ────────────────────────────────────────────────────

describe('kala_temporal_bundle — source_citation', () => {
  it('provenance_envelope.source_citation is exact', async () => {
    const result = await getBundle(false)
    expect(result.provenance_envelope.source_citation).toBe(SOURCE_CITATION)
  })
})

// ── Tests: unreachable registry (honest empty, never fabricated) ─────────────

describe('kala_temporal_bundle — registry unreachable', () => {
  it('every array is empty and sidecar_available is false', async () => {
    const result = await getBundle(false)
    expect(result.timeline_excerpt).toEqual([])
    expect(result.convergence_windows).toEqual([])
    expect(result.obstructions).toEqual([])
    expect(result.provenance_envelope.sidecar_available).toBe(false)
  })

  it('snapshot is present but every derived field is honestly null/unreachable — never fabricated', async () => {
    const result = await getBundle(false, true)
    expect(result.snapshot).not.toBeNull()
    expect(result.snapshot?.active_dasha).toBeNull()
    expect(result.snapshot?.kala_readiness.score).toBeNull()
    expect(result.snapshot?.provenance_envelope['mode']).toBe('unreachable')
  })

  it('snapshot is null when include_snapshot=false', async () => {
    const result = await getBundle(false, false)
    expect(result.snapshot).toBeNull()
  })
})

// ── Tests: live registry (CR-40/T-1 fix — real rows flow through) ────────────

describe('kala_temporal_bundle — live registry', () => {
  it('timeline_excerpt carries real kala_avadhi rows', async () => {
    const result = await getBundle(true)
    expect(result.timeline_excerpt.length).toBeGreaterThan(0)
    expect(result.timeline_excerpt[0].lord_graha).toBe('Mercury')
  })

  it('convergence_windows carries real kala_convergence rows', async () => {
    const result = await getBundle(true)
    expect(result.convergence_windows.length).toBeGreaterThan(0)
    expect(result.convergence_windows[0].convergence_score).toBe(72.5)
  })

  it('obstructions carries real kala_obstruction rows', async () => {
    const result = await getBundle(true)
    expect(result.obstructions.length).toBeGreaterThan(0)
    expect(result.obstructions[0].obstruction_type).toBe('sade_sati')
  })

  it('sidecar_available is true when every sub-asset call succeeds', async () => {
    const result = await getBundle(true)
    expect(result.provenance_envelope.sidecar_available).toBe(true)
  })

  it('snapshot composes active_dasha from MD (level 1) + AD (level 2) dossier rows', async () => {
    const result = await getBundle(true, true)
    expect(result.snapshot?.active_dasha).not.toBeNull()
    expect(result.snapshot?.active_dasha?.md_lord).toBe('Venus')
    expect(result.snapshot?.active_dasha?.ad_lord).toBe('Mercury')
  })

  it('snapshot.active_pratyantardasha composed from level-3 dossier row', async () => {
    const result = await getBundle(true, true)
    expect(result.snapshot?.active_pratyantardasha?.pd_lord).toBe('Saturn')
  })

  it('snapshot.kala_readiness reflects the active kala_darshana confluence row', async () => {
    const result = await getBundle(true, true)
    expect(result.snapshot?.kala_readiness.score).toBe(55.2)
    expect(result.snapshot?.kala_readiness.interpretation).toBe('favorable')
  })

  it('snapshot.chart_id matches the caller-supplied chart_id', async () => {
    const result = await getBundle(true, true)
    expect(result.snapshot?.chart_id).toBe(TEST_CHART_ID)
  })
})

// ── Tests: provenance_envelope ────────────────────────────────────────────────

describe('kala_temporal_bundle — provenance_envelope', () => {
  it('provenance_envelope present and has required fields', async () => {
    const result = await getBundle(true)
    const pe = result.provenance_envelope
    expect(pe.source).toBe('kala.temporal_bundle')
    expect(Array.isArray(pe.assets)).toBe(true)
    expect(pe.assets.length).toBe(4)
    expect(typeof pe.computed_at).toBe('string')
    expect(typeof pe.timeline_count).toBe('number')
    expect(typeof pe.convergence_count).toBe('number')
    expect(typeof pe.obstruction_count).toBe('number')
  })

  it('obstructions_not_date_filtered is always true (honest disclosure — kala_obstruction has no date range)', async () => {
    const result = await getBundle(true)
    expect(result.provenance_envelope.obstructions_not_date_filtered).toBe(true)
  })

  it('snapshot_included reflects include_snapshot param', async () => {
    const withSnap = await getBundle(true, true)
    const withoutSnap = await getBundle(true, false)
    expect(withSnap.provenance_envelope.snapshot_included).toBe(true)
    expect(withoutSnap.provenance_envelope.snapshot_included).toBe(false)
  })
})

// ── Tests: double-unwrap regression (the bug this file exists to catch) ──────

describe('kala_temporal_bundle — double-content-unwrap regression', () => {
  it('extracts rows from the real double-wrapped envelope shape ({ ok, content: { content: { rows }, is_error } })', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true,
      json: async () => ({
        ok: true,
        content: { content: { rows: [TIMELINE_ROW] }, is_error: false },
      }),
      text: async () => '',
    } as Response)))

    const result = await computeKalaTemporalBundle(TEST_CHART_ID, DATE_RANGE, false, TEST_PRINCIPAL)
    expect(result.timeline_excerpt).toHaveLength(1)
    expect(result.timeline_excerpt[0].lord_graha).toBe('Mercury')
    expect(result.provenance_envelope.timeline_count).toBe(1)
  })

  it('does not mistake a single-wrapped payload lacking `is_error` for the double-wrapped contract', async () => {
    // A capability payload that legitimately has `rows` at the top level (no `is_error` key)
    // must NOT be misread as needing a further unwrap — the fix is shape-defensive, not a
    // blind "always go one level deeper".
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true,
      json: async () => ({ ok: true, content: { rows: [TIMELINE_ROW] } }),
      text: async () => '',
    } as Response)))

    const result = await computeKalaTemporalBundle(TEST_CHART_ID, DATE_RANGE, false, TEST_PRINCIPAL)
    expect(result.timeline_excerpt).toHaveLength(1)
  })
})

// ── Tests: tool registration ──────────────────────────────────────────────────

describe('kala_temporal_bundle — tool registration', () => {
  it('registerKalaTemporalRetrievalTool(server, principal) registers kala_temporal_bundle tool', () => {
    let registeredName: string | null = null
    const mockServer = {
      tool: (name: string, _desc: string, _schema: unknown, _handler: unknown) => {
        registeredName = name
      },
    } as unknown as McpServer

    registerKalaTemporalRetrievalTool(mockServer, TEST_PRINCIPAL)
    expect(registeredName).toBe('kala_temporal_bundle')
  })

  it('registerKalaTemporalRetrievalTool called with 4 args', () => {
    let callArgs: unknown[] = []
    const mockServer = {
      tool: (...args: unknown[]) => { callArgs = args },
    } as unknown as McpServer

    registerKalaTemporalRetrievalTool(mockServer, TEST_PRINCIPAL)
    expect(callArgs).toHaveLength(4)
    expect(typeof callArgs[0]).toBe('string')   // name
    expect(typeof callArgs[1]).toBe('string')   // description
    expect(typeof callArgs[2]).toBe('object')   // schema
    expect(typeof callArgs[3]).toBe('function') // handler
  })
})
