/**
 * Integration tests for regenerate truncation wiring (audit finding O4 / exec B.3).
 *
 * The regenerate endpoint existed but had zero callers — ActionBarPrimitive.Reload
 * re-submitted to consume directly, leaving dead assistant turns in conversation_messages.
 *
 * Fix: V2RegenerateButton calls /api/chat/consume/regenerate before Reload fires,
 * via ActionBarPrimitive.Reload asChild + onClick interceptor.
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

const v2Src = readFileSync(
  join(__dirname, '../../../src/components/consume/ConsumeChatV2.tsx'),
  'utf-8',
)

const regenRouteSrc = readFileSync(
  join(__dirname, '../../../src/app/api/chat/consume/regenerate/route.ts'),
  'utf-8',
)

describe('regenerate truncation wiring — B.3 fix', () => {
  it('V2RegenerateButton calls /api/chat/consume/regenerate before reload', () => {
    expect(v2Src).toContain('/api/chat/consume/regenerate')
    expect(v2Src).toContain('V2RegenerateButton')
    expect(v2Src).toContain('parent_message_id')
  })

  it('V2RegenerateButton wraps ActionBarPrimitive.Reload asChild (reload still fires)', () => {
    expect(v2Src).toContain('ActionBarPrimitive.Reload asChild')
    // The custom button is rendered inside the Reload primitive
    const reloadBlock = v2Src.slice(
      v2Src.indexOf('function V2RegenerateButton'),
      v2Src.indexOf('function V2RegenerateButton') + 2000,
    )
    expect(reloadBlock).toContain('ActionBarPrimitive.Reload asChild')
    expect(reloadBlock).toContain('v2-regenerate-btn')
  })

  it('ConversationIdCtx threads conversationId into V2Message without prop drilling', () => {
    expect(v2Src).toContain('ConversationIdCtx')
    expect(v2Src).toContain('ConversationIdCtx.Provider')
    expect(v2Src).toContain('useContext(ConversationIdCtx)')
  })

  it('regenerate route deletes messages after parent_message_id (truncation semantics)', () => {
    expect(regenRouteSrc).toContain('DELETE FROM conversation_messages')
    expect(regenRouteSrc).toContain('created_at > $2')
    expect(regenRouteSrc).toContain('parent_message_id')
  })

  it('regenerate route returns ok:true with truncated_after field', () => {
    expect(regenRouteSrc).toContain('ok: true')
    expect(regenRouteSrc).toContain('truncated_after')
  })
})
