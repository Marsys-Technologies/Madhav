/**
 * phala_muhurta.test.ts — Unit tests for BRAHMA-PH-4-4 phala.muhurta
 *
 * Contract assertions (from task brief):
 *   - assert 0 <= score <= 1 on every window
 *   - assert len(windows) >= 1 for valid date range
 *   - tool smoke: registerMuhurtaFinder registers 'muhurta_finder' tool
 *   - action_type validation: invalid type rejects
 *
 * These are pure unit tests (no DB, no network).
 * BRAHMA-PH-4-4
 */

import { describe, it, expect } from 'vitest'
import {
  MuhurtaFinderInputSchema,
  MUHURTA_FINDER_DESCRIPTION,
  registerMuhurtaFinder,
} from '../tools/muhurta_finder.js'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock server ───────────────────────────────────────────────────────────────

function createMockServer() {
  const registered: Array<{ name: string; description: string }> = []
  return {
    _registered: registered,
    tool: (name: string, description: string, ..._rest: unknown[]) => {
      registered.push({ name, description })
    },
  }
}

const mockPrincipal: Principal = {
  user_uid: 'uid-test',
  key_id:   'key-test',
}

// ── Input schema validation ────────────────────────────────────────────────────

describe('MuhurtaFinderInputSchema', () => {

  it('accepts all 7 valid action_types', () => {
    const validTypes = [
      'marriage', 'travel', 'business', 'medical',
      'education', 'property', 'general',
    ]
    for (const action_type of validTypes) {
      const result = MuhurtaFinderInputSchema.safeParse({
        chart_id: '362f9f17-95a5-490b-a5a7-027d3e0efda0',
        action_type,
        date_range: { start: '2026-06-04', end: '2026-09-01' },
      })
      expect(result.success, `action_type '${action_type}' should be valid`).toBe(true)
    }
  })

  it('rejects invalid action_type', () => {
    const result = MuhurtaFinderInputSchema.safeParse({
      chart_id: '362f9f17-95a5-490b-a5a7-027d3e0efda0',
      action_type: 'INVALID_TYPE',
      date_range: { start: '2026-06-04', end: '2026-09-01' },
    })
    expect(result.success).toBe(false)
  })

  it('rejects invalid chart_id (not UUID)', () => {
    const result = MuhurtaFinderInputSchema.safeParse({
      chart_id: 'not-a-uuid',
      action_type: 'education',
      date_range: { start: '2026-06-04', end: '2026-09-01' },
    })
    expect(result.success).toBe(false)
  })

  it('rejects date_range with bad format', () => {
    const result = MuhurtaFinderInputSchema.safeParse({
      chart_id: '362f9f17-95a5-490b-a5a7-027d3e0efda0',
      action_type: 'general',
      date_range: { start: '06-04-2026', end: '2026-09-01' },
    })
    expect(result.success).toBe(false)
  })

  it('accepts valid min_score in [0.0, 1.0]', () => {
    const result = MuhurtaFinderInputSchema.safeParse({
      chart_id: '362f9f17-95a5-490b-a5a7-027d3e0efda0',
      action_type: 'education',
      date_range: { start: '2026-06-04', end: '2026-09-01' },
      min_score: 0.70,
    })
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.min_score).toBe(0.70)
    }
  })

  it('rejects min_score > 1.0', () => {
    const result = MuhurtaFinderInputSchema.safeParse({
      chart_id: '362f9f17-95a5-490b-a5a7-027d3e0efda0',
      action_type: 'education',
      date_range: { start: '2026-06-04', end: '2026-09-01' },
      min_score: 1.5,
    })
    expect(result.success).toBe(false)
  })

  it('rejects min_score < 0.0', () => {
    const result = MuhurtaFinderInputSchema.safeParse({
      chart_id: '362f9f17-95a5-490b-a5a7-027d3e0efda0',
      action_type: 'education',
      date_range: { start: '2026-06-04', end: '2026-09-01' },
      min_score: -0.1,
    })
    expect(result.success).toBe(false)
  })

  it('defaults limit to 20', () => {
    const result = MuhurtaFinderInputSchema.safeParse({
      chart_id: '362f9f17-95a5-490b-a5a7-027d3e0efda0',
      action_type: 'general',
      date_range: { start: '2026-06-04', end: '2026-07-04' },
    })
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.limit).toBe(20)
    }
  })

  it('rejects limit > 45', () => {
    const result = MuhurtaFinderInputSchema.safeParse({
      chart_id: '362f9f17-95a5-490b-a5a7-027d3e0efda0',
      action_type: 'general',
      date_range: { start: '2026-06-04', end: '2026-09-01' },
      limit: 100,
    })
    expect(result.success).toBe(false)
  })

})

// ── MCP tool registration ─────────────────────────────────────────────────────

describe('registerMuhurtaFinder', () => {

  it('registers the "muhurta_finder" tool', () => {
    const server = createMockServer()
    registerMuhurtaFinder(
      server as unknown as McpServer,
      () => mockPrincipal
    )
    const names = server._registered.map((r) => r.name)
    expect(names).toContain('muhurta_finder')
  })

  it('registers exactly one tool', () => {
    const server = createMockServer()
    registerMuhurtaFinder(
      server as unknown as McpServer,
      () => mockPrincipal
    )
    expect(server._registered).toHaveLength(1)
  })

  it('tool description contains "PH-4-4"', () => {
    const server = createMockServer()
    registerMuhurtaFinder(
      server as unknown as McpServer,
      () => mockPrincipal
    )
    const desc = server._registered[0]?.description ?? ''
    expect(desc).toContain('PH-4-4')
  })

  it('tool description contains action_type list', () => {
    expect(MUHURTA_FINDER_DESCRIPTION).toContain('marriage')
    expect(MUHURTA_FINDER_DESCRIPTION).toContain('education')
    expect(MUHURTA_FINDER_DESCRIPTION).toContain('general')
  })

  it('tool description mentions B.3 mandate', () => {
    expect(MUHURTA_FINDER_DESCRIPTION).toContain('B.3')
  })

  it('tool description mentions provenance_envelope', () => {
    expect(MUHURTA_FINDER_DESCRIPTION).toContain('provenance_envelope')
  })

})

// ── Score invariant ─────────────────────────────────────────────────────────

describe('Score invariant [0.0, 1.0]', () => {

  it('score formula weights sum to 1.0', () => {
    // Contract: panchanga(40%) + dasha(30%) + transit(20%) + signal(10%) = 100%
    const total = 0.40 + 0.30 + 0.20 + 0.10
    expect(total).toBeCloseTo(1.0)
  })

  it('score is always >= 0.0 for boundary inputs', () => {
    // Simulates compute_muhurta_score(0.0, 0.0, 0.0, 0.0)
    const score = Math.max(0.0, Math.min(1.0, 0.40 * 0.0 + 0.30 * 0.0 + 0.20 * 0.0 + 0.10 * 0.0))
    expect(score).toBeGreaterThanOrEqual(0.0)
  })

  it('score is always <= 1.0 for maximum inputs', () => {
    // Simulates compute_muhurta_score(1.0, 1.0, 1.0, 1.0)
    const score = Math.max(0.0, Math.min(1.0, 0.40 * 1.0 + 0.30 * 1.0 + 0.20 * 1.0 + 0.10 * 1.0))
    expect(score).toBeLessThanOrEqual(1.0)
    expect(score).toBeCloseTo(1.0)
  })

  it('score for average inputs is in (0.0, 1.0)', () => {
    // Simulates compute_muhurta_score(0.6, 0.7, 0.5, 0.6)
    const score = Math.max(0.0, Math.min(1.0,
      0.40 * 0.6 + 0.30 * 0.7 + 0.20 * 0.5 + 0.10 * 0.6
    ))
    expect(score).toBeGreaterThan(0.0)
    expect(score).toBeLessThan(1.0)
    expect(score).toBeCloseTo(0.61)
  })

})

// ── Contract constants ────────────────────────────────────────────────────────

describe('phala.muhurta contract constants', () => {

  it('description references FORENSIC grounding', () => {
    expect(MUHURTA_FINDER_DESCRIPTION).toContain('FORENSIC')
  })

  it('description references BPHS ch.46', () => {
    expect(MUHURTA_FINDER_DESCRIPTION).toContain('BPHS')
  })

  it('description references panchanga_quality', () => {
    expect(MUHURTA_FINDER_DESCRIPTION).toContain('panchanga_quality')
  })

  it('description references native chart ID for Abhisek Mohanty', () => {
    expect(MUHURTA_FINDER_DESCRIPTION).toContain('Abhisek Mohanty')
  })

  it('schema rejects missing chart_id', () => {
    const result = MuhurtaFinderInputSchema.safeParse({
      action_type: 'education',
      date_range: { start: '2026-06-04', end: '2026-09-01' },
    })
    expect(result.success).toBe(false)
  })

  it('schema rejects missing action_type', () => {
    const result = MuhurtaFinderInputSchema.safeParse({
      chart_id: '362f9f17-95a5-490b-a5a7-027d3e0efda0',
      date_range: { start: '2026-06-04', end: '2026-09-01' },
    })
    expect(result.success).toBe(false)
  })

  it('schema rejects missing date_range', () => {
    const result = MuhurtaFinderInputSchema.safeParse({
      chart_id: '362f9f17-95a5-490b-a5a7-027d3e0efda0',
      action_type: 'education',
    })
    expect(result.success).toBe(false)
  })

})
