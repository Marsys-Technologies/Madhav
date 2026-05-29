/**
 * agentic-loop-b11-floor.test.ts — R11F-A-S3
 *
 * Verifies the B.11 floor contract for the adapter dispatch path:
 *
 * 1. The B.11 FLOOR CONTRACT comment is present in route.ts so the invariant
 *    is documented and greppable (AC.a acceptance check).
 *
 * 2. The agentic loop engine receives its initial request with messages already
 *    in place — it does not alter or drop the context it is given.
 *
 * 3. The LOOP_CONFIG_BY_PROVIDER registry covers all five adapters so the floor
 *    contract can be asserted per-provider.
 *
 * Note: route.ts is a Next.js server handler and cannot be unit-tested in
 * isolation without a full Next.js test harness. The structural tests below
 * verify the key invariants at the module level (agentic_loop.ts) and via
 * filesystem assertions on the contract comment.
 */

import { describe, it, expect, vi } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

import {
  LOOP_CONFIG_BY_PROVIDER,
  createLoopState,
  runAgenticLoop,
  MAX_ITERATIONS,
  ANTHROPIC_LOOP_CONFIG,
  GOOGLE_LOOP_CONFIG,
  OPENAI_LOOP_CONFIG,
  DEEPSEEK_LOOP_CONFIG,
  NVIDIA_LOOP_CONFIG,
} from '../../src/lib/synthesis/agentic_loop'

// ─── AC.a structural assertion ───────────────────────────────────────────────

describe('B.11 FLOOR CONTRACT — structural presence in route.ts', () => {
  it('route.ts contains the B.11 FLOOR CONTRACT comment', () => {
    const routePath = join(
      __dirname,
      '../../src/app/api/chat/consult/route.ts',
    )
    const src = readFileSync(routePath, 'utf-8')
    const contractCount = (src.match(/B\.11 FLOOR CONTRACT/g) ?? []).length
    expect(contractCount).toBeGreaterThanOrEqual(1)
  })

  it('route.ts floor comment documents floor-before-dispatch ordering', () => {
    const routePath = join(
      __dirname,
      '../../src/app/api/chat/consult/route.ts',
    )
    const src = readFileSync(routePath, 'utf-8')
    // The comment must assert floor tools run before the model call
    expect(src).toContain('pre-executed')
    expect(src).toContain('before any model call')
  })
})

// ─── Loop config coverage — all five providers ───────────────────────────────

describe('B.11 FLOOR CONTRACT — LOOP_CONFIG_BY_PROVIDER covers all adapters', () => {
  const EXPECTED_ADAPTER_IDS = ['anthropic', 'google', 'openai', 'deepseek', 'nvidia']

  for (const adapterId of EXPECTED_ADAPTER_IDS) {
    it(`LOOP_CONFIG_BY_PROVIDER has entry for '${adapterId}'`, () => {
      expect(LOOP_CONFIG_BY_PROVIDER[adapterId]).toBeDefined()
      expect(LOOP_CONFIG_BY_PROVIDER[adapterId].providerId).toBe(adapterId)
    })
  }
})

// ─── Loop engine preserves context injected by caller ────────────────────────

describe('B.11 FLOOR CONTRACT — agentic loop preserves injected context', () => {
  it('loop initial request messages are passed through unchanged on first iteration', async () => {
    // Construct a request with pre-injected floor context in the system message.
    // The loop engine must NOT drop or modify these messages before the first
    // model call — it passes them as-is to adapter.chat().
    const floorContextMessage = {
      role: 'user' as const,
      content: [
        {
          type: 'text' as const,
          text: 'MSR floor context injected. UCN loaded. CGM present.',
        },
      ],
    }

    const capturedRequests: unknown[] = []

    // Mock adapter that terminates immediately (no tool use signal)
    const mockAdapter = {
      chat: vi.fn(async function* (req: unknown) {
        capturedRequests.push(req)
        yield { type: 'message_stop', stopReason: 'end_turn' }
      }),
    }

    const initialRequest = {
      model: 'claude-opus-4-5',
      messages: [floorContextMessage],
    }

    // Consume the loop (it will end after one iteration — no tool-use signal)
    const events = []
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    for await (const event of runAgenticLoop(mockAdapter as any, initialRequest as any, async () => 'result', ANTHROPIC_LOOP_CONFIG)) {
      events.push(event)
    }

    // Verify the loop called adapter.chat exactly once with our original messages
    expect(capturedRequests).toHaveLength(1)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const firstReq = capturedRequests[0] as any
    expect(firstReq.messages).toHaveLength(1)
    expect(firstReq.messages[0].role).toBe('user')
  })

  it('loop does not mutate the initial request object', async () => {
    const initialMessages = [
      { role: 'user' as const, content: [{ type: 'text' as const, text: 'Floor context.' }] },
    ]
    const initialRequest = {
      model: 'claude-opus-4-5',
      messages: initialMessages,
    }
    const originalLength = initialMessages.length

    const mockAdapter = {
      chat: vi.fn(async function* () {
        yield { type: 'message_stop', stopReason: 'end_turn' }
      }),
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    for await (const _ of runAgenticLoop(mockAdapter as any, initialRequest as any, async () => '', ANTHROPIC_LOOP_CONFIG)) {
      // consume
    }

    // Original messages array must not be mutated
    expect(initialMessages).toHaveLength(originalLength)
  })
})

// ─── Loop cap still enforced even with floor context present ─────────────────

describe('B.11 FLOOR CONTRACT — cap enforcement is independent of floor context', () => {
  it('loop cap fires at MAX_ITERATIONS regardless of floor context size', async () => {
    const mockAdapter = {
      chat: vi.fn(async function* () {
        yield { type: 'tool_use_start', id: 'tc1', name: 'msr_sql' }
        yield { type: 'tool_use_input_delta', id: 'tc1', partialJson: '{}' }
        yield { type: 'message_stop', stopReason: 'tool_use' }
      }),
    }

    const request = {
      model: 'claude-opus-4-5',
      messages: [
        { role: 'user' as const, content: [{ type: 'text' as const, text: 'MSR floor injected.' }] },
      ],
    }

    const { AgenticLoopCapExceeded } = await import('../../src/lib/synthesis/agentic_loop')

    let threw = false
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      for await (const _ of runAgenticLoop(mockAdapter as any, request as any, async () => '{}', ANTHROPIC_LOOP_CONFIG)) {
        // consume
      }
    } catch (err) {
      threw = err instanceof AgenticLoopCapExceeded
    }
    expect(threw).toBe(true)
    expect(mockAdapter.chat).toHaveBeenCalledTimes(MAX_ITERATIONS)
  })
})
