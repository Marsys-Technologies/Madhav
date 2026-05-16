/**
 * abort_propagation — β7 structural + logic tests.
 *
 * Verifies:
 * - QueryRequest.abortSignal field exists in adapters/types.ts
 * - StreamTextOptions.abortSignal field exists in adapters/providers/base.ts
 * - All 5 provider adapters forward abortSignal in prepareRequest
 * - All 5 provider stream() loops check req.abortSignal?.aborted
 * - panel_strategy passes abortSignal to streamAdapterRaw
 * - panel/member_runner passes abortSignal to runAdapter
 * - route.ts has early-exit guard in tool fetch mapper
 * - AbortController signal propagation shape (unit logic)
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

const src = (rel: string) => readFileSync(join(process.cwd(), rel), 'utf-8')

const types = src('src/lib/adapters/types.ts')
const base = src('src/lib/adapters/providers/base.ts')
const anthropic = src('src/lib/adapters/providers/adapter_anthropic.ts')
const gemini = src('src/lib/adapters/providers/adapter_gemini.ts')
const openai = src('src/lib/adapters/providers/adapter_openai.ts')
const deepseek = src('src/lib/adapters/providers/adapter_deepseek.ts')
const nim = src('src/lib/adapters/providers/adapter_nim.ts')
const panel = src('src/lib/synthesis/panel_strategy.ts')
const memberRunner = src('src/lib/synthesis/panel/member_runner.ts')
const route = src('src/app/api/chat/consume/route.ts')

// ─── Type definitions ─────────────────────────────────────────────────────────

describe('QueryRequest.abortSignal', () => {
  it('is declared in adapters/types.ts', () => {
    expect(types).toContain('abortSignal?: AbortSignal')
  })
})

describe('StreamTextOptions.abortSignal', () => {
  it('is declared in adapters/providers/base.ts', () => {
    expect(base).toContain('abortSignal?: AbortSignal')
  })
})

// ─── prepareRequest forwarding ────────────────────────────────────────────────

describe('adapter prepareRequest — abortSignal forwarding', () => {
  it('anthropic forwards abortSignal', () => {
    expect(anthropic).toContain('req.abortSignal')
    expect(anthropic).toContain('abortSignal: req.abortSignal')
  })

  it('gemini forwards abortSignal', () => {
    expect(gemini).toContain('req.abortSignal')
    expect(gemini).toContain('abortSignal: req.abortSignal')
  })

  it('openai forwards abortSignal', () => {
    expect(openai).toContain('req.abortSignal')
    expect(openai).toContain('abortSignal: req.abortSignal')
  })

  it('deepseek forwards abortSignal', () => {
    expect(deepseek).toContain('req.abortSignal')
    expect(deepseek).toContain('abortSignal: req.abortSignal')
  })

  it('nim forwards abortSignal', () => {
    expect(nim).toContain('req.abortSignal')
    expect(nim).toContain('abortSignal: req.abortSignal')
  })
})

// ─── stream() loop abort guards ───────────────────────────────────────────────

describe('adapter stream() — for-await abort guard', () => {
  it('anthropic stream loop checks aborted', () => {
    expect(anthropic).toContain("req.abortSignal?.aborted")
  })

  it('gemini stream loop checks aborted', () => {
    expect(gemini).toContain("req.abortSignal?.aborted")
  })

  it('openai stream loop checks aborted', () => {
    expect(openai).toContain("req.abortSignal?.aborted")
  })

  it('deepseek stream loop checks aborted', () => {
    expect(deepseek).toContain("req.abortSignal?.aborted")
  })

  it('nim stream loop checks aborted', () => {
    expect(nim).toContain("req.abortSignal?.aborted")
  })
})

// ─── Panel path ───────────────────────────────────────────────────────────────

describe('panel_strategy — abortSignal propagation', () => {
  it('passthrough streamAdapterRaw call includes abortSignal', () => {
    expect(panel).toContain('request.abortSignal')
    expect(panel).toContain('abortSignal: request.abortSignal')
  })
})

describe('panel/member_runner — abortSignal propagation', () => {
  it('runAdapter call includes abortSignal', () => {
    expect(memberRunner).toContain('request.abortSignal')
    expect(memberRunner).toContain('abortSignal: request.abortSignal')
  })
})

// ─── Route tool fetch early-exit ─────────────────────────────────────────────

describe('route.ts — tool fetch abort early-exit', () => {
  it('has early-exit guard before tool execution', () => {
    expect(route).toContain('request.signal.aborted')
  })

  it('early-exit returns null (so Promise.all can settle)', () => {
    const guardLine = route
      .split('\n')
      .find(l => l.includes('request.signal.aborted'))
    expect(guardLine).toBeDefined()
    expect(guardLine).toContain('return null')
  })
})

// ─── AbortController unit logic ───────────────────────────────────────────────

describe('AbortController abort propagation logic', () => {
  it('aborted signal is detectable via signal.aborted', () => {
    const controller = new AbortController()
    expect(controller.signal.aborted).toBe(false)
    controller.abort()
    expect(controller.signal.aborted).toBe(true)
  })

  it('abort reason is accessible post-abort', () => {
    const controller = new AbortController()
    controller.abort(new Error('stream-cancelled'))
    expect(controller.signal.aborted).toBe(true)
    expect(controller.signal.reason).toBeInstanceOf(Error)
  })

  it('for-await loop breaks when signal is pre-aborted', async () => {
    const controller = new AbortController()
    controller.abort()

    async function* gen() {
      yield 1
      yield 2
      yield 3
    }

    const collected: number[] = []
    for await (const x of gen()) {
      if (controller.signal.aborted) break
      collected.push(x)
    }
    expect(collected).toHaveLength(0)
  })

  it('for-await loop breaks mid-stream on abort', async () => {
    const controller = new AbortController()

    async function* gen() {
      yield 1
      yield 2
      controller.abort()
      yield 3
    }

    const collected: number[] = []
    for await (const x of gen()) {
      if (controller.signal.aborted) break
      collected.push(x)
    }
    expect(collected).toEqual([1, 2])
  })

  it('optional chaining on absent signal does not throw', () => {
    function maybeAborted(signal?: AbortSignal): boolean {
      return signal?.aborted ?? false
    }
    expect(maybeAborted(undefined)).toBe(false)
    const c = new AbortController()
    expect(maybeAborted(c.signal)).toBe(false)
    c.abort()
    expect(maybeAborted(c.signal)).toBe(true)
  })
})
