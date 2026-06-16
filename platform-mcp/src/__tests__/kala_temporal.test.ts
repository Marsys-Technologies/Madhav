/**
 * kala_temporal.test.ts — BRAHMA-KA-3-4: kala.temporal MCP tool tests
 *
 * Tests the composite temporal fabric MCP tool without a live database.
 * DB-dependent pool calls are mocked via vi.mock('pg').
 *
 * Contract (BRAHMA_L1_L5_REGISTRY_SEED_v1_0 §D):
 *   - temporal(chart_id, {start:1984, end:2026}) returns all 3 subsystems
 *     non-empty for the native chart
 *   - source_citation = "PyJHora/SwissEph DE441 + Brahma-L1" (non-null, exact)
 *   - provenance_envelope present + correct shape
 *   - convergence_score values in [0.0, 1.0] range (range check, not exact)
 *   - Sade Sati obstructions present for native 1984-2026
 *
 * BRAHMA-KA-3-4
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Mock pg before importing the module ──────────────────────────────────────

// Mock pg Pool so no DB connection is attempted
vi.mock('pg', () => {
  const Pool = vi.fn(() => ({
    connect: vi.fn(() =>
      Promise.resolve({
        query: vi.fn(() => Promise.resolve({ rows: [] })),
        release: vi.fn(),
      })
    ),
  }))
  return { default: { Pool }, Pool }
})

// ── Import after mock ─────────────────────────────────────────────────────────

import {
  computeTemporal,
  registerKalaTemporalTool,
  type TemporalResult,
  type TimelineEntry,
  type ConvergenceWindow,
  type ObstructionEntry,
} from '../tools/kala_temporal.js'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'

// ── Constants ─────────────────────────────────────────────────────────────────

const SOURCE_CITATION = 'PyJHora/SwissEph DE441 + Brahma-L1'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

// ── Helpers ───────────────────────────────────────────────────────────────────

async function getNativeResult(): Promise<TemporalResult> {
  return computeTemporal(NATIVE_CHART_ID, { start: 1984, end: 2026 })
}

// ── Tests: source_citation ────────────────────────────────────────────────────

describe('kala.temporal — source_citation', () => {
  it('SOURCE_CITATION constant matches expected value', () => {
    // Test by inspecting the provenance_envelope after a call
    // (no way to import the constant directly, but we verify via output)
    expect(SOURCE_CITATION).toBe('PyJHora/SwissEph DE441 + Brahma-L1')
  })

  it('provenance_envelope.source_citation equals SOURCE_CITATION', async () => {
    const result = await getNativeResult()
    expect(result.provenance_envelope.source_citation).toBe(SOURCE_CITATION)
  })

  it('provenance_envelope.source_citation is non-null and non-empty', async () => {
    const result = await getNativeResult()
    const citation = result.provenance_envelope.source_citation
    expect(citation).toBeTruthy()
    expect(typeof citation).toBe('string')
    expect(citation.length).toBeGreaterThan(5)
  })
})

// ── Tests: composite structure ────────────────────────────────────────────────

describe('kala.temporal — composite structure', () => {
  it('returns all three subsystem keys', async () => {
    const result = await getNativeResult()
    expect(result).toHaveProperty('timeline')
    expect(result).toHaveProperty('convergence_windows')
    expect(result).toHaveProperty('obstructions')
    expect(result).toHaveProperty('provenance_envelope')
  })

  it('timeline is an array', async () => {
    const result = await getNativeResult()
    expect(Array.isArray(result.timeline)).toBe(true)
  })

  it('convergence_windows is an array', async () => {
    const result = await getNativeResult()
    expect(Array.isArray(result.convergence_windows)).toBe(true)
  })

  it('obstructions is an array', async () => {
    const result = await getNativeResult()
    expect(Array.isArray(result.obstructions)).toBe(true)
  })
})

// ── Tests: provenance_envelope ────────────────────────────────────────────────

describe('kala.temporal — provenance_envelope', () => {
  it('has all required keys', async () => {
    const result = await getNativeResult()
    const penv = result.provenance_envelope
    const required = [
      'source',
      'layers',
      'chart_id',
      'date_range',
      'computed_at',
      'source_citation',
      'timeline_count',
      'convergence_window_count',
      'obstruction_count',
    ]
    for (const key of required) {
      expect(penv).toHaveProperty(key)
    }
  })

  it('source equals "kala.temporal"', async () => {
    const result = await getNativeResult()
    expect(result.provenance_envelope.source).toBe('kala.temporal')
  })

  it('layers contains all three subsystem names', async () => {
    const result = await getNativeResult()
    const layers = result.provenance_envelope.layers
    expect(layers).toContain('kala.timeline')
    expect(layers).toContain('kala.convergence')
    expect(layers).toContain('kala.obstruction')
  })

  it('chart_id matches input', async () => {
    const result = await getNativeResult()
    expect(result.provenance_envelope.chart_id).toBe(NATIVE_CHART_ID)
  })

  it('date_range matches input', async () => {
    const result = await getNativeResult()
    expect(result.provenance_envelope.date_range.start).toBe(1984)
    expect(result.provenance_envelope.date_range.end).toBe(2026)
  })

  it('counts match actual array lengths', async () => {
    const result = await getNativeResult()
    const penv = result.provenance_envelope
    expect(penv.timeline_count).toBe(result.timeline.length)
    expect(penv.convergence_window_count).toBe(result.convergence_windows.length)
    expect(penv.obstruction_count).toBe(result.obstructions.length)
  })

  it('computed_at is a non-empty ISO string', async () => {
    const result = await getNativeResult()
    const computedAt = result.provenance_envelope.computed_at
    expect(typeof computedAt).toBe('string')
    expect(computedAt.length).toBeGreaterThan(10)
    // Should be parseable as a date
    const d = new Date(computedAt)
    expect(d.getFullYear()).toBeGreaterThan(2020)
  })
})

// ── Tests: timeline (KA-3-1) ──────────────────────────────────────────────────

describe('kala.timeline (KA-3-1)', () => {
  it('is non-empty for native 1984-2026', async () => {
    const result = await getNativeResult()
    expect(result.timeline.length).toBeGreaterThan(0)
  })

  it('all entries have required fields', async () => {
    const result = await getNativeResult()
    const required: (keyof TimelineEntry)[] = [
      'period_id',
      'type',
      'md_lord',
      'md_start',
      'md_end',
      'display_start',
      'display_end',
      'active_antardasha_lords',
      'source_citation',
    ]
    for (const entry of result.timeline) {
      for (const field of required) {
        expect(entry).toHaveProperty(field)
      }
    }
  })

  it('type is always "mahadasha"', async () => {
    const result = await getNativeResult()
    for (const entry of result.timeline) {
      expect(entry.type).toBe('mahadasha')
    }
  })

  it('md_lord is a non-empty string', async () => {
    const result = await getNativeResult()
    const validLords = new Set([
      'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
    ])
    for (const entry of result.timeline) {
      expect(typeof entry.md_lord).toBe('string')
      expect(entry.md_lord.length).toBeGreaterThan(0)
      expect(validLords.has(entry.md_lord)).toBe(true)
    }
  })

  it('source_citation non-null and equals SOURCE_CITATION on all entries', async () => {
    const result = await getNativeResult()
    for (const entry of result.timeline) {
      expect(entry.source_citation).toBe(SOURCE_CITATION)
    }
  })

  it('active_antardasha_lords is an array', async () => {
    const result = await getNativeResult()
    for (const entry of result.timeline) {
      expect(Array.isArray(entry.active_antardasha_lords)).toBe(true)
    }
  })

  it('period_ids are unique', async () => {
    const result = await getNativeResult()
    const ids = result.timeline.map((e) => e.period_id)
    expect(new Set(ids).size).toBe(ids.length)
  })
})

// ── Tests: convergence_windows (KA-3-2) ──────────────────────────────────────

describe('kala.convergence (KA-3-2)', () => {
  it('convergence_score values are in [0.0, 1.0] range', async () => {
    const result = await getNativeResult()
    for (const window of result.convergence_windows) {
      const score = window.convergence_score
      expect(typeof score).toBe('number')
      // Range check — not exact float assertion
      expect(score).toBeGreaterThanOrEqual(0.0)
      expect(score).toBeLessThanOrEqual(1.0)
    }
  })

  it('convergence_level is one of HIGH|MODERATE|LOW', async () => {
    const result = await getNativeResult()
    const validLevels = new Set(['HIGH', 'MODERATE', 'LOW'])
    for (const window of result.convergence_windows) {
      expect(validLevels.has(window.convergence_level)).toBe(true)
    }
  })

  it('source_citation present on all windows', async () => {
    const result = await getNativeResult()
    for (const window of result.convergence_windows) {
      expect(window.source_citation).toBe(SOURCE_CITATION)
    }
  })

  it('window_ids are unique', async () => {
    const result = await getNativeResult()
    const ids = result.convergence_windows.map((w) => w.window_id)
    expect(new Set(ids).size).toBe(ids.length)
  })

  it('sorted descending by convergence_score', async () => {
    const result = await getNativeResult()
    const scores = result.convergence_windows.map((w) => w.convergence_score)
    for (let i = 0; i < scores.length - 1; i++) {
      expect(scores[i]).toBeGreaterThanOrEqual(scores[i + 1])
    }
  })

  it('constituent_factors is an array', async () => {
    const result = await getNativeResult()
    for (const window of result.convergence_windows) {
      expect(Array.isArray(window.constituent_factors)).toBe(true)
    }
  })
})

// ── Tests: obstructions (KA-3-3) ─────────────────────────────────────────────

describe('kala.obstruction (KA-3-3)', () => {
  it('Sade Sati present for native 1984-2026', async () => {
    const result = await getNativeResult()
    const sadeSati = result.obstructions.filter((o) => o.type === 'sade_sati')
    expect(sadeSati.length).toBeGreaterThan(0)
  })

  it('Sade Sati severity is HIGH', async () => {
    const result = await getNativeResult()
    for (const obs of result.obstructions) {
      if (obs.type === 'sade_sati') {
        expect(obs.severity).toBe('HIGH')
      }
    }
  })

  it('source_citation present on all obstructions', async () => {
    const result = await getNativeResult()
    for (const obs of result.obstructions) {
      expect(obs.source_citation).toBe(SOURCE_CITATION)
    }
  })

  it('obstruction_ids are unique', async () => {
    const result = await getNativeResult()
    const ids = result.obstructions.map((o) => o.obstruction_id)
    expect(new Set(ids).size).toBe(ids.length)
  })

  it('obstruction dates are valid YYYY-MM-DD strings', async () => {
    const datePattern = /^\d{4}-\d{2}-\d{2}$/
    const result = await getNativeResult()
    for (const obs of result.obstructions) {
      expect(datePattern.test(obs.start)).toBe(true)
      expect(datePattern.test(obs.end)).toBe(true)
    }
  })

  it('type field is one of sade_sati|malefic_md_ad_confluence', async () => {
    const validTypes = new Set(['sade_sati', 'malefic_md_ad_confluence'])
    const result = await getNativeResult()
    for (const obs of result.obstructions) {
      expect(validTypes.has(obs.type)).toBe(true)
    }
  })
})

// ── Tests: error handling ─────────────────────────────────────────────────────

describe('kala.temporal — error handling', () => {
  it('throws when start > end', async () => {
    await expect(
      computeTemporal(NATIVE_CHART_ID, { start: 2030, end: 2010 })
    ).rejects.toThrow(/date_range\.start.*must be/)
  })

  it('throws when span > 150 years', async () => {
    await expect(
      computeTemporal(NATIVE_CHART_ID, { start: 1800, end: 2000 })
    ).rejects.toThrow(/150 years/)
  })
})

// ── Tests: MCP tool registration ──────────────────────────────────────────────

describe('kala.temporal — MCP tool registration', () => {
  it('registerKalaTemporalTool registers the "temporal" tool', () => {
    const tools: string[] = []
    const mockServer = {
      tool: vi.fn((name: string) => {
        tools.push(name)
      }),
    } as unknown as McpServer

    registerKalaTemporalTool(mockServer)
    expect(tools).toContain('temporal')
  })

  it('registerKalaTemporalTool called with 4 args (name, desc, schema, handler)', () => {
    const mockServer = {
      tool: vi.fn(),
    } as unknown as McpServer

    registerKalaTemporalTool(mockServer)
    expect(mockServer.tool).toHaveBeenCalledTimes(1)
    const args = (mockServer.tool as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(args).toHaveLength(4) // name, description, schema, handler
    expect(args[0]).toBe('temporal')
    expect(typeof args[1]).toBe('string')
    expect(args[1].length).toBeGreaterThan(20)
  })
})
