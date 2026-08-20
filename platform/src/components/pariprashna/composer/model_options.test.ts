/**
 * Lane P2-C (PPR-09/16) — proves the composer's Model pill can no longer lie.
 *
 * The defect this guards against: `MODEL_ROWS` used to be a hand-written list
 * whose `value`s ('Claude Opus', 'Kimi K2 · OpenRouter', …) named no real
 * `@/lib/models/registry` id, so `isValidModelId` would silently reject every
 * selection server-side. This test asserts the picker rows are ALWAYS
 * registry-backed, so that specific regression can never come back unnoticed.
 */

import { describe, it, expect } from 'vitest'

import { getSynthesisModelRows } from './model_options'
import { isValidModelId, getModelMeta } from '@/lib/models/registry'

describe('getSynthesisModelRows', () => {
  it('always includes an Auto row using the "auto" sentinel', () => {
    const rows = getSynthesisModelRows()
    expect(rows[0]).toMatchObject({ value: 'auto', label: 'Auto' })
  })

  it('every non-Auto row value is a REAL, valid registry model id', () => {
    const rows = getSynthesisModelRows()
    const nonAuto = rows.filter((r) => r.value !== 'auto')
    expect(nonAuto.length).toBeGreaterThan(0)
    for (const row of nonAuto) {
      expect(isValidModelId(row.value)).toBe(true)
    }
  })

  it('only offers models synthesis can actually use (role synthesis|both)', () => {
    const rows = getSynthesisModelRows()
    for (const row of rows) {
      if (row.value === 'auto') continue
      const meta = getModelMeta(row.value)
      expect(meta).toBeDefined()
      expect(['synthesis', 'both']).toContain(meta!.role)
    }
  })

  it('never offers a row labelled deprecated/unavailable/internal/EOL/degraded', () => {
    const rows = getSynthesisModelRows()
    for (const row of rows) {
      expect(row.label).not.toMatch(/\[(unavailable|deprecated|internal label only|eol|degraded)\]/i)
    }
  })

  it('has no duplicate values', () => {
    const rows = getSynthesisModelRows()
    const values = rows.map((r) => r.value)
    expect(new Set(values).size).toBe(values.length)
  })
})
