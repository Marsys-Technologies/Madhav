/**
 * Integration tests for B.8 — cost data part emission (audit finding O1).
 *
 * O1: costPart was imported but never emitted. The PerMessageDetailsDrawer
 * reads data-cost parts to populate the token/cost section during the live
 * session (before reload). This verifies the route emits the part correctly.
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

const routeSrc = readFileSync(
  join(__dirname, '../../../src/app/api/chat/consume/route.ts'),
  'utf-8',
)

describe('B.8 — cost data part emission (O1)', () => {
  it('route destructures usageHolder from orchestrator.synthesize()', () => {
    expect(routeSrc).toContain('usageHolder')
    const synthLine = routeSrc.split('\n').find(l => l.includes('orchestrator.synthesize') && l.includes('const {'))
    expect(synthLine).toBeTruthy()
    expect(synthLine).toContain('usageHolder')
  })

  it('route emits data-cost writer.write in onFinish', () => {
    expect(routeSrc).toContain("type: 'data-cost'")
    expect(routeSrc).toContain('costPart({')
    const costIdx = routeSrc.indexOf("type: 'data-cost'")
    const costBlock = routeSrc.slice(costIdx, costIdx + 300)
    expect(costBlock).toContain('input_tokens')
    expect(costBlock).toContain('output_tokens')
    expect(costBlock).toContain('dollars')
    expect(costBlock).toContain('ms')
    expect(costBlock).toContain('model: modelId')
  })

  it('route uses computeCostUsd + getModelPricingSync to compute dollars', () => {
    expect(routeSrc).toContain('getModelPricingSync(modelId)')
    expect(routeSrc).toContain('computeCostUsd(pricing,')
  })
})
