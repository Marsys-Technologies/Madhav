/**
 * mock_server.ts — local, in-process HTTP target for `--target=local` / `--dry-run`.
 *
 * This is what makes the harness self-verifiable without a live deployed connector
 * (Task 12's own constraint: no credential for `amjis-mcp`/`amjis-web` is available in
 * this session, and running against the real connector is explicitly Task 13's job,
 * not this one's). It stands up a tiny real `node:http` server on localhost and
 * exercises the harness's four measurement modes against it end-to-end (real sockets,
 * real latency, real concurrency), so the dry-run proves the HTTP client, percentile
 * math, and cache/QoS detection logic all work — not just that they compile.
 *
 * Two of its three behaviors are DELIBERATELY REAL production code, not simulated:
 *
 *  - QoS/backpressure: this server embeds the ACTUAL `QosDispatchQueue`
 *    (`platform/src/lib/retrieval/qos/dispatch_queue.ts`, W5 Lane L7 / plan §9.7 W-30)
 *    — the same class the live `consult` route dispatches tool-fetch work through via
 *    `getSharedQosDispatchQueue()`. Every request is submitted to a small, bounded
 *    instance of the real queue with an explicit `priorityClass`; a `QueueSaturatedError`
 *    becomes an honest 503 (`{ error: 'queue_saturated' }`), never a silently-thinned
 *    200. This lets the harness measure the real production honest-degradation rule,
 *    not a bespoke stand-in for it.
 *
 *  - The `served_from_cache` field on every response is the actual field name/shape
 *    carried on `ToolBundle` (`platform/src/lib/retrieval/shared_types.ts`), asserted
 *    throughout `platform/src/lib/cache/with_cache.ts`'s tests. The CACHING MECHANISM
 *    itself here is a small local Map keyed on the request body — a deliberately
 *    simple stand-in for the production two-tier (`with_cache.ts`) / precompiled-floor
 *    (`floor_cache.ts`) caches, good enough to drive real cache-hit/miss traffic
 *    through a real HTTP round trip without needing Redis or a DB connection. This one
 *    piece IS simulated — called out explicitly so nobody mistakes it for a claim that
 *    this harness measured the production cache's real hit rate.
 *
 * Concurrency-capacity degradation (compute latency growing with load, ahead of the
 * QoS queue's own admission) is also a simple simulated model — real production
 * degradation depends on DB pool size, sidecar load, etc. that only a live target can
 * exhibit; this harness's job is to prove the MEASUREMENT machinery is correct so it
 * can be pointed at that live target later (Task 13), not to predict the live target's
 * numbers.
 */
import { createServer, type Server } from 'node:http'
import { AddressInfo } from 'node:net'
import { QosDispatchQueue, QueueSaturatedError } from '@/lib/retrieval/qos/dispatch_queue'

export interface MockServerOptions {
  /** TTL for the simulated response cache, ms. */
  cacheTtlMs?: number
  /** Base simulated compute latency (ms) for a cache miss with zero contention. */
  baseComputeMs?: number
  /** Hard concurrency ceiling. Requests admitted past this into the compute path are
   *  refused (503 `overloaded`) rather than served — the "concurrency capacity" half
   *  of honest degradation (independent of the QoS queue, which governs its own
   *  submitted work separately). */
  hardConcurrencyCap?: number
  /** Real `QosDispatchQueue` sizing — deliberately small so a load-test-scale burst
   *  actually contends against it (mirrors this repo's own W5 battery rationale for
   *  picking a concurrency N large relative to a small keyspace/capacity). */
  qosConcurrency?: number
  qosMaxQueueDepth?: number
}

export interface MockServerHandle {
  readonly url: string
  readonly port: number
  close(): Promise<void>
}

interface CacheEntry {
  body: unknown
  expiresAt: number
}

/** Start the local mock target. Resolves once listening on an OS-assigned port. */
export async function startMockServer(opts: MockServerOptions = {}): Promise<MockServerHandle> {
  const cacheTtlMs = opts.cacheTtlMs ?? 5000
  const baseComputeMs = opts.baseComputeMs ?? 15
  const hardConcurrencyCap = opts.hardConcurrencyCap ?? 40
  const qos = new QosDispatchQueue({
    concurrency: opts.qosConcurrency ?? 6,
    maxQueueDepth: opts.qosMaxQueueDepth ?? 12,
  })

  const cache = new Map<string, CacheEntry>()
  let inFlight = 0

  function cacheKeyFor(body: unknown): string {
    // Stable enough for this mock: JSON.stringify with sorted keys at the top level.
    if (body === null || typeof body !== 'object') return JSON.stringify(body)
    const obj = body as Record<string, unknown>
    const sortedKeys = Object.keys(obj).sort()
    return JSON.stringify(Object.fromEntries(sortedKeys.map((k) => [k, obj[k]])))
  }

  async function compute(body: Record<string, unknown>): Promise<Record<string, unknown>> {
    // Simulated degradation: compute cost grows with current contention, modeling a
    // shared resource (DB/sidecar) getting slower under load rather than instantly
    // failing — the harness's concurrency-capacity mode is what's meant to observe this.
    const degradationFactor = 1 + inFlight / 8
    const delayMs = baseComputeMs * degradationFactor + Math.random() * 5
    await new Promise((r) => setTimeout(r, delayMs))
    return {
      served_from_cache: false,
      query_class: typeof body.family === 'string' ? body.family : 'unknown',
      result: 'ok',
    }
  }

  const server: Server = createServer((req, res) => {
    if (req.method !== 'POST') {
      res.writeHead(405, { 'content-type': 'application/json' })
      res.end(JSON.stringify({ error: 'method_not_allowed' }))
      return
    }

    const chunks: Buffer[] = []
    req.on('data', (c) => chunks.push(c))
    req.on('end', () => {
      void (async () => {
        let parsed: Record<string, unknown> = {}
        try {
          const raw = Buffer.concat(chunks).toString('utf-8')
          parsed = raw ? (JSON.parse(raw) as Record<string, unknown>) : {}
        } catch {
          res.writeHead(400, { 'content-type': 'application/json' })
          res.end(JSON.stringify({ error: 'bad_json' }))
          return
        }

        // ── W-28 simulated cache check ────────────────────────────────────────
        const key = cacheKeyFor(parsed)
        const cached = cache.get(key)
        if (cached && cached.expiresAt > Date.now()) {
          res.writeHead(200, { 'content-type': 'application/json' })
          res.end(JSON.stringify({ ...(cached.body as object), served_from_cache: true }))
          return
        }

        // ── W-29 hard concurrency ceiling (independent of the QoS queue) ───────
        if (inFlight >= hardConcurrencyCap) {
          res.writeHead(503, { 'content-type': 'application/json' })
          res.end(JSON.stringify({ error: 'overloaded', honest_refusal: true }))
          return
        }

        const principalId = typeof parsed.principalId === 'string' ? parsed.principalId : 'anon'
        const priorityClass = parsed.priorityClass === 'background' ? 'background' : 'interactive'

        inFlight++
        try {
          // ── W-30 real QosDispatchQueue admission ─────────────────────────────
          const body = await qos.submit({
            principalId,
            priorityClass,
            run: () => compute(parsed),
          })
          cache.set(key, { body, expiresAt: Date.now() + cacheTtlMs })
          res.writeHead(200, { 'content-type': 'application/json' })
          res.end(JSON.stringify(body))
        } catch (err) {
          if (err instanceof QueueSaturatedError) {
            res.writeHead(503, {
              'content-type': 'application/json',
            })
            res.end(
              JSON.stringify({
                error: 'queue_saturated',
                honest_refusal: true,
                priority_class: err.priorityClass,
                queue_depth: err.queueDepth,
              }),
            )
          } else {
            res.writeHead(500, { 'content-type': 'application/json' })
            res.end(JSON.stringify({ error: 'internal_error', message: String(err) }))
          }
        } finally {
          inFlight--
        }
      })()
    })
  })

  await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve))
  const addr = server.address() as AddressInfo
  const port = addr.port
  const url = `http://127.0.0.1:${port}`

  return {
    url,
    port,
    close: () =>
      new Promise<void>((resolve, reject) => {
        server.close((err) => (err ? reject(err) : resolve()))
      }),
  }
}
