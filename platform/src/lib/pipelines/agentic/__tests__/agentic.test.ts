import { describe, it, expect } from 'vitest'
import { agenticPipeline } from '../index'

describe('agenticPipeline', () => {
  it('declares kind === "agentic"', () => {
    expect(agenticPipeline.kind).toBe('agentic')
  })

  it('describe() returns the canonical strategy summary', () => {
    const d = agenticPipeline.describe()
    expect(d.kind).toBe('agentic')
    expect(d.description).toMatch(/bounded.*loop|MAX_ITERATIONS=8/i)
    expect(d.description).toMatch(/claude-style/i)
  })
})
