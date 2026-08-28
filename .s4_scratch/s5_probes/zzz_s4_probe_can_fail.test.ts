import { describe, it, expect, vi } from 'vitest'

describe('S5 demonstrated-can-fail: compileFloorForPlan failure disclosure', () => {
  it('compileFloorForPlan DOES set compileFailed:true when compileContract throws (registry-completeness bug)', async () => {
    vi.resetModules()
    vi.doMock('@/lib/vidhi/compiler', () => ({
      compileContract: () => {
        throw new Error('simulated registry-completeness bug: unregistered primitive_id')
      },
      defaultRegistry: () => ({ primitives: [], floors: [] }),
    }))
    const { compileFloorForPlan } = await import('@/lib/pipeline/compiled_floor_adapter')
    const tuple = {
      intent: 'chart_overview' as const,
      domains: [],
      width: 'standard' as const,
      depth: 'standard' as const,
      horizon: 'present' as const,
      intervention: 'none' as const,
      entitlement: 'native' as const,
    }
    const result = compileFloorForPlan(tuple, 'test-chart-id')
    expect(result.compileFailed).toBe(true)
    expect(result.toolCalls).toEqual([])
    console.log('compileFloorForPlan result on registry-completeness bug:', JSON.stringify(result))
    vi.doUnmock('@/lib/vidhi/compiler')
  })

  it('DOCUMENTS that plan_stage.ts never reads compiledFloor.compileFailed / unmappedPrimitives (grep evidence)', async () => {
    const fs = await import('fs')
    const src = fs.readFileSync(
      new URL('../../pariprashna/pipeline/plan_stage.ts', import.meta.url),
      'utf-8',
    )
    // The compileFloorForPlan call site
    expect(src).toContain('compileFloorForPlan(plan.scope_tuple, chartId)')
    // Assert the failure/coverage fields are NEVER referenced anywhere in the file —
    // this is the silent-drop this probe demonstrates.
    expect(src).not.toContain('compiledFloor.compileFailed')
    expect(src).not.toContain('compiledFloor.unmappedPrimitives')
    expect(src).not.toContain('compiledFloor.mappedPrimitives')
  })
})
