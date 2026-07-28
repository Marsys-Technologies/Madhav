#!/usr/bin/env tsx
/**
 * Paripraśna replay harness — server.
 *
 * A tiny, dependency-free (Node `http` only) server with two jobs:
 *
 *  1. `GET /stream?fixture=<name>[&violate=<key>]` — replays a recorded
 *     fixture as a real SSE (`text/event-stream`) response, honoring the
 *     fixture's timing (`delay_ms`), transport-fragmentation
 *     (`chunk_bytes`), and abrupt-disconnect (`abrupt_end_after_seq`)
 *     directives. `violate` is passed through completely inert to the
 *     server — it is forwarded to the client harness (which reads it off
 *     `location.search`) so the CLIENT can seed a deliberate rendering
 *     violation for the red-then-green gate proofs. The server itself never
 *     alters event content based on `violate`.
 *
 *  2. Static file serving for the test-only DOM harness at
 *     `tests/pariprashna/harness/public/**` — this is NOT part of the real
 *     product; it exists solely so Playwright has something to point a
 *     browser at before C-1's real renderer lands.
 *
 * Run: `npm run pariprashna:replay-server` (used as Playwright's webServer
 * for `tests/pariprashna/playwright.config.ts`).
 */
import { createServer, type IncomingMessage, type ServerResponse } from 'http'
import { readFile, readdir } from 'fs/promises'
import { existsSync } from 'fs'
import { extname, join, normalize } from 'path'
import type { FixtureSpec } from './fixture_types'

const PORT = Number(process.env.PARIPRASHNA_REPLAY_PORT ?? 4795)
const FIXTURES_DIR = join(__dirname, '..', '..', 'tests', 'pariprashna', 'fixtures')
const HARNESS_PUBLIC_DIR = join(__dirname, '..', '..', 'tests', 'pariprashna', 'harness', 'public')
const REDUCER_PATH = join(__dirname, '..', '..', 'tests', 'pariprashna', 'reducer', 'reducer.mjs')

const MIME: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.mjs': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
}

async function loadFixture(name: string): Promise<FixtureSpec | null> {
  const path = join(FIXTURES_DIR, `${name}.json`)
  // Guard against path traversal via the query param.
  if (!normalize(path).startsWith(FIXTURES_DIR)) return null
  if (!existsSync(path)) return null
  const raw = await readFile(path, 'utf8')
  return JSON.parse(raw) as FixtureSpec
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/** Write `payload` to the response, optionally in `chunkBytes`-sized pieces
 *  instead of one write() call — simulates a fragmenting transport so the
 *  client's SSE frame-reassembly is genuinely exercised across many small
 *  chunks. Deliberately does NOT add a per-chunk delay: the fixture's own
 *  `delay_ms` already controls per-EVENT pacing, and adding real wall-clock
 *  latency per BYTE as well (as an earlier version did, at 1ms/byte) made a
 *  ~100-byte-per-event, 78-event fixture take 10+ real seconds to replay for
 *  no benefit — frame-reassembly robustness only requires that the bytes
 *  arrive as separate writes, not that they arrive slowly. */
async function writeChunked(res: ServerResponse, payload: string, chunkBytes?: number): Promise<void> {
  if (!chunkBytes || chunkBytes <= 0 || chunkBytes >= payload.length) {
    res.write(payload)
    return
  }
  const buf = Buffer.from(payload, 'utf8')
  for (let i = 0; i < buf.length; i += chunkBytes) {
    res.write(buf.subarray(i, i + chunkBytes))
  }
  // Yield once after the whole frame so Node actually flushes the writes as
  // distinct chunks on the wire instead of the OS/runtime coalescing a tight
  // synchronous loop into one packet.
  await sleep(0)
}

async function handleStream(req: IncomingMessage, res: ServerResponse, url: URL): Promise<void> {
  const fixtureName = url.searchParams.get('fixture')
  if (!fixtureName) {
    res.writeHead(400, { 'content-type': 'application/json' })
    res.end(JSON.stringify({ error: 'missing ?fixture=' }))
    return
  }
  const fixture = await loadFixture(fixtureName)
  if (!fixture) {
    res.writeHead(404, { 'content-type': 'application/json' })
    res.end(JSON.stringify({ error: `unknown fixture: ${fixtureName}` }))
    return
  }

  res.writeHead(200, {
    'content-type': 'text/event-stream',
    'cache-control': 'no-cache, no-transform',
    connection: 'keep-alive',
    'x-accel-buffering': 'no',
    'x-fixture-event-count': String(fixture.events.length),
  })
  // Flush headers immediately so the client sees the connection open before
  // the first (possibly delayed) event — matters for the 3s-stall fixture.
  ;(res as ServerResponse & { flushHeaders?: () => void }).flushHeaders?.()

  let closed = false
  req.on('close', () => {
    closed = true
  })

  for (const entry of fixture.events) {
    if (closed) return
    await sleep(entry.delay_ms)
    if (closed) return
    const frame = `data: ${JSON.stringify(entry.event)}\n\n`
    await writeChunked(res, frame, fixture.chunk_bytes)

    const seq = (entry.event as { seq?: number }).seq
    if (
      fixture.abrupt_end_after_seq !== undefined &&
      typeof seq === 'number' &&
      seq >= fixture.abrupt_end_after_seq
    ) {
      // Simulate a hard disconnect: destroy the socket rather than ending
      // the response cleanly. No further events are sent even if defined.
      req.socket.destroy()
      return
    }
  }
  res.end()
}

async function handleFixtureList(_req: IncomingMessage, res: ServerResponse): Promise<void> {
  const files = (await readdir(FIXTURES_DIR)).filter((f) => f.endsWith('.json'))
  const list = await Promise.all(
    files.map(async (f) => {
      const spec = JSON.parse(await readFile(join(FIXTURES_DIR, f), 'utf8')) as FixtureSpec
      return { name: spec.name, description: spec.description, event_count: spec.events.length }
    }),
  )
  res.writeHead(200, { 'content-type': 'application/json' })
  res.end(JSON.stringify(list, null, 2))
}

async function handleStatic(req: IncomingMessage, res: ServerResponse, pathname: string): Promise<void> {
  if (pathname === '/reducer.mjs') {
    const body = await readFile(REDUCER_PATH, 'utf8')
    res.writeHead(200, { 'content-type': MIME['.mjs'] })
    res.end(body)
    return
  }

  const rel = pathname === '/' ? '/index.html' : pathname
  const path = normalize(join(HARNESS_PUBLIC_DIR, rel))
  if (!path.startsWith(HARNESS_PUBLIC_DIR) || !existsSync(path)) {
    res.writeHead(404, { 'content-type': 'text/plain' })
    res.end('not found')
    return
  }
  const body = await readFile(path)
  res.writeHead(200, { 'content-type': MIME[extname(path)] ?? 'application/octet-stream' })
  res.end(body)
}

const server = createServer((req, res) => {
  const url = new URL(req.url ?? '/', `http://localhost:${PORT}`)
  const handler =
    url.pathname === '/stream'
      ? handleStream(req, res, url)
      : url.pathname === '/fixtures'
        ? handleFixtureList(req, res)
        : url.pathname === '/health'
          ? Promise.resolve(res.writeHead(200).end('ok'))
          : handleStatic(req, res, url.pathname)

  handler.catch((err) => {
    console.error('[replay/server] request handler error', err)
    if (!res.headersSent) res.writeHead(500)
    res.end(String(err))
  })
})

server.listen(PORT, () => {
  console.log(`[replay/server] listening on http://localhost:${PORT}`)
  console.log(`[replay/server] fixtures dir: ${FIXTURES_DIR}`)
})
