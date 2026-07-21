import { describe, it, expect, beforeEach } from 'vitest'
import {
  QosDispatchQueue,
  QueueSaturatedError,
  getSharedQosDispatchQueue,
  __setSharedQosDispatchQueueForTests,
} from '../dispatch_queue'

function deferred<T = void>() {
  let resolve!: (v: T) => void
  let reject!: (e: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

describe('QosDispatchQueue — concurrency bound', () => {
  it('never runs more than `concurrency` tasks at once, under simulated concurrent load', async () => {
    const queue = new QosDispatchQueue({ concurrency: 3 })
    let inFlight = 0
    let maxObservedInFlight = 0
    const gates = Array.from({ length: 20 }, () => deferred<void>())

    const promises = gates.map((gate, i) =>
      queue.submit({
        principalId: 'p1',
        run: async () => {
          inFlight++
          maxObservedInFlight = Math.max(maxObservedInFlight, inFlight)
          await gate.promise
          inFlight--
          return i
        },
      })
    )

    // Release tasks in waves, verifying the in-flight ceiling holds throughout.
    for (const gate of gates) {
      await new Promise(r => setTimeout(r, 0))
      expect(inFlight).toBeLessThanOrEqual(3)
      gate.resolve()
    }
    const results = await Promise.all(promises)
    expect(results.sort((a, b) => a - b)).toEqual(gates.map((_, i) => i))
    expect(maxObservedInFlight).toBeLessThanOrEqual(3)
    expect(maxObservedInFlight).toBeGreaterThan(0)
  })
})

describe('QosDispatchQueue — priority ordering (interactive > background)', () => {
  it('dispatches interactive tasks ahead of background tasks under contention', async () => {
    const queue = new QosDispatchQueue({ concurrency: 1, maxBackgroundSkips: 1000 })
    const dispatchOrder: string[] = []
    const block = deferred<void>()

    // Occupy the single concurrency slot so everything else queues up first.
    const blocker = queue.submit({
      principalId: 'blocker',
      run: async () => {
        await block.promise
        return 'blocker'
      },
    })

    // Queue background tasks BEFORE interactive tasks — priority ordering must
    // still put interactive first once the slot frees, proving priority beats
    // arrival order.
    const bg = queue.submit({
      principalId: 'bg-caller',
      priorityClass: 'background',
      run: async () => {
        dispatchOrder.push('background')
        return 'bg'
      },
    })
    const interactive = queue.submit({
      principalId: 'int-caller',
      priorityClass: 'interactive',
      run: async () => {
        dispatchOrder.push('interactive')
        return 'int'
      },
    })

    block.resolve()
    await blocker
    await Promise.all([bg, interactive])

    expect(dispatchOrder[0]).toBe('interactive')
    expect(dispatchOrder[1]).toBe('background')
  })
})

describe('QosDispatchQueue — fairness bound (no starvation)', () => {
  it('guarantees a background task runs within maxBackgroundSkips interactive dispatches, under a sustained interactive stream', async () => {
    const MAX_SKIPS = 5
    const queue = new QosDispatchQueue({ concurrency: 1, maxBackgroundSkips: MAX_SKIPS, interactiveWeight: 1000 })
    const dispatchOrder: string[] = []
    let backgroundDispatchedAtInteractiveCount = -1

    const bgDone = queue.submit({
      principalId: 'bg-caller',
      priorityClass: 'background',
      run: async () => {
        dispatchOrder.push('background')
        backgroundDispatchedAtInteractiveCount = dispatchOrder.filter(x => x === 'interactive').length
        return 'bg'
      },
    })

    // Fire a continuous stream of interactive tasks — without the anti-
    // starvation force-promotion, `interactiveWeight: 1000` would let this
    // starve the background task indefinitely.
    const interactiveTasks: Promise<unknown>[] = []
    for (let i = 0; i < 40; i++) {
      interactiveTasks.push(
        queue.submit({
          principalId: 'int-caller',
          priorityClass: 'interactive',
          run: async () => {
            dispatchOrder.push('interactive')
            return i
          },
        })
      )
    }

    await Promise.all([bgDone, ...interactiveTasks])

    expect(dispatchOrder).toContain('background')
    // The bound is stated in terms of interactive dispatches skipped before
    // force-promotion — must not exceed the configured MAX_SKIPS.
    expect(backgroundDispatchedAtInteractiveCount).toBeLessThanOrEqual(MAX_SKIPS)
    expect(backgroundDispatchedAtInteractiveCount).toBeGreaterThanOrEqual(0)
  })
})

describe('QosDispatchQueue — per-principal fairness', () => {
  it('never dispatches the same principal twice in a row within a lane while another principal has work waiting, under concurrent multi-principal load', async () => {
    const queue = new QosDispatchQueue({ concurrency: 1 })
    const dispatchOrder: string[] = []

    const submissions: Promise<unknown>[] = []
    // Two principals each submit a burst of 10 tasks, interleaved arrival.
    for (let i = 0; i < 10; i++) {
      submissions.push(
        queue.submit({
          principalId: 'alice',
          run: async () => {
            dispatchOrder.push('alice')
          },
        })
      )
      submissions.push(
        queue.submit({
          principalId: 'bob',
          run: async () => {
            dispatchOrder.push('bob')
          },
        })
      )
    }

    await Promise.all(submissions)

    expect(dispatchOrder.length).toBe(20)
    // Core fairness property: no two consecutive dispatches are the same
    // principal while the other principal still had waiting work — verify by
    // checking there is no run of length >= 3 of the same principal (a run of
    // 2 can legitimately occur only when the OTHER principal's queue emptied,
    // which cannot happen here since both start with equal counts and this
    // guarantee alternates strictly when both are non-empty).
    let maxRun = 1
    let currentRun = 1
    for (let i = 1; i < dispatchOrder.length; i++) {
      if (dispatchOrder[i] === dispatchOrder[i - 1]) {
        currentRun++
        maxRun = Math.max(maxRun, currentRun)
      } else {
        currentRun = 1
      }
    }
    expect(maxRun).toBeLessThanOrEqual(1)
    expect(dispatchOrder.filter(p => p === 'alice').length).toBe(10)
    expect(dispatchOrder.filter(p => p === 'bob').length).toBe(10)
  })

  it('does not stall when only one principal has waiting work in a lane', async () => {
    const queue = new QosDispatchQueue({ concurrency: 2 })
    const results = await Promise.all(
      Array.from({ length: 5 }, (_, i) =>
        queue.submit({ principalId: 'solo', run: async () => i })
      )
    )
    expect(results.sort()).toEqual([0, 1, 2, 3, 4])
  })
})

describe('QosDispatchQueue — honest-degradation rule (queue/refuse, never thin quality)', () => {
  it('rejects new submissions with QueueSaturatedError once maxQueueDepth is hit, rather than silently truncating or dropping', async () => {
    const queue = new QosDispatchQueue({ concurrency: 1, maxQueueDepth: 2 })
    const block = deferred<void>()

    // Occupy the concurrency slot.
    const blocker = queue.submit({ principalId: 'p', run: () => block.promise })
    // Fill the queue to its depth limit.
    const q1 = queue.submit({ principalId: 'p', run: async () => 1 })
    const q2 = queue.submit({ principalId: 'p', run: async () => 2 })

    // A third queued submission exceeds maxQueueDepth (2 already queued) — must
    // be refused outright, not silently dropped or run with reduced fidelity.
    await expect(queue.submit({ principalId: 'p', run: async () => 3 })).rejects.toBeInstanceOf(
      QueueSaturatedError
    )

    block.resolve()
    await blocker
    expect(await q1).toBe(1)
    expect(await q2).toBe(2)
  })

  it('runs every admitted task to full completion — never partially executes or thins a result', async () => {
    const queue = new QosDispatchQueue({ concurrency: 2 })
    const result = await queue.submit({
      principalId: 'p',
      run: async () => {
        const parts: number[] = []
        for (let i = 0; i < 5; i++) {
          await new Promise(r => setTimeout(r, 0))
          parts.push(i)
        }
        return parts
      },
    })
    expect(result).toEqual([0, 1, 2, 3, 4])
  })
})

describe('QosDispatchQueue — stats()', () => {
  it('reports inFlight and per-lane queued counts', async () => {
    const queue = new QosDispatchQueue({ concurrency: 1 })
    const block = deferred<void>()
    const blocker = queue.submit({ principalId: 'p', run: () => block.promise })
    const queuedInteractive = queue.submit({ principalId: 'p2', run: async () => 1 })
    const queuedBackground = queue.submit({ principalId: 'p3', priorityClass: 'background', run: async () => 2 })

    await new Promise(r => setTimeout(r, 0))
    const stats = queue.stats()
    expect(stats.inFlight).toBe(1)
    expect(stats.interactiveQueued).toBe(1)
    expect(stats.backgroundQueued).toBe(1)

    block.resolve()
    await Promise.all([blocker, queuedInteractive, queuedBackground])
  })
})

describe('getSharedQosDispatchQueue', () => {
  beforeEach(() => {
    __setSharedQosDispatchQueueForTests(undefined)
  })

  it('returns the same instance across calls (process-wide shared queue)', () => {
    const a = getSharedQosDispatchQueue()
    const b = getSharedQosDispatchQueue()
    expect(a).toBe(b)
  })

  it('can be swapped for a test-controlled instance', () => {
    const custom = new QosDispatchQueue({ concurrency: 1 })
    __setSharedQosDispatchQueueForTests(custom)
    expect(getSharedQosDispatchQueue()).toBe(custom)
  })
})
