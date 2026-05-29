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
  join(__dirname, '../../../src/app/api/chat/consult/regenerate/route.ts'),
  'utf-8',
)

describe('regenerate truncation wiring — B.3 fix', () => {
  it('V2RegenerateButton calls /api/chat/consume/regenerate before reload', () => {
    expect(v2Src).toContain('/api/chat/consume/regenerate')
    expect(v2Src).toContain('V2RegenerateButton')
    expect(v2Src).toContain('parent_message_id')
  })

  it('V2RegenerateButton awaits truncation then calls messageRuntime.reload() (race-condition-free)', () => {
    // Commit 220e366 replaced ActionBarPrimitive.Reload asChild with an explicit
    // await-then-reload pattern to eliminate the race where synthesis started against
    // an un-truncated conversation.
    const reloadBlock = v2Src.slice(
      v2Src.indexOf('function V2RegenerateButton'),
      v2Src.indexOf('function V2RegenerateButton') + 2000,
    )
    expect(reloadBlock).toContain('messageRuntime.reload()')
    expect(reloadBlock).toContain('v2-regenerate-btn')
    expect(reloadBlock).toContain('/api/chat/consume/regenerate')
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
