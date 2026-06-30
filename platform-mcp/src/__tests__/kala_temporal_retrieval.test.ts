/**
 * kala_temporal_retrieval.test.ts — BRAHMA-KA-3-COMPOSITE: kala.temporal_bundle tests
 *
 * Tests the composite L3 Kāla retrieval tool without a live sidecar or DB.
 * Sidecar fetch is expected to fail (no sidecar in test env) → graceful-empty fallback
 * (D7 remediation: native-specific FORENSIC data arrays removed; empty is correct).
 *
 * Contract gates:
 *   ✓ computeKalaTemporalBundle returns all 4 sub-assets
 *   ✓ timeline_excerpt is an array (empty when sidecar unavailable — D7)
 *   ✓ convergence_windows is an array (empty when sidecar unavailable — D7)
 *   ✓ obstructions is an array (empty when sidecar unavailable — D7)
 *   ✓ snapshot is non-null with graceful-empty fields (active_dasha=null, score=null)
 *   ✓ source_citation = "PyJHora/SwissEph DE441 + Brahma-L1"
 *   ✓ registerKalaTemporalRetrievalTool registers 'kala_temporal_bundle' tool
 *   ✓ provenance_envelope.sidecar_available = false (no sidecar in test)
 *
 * D7 remediation note: The fallback was formerly populated with native-specific
 * FORENSIC data (chart 482012f1-...). That data has been removed — graceful-empty
 * arrays and null scores are the correct no-sidecar behavior for any chart.
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
// D7: Use a generic test UUID — not the native chart_id. The tool is chart-agnostic.
const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'
const DATE_RANGE = { start: '1984-01-01', end: '2040-12-31' }

// ── Helper ────────────────────────────────────────────────────────────────────

async function getBundle(includeSnapshot = true): Promise<KalaTemporalBundle> {
  return computeKalaTemporalBundle(TEST_CHART_ID, DATE_RANGE, includeSnapshot)
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
  // D7: fallback is graceful-empty — sidecar required for real data.
  it('timeline_excerpt is an array (empty when sidecar unavailable)', async () => {
    const result = await getBundle()
    expect(Array.isArray(result.timeline_excerpt)).toBe(true)
    // Empty is correct: native-specific FORENSIC data removed by D7 remediation.
    // Real data requires the Python sidecar.
    expect(result.timeline_excerpt.length).toBe(0)
  })

  it('timeline entries (if any) have md_lord and ad_lord', async () => {
    const result = await getBundle()
    for (const row of result.timeline_excerpt) {
      expect(typeof row.md_lord).toBe('string')
      expect(typeof row.ad_lord).toBe('string')
      expect(row.md_lord.length).toBeGreaterThan(0)
    }
  })

  it('alignment_score values (if any rows) are in [0.0, 1.0]', async () => {
    const result = await getBundle()
    for (const row of result.timeline_excerpt) {
      expect(row.alignment_score).toBeGreaterThanOrEqual(0.0)
      expect(row.alignment_score).toBeLessThanOrEqual(1.0)
    }
  })
})

// ── Tests: convergence_windows ────────────────────────────────────────────────

describe('kala_temporal_bundle — convergence_windows', () => {
  // D7: fallback is graceful-empty — sidecar required for real data.
  it('convergence_windows is an array (empty when sidecar unavailable)', async () => {
    const result = await getBundle()
    expect(Array.isArray(result.convergence_windows)).toBe(true)
    expect(result.convergence_windows.length).toBe(0)
  })

  it('convergence_score (if any windows) in [0.0, 1.0]', async () => {
    const result = await getBundle()
    for (const w of result.convergence_windows) {
      expect(w.convergence_score).toBeGreaterThanOrEqual(0.0)
      expect(w.convergence_score).toBeLessThanOrEqual(1.0)
    }
  })

  it('convergence windows (if any) have source_citation', async () => {
    const result = await getBundle()
    for (const w of result.convergence_windows) {
      expect(typeof w.source_citation).toBe('string')
      expect(w.source_citation.length).toBeGreaterThan(0)
    }
  })
})

// ── Tests: obstructions ───────────────────────────────────────────────────────

describe('kala_temporal_bundle — obstructions', () => {
  // D7: fallback is graceful-empty — sidecar required for real data.
  it('obstructions is an array (empty when sidecar unavailable)', async () => {
    const result = await getBundle()
    expect(Array.isArray(result.obstructions)).toBe(true)
    expect(result.obstructions.length).toBe(0)
  })

  it('severity values (if any obstructions) in [0.0, 1.0]', async () => {
    const result = await getBundle()
    for (const obs of result.obstructions) {
      expect(obs.severity).toBeGreaterThanOrEqual(0.0)
      expect(obs.severity).toBeLessThanOrEqual(1.0)
    }
  })

  it('obstructions (if any) have source_citation', async () => {
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

  // D7: active_dasha is null in graceful-empty fallback (sidecar unavailable).
  // Native-specific assertion (md_lord=Mercury) removed — chart-agnostic required.
  it('snapshot.active_dasha is null when sidecar unavailable (D7 graceful-empty)', async () => {
    const result = await getBundle(true)
    expect(result.snapshot?.active_dasha).toBeNull()
  })

  // D7: kala_readiness.score is null when sidecar unavailable — not a numeric score.
  it('snapshot.kala_readiness.score is null when sidecar unavailable', async () => {
    const result = await getBundle(true)
    expect(result.snapshot?.kala_readiness?.score).toBeNull()
  })

  it('snapshot is null when include_snapshot=false', async () => {
    const result = await getBundle(false)
    expect(result.snapshot).toBeNull()
  })

  it('snapshot has kala_summary string', async () => {
    const result = await getBundle(true)
    expect(typeof result.snapshot?.kala_summary).toBe('string')
    expect((result.snapshot?.kala_summary ?? '').length).toBeGreaterThan(0)
  })

  it('snapshot.chart_id matches the caller-supplied chart_id (not a placeholder)', async () => {
    const result = await getBundle(true)
    expect(result.snapshot?.chart_id).toBe(TEST_CHART_ID)
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
