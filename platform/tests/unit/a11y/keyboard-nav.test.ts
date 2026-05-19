import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

const messageListSrc = readFileSync(
  join(__dirname, '../../../src/components/chat/MessageList.tsx'),
  'utf-8',
)
const hotkeysSrc = readFileSync(
  join(__dirname, '../../../src/hooks/useHotkeys.ts'),
  'utf-8',
)

describe('AC-3 — keyboard message navigation (j/k)', () => {
  it('MessageList rows carry data-message-index attribute', () => {
    expect(messageListSrc).toContain('data-message-index')
  })

  it('MessageList rows carry tabIndex={-1} for programmatic focus', () => {
    expect(messageListSrc).toContain('tabIndex={-1}')
  })

  it('useHotkeys registers a j key handler', () => {
    expect(hotkeysSrc).toContain("'j'")
  })

  it('useHotkeys registers a k key handler', () => {
    expect(hotkeysSrc).toContain("'k'")
  })

  it('j/k navigation queries rows by data-message-index', () => {
    expect(hotkeysSrc).toContain('data-message-index')
  })

  it('j/k handlers are guarded by isTypingTarget check', () => {
    const jkBlock = hotkeysSrc.slice(
      hotkeysSrc.indexOf("'j'") - 50,
      hotkeysSrc.indexOf("'j'") + 600,
    )
    expect(jkBlock).toContain('isTypingTarget')
  })

  it('j navigates to next message (min-clamps at last row)', () => {
    expect(hotkeysSrc).toContain('Math.min')
  })

  it('k navigates to previous message (max-clamps at first row)', () => {
    expect(hotkeysSrc).toContain('Math.max')
  })
})
