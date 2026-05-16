/**
 * γ4 — Validator failure surface
 *
 * Tests:
 *   - CitationGatePart schema validation (pass / warn / fail variants)
 *   - citationGatePart helper constructor
 *   - Gate status extraction logic (mirrors V2Message useMemo logic)
 *   - Disclosure-tier prop-gating logic
 */

import { describe, it, expect } from 'vitest'
import {
  CitationGatePartSchema,
  citationGatePart,
} from '../../../src/lib/streams/data_parts'

// ── Schema validation ──────────────────────────────────────────────────────────

describe('CitationGatePartSchema', () => {
  it('accepts a pass result', () => {
    const part = { type: 'citation_gate', status: 'pass', issues: [] }
    expect(CitationGatePartSchema.parse(part)).toMatchObject({ status: 'pass' })
  })

  it('accepts a warn result with issues', () => {
    const part = { type: 'citation_gate', status: 'warn', issues: ['SIG.MSR.001 not found in L1'] }
    const parsed = CitationGatePartSchema.parse(part)
    expect(parsed.status).toBe('warn')
    expect(parsed.issues).toHaveLength(1)
  })

  it('accepts a fail result with multiple issues', () => {
    const part = {
      type: 'citation_gate',
      status: 'fail',
      issues: ['SIG.MSR.002 layer mismatch', 'SIG.MSR.003 not found'],
    }
    const parsed = CitationGatePartSchema.parse(part)
    expect(parsed.status).toBe('fail')
    expect(parsed.issues).toHaveLength(2)
  })

  it('accepts a pass result with no issues field (optional)', () => {
    const part = { type: 'citation_gate', status: 'pass' }
    expect(() => CitationGatePartSchema.parse(part)).not.toThrow()
  })

  it('rejects an unknown status', () => {
    const part = { type: 'citation_gate', status: 'unknown' }
    expect(() => CitationGatePartSchema.parse(part)).toThrow()
  })

  it('rejects missing type field', () => {
    const part = { status: 'pass' }
    expect(() => CitationGatePartSchema.parse(part)).toThrow()
  })
})

// ── Helper constructor ─────────────────────────────────────────────────────────

describe('citationGatePart helper', () => {
  it('builds a pass part', () => {
    const part = citationGatePart({ status: 'pass', issues: [] })
    expect(part.type).toBe('citation_gate')
    expect(part.status).toBe('pass')
    expect(part.issues).toEqual([])
  })

  it('builds a warn part with issues', () => {
    const part = citationGatePart({ status: 'warn', issues: ['SIG.MSR.001 missing'] })
    expect(part.status).toBe('warn')
    expect(part.issues).toContain('SIG.MSR.001 missing')
  })

  it('builds a fail part with issues', () => {
    const part = citationGatePart({ status: 'fail', issues: ['layer mismatch'] })
    expect(part.status).toBe('fail')
  })

  it('omits issues when not provided (optional field)', () => {
    const part = citationGatePart({ status: 'pass' })
    expect(part.status).toBe('pass')
    expect(part.issues).toBeUndefined()
  })
})

// ── Gate status extraction logic ──────────────────────────────────────────────

function extractCitationGate(
  dataParts: ReadonlyArray<unknown>,
): { status?: string; issues?: string[] } | null {
  const entry = dataParts.find(
    (d): d is { type: string; data: { status?: string; issues?: string[] } } =>
      typeof d === 'object' && d !== null &&
      (d as Record<string, unknown>).type === 'data-citation-gate',
  )
  return entry ? (entry as { type: string; data: { status?: string; issues?: string[] } }).data : null
}

describe('citation gate extraction from dataParts', () => {
  it('returns null when no gate part exists', () => {
    const parts = [
      { type: 'data-cost', data: { dollars: 0.001 } },
    ]
    expect(extractCitationGate(parts)).toBeNull()
  })

  it('returns gate data for a pass part', () => {
    const parts = [
      { type: 'data-citation-gate', data: { status: 'pass', issues: [] } },
    ]
    expect(extractCitationGate(parts)).toMatchObject({ status: 'pass' })
  })

  it('returns gate data for a fail part with issues', () => {
    const parts = [
      { type: 'data-citation-gate', data: { status: 'fail', issues: ['SIG.MSR.099 missing'] } },
    ]
    const gate = extractCitationGate(parts)
    expect(gate?.status).toBe('fail')
    expect(gate?.issues).toContain('SIG.MSR.099 missing')
  })

  it('returns gate data for a warn part', () => {
    const parts = [
      { type: 'data-panel-member', data: { member_index: 0 } }, // noise
      { type: 'data-citation-gate', data: { status: 'warn', issues: ['low confidence'] } },
    ]
    const gate = extractCitationGate(parts)
    expect(gate?.status).toBe('warn')
  })

  it('ignores non-gate parts mixed in', () => {
    const parts = [
      { type: 'data-cost', data: { dollars: 0.002 } },
      { type: 'data-observability', data: { query_id: 'abc' } },
    ]
    expect(extractCitationGate(parts)).toBeNull()
  })
})

// ── Disclosure-tier gating logic ───────────────────────────────────────────────

describe('disclosure tier gating for validator surface', () => {
  it('super_admin sees full issue list (isSuperAdmin=true)', () => {
    const isSuperAdmin = true
    const issues = ['SIG.MSR.001 missing', 'SIG.MSR.002 layer mismatch']
    const shouldShowIssues = isSuperAdmin && issues.length > 0
    expect(shouldShowIssues).toBe(true)
  })

  it('non-admin sees summary only (isSuperAdmin=false)', () => {
    const isSuperAdmin = false
    const issues = ['SIG.MSR.001 missing']
    const shouldShowIssues = isSuperAdmin && issues.length > 0
    expect(shouldShowIssues).toBe(false)
  })

  it('super_admin with empty issues list does not show empty ul', () => {
    const isSuperAdmin = true
    const issues: string[] = []
    const shouldShowIssues = isSuperAdmin && issues.length > 0
    expect(shouldShowIssues).toBe(false)
  })

  it('warn chip shows first issue as tooltip for super_admin only', () => {
    const issues = ['low confidence citation']
    const isSuperAdmin = true
    const tooltip = isSuperAdmin && issues[0] ? issues[0] : undefined
    expect(tooltip).toBe('low confidence citation')
  })

  it('warn chip has no tooltip for non-admin', () => {
    const issues = ['low confidence citation']
    const isSuperAdmin = false
    const tooltip = isSuperAdmin && issues[0] ? issues[0] : undefined
    expect(tooltip).toBeUndefined()
  })
})
