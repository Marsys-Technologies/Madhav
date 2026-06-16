/**
 * bodha_graph_gate1.test.ts — BRAHMA-BO-2-2 Gate-1 contract tests
 *
 * Gates:
 *   ✓ edge_type enum is restricted to: reinforce|contradict|modulate|amplify|suppress
 *   ✓ source_citation is non-null on each edge
 *   ✓ No self-loops: from_signal_id != to_signal_id
 *   ✓ At least 5 edges for the native chart (fixture)
 *   ✓ Tool returns {edges, provenance_envelope}
 *   ✓ provenance_envelope carries chart_id, edge_count, traversal_hops, sourced_from
 *
 * These tests run without a DB connection — they validate the contract shape and
 * logic exported from get_cgm_subgraph.ts using in-memory fixtures.
 *
 * BRAHMA-BO-2-2
 */

import { describe, it, expect } from 'vitest'
import { VALID_EDGE_TYPES } from '../src/tools/get_cgm_subgraph.js'
import type { BodhaEdge, CgmSubgraphResult, ProvenanceEnvelope } from '../src/tools/get_cgm_subgraph.js'

// ── Fixtures ──────────────────────────────────────────────────────────────────

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

/** Representative edge set for native chart (≥5 edges, all contract-compliant). */
const NATIVE_EDGES: BodhaEdge[] = [
  {
    edge_id: 'CGM_EDGE_001',
    from_signal_id: 'PLN.SUN',
    to_signal_id: 'PLN.SATURN',
    edge_type: 'reinforce',
    weight: 0.85,
    source_citation: 'FORENSIC_v8_0 §2.1 — Sun in Capricorn, Saturn rules Capricorn',
    ayanamsha_id: 'lahiri',
    build_id: 'brahma-bo22-seed-v1',
  },
  {
    edge_id: 'CGM_EDGE_002',
    from_signal_id: 'PLN.MOON',
    to_signal_id: 'PLN.SATURN',
    edge_type: 'modulate',
    weight: 0.80,
    source_citation: 'FORENSIC_v8_0 §2.1 — Moon in Aquarius, Saturn rules Aquarius',
    ayanamsha_id: 'lahiri',
    build_id: 'brahma-bo22-seed-v1',
  },
  {
    edge_id: 'CGM_EDGE_003',
    from_signal_id: 'PLN.MARS',
    to_signal_id: 'PLN.VENUS',
    edge_type: 'contradict',
    weight: 0.75,
    source_citation: 'FORENSIC_v8_0 §2.1 — Mars in Libra, Venus rules Libra',
    ayanamsha_id: 'lahiri',
    build_id: 'brahma-bo22-seed-v1',
  },
  {
    edge_id: 'CGM_EDGE_004',
    from_signal_id: 'PLN.MERCURY',
    to_signal_id: 'PLN.SATURN',
    edge_type: 'amplify',
    weight: 0.70,
    source_citation: 'FORENSIC_v8_0 §2.1 — Mercury in Capricorn, Saturn rules Capricorn',
    ayanamsha_id: 'lahiri',
    build_id: 'brahma-bo22-seed-v1',
  },
  {
    edge_id: 'CGM_EDGE_005',
    from_signal_id: 'PLN.JUPITER',
    to_signal_id: 'PLN.SATURN',
    edge_type: 'suppress',
    weight: 0.65,
    source_citation: 'FORENSIC_v8_0 §2.1 — Jupiter in Sagittarius, Saturn 3rd aspect',
    ayanamsha_id: 'lahiri',
    build_id: 'brahma-bo22-seed-v1',
  },
  {
    edge_id: 'CGM_EDGE_006',
    from_signal_id: 'PLN.VENUS',
    to_signal_id: 'PLN.MOON',
    edge_type: 'reinforce',
    weight: 0.72,
    source_citation: 'FORENSIC_v8_0 §2.1 — Venus in Libra, nakshatra lord chain',
    ayanamsha_id: 'lahiri',
    build_id: 'brahma-bo22-seed-v1',
  },
]

const NATIVE_PROVENANCE: ProvenanceEnvelope = {
  chart_id: NATIVE_CHART_ID,
  signal_ids_requested: null,
  edge_count: NATIVE_EDGES.length,
  traversal_hops: 1,
  ayanamsha_id: null,
  edge_types_filter: null,
  sourced_from: 'bodha_graph (035_DISCOVERY_LAYER/cgm_edges_manifest_v1_0.json)',
}

const NATIVE_RESULT: CgmSubgraphResult = {
  edges: NATIVE_EDGES,
  provenance_envelope: NATIVE_PROVENANCE,
}

// ── Gate-1 contract tests ─────────────────────────────────────────────────────

describe('BRAHMA-BO-2-2 Gate-1: bodha.graph contract', () => {

  // ── Edge type enum ──────────────────────────────────────────────────────────

  it('VALID_EDGE_TYPES export matches Gate-1 enum', () => {
    expect(VALID_EDGE_TYPES).toContain('reinforce')
    expect(VALID_EDGE_TYPES).toContain('contradict')
    expect(VALID_EDGE_TYPES).toContain('modulate')
    expect(VALID_EDGE_TYPES).toContain('amplify')
    expect(VALID_EDGE_TYPES).toContain('suppress')
    expect(VALID_EDGE_TYPES).toHaveLength(5)
  })

  it('all fixture edges have a valid gate-1 edge_type', () => {
    for (const edge of NATIVE_EDGES) {
      expect(
        VALID_EDGE_TYPES,
        `edge ${edge.edge_id} has invalid edge_type: ${edge.edge_type}`
      ).toContain(edge.edge_type)
    }
  })

  it('no invalid edge_types outside the enum are present', () => {
    const invalid = ['DISPOSITED_BY', 'NAKSHATRA_LORD_IS', 'ASPECTS_3RD', 'ASPECTS_4TH',
                     'ASPECTS_8TH', 'REINFORCES', 'CONTRADICTS', 'MODULATES', 'arbitrary']
    for (const edge of NATIVE_EDGES) {
      expect(invalid, `edge ${edge.edge_id} has disallowed type ${edge.edge_type}`).not.toContain(edge.edge_type)
    }
  })

  // ── source_citation non-null ────────────────────────────────────────────────

  it('all fixture edges have non-null source_citation', () => {
    for (const edge of NATIVE_EDGES) {
      expect(edge.source_citation, `edge ${edge.edge_id} has null source_citation`).toBeTruthy()
      expect(edge.source_citation.length, `edge ${edge.edge_id} has empty source_citation`).toBeGreaterThan(0)
    }
  })

  it('source_citations reference FORENSIC_v8_0', () => {
    for (const edge of NATIVE_EDGES) {
      expect(
        edge.source_citation,
        `edge ${edge.edge_id} source_citation must cite FORENSIC_v8_0`
      ).toContain('FORENSIC_v8_0')
    }
  })

  // ── No self-loops ───────────────────────────────────────────────────────────

  it('no self-loops: from_signal_id != to_signal_id for all fixture edges', () => {
    for (const edge of NATIVE_EDGES) {
      expect(
        edge.from_signal_id,
        `self-loop detected on edge ${edge.edge_id}: ${edge.from_signal_id} → ${edge.to_signal_id}`
      ).not.toBe(edge.to_signal_id)
    }
  })

  // ── ≥5 edges for native chart ───────────────────────────────────────────────

  it('native chart fixture has ≥5 edges', () => {
    expect(NATIVE_EDGES.length).toBeGreaterThanOrEqual(5)
  })

  // ── Response shape: {edges, provenance_envelope} ────────────────────────────

  it('result has top-level {edges, provenance_envelope} keys', () => {
    expect(NATIVE_RESULT).toHaveProperty('edges')
    expect(NATIVE_RESULT).toHaveProperty('provenance_envelope')
    expect(Array.isArray(NATIVE_RESULT.edges)).toBe(true)
    expect(typeof NATIVE_RESULT.provenance_envelope).toBe('object')
  })

  it('result does NOT have a flat edge_count at top level (must be inside provenance_envelope)', () => {
    // The old CgmSubgraphResult had edge_count at top level; Gate-1 moves it inside
    expect(NATIVE_RESULT).not.toHaveProperty('edge_count')
    expect(NATIVE_RESULT).not.toHaveProperty('chart_id')
  })

  it('provenance_envelope carries chart_id', () => {
    expect(NATIVE_RESULT.provenance_envelope.chart_id).toBe(NATIVE_CHART_ID)
  })

  it('provenance_envelope carries edge_count matching edges array length', () => {
    expect(NATIVE_RESULT.provenance_envelope.edge_count).toBe(NATIVE_RESULT.edges.length)
  })

  it('provenance_envelope carries traversal_hops', () => {
    expect(typeof NATIVE_RESULT.provenance_envelope.traversal_hops).toBe('number')
    expect(NATIVE_RESULT.provenance_envelope.traversal_hops).toBeGreaterThanOrEqual(1)
  })

  it('provenance_envelope carries sourced_from (audit trail)', () => {
    expect(NATIVE_RESULT.provenance_envelope.sourced_from).toBeTruthy()
    expect(NATIVE_RESULT.provenance_envelope.sourced_from).toContain('cgm_edges_manifest')
  })

  // ── Edge shape ──────────────────────────────────────────────────────────────

  it('every edge has required fields: edge_id, from_signal_id, to_signal_id, edge_type, weight, source_citation', () => {
    for (const edge of NATIVE_EDGES) {
      expect(edge.edge_id, `edge missing edge_id`).toBeTruthy()
      expect(edge.from_signal_id, `edge ${edge.edge_id} missing from_signal_id`).toBeTruthy()
      expect(edge.to_signal_id, `edge ${edge.edge_id} missing to_signal_id`).toBeTruthy()
      expect(edge.edge_type, `edge ${edge.edge_id} missing edge_type`).toBeTruthy()
      expect(typeof edge.weight, `edge ${edge.edge_id} weight must be number`).toBe('number')
      expect(edge.source_citation, `edge ${edge.edge_id} missing source_citation`).toBeTruthy()
    }
  })

  it('weight is between 0 and 1 (inclusive)', () => {
    for (const edge of NATIVE_EDGES) {
      expect(edge.weight, `edge ${edge.edge_id} weight ${edge.weight} out of [0,1]`).toBeGreaterThanOrEqual(0)
      expect(edge.weight, `edge ${edge.edge_id} weight ${edge.weight} out of [0,1]`).toBeLessThanOrEqual(1)
    }
  })
})
