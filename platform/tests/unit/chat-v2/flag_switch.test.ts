/**
 * α7 — master flag switch tests.
 *
 * Verifies that ConsumeChat.tsx is a thin switch that delegates to:
 *   - ConsumeChatLegacy when chatV2Enabled=false (default)
 *   - ConsumeChatV2    when chatV2Enabled=true
 *
 * Uses source-level assertions (no DOM rendering) because the components
 * require Next.js router context and assistant-ui providers. Integration
 * rendering is covered by the E2E tests.
 */

import { describe, it, expect } from 'vitest'
import * as fs from 'node:fs'
import * as path from 'node:path'

const CONSUME_DIR = path.resolve(
  import.meta.dirname,
  '../../../src/components/consume'
)

describe('α7 — ConsumeChat thin switch (source-level)', () => {
  it('ConsumeChat.tsx imports both ConsumeChatLegacy and ConsumeChatV2', () => {
    const src = fs.readFileSync(path.join(CONSUME_DIR, 'ConsumeChat.tsx'), 'utf8')
    expect(src).toContain("from './ConsumeChatLegacy'")
    expect(src).toContain("from './ConsumeChatV2'")
  })

  it('ConsumeChat.tsx exports the ConsumeChat function', () => {
    const src = fs.readFileSync(path.join(CONSUME_DIR, 'ConsumeChat.tsx'), 'utf8')
    expect(src).toContain('export function ConsumeChat')
  })

  it('ConsumeChat.tsx has chatV2Enabled prop in SwitchProps', () => {
    const src = fs.readFileSync(path.join(CONSUME_DIR, 'ConsumeChat.tsx'), 'utf8')
    expect(src).toContain('chatV2Enabled')
  })

  it('ConsumeChat.tsx branches on chatV2Enabled to render V2 or Legacy', () => {
    const src = fs.readFileSync(path.join(CONSUME_DIR, 'ConsumeChat.tsx'), 'utf8')
    expect(src).toContain('if (chatV2Enabled)')
    expect(src).toContain('ConsumeChatV2')
    expect(src).toContain('ConsumeChatLegacy')
  })

  it('ConsumeChatLegacy.tsx exports ConsumeChatLegacy function', () => {
    const src = fs.readFileSync(path.join(CONSUME_DIR, 'ConsumeChatLegacy.tsx'), 'utf8')
    expect(src).toContain('export function ConsumeChatLegacy')
  })

  it('ConsumeChatLegacy.tsx exports ConsumeChatProps interface', () => {
    const src = fs.readFileSync(path.join(CONSUME_DIR, 'ConsumeChatLegacy.tsx'), 'utf8')
    expect(src).toContain('export interface ConsumeChatProps')
  })

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

  it('both page files pass chatV2Enabled to ConsumeChat', () => {
    const pages = [
      path.resolve(
        import.meta.dirname,
        '../../../src/app/clients/[id]/consume/page.tsx'
      ),
      path.resolve(
        import.meta.dirname,
        '../../../src/app/clients/[id]/consume/[conversationId]/page.tsx'
      ),
    ]
    for (const p of pages) {
      const src = fs.readFileSync(p, 'utf8')
      expect(src).toContain("getFlag('CHAT_V2_ENABLED')")
      expect(src).toContain('chatV2Enabled={chatV2Enabled}')
    }
  })
})
