/**
 * E-S8: iteration-cap.test.ts
 *
 * Verifies the 8-iteration cap safety in the agentic loop:
 * - MAX_ITERATIONS=8 constant is declared
 * - AgenticLoopCapExceeded is thrown at MAX_ITERATIONS
 * - Error message references the cap value
 * - Per-provider cap override via maxIterations config works
 */

import { describe, it, expect } from 'vitest'
import {
  MAX_ITERATIONS,
  AgenticLoopCapExceeded,
  checkIterationCap,
  createLoopState,
  ANTHROPIC_LOOP_CONFIG,
  GOOGLE_LOOP_CONFIG,
  OPENAI_LOOP_CONFIG,
} from '../../src/lib/synthesis/agentic_loop'

describe('E-S8: MAX_ITERATIONS constant', () => {
  it('MAX_ITERATIONS is 8', () => {
    expect(MAX_ITERATIONS).toBe(8)
  })
})

describe('E-S8: AgenticLoopCapExceeded error shape', () => {
  it('is an Error subclass', () => {
    const err = new AgenticLoopCapExceeded(8)
    expect(err).toBeInstanceOf(Error)
    expect(err).toBeInstanceOf(AgenticLoopCapExceeded)
  })

  it('has name=AgenticLoopCapExceeded', () => {
    const err = new AgenticLoopCapExceeded(8)
    expect(err.name).toBe('AgenticLoopCapExceeded')
  })

  it('records the iterations count', () => {
    const err = new AgenticLoopCapExceeded(8)
    expect(err.iterations).toBe(8)
  })

  it('message mentions MAX_ITERATIONS', () => {
    const err = new AgenticLoopCapExceeded(8)
    expect(err.message).toContain('MAX_ITERATIONS')
  })

  it('message mentions the iteration count', () => {
    const err = new AgenticLoopCapExceeded(8)
    expect(err.message).toContain('8')
  })
})

describe('E-S8: checkIterationCap — throw on overflow', () => {
  it('does NOT throw at iteration 7 (one below cap)', () => {
    const state = createLoopState(ANTHROPIC_LOOP_CONFIG)
    state.iterations = MAX_ITERATIONS - 1
    expect(() => checkIterationCap(state)).not.toThrow()
  })

  it('throws at iteration 8 (= MAX_ITERATIONS)', () => {
    const state = createLoopState(ANTHROPIC_LOOP_CONFIG)
    state.iterations = MAX_ITERATIONS
    expect(() => checkIterationCap(state)).toThrow(AgenticLoopCapExceeded)
  })

  it('throws at iteration 9 (> MAX_ITERATIONS)', () => {
    const state = createLoopState(ANTHROPIC_LOOP_CONFIG)
    state.iterations = MAX_ITERATIONS + 1
    expect(() => checkIterationCap(state)).toThrow(AgenticLoopCapExceeded)
  })

  it('does NOT throw at iteration 0', () => {
    const state = createLoopState(ANTHROPIC_LOOP_CONFIG)
    expect(state.iterations).toBe(0)
    expect(() => checkIterationCap(state)).not.toThrow()
  })
})

describe('E-S8: per-provider cap override', () => {
  it('respects custom maxIterations in config', () => {
    const state = createLoopState({
      ...GOOGLE_LOOP_CONFIG,
      maxIterations: 4, // lower cap for testing
    })
    state.iterations = 3
    expect(() => checkIterationCap(state)).not.toThrow()
    state.iterations = 4
    expect(() => checkIterationCap(state)).toThrow(AgenticLoopCapExceeded)
  })

  it('uses MAX_ITERATIONS default when no override', () => {
    const state = createLoopState(OPENAI_LOOP_CONFIG) // no maxIterations in config
    state.iterations = MAX_ITERATIONS
    expect(() => checkIterationCap(state)).toThrow(AgenticLoopCapExceeded)
  })
})

describe('E-S8: cap exceeded error is catchable at route layer', () => {
  it('thrown error has correct instanceof chain for route.ts to catch', () => {
    const state = createLoopState(ANTHROPIC_LOOP_CONFIG)
    state.iterations = MAX_ITERATIONS
    let caught: unknown = null
    try {
      checkIterationCap(state)
    } catch (err) {
      caught = err
    }
    expect(caught).not.toBeNull()
    expect(caught instanceof AgenticLoopCapExceeded).toBe(true)
    expect(caught instanceof Error).toBe(true)
    if (caught instanceof AgenticLoopCapExceeded) {
      expect(caught.iterations).toBe(MAX_ITERATIONS)
    }
  })
})
