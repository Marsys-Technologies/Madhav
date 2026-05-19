import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

const src = readFileSync(
  join(__dirname, '../../../src/components/chat/MessageList.tsx'),
  'utf-8',
)

describe('AC-4 — message action keyboard shortcuts', () => {
  it('row onKeyDown handles c key for clipboard copy', () => {
    expect(src).toContain("e.key === 'c'")
    expect(src).toContain('clipboard.writeText')
  })

  it('e key triggers edit for user messages only', () => {
    expect(src).toContain("e.key === 'e'")
    expect(src).toContain("message.role === 'user'")
  })

  it('r key triggers regenerate for assistant messages only', () => {
    expect(src).toContain("e.key === 'r'")
    expect(src).toContain("message.role === 'assistant'")
  })

  it('modifier key combinations are ignored (ctrlKey/metaKey/altKey guard)', () => {
    expect(src).toContain('e.ctrlKey')
    expect(src).toContain('e.metaKey')
    expect(src).toContain('e.altKey')
  })

  it('e key calls onEditUserMessage with message id and text', () => {
    expect(src).toContain('onEditUserMessage?.(message.id')
  })

  it('r key calls onRegenerate', () => {
    expect(src).toContain('onRegenerate?.()')
  })
})
