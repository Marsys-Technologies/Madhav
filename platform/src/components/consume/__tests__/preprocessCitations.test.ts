import { describe, it, expect } from 'vitest'
import { preprocessCitations } from '../ConsumeChatV2'

describe('preprocessCitations', () => {
  it('AC-1: arrow-wrapped signal produces exactly one badge, no double-wrap', () => {
    const { processedText, count } = preprocessCitations('(→ SIG.MSR.042)')
    expect(count).toBe(1)
    expect(processedText).toContain('`CITE:1:SIG.MSR.042`')
    expect(processedText).not.toMatch(/`CITE:\d+:`CITE/)
  })

  it('AC-2: bare signal produces exactly one badge', () => {
    const { processedText, count } = preprocessCitations('SIG.MSR.001 is active')
    expect(count).toBe(1)
    expect(processedText).toContain('`CITE:1:SIG.MSR.001`')
    expect(processedText).not.toMatch(/`CITE:\d+:`CITE/)
  })

  it('AC-3: mixed paragraph — correct badge count, no duplication', () => {
    const text = '(→ SIG.MSR.001, SIG.MSR.002) and also SIG.MSR.003 plus bare SIG.MSR.001'
    const { processedText, count } = preprocessCitations(text)
    // Three unique signals
    expect(count).toBe(3)
    // SIG.MSR.001 appears twice (arrow + bare position) with same index
    const matches = [...processedText.matchAll(/`CITE:(\d+):SIG\.MSR\.001`/g)]
    expect(matches).toHaveLength(2)
    expect(matches[0][1]).toBe(matches[1][1]) // same index
    // No double-wrap nesting
    expect(processedText).not.toMatch(/`CITE:\d+:`CITE/)
  })

  it('AC-4: pre-badged input is left unchanged (idempotent)', () => {
    const alreadyBadged = '`CITE:1:SIG.MSR.001`'
    const { processedText, count } = preprocessCitations(alreadyBadged)
    expect(processedText).toBe(alreadyBadged)
    expect(count).toBe(0)
  })
})
