/**
 * kala_temporal_retrieval.test.ts — BRAHMA-KA-3-COMPOSITE: kala.temporal_bundle tests
 *
 * Tests the composite L3 Kāla retrieval tool without a live sidecar or DB.
 * Sidecar fetch is expected to fail (no sidecar in test env) → falls back to
 * FORENSIC-grounded pre-computed data embedded in the module.
 *
 * Contract gates:
 *   ✓ computeKalaTemporalBundle returns all 4 sub-assets
 *   ✓ timeline_excerpt non-empty (fallback FORENSIC data)
 *   ✓ convergence_windows non-empty
 *   ✓ obstructions non-empty
 *   ✓ snapshot includes kala_readiness.score in [0,100]
 *   ✓ source_citation = "PyJHora/SwissEph DE441 + Brahma-L1"
 *   ✓ registerKalaTemporalRetrievalTool registers 'kala_temporal_bundle' tool
 *   ✓ provenance_envelope.sidecar_available = false (no sidecar in test)
 *
 * BRAHMA-KA-3-COMPOSITE / l3-kala
 */

import { describe, it, expect, vi } from 'vitest'

// ── Mock fetch to simulate no-sidecar environment ────────────────────────────

vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('fetch unavailable in test'))))

// ── Import after mock ─────────────────────────────────────────────────────────

import {
  computeKalaTemporalBundle,
  registerKalaTemporalRetrievalTool,
  type KalaTemporalBundle,
} from '../tools/retrieval/kala_temporal.js'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'

// ── Constants ─────────────────────────────────────────────────────────────────

const SOURCE_CITATION = 'PyJHora/SwissEph DE441 + Brahma-L1'
const NATIVE_CHART_ID = '362f9f17-95a5-490b-a5a7-027d3e0efda0'
const DATE_RANGE = { start: '1984-01-01', end: '2040-12-31' }

// ── Helper ────────────────────────────────────────────────────────────────────

async function getBundle(includeSnapshot = true): Promise<KalaTemporalBundle> {
  return computeKalaTemporalBundle(NATIVE_CHART_ID, DATE_RANGE, includeSnapshot)
}

// ── Tests: source_citation ────────────────────────────────────────────────────

describe('kala_temporal_bundle — source_citation', () => {
  it('provenance_envelope.source_citation is exact', async () => {
    const result = await getBundle()
    expect(result.provenance_envelope.source_citation).toBe(SOURCE_CITATION)
  })
})

// ── Tests: timeline_excerpt ───────────────────────────────────────────────────

describe('kala_temporal_bundle — timeline_excerpt', () => {
  it('timeline_excerpt is non-empty (fallback FORENSIC data)', async () => {
    const result = await getBundle()
    expect(result.timeline_excerpt.length).toBeGreaterThan(0)
  })

  it('timeline entries have md_lord and ad_lord', async () => {
    const result = await getBundle()
    for (const row of result.timeline_excerpt) {
      expect(typeof row.md_lord).toBe('string')
      expect(typeof row.ad_lord).toBe('string')
      expect(row.md_lord.length).toBeGreaterThan(0)
    }
  })

  it('alignment_score values are in [0.0, 1.0]', async () => {
    const result = await getBundle()
    for (const row of result.timeline_excerpt) {
      expect(row.alignment_score).toBeGreaterThanOrEqual(0.0)
      expect(row.alignment_score).toBeLessThanOrEqual(1.0)
    }
  })

  it('Mercury MD entries present in timeline', async () => {
    const result = await getBundle()
    const mercuryRows = result.timeline_excerpt.filter((r) => r.md_lord === 'Mercury')
    expect(mercuryRows.length).toBeGreaterThan(0)
  })
})

// ── Tests: convergence_windows ────────────────────────────────────────────────

describe('kala_temporal_bundle — convergence_windows', () => {
  it('convergence_windows is non-empty', async () => {
    const result = await getBundle()
    expect(result.convergence_windows.length).toBeGreaterThan(0)
  })

  it('convergence_score in [0.0, 1.0]', async () => {
    const result = await getBundle()
    for (const w of result.convergence_windows) {
      expect(w.convergence_score).toBeGreaterThanOrEqual(0.0)
      expect(w.convergence_score).toBeLessThanOrEqual(1.0)
    }
  })

  it('convergence windows have source_citation', async () => {
    const result = await getBundle()
    for (const w of result.convergence_windows) {
      expect(typeof w.source_citation).toBe('string')
      expect(w.source_citation.length).toBeGreaterThan(0)
    }
  })
})

// ── Tests: obstructions ───────────────────────────────────────────────────────

describe('kala_temporal_bundle — obstructions', () => {
  it('obstructions is non-empty', async () => {
    const result = await getBundle()
    expect(result.obstructions.length).toBeGreaterThan(0)
  })

  it('Sade Sati Cycle 2 Peak present in obstructions', async () => {
    const result = await getBundle()
    const sadeSati = result.obstructions.filter((o) => o.obstruction_type === 'sade_sati')
    expect(sadeSati.length).toBeGreaterThan(0)
  })

  it('severity values in [0.0, 1.0]', async () => {
    const result = await getBundle()
    for (const obs of result.obstructions) {
      expect(obs.severity).toBeGreaterThanOrEqual(0.0)
      expect(obs.severity).toBeLessThanOrEqual(1.0)
    }
  })

  it('obstructions have source_citation', async () => {
    const result = await getBundle()
    for (const obs of result.obstructions) {
      expect(typeof obs.source_citation).toBe('string')
      expect(obs.source_citation.length).toBeGreaterThan(0)
    }
  })
})

// ── Tests: snapshot ───────────────────────────────────────────────────────────

describe('kala_temporal_bundle — snapshot', () => {
  it('snapshot is non-null when include_snapshot=true', async () => {
    const result = await getBundle(true)
    expect(result.snapshot).not.toBeNull()
  })

  it('snapshot.active_dasha.md_lord is Mercury (2026-06-05)', async () => {
    const result = await getBundle(true)
    expect(result.snapshot?.active_dasha?.md_lord).toBe('Mercury')
  })

  it('snapshot.kala_readiness.score in [0, 100]', async () => {
    const result = await getBundle(true)
    const score = result.snapshot?.kala_readiness?.score ?? -1
    expect(score).toBeGreaterThanOrEqual(0)
    expect(score).toBeLessThanOrEqual(100)
  })

  it('snapshot is null when include_snapshot=false', async () => {
    const result = await getBundle(false)
    expect(result.snapshot).toBeNull()
  })

  it('snapshot has kala_summary string', async () => {
    const result = await getBundle(true)
    expect(typeof result.snapshot?.kala_summary).toBe('string')
    expect((result.snapshot?.kala_summary ?? '').length).toBeGreaterThan(50)
  })
})

// ── Tests: provenance_envelope ────────────────────────────────────────────────

describe('kala_temporal_bundle — provenance_envelope', () => {
  it('provenance_envelope present and has required fields', async () => {
    const result = await getBundle()
    const pe = result.provenance_envelope
    expect(pe.source).toBe('kala.temporal_bundle')
    expect(Array.isArray(pe.assets)).toBe(true)
    expect(pe.assets.length).toBe(4)
    expect(typeof pe.computed_at).toBe('string')
    expect(typeof pe.timeline_count).toBe('number')
    expect(typeof pe.convergence_count).toBe('number')
    expect(typeof pe.obstruction_count).toBe('number')
  })

  it('sidecar_available is false (no sidecar in test)', async () => {
    const result = await getBundle()
    expect(result.provenance_envelope.sidecar_available).toBe(false)
  })

  it('snapshot_included reflects include_snapshot param', async () => {
    const withSnap = await getBundle(true)
    const withoutSnap = await getBundle(false)
    expect(withSnap.provenance_envelope.snapshot_included).toBe(true)
    expect(withoutSnap.provenance_envelope.snapshot_included).toBe(false)
  })
})

// ── Tests: tool registration ──────────────────────────────────────────────────

describe('kala_temporal_bundle — tool registration', () => {
  it('registerKalaTemporalRetrievalTool registers kala_temporal_bundle tool', () => {
    let registeredName: string | null = null
    const mockServer = {
      tool: (name: string, _desc: string, _schema: unknown, _handler: unknown) => {
        registeredName = name
      },
    } as unknown as McpServer

    registerKalaTemporalRetrievalTool(mockServer)
    expect(registeredName).toBe('kala_temporal_bundle')
  })

  it('registerKalaTemporalRetrievalTool called with 4 args', () => {
    let callArgs: unknown[] = []
    const mockServer = {
      tool: (...args: unknown[]) => { callArgs = args },
    } as unknown as McpServer

    registerKalaTemporalRetrievalTool(mockServer)
    expect(callArgs).toHaveLength(4)
    expect(typeof callArgs[0]).toBe('string')   // name
    expect(typeof callArgs[1]).toBe('string')   // description
    expect(typeof callArgs[2]).toBe('object')   // schema
    expect(typeof callArgs[3]).toBe('function') // handler
  })
})
