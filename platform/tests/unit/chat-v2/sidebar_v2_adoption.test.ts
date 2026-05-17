/**
 * C.2 — ConversationSidebarV2 adopted in ConsumeChatV2.
 *
 * Verifies the inlined ConversationSidebar is removed and ConversationSidebarV2
 * is imported and used in its place.
 */

import { describe, it, expect } from 'vitest'
import * as fs from 'node:fs'
import * as path from 'node:path'

const CONSUME_DIR = path.resolve(
  import.meta.dirname,
  '../../../src/components/consume'
)

const src = fs.readFileSync(path.join(CONSUME_DIR, 'ConsumeChatV2.tsx'), 'utf8')

describe('C.2 — ConversationSidebarV2 adopted in ConsumeChatV2', () => {
  it('imports ConversationSidebarV2 from dedicated module', () => {
    expect(src).toContain("from '@/components/consume/ConversationSidebarV2'")
  })

  it('uses ConversationSidebarV2 in render (not the inlined ConversationSidebar)', () => {
    expect(src).toContain('<ConversationSidebarV2')
  })

  it('does NOT define an inline ConversationSidebarProps interface', () => {
    expect(src).not.toContain('interface ConversationSidebarProps')
  })

  it('does NOT export ConversationSidebar from ConsumeChatV2', () => {
    expect(src).not.toContain('export function ConversationSidebar')
  })

  it('ConversationSidebarV2 module has date-grouping (Today/Yesterday/Older)', () => {
    const v2Src = fs.readFileSync(path.join(CONSUME_DIR, 'ConversationSidebarV2.tsx'), 'utf8')
    expect(v2Src).toContain("'Today'")
    expect(v2Src).toContain("'Yesterday'")
    expect(v2Src).toContain("'Older'")
  })
})
