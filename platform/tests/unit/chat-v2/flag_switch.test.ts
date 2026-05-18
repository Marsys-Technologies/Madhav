/**
 * Post-§M.16 — ConsumeChat V2 source-level guards.
 *
 * The α7 thin-switch assertions (chatV2Enabled, ConsumeChatLegacy) were
 * retired at §M.16 (2026-05-18). V2 is the only path; the switch and
 * legacy file are deleted. Only V2 behavioral guards remain.
 */

import { describe, it, expect } from 'vitest'
import * as fs from 'node:fs'
import * as path from 'node:path'

const CONSUME_DIR = path.resolve(
  import.meta.dirname,
  '../../../src/components/consume'
)

describe('§M.16 — ConsumeChatV2 source-level guards', () => {
  it('ConsumeChatV2.tsx exports ConsumeChatV2 function', () => {
    const src = fs.readFileSync(path.join(CONSUME_DIR, 'ConsumeChatV2.tsx'), 'utf8')
    expect(src).toContain('export function ConsumeChatV2')
  })

  it('ConsumeChatV2.tsx uses DefaultChatTransport per F.1', () => {
    const src = fs.readFileSync(path.join(CONSUME_DIR, 'ConsumeChatV2.tsx'), 'utf8')
    // F.1: every transport binding uses new DefaultChatTransport({ api: ... })
    expect(src).toContain('new DefaultChatTransport(')
    expect(src).toContain("api: '/api/chat/consume'")
  })

  it('ConsumeChatV2.tsx uses F.2-compliant MessagePrimitive.Parts components', () => {
    const src = fs.readFileSync(path.join(CONSUME_DIR, 'ConsumeChatV2.tsx'), 'utf8')
    // F.2: flat props — (props) => props.text, not ({ part }) => part.text
    expect(src).toContain('props.text')
    expect(src).not.toContain('part.text')
    expect(src).not.toContain('{ part }')
  })

  it('ConsumeChatV2.tsx uses useThreadRuntime().subscribe() per F.3', () => {
    const src = fs.readFileSync(path.join(CONSUME_DIR, 'ConsumeChatV2.tsx'), 'utf8')
    // F.3: useThreadRuntime + subscribe, not deprecated ComposerPrimitive.If sending
    expect(src).toContain('useThreadRuntime')
    expect(src).toContain('.subscribe(')
    expect(src).not.toContain('ComposerPrimitive.If')
  })
})
