import { describe, it, expect } from 'vitest'
import * as fs from 'node:fs'
import * as path from 'node:path'

/**
 * F.2 — initialMessages prop seeding regression guard.
 *
 * Bug (WRAPUP-S3 root cause): ConsumeChatV2 did not destructure `initialMessages`
 * from props, and its local useState was seeded with `undefined`, silently dropping
 * any deeplink context passed by the /panchang AskMadhavLink flow.
 *
 * Fix: add `initialMessages: initialMessagesProp` to the destructuring and seed
 * `useState(initialMessagesProp)` so the prop value is honoured on mount.
 *
 * We use the same source-level guard pattern as ConsumeChat.lel.test.tsx —
 * mounting the full ConsumeChatV2 tree requires the entire AI SDK runtime stack.
 *
 * Guards:
 *   1. Props interface declares `initialMessages?: UIMessage[]`.
 *   2. Function signature destructures `initialMessages: initialMessagesProp`.
 *   3. Local useState is seeded from `initialMessagesProp`, not from `undefined`.
 *   4. handleNewConversation still explicitly resets to undefined (regression check).
 */

const consumeChatPath = path.resolve(__dirname, '..', 'ConsumeChatV2.tsx')
const source = fs.readFileSync(consumeChatPath, 'utf8')

describe('ConsumeChatV2 — F.2 initialMessages prop seeding', () => {
  it('ConsumeChatProps declares initialMessages as optional UIMessage[]', () => {
    expect(source).toMatch(/initialMessages\?\s*:\s*UIMessage\[\]/)
  })

  it('ConsumeChatV2 function signature destructures initialMessages as initialMessagesProp', () => {
    // The function signature must contain the rename destructure.
    expect(source).toMatch(/initialMessages\s*:\s*initialMessagesProp/)
  })

  it('useState is seeded from initialMessagesProp (not hardcoded undefined)', () => {
    // Find the line that declares local initialMessages state.
    const stateLineMatch = source.match(
      /const\s+\[initialMessages,\s*setInitialMessages\]\s*=\s*useState[^(]*\(([^)]+)\)/
    )
    expect(stateLineMatch).not.toBeNull()
    const seedArg = stateLineMatch![1].trim()
    // Must be seeded from the prop alias, not from `undefined`.
    expect(seedArg).toBe('initialMessagesProp')
    expect(seedArg).not.toBe('undefined')
  })

  it('handleNewConversation resets to undefined (new chat has no deeplink context)', () => {
    // setInitialMessages(undefined) must still exist for new conversation flow.
    expect(source).toMatch(/setInitialMessages\(undefined\)/)
  })

  it('initialMessages state is passed down to V2ChatRuntime', () => {
    // The runtime invocation must receive the local state so deeplink messages render.
    expect(source).toMatch(/initialMessages=\{initialMessages\}/)
  })
})
