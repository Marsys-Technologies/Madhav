/**
 * dispatch_queue.ts — QoS priority classes + fairness + job queue (W5 Lane L7).
 * ================================================================================
 * `RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md` §9.7 W-30: "priority classes (interactive
 * > background), per-principal fairness, prashna_ask job queue with backpressure
 * (feeds the OT-2 ruling), and the honest-degradation rule — queue/refuse, never
 * thin quality."
 *
 * AXIS INVESTIGATION (per this lane's brief — worth recording, not just asserting):
 * the natural candidate axis was the W5 L2 `mcp_profile.ts` full/compact/consult
 * OAuth-scope axis (already landed on `impl/wave-5`, see that file's banner) — a
 * caller's ENTITLEMENT to a tool surface. Rejected as the QoS axis: W-30's own text
 * names the axis "interactive > background", which is a REQUEST-shape classification
 * (is a human waiting synchronously on this call right now, or is this an
 * async/batch/background dispatch — e.g. a future prashna_ask job, a bulk export, a
 * scheduled sweep), not a caller-identity/entitlement classification. A `consult`-
 * profile OAuth caller can easily be a live, latency-sensitive interactive session
 * (a third-party MCP connector's end user waiting on a reply) — conflating "low
 * entitlement" with "low QoS priority" would incorrectly de-prioritize legitimate
 * interactive callers purely for holding a narrower tool scope, which is an
 * entitlement question, not a scheduling question. The two axes are orthogonal and
 * compose: this module takes an explicit `priorityClass` per submitted task
 * (defaulting to `interactive`, the safe default for the live consult path), and a
 * caller's mcp_profile is irrelevant input to it. `per-principal fairness` is a
 * THIRD, also-orthogonal axis (which caller submitted the task) — implemented here
 * as its own bounded-unfairness guarantee, independent of priority class.
 *
 * WHAT THIS IS: a generic, in-process, priority + fair-share bounded-concurrency
 * dispatch queue for async tool-call work. It is the "job queue" named in this
 * lane's scope line, in its buildable-now form.
 *
 * WHAT THIS IS NOT (named residual, deferred to W6 by design, not by oversight):
 * `prashna_ask`'s own full job-handle contract (C-1 signature: job creation,
 * poll/notification semantics, cost caps, NO-LEAKAGE arm-2 exclusion) is explicitly
 * W6 scope per `RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §E W6` ("prashna_ask full
 * contract (C-1 signature, job-handle + notifications, cost caps ...)"), and W5 L2's
 * own landed lane note independently reached the same line ("`prashna_ask` ... is W6
 * scope"). Building that contract here would be scope creep ahead of its own wave.
 * What W5 CAN and does build: the general backpressure-aware dispatch substrate a
 * future `prashna_ask` job-handle layer can submit `priorityClass: 'background'`
 * work to, without this module knowing anything about prashna_ask's shape.
 *
 * HONEST-DEGRADATION RULE (W-30): this queue never thins a task's quality to fit
 * capacity — a task either runs to completion via `run()` or is queued/backpressured
 * (see `QueueSaturatedError`). There is no silent truncation of an in-flight task.
 */

// ── Types ─────────────────────────────────────────────────────────────────────

/** The two QoS priority classes named in plan §9.7 W-30. */
export type QosPriorityClass = 'interactive' | 'background'

export interface QosTaskSubmission<T> {
  /** Caller/session identity for the per-principal fairness guarantee. Any stable
   *  string works (user uid, OAuth client id, API key id, ...). */
  principalId: string
  /** Defaults to 'interactive' — the safe default for the live consult path;
   *  callers doing bulk/scheduled/async work must opt IN to 'background'. */
  priorityClass?: QosPriorityClass
  /** The actual async work. Not started until the queue admits it. */
  run: () => Promise<T>
}

export interface QosDispatchQueueOptions {
  /** Max tasks in flight at once, across both priority classes. */
  concurrency?: number
  /** Anti-starvation bound (W-30 "no priority class can starve another"): once a
   *  waiting background task has been passed over this many times in favor of
   *  interactive dispatches, it is force-promoted to the front of the line ahead
   *  of every interactive task, guaranteeing a hard ceiling on its wait measured
   *  in "interactive dispatches skipped", not an unbounded queue depth. */
  maxBackgroundSkips?: number
  /** Weighted round robin: how many interactive dispatches happen per background
   *  dispatch when both lanes have ready work and neither is starved. */
  interactiveWeight?: number
  backgroundWeight?: number
  /** Honest-degradation rule (W-30 "queue/refuse, never thin quality"): once this
   *  many tasks are queued (not yet dispatched), `submit()` rejects new work with
   *  `QueueSaturatedError` instead of accepting unbounded backlog. `undefined` =
   *  unbounded queueing (still bounded CONCURRENCY of in-flight work). */
  maxQueueDepth?: number
}

/** Thrown by `submit()` when `maxQueueDepth` is configured and exceeded — the
 *  "refuse" half of the honest-degradation rule (queue/refuse, never thin quality). */
export class QueueSaturatedError extends Error {
  constructor(public readonly priorityClass: QosPriorityClass, public readonly queueDepth: number) {
    super(`QoS dispatch queue saturated: ${queueDepth} tasks already queued in '${priorityClass}' lane`)
    this.name = 'QueueSaturatedError'
  }
}

interface QueuedTask<T> {
  principalId: string
  priorityClass: QosPriorityClass
  run: () => Promise<T>
  resolve: (v: T) => void
  reject: (e: unknown) => void
  enqueuedAtMs: number
  /** Number of times an interactive dispatch happened while this task waited.
   *  Drives the anti-starvation force-promotion. */
  skipCount: number
}

export interface QosDispatchStats {
  inFlight: number
  interactiveQueued: number
  backgroundQueued: number
}

const DEFAULT_CONCURRENCY = 24
const DEFAULT_MAX_BACKGROUND_SKIPS = 8
const DEFAULT_INTERACTIVE_WEIGHT = 4
const DEFAULT_BACKGROUND_WEIGHT = 1

/**
 * Priority-class + per-principal-fair-share bounded-concurrency dispatch queue.
 *
 * Fairness guarantees, precisely stated (so they're testable, not just claimed):
 *  1. PRIORITY BOUND: a `background` task is dispatched within `maxBackgroundSkips`
 *     interactive dispatches of becoming the oldest background task, regardless of
 *     how much interactive work keeps arriving — it cannot be starved indefinitely.
 *  2. PER-PRINCIPAL BOUND: within a single priority lane, no principal is selected
 *     for dispatch on two consecutive picks from that lane while a DIFFERENT
 *     principal has work waiting in the same lane — one bursty principal cannot
 *     monopolize a lane while peers wait.
 *  3. CONCURRENCY BOUND: `inFlight` never exceeds `concurrency`.
 */
export class QosDispatchQueue {
  private readonly concurrency: number
  private readonly maxBackgroundSkips: number
  private readonly interactiveWeight: number
  private readonly backgroundWeight: number
  private readonly maxQueueDepth?: number

  private inFlight = 0
  private readonly interactiveQueue: QueuedTask<unknown>[] = []
  private readonly backgroundQueue: QueuedTask<unknown>[] = []
  /** Weighted-round-robin state: which lane the current mini-cycle favors, and
   *  how many dispatches have happened from it so far in this cycle. */
  private wrrPhase: QosPriorityClass = 'interactive'
  private wrrPhaseCount = 0
  private lastInteractivePrincipal: string | null = null
  private lastBackgroundPrincipal: string | null = null

  constructor(opts: QosDispatchQueueOptions = {}) {
    this.concurrency = opts.concurrency ?? DEFAULT_CONCURRENCY
    this.maxBackgroundSkips = opts.maxBackgroundSkips ?? DEFAULT_MAX_BACKGROUND_SKIPS
    this.interactiveWeight = opts.interactiveWeight ?? DEFAULT_INTERACTIVE_WEIGHT
    this.backgroundWeight = opts.backgroundWeight ?? DEFAULT_BACKGROUND_WEIGHT
    this.maxQueueDepth = opts.maxQueueDepth
  }

  /** Submit a unit of work. Resolves/rejects with the task's own outcome once
   *  dispatched and run — never silently drops or thins a task's result. */
  submit<T>(task: QosTaskSubmission<T>): Promise<T> {
    const priorityClass = task.priorityClass ?? 'interactive'
    const lane = priorityClass === 'background' ? this.backgroundQueue : this.interactiveQueue
    if (this.maxQueueDepth !== undefined && lane.length >= this.maxQueueDepth) {
      return Promise.reject(new QueueSaturatedError(priorityClass, lane.length))
    }
    return new Promise<T>((resolve, reject) => {
      const queued: QueuedTask<T> = {
        principalId: task.principalId,
        priorityClass,
        run: task.run,
        resolve,
        reject,
        enqueuedAtMs: Date.now(),
        skipCount: 0,
      }
      lane.push(queued as QueuedTask<unknown>)
      this.pump()
    })
  }

  stats(): QosDispatchStats {
    return {
      inFlight: this.inFlight,
      interactiveQueued: this.interactiveQueue.length,
      backgroundQueued: this.backgroundQueue.length,
    }
  }

  private pump(): void {
    while (this.inFlight < this.concurrency) {
      const next = this.selectNext()
      if (!next) break
      this.inFlight++
      next
        .run()
        .then(
          v => {
            this.inFlight--
            next.resolve(v)
          },
          e => {
            this.inFlight--
            next.reject(e)
          }
        )
        .finally(() => this.pump())
    }
  }

  private selectNext(): QueuedTask<unknown> | undefined {
    // Guarantee 1 (priority bound): a background task starved past the bound is
    // force-promoted ahead of everything, including fresh interactive work.
    const starvedIdx = this.backgroundQueue.findIndex(t => t.skipCount >= this.maxBackgroundSkips)
    if (starvedIdx !== -1) {
      const [t] = this.backgroundQueue.splice(starvedIdx, 1)
      this.lastBackgroundPrincipal = t.principalId
      // A forced promotion resets the weighted-round-robin cycle so it starts
      // fresh rather than compounding against the interactive lane.
      this.wrrPhase = 'interactive'
      this.wrrPhaseCount = 0
      return t
    }

    if (this.interactiveQueue.length === 0 && this.backgroundQueue.length === 0) return undefined
    if (this.interactiveQueue.length === 0) return this.dequeueFairShare(this.backgroundQueue, false)
    if (this.backgroundQueue.length === 0) return this.dequeueFairShare(this.interactiveQueue, true)

    // Weighted round robin between the two non-empty lanes: dispatch up to
    // `interactiveWeight` interactive tasks, then up to `backgroundWeight`
    // background tasks, then repeat.
    if (this.wrrPhase === 'interactive') {
      if (this.wrrPhaseCount >= this.interactiveWeight) {
        this.wrrPhase = 'background'
        this.wrrPhaseCount = 0
      } else {
        this.wrrPhaseCount++
        for (const t of this.backgroundQueue) t.skipCount++
        return this.dequeueFairShare(this.interactiveQueue, true)
      }
    }
    // wrrPhase === 'background' here (either already was, or just switched above).
    this.wrrPhaseCount++
    const dispatched = this.dequeueFairShare(this.backgroundQueue, false)
    if (this.wrrPhaseCount >= this.backgroundWeight) {
      this.wrrPhase = 'interactive'
      this.wrrPhaseCount = 0
    }
    return dispatched
  }

  /** Guarantee 2 (per-principal bound): avoid repeating the immediately-prior
   *  dispatched principal in this lane whenever a different principal has work
   *  waiting, without needing a full round-robin index over a mutating array. */
  private dequeueFairShare(lane: QueuedTask<unknown>[], isInteractive: boolean): QueuedTask<unknown> | undefined {
    if (lane.length === 0) return undefined
    const last = isInteractive ? this.lastInteractivePrincipal : this.lastBackgroundPrincipal
    let idx = lane.findIndex(t => t.principalId !== last)
    if (idx === -1) idx = 0
    const [task] = lane.splice(idx, 1)
    if (isInteractive) this.lastInteractivePrincipal = task.principalId
    else this.lastBackgroundPrincipal = task.principalId
    return task
  }
}

/**
 * Process-wide default queue for the live consult tool-fetch dispatch path
 * (`platform/src/app/api/chat/consult/route.ts`). A single shared instance so
 * fairness/priority is enforced ACROSS concurrent HTTP requests (the real
 * contention scenario — a single request's own ≤10ish tool calls rarely bump
 * into `DEFAULT_CONCURRENCY`), not just within one request's own fan-out.
 */
let sharedQueue: QosDispatchQueue | undefined

export function getSharedQosDispatchQueue(): QosDispatchQueue {
  if (!sharedQueue) sharedQueue = new QosDispatchQueue()
  return sharedQueue
}

/** Test-only: replace the shared queue (e.g. with a tiny-concurrency instance)
 *  or reset it to a fresh default. Never call from production code paths. */
export function __setSharedQosDispatchQueueForTests(queue: QosDispatchQueue | undefined): void {
  sharedQueue = queue
}
