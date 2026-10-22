/**
 * /health states image_digest and migration_set (KĀLA-YANTRA D-FLIP F-12), each null with a named reason when unavailable.
 *
 * Claims and sources:
 *   C1  image_digest is the digest the deploy states, verbatim            — OCI image-spec digest grammar `sha256:<64 hex>`
 *   C2  a tag / commit sha / short or upper-case digest is refused (null + reason) — a mutable reference is not an identity
 *   C3  an unset digest is null with a reason, never a placeholder        — CLAUDE.md §N.7.6
 *   C4  a platform answer that is not a valid digest, or a non-200, is null with a reason
 *   C5  a good ledger reading is cached; an unavailable one is cached shorter; concurrent reads share one fetch
 *   C6  a platform that never answers cannot hang /health                 — timeout → null + reason
 *   C7  the handler keeps the established fields and adds exactly the four identity fields, small and secret-free
 */
import { describe, it, expect, vi } from 'vitest'
import {
  createHealthHandler,
  createMigrationSetReader,
  parseLedgerResponse,
  readImageDigest,
  IMAGE_DIGEST_ENV,
} from '../lib/deploy_identity.js'

const DIGEST = `sha256:${'a1'.repeat(32)}`
const GOOD_BODY = { ok: true, migration_set: { count: 3, sha256: 'c3'.repeat(32), algorithm: 'sha256 of filenames' } }

describe('C1/C2/C3 image_digest', () => {
  it('C1 states the deploy-time digest verbatim', () => {
    expect(readImageDigest({ [IMAGE_DIGEST_ENV]: DIGEST })).toEqual({ value: DIGEST, reason: null })
  })

  it.each([
    ['a tag', 'amjis-mcp:latest'],
    ['the registry path with a tag', 'asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-mcp:0123456789abcdef0123456789abcdef01234567'],
    ['a commit sha', '0123456789abcdef0123456789abcdef01234567'],
    ['a short digest', 'sha256:abc123'],
    ['an upper-case digest', `sha256:${'A1'.repeat(32)}`],
    ['a digest with a suffix', `${DIGEST}:latest`],
  ])('C2 refuses %s', (_name, raw) => {
    const got = readImageDigest({ [IMAGE_DIGEST_ENV]: raw })
    expect(got.value).toBeNull()
    expect(got.reason).toMatch(/not a sha256 image digest/)
  })

  it.each([[undefined], ['']])('C3 an unset digest (%j) is null with a reason, not a placeholder', (raw) => {
    const got = readImageDigest({ [IMAGE_DIGEST_ENV]: raw })
    expect(got.value).toBeNull()
    expect(got.reason).toMatch(/not set/)
  })
})

describe('C4 platform answer', () => {
  it('passes a valid digest through', () => {
    expect(parseLedgerResponse({ status: 200, body: GOOD_BODY })).toEqual({ value: GOOD_BODY.migration_set, reason: null })
  })

  it('keeps the platform refusal reason when the ledger is unreadable (503)', () => {
    const got = parseLedgerResponse({ status: 503, body: { ok: false, reason: 'ledger_unreadable: the _migrations_applied query failed (Error)' } })
    expect(got.value).toBeNull()
    expect(got.reason).toMatch(/HTTP 503.*ledger_unreadable/)
  })

  it('names the status when the route is absent (an older platform revision)', () => {
    const got = parseLedgerResponse({ status: 404, body: null })
    expect(got.value).toBeNull()
    expect(got.reason).toMatch(/HTTP 404/)
  })

  it.each([
    ['count 0', { ok: true, migration_set: { ...GOOD_BODY.migration_set, count: 0 } }],
    ['a non-hex digest', { ok: true, migration_set: { ...GOOD_BODY.migration_set, sha256: 'xyz' } }],
    ['no algorithm', { ok: true, migration_set: { count: 3, sha256: 'c3'.repeat(32) } }],
    ['ok false on a 200', { ok: false, migration_set: GOOD_BODY.migration_set }],
    ['no body', null],
  ])('a 200 with %s is null with a reason', (_name, body) => {
    const got = parseLedgerResponse({ status: 200, body })
    expect(got.value).toBeNull()
    expect(got.reason).toMatch(/without a valid migration_set digest/)
  })
})

describe('C5/C6 cached, bounded reader', () => {
  it('C5 reuses a good reading until its TTL, then reads again', async () => {
    let clock = 0
    const fetchLedger = vi.fn(async () => ({ status: 200, body: GOOD_BODY }))
    const read = createMigrationSetReader({ fetchLedger, now: () => clock, okTtlMs: 1000, failTtlMs: 100 })
    await read(); await read()
    expect(fetchLedger).toHaveBeenCalledTimes(1)
    clock = 1001
    await read()
    expect(fetchLedger).toHaveBeenCalledTimes(2)
  })

  it('C5 reuses an unavailable reading only for the shorter TTL', async () => {
    let clock = 0
    const fetchLedger = vi.fn(async () => ({ status: 503, body: { ok: false, reason: 'ledger_unreadable' } }))
    const read = createMigrationSetReader({ fetchLedger, now: () => clock, okTtlMs: 1000, failTtlMs: 100 })
    expect((await read()).value).toBeNull()
    clock = 99
    await read()
    expect(fetchLedger).toHaveBeenCalledTimes(1)
    clock = 101
    await read()
    expect(fetchLedger).toHaveBeenCalledTimes(2)
  })

  it('C5 concurrent reads share one fetch', async () => {
    const fetchLedger = vi.fn(async () => ({ status: 200, body: GOOD_BODY }))
    const read = createMigrationSetReader({ fetchLedger })
    await Promise.all([read(), read(), read()])
    expect(fetchLedger).toHaveBeenCalledTimes(1)
  })

  it('C6 a platform that never answers yields null with a reason within the bound', async () => {
    const read = createMigrationSetReader({ fetchLedger: () => new Promise(() => undefined), timeoutMs: 20 })
    const got = await read()
    expect(got.value).toBeNull()
    expect(got.reason).toMatch(/unreachable.*no answer within 20 ms/)
  })

  it('C6 a thrown network error is null with the error class, not its message', async () => {
    const read = createMigrationSetReader({ fetchLedger: async () => { throw new TypeError('fetch failed: connect ECONNREFUSED 10.1.2.3') } })
    const got = await read()
    expect(got.value).toBeNull()
    expect(got.reason).toBe('platform ledger route unreachable (TypeError)')
  })
})

describe('C7 the /health body', () => {
  async function call(env: Record<string, string | undefined>, reading: Awaited<ReturnType<ReturnType<typeof createMigrationSetReader>>>) {
    let body: Record<string, unknown> = {}
    const handler = createHealthHandler({ toolCount: 88, env, readMigrationSet: async () => reading })
    await handler({} as never, { json: (b: Record<string, unknown>) => { body = b } } as never)
    return body
  }

  it('states both identities and keeps the established fields', async () => {
    const body = await call(
      { NIRMANA_DEPLOYED_SHA: 'd'.repeat(40), K_REVISION: 'amjis-mcp-00042', [IMAGE_DIGEST_ENV]: DIGEST },
      { value: GOOD_BODY.migration_set, reason: null },
    )
    expect(body).toEqual({
      status: 'ok', service: 'marsys-mcp', version: '1.0.0',
      deployed_sha: 'd'.repeat(40), revision: 'amjis-mcp-00042',
      image_digest: DIGEST, image_digest_reason: null,
      migration_set: GOOD_BODY.migration_set, migration_set_reason: null,
      tools: 88, stream_g_capabilities: ['compute_natal_positions', 'query_dasha_periods', 'query_special_lagnas'],
    })
    expect(JSON.stringify(body).length).toBeLessThan(1024)
  })

  it('states neither when neither is available, each with its own reason', async () => {
    const body = await call({}, { value: null, reason: 'platform ledger route unreachable (TypeError)' })
    expect(body['image_digest']).toBeNull()
    expect(body['image_digest_reason']).toMatch(/not set/)
    expect(body['migration_set']).toBeNull()
    expect(body['migration_set_reason']).toMatch(/unreachable/)
    expect(body['deployed_sha']).toBeNull()
  })

  it('never echoes the internal token or a Bearer value', async () => {
    const body = await call(
      { MCP_INTERNAL_TOKEN: 'sekret-token-value', [IMAGE_DIGEST_ENV]: DIGEST },
      { value: GOOD_BODY.migration_set, reason: null },
    )
    expect(JSON.stringify(body)).not.toMatch(/sekret-token-value|Bearer/)
  })
})
