import { describe, it, expect } from 'vitest'
import { compileFloorForPlan } from '@/lib/pipeline/compiled_floor_adapter'

describe('S5 PPR-30 door parity: web door single-domain precedence vs MCP door multi-domain union', () => {
  it('web door compileFloorForPlan only compiles ONE intent floor (first-match precedence) for a 2-domain query', () => {
    // Realistic classifier tuple for "how do my career and wealth look given current dasha" —
    // two deepdive-eligible domains, standard width/depth.
    const tuple = {
      intent: 'domain_deepdive' as any,
      domains: ['career', 'wealth'],
      width: 'standard' as const,
      depth: 'deep' as const,
      horizon: 'present' as const,
      intervention: 'none' as const,
      entitlement: 'native' as const,
    }
    const result = compileFloorForPlan(tuple as any, '1c826d5a-41cb-4450-b4dc-59d440e5f75a')
    console.log('web door compilerIntent (single, precedence-based):', result.compilerIntent)
    console.log('web door mapped primitive count:', result.mappedPrimitives.length, '+ unmapped:', result.unmappedPrimitives.length)
    // Precedence picks the FIRST domain in the classifier tuple's domains[] that has a
    // registered deepdive floor -- 'career' wins, 'wealth' floor is never compiled at all.
    expect(result.compilerIntent).toBe('career_deepdive')
  })
})
