/**
 * b11_guard.test.ts — B.11 runtime enforcement guard unit tests
 */
import { describe, it, expect } from 'vitest'

import {
  checkB11Compliance,
  B11_REQUIRED_LAYERS,
} from '@/lib/synthesis/b11_guard'

const ALL_LAYERS_CONTEXT = `
=== L2.5: MSR — MASTER SIGNAL REGISTER ===
MSR signals loaded. 499 signals from Master Signal Register.

=== L2.5: UCN — UNIFIED CHART NARRATIVE ===
Unified Chart Narrative context loaded.

=== L2.5: CDLM — CROSS-DOMAIN LINKAGE MATRIX ===
Cross-Domain Linkage Matrix present.

=== L2.5: CGM — CAUSAL GRAPH MODEL ===
Causal Graph Model relationships present.

=== L2.5: RM — RESONANCE MAP ===
Resonance Map patterns loaded.
`

const PARTIAL_CONTEXT_MISSING_CGM_RM = `
MSR signals from Master Signal Register.
UCN: Unified Chart Narrative context.
CDLM linkages present.
`

const EMPTY_CONTEXT = ''

describe('checkB11Compliance — compliant cases', () => {
  it('returns compliant: true when all 5 layers are present', () => {
    const result = checkB11Compliance(ALL_LAYERS_CONTEXT)
    expect(result.compliant).toBe(true)
    expect(result.annotation).toBeNull()
    expect(result.missingLayers).toHaveLength(0)
  })

  it('returns compliant: true when only the 3 required layers are present', () => {
    const context = 'MSR signals present. UCN narrative loaded. CGM causal graph present.'
    const result = checkB11Compliance(context)
    expect(result.compliant).toBe(true)
    expect(result.annotation).toBeNull()
  })

  it('presentLayers includes all 5 when all are in context', () => {
    const result = checkB11Compliance(ALL_LAYERS_CONTEXT)
    expect(result.presentLayers).toContain('MSR')
    expect(result.presentLayers).toContain('UCN')
    expect(result.presentLayers).toContain('CDLM')
    expect(result.presentLayers).toContain('CGM')
    expect(result.presentLayers).toContain('RM')
  })
})

describe('checkB11Compliance — violation cases', () => {
  it('returns compliant: false when CGM and RM are missing', () => {
    const result = checkB11Compliance(PARTIAL_CONTEXT_MISSING_CGM_RM)
    expect(result.compliant).toBe(false)
    expect(result.missingLayers).toContain('CGM')
  })

  it('returns compliant: false when context is empty', () => {
    const result = checkB11Compliance(EMPTY_CONTEXT)
    expect(result.compliant).toBe(false)
    expect(result.missingLayers).toEqual(expect.arrayContaining([...B11_REQUIRED_LAYERS]))
  })

  it('returns compliant: false when all required layers are missing', () => {
    const result = checkB11Compliance('Some unrelated content with no L2.5 references.')
    expect(result.compliant).toBe(false)
    expect(result.missingLayers.length).toBeGreaterThanOrEqual(B11_REQUIRED_LAYERS.length)
  })
})

describe('annotation format', () => {
  it('annotation is null when compliant', () => {
    const result = checkB11Compliance(ALL_LAYERS_CONTEXT)
    expect(result.annotation).toBeNull()
  })

  it('annotation matches "[B.11-PARTIAL: missing X, Y]" format', () => {
    const result = checkB11Compliance('Only MSR and UCN present.')
    expect(result.annotation).not.toBeNull()
    expect(result.annotation).toMatch(/^\[B\.11-PARTIAL: missing/)
    expect(result.annotation).toContain('CGM')
  })

  it('annotation lists all missing required layers', () => {
    const result = checkB11Compliance(EMPTY_CONTEXT)
    for (const layer of B11_REQUIRED_LAYERS) {
      expect(result.annotation).toContain(layer)
    }
  })
})

describe('input type handling', () => {
  it('accepts an array of strings', () => {
    const context = ['MSR signals present', 'UCN loaded', 'CGM present']
    const result = checkB11Compliance(context)
    expect(result.compliant).toBe(true)
  })

  it('accepts null without throwing', () => {
    expect(() => checkB11Compliance(null)).not.toThrow()
  })

  it('accepts undefined without throwing', () => {
    expect(() => checkB11Compliance(undefined)).not.toThrow()
  })

  it('detects layer via full name "Master Signal Register"', () => {
    const result = checkB11Compliance('Master Signal Register is present. UCN also. Causal Graph Model here.')
    expect(result.presentLayers).toContain('MSR')
    expect(result.presentLayers).toContain('CGM')
  })
})
