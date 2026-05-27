import { describe, it, expect } from 'vitest'
import { singlePassPipeline } from '../index'

describe('singlePassPipeline', () => {
  it('declares kind === "single_pass"', () => {
    expect(singlePassPipeline.kind).toBe('single_pass')
  })

  it('describe() returns the canonical strategy summary', () => {
    const d = singlePassPipeline.describe()
    expect(d.kind).toBe('single_pass')
    expect(d.description).toMatch(/non-agentic|one synthesis/i)
    expect(d.description).toMatch(/classic marsys/i)
  })
})
