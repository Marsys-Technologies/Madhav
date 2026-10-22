/**
 * deploy_identity.ts — what the MCP service's /health states about WHICH image and WHICH migration ledger it runs
 * against (KĀLA-YANTRA D-FLIP F-12; read by fleet/http_probe.py `stated()` as `image` and `migration_set`).
 *
 *   image_digest   the running image's immutable digest, taken ONLY from NIRMANA_IMAGE_DIGEST, which deploy.yml sets
 *                  from the image build step's `digest` output. A tag, a commit sha or anything that is not
 *                  `sha256:<64 hex>` is refused: a mutable reference must never read as an identity.
 *   migration_set  {count, sha256, algorithm}: digest of the applied-migration ledger's filenames, read through the
 *                  platform (this service holds no database connection) and cached.
 *
 * Either is null with a named `*_reason` when unavailable (CLAUDE.md §N.7.6): never a placeholder, never inferred.
 * No secret is read or echoed; the health route's auth is unchanged.
 */
import type { Request, Response } from 'express'

export const IMAGE_DIGEST_ENV = 'NIRMANA_IMAGE_DIGEST'
export const MIGRATION_LEDGER_PATH = '/api/mcp/health/migrations'

const IMAGE_DIGEST_RE = /^sha256:[0-9a-f]{64}$/
const HEX64_RE = /^[0-9a-f]{64}$/

export interface Stated<T> {
  value: T | null
  reason: string | null
}

export interface MigrationSetDigest {
  count: number
  sha256: string
  algorithm: string
}

export function readImageDigest(env: Record<string, string | undefined> = process.env): Stated<string> {
  const raw = env[IMAGE_DIGEST_ENV]
  if (raw === undefined || raw === '') {
    return { value: null, reason: `${IMAGE_DIGEST_ENV} is not set: the deploy did not state the image digest` }
  }
  if (!IMAGE_DIGEST_RE.test(raw)) {
    return {
      value: null,
      reason: `${IMAGE_DIGEST_ENV} is not a sha256 image digest (a tag or commit sha is mutable and is refused)`,
    }
  }
  return { value: raw, reason: null }
}

export interface LedgerResponse {
  status: number
  body: unknown
}

/** Validates what the platform returned; the platform's own refusal reason is passed through. */
export function parseLedgerResponse(res: LedgerResponse): Stated<MigrationSetDigest> {
  const body = (typeof res.body === 'object' && res.body !== null ? res.body : {}) as Record<string, unknown>
  if (res.status !== 200) {
    const why = typeof body['reason'] === 'string' ? `: ${body['reason'].slice(0, 200)}` : ''
    return { value: null, reason: `platform ledger route answered HTTP ${res.status}${why}` }
  }
  const set = body['migration_set'] as Record<string, unknown> | undefined
  if (
    body['ok'] !== true || typeof set !== 'object' || set === null ||
    !Number.isInteger(set['count']) || (set['count'] as number) < 1 ||
    typeof set['sha256'] !== 'string' || !HEX64_RE.test(set['sha256']) ||
    typeof set['algorithm'] !== 'string' || set['algorithm'] === ''
  ) {
    return { value: null, reason: 'platform ledger route answered 200 without a valid migration_set digest' }
  }
  return {
    value: { count: set['count'] as number, sha256: set['sha256'], algorithm: set['algorithm'] },
    reason: null,
  }
}

export interface MigrationSetReaderOptions {
  fetchLedger: () => Promise<LedgerResponse>
  now?: () => number
  /** How long a good reading is reused (the ledger changes only at deploy). */
  okTtlMs?: number
  /** How long an unavailable reading is reused, so a down platform is not hammered by every health check. */
  failTtlMs?: number
  /** Hard bound on one read: /health must answer even when the platform does not. */
  timeoutMs?: number
}

export function createMigrationSetReader(options: MigrationSetReaderOptions): () => Promise<Stated<MigrationSetDigest>> {
  const now = options.now ?? Date.now
  const okTtl = options.okTtlMs ?? 5 * 60_000
  const failTtl = options.failTtlMs ?? 30_000
  const timeoutMs = options.timeoutMs ?? 4_000
  let cached: { at: number; ttl: number; reading: Stated<MigrationSetDigest> } | null = null
  let inFlight: Promise<Stated<MigrationSetDigest>> | null = null

  async function fetchOnce(): Promise<Stated<MigrationSetDigest>> {
    let timer: ReturnType<typeof setTimeout> | undefined
    try {
      const timeout = new Promise<never>((_, reject) => {
        timer = setTimeout(() => reject(new Error('timeout')), timeoutMs)
      })
      const res = await Promise.race([options.fetchLedger(), timeout])
      return parseLedgerResponse(res)
    } catch (err) {
      const kind = err instanceof Error && err.message === 'timeout' ? `no answer within ${timeoutMs} ms`
        : err instanceof Error ? err.name : typeof err
      return { value: null, reason: `platform ledger route unreachable (${kind})` }
    } finally {
      if (timer !== undefined) clearTimeout(timer)
    }
  }

  return async function read(): Promise<Stated<MigrationSetDigest>> {
    if (cached !== null && now() - cached.at < cached.ttl) return cached.reading
    if (inFlight === null) {
      inFlight = fetchOnce().then((reading) => {
        cached = { at: now(), ttl: reading.value === null ? failTtl : okTtl, reading }
        return reading
      }).finally(() => { inFlight = null })
    }
    return inFlight
  }
}

let defaultReader: (() => Promise<Stated<MigrationSetDigest>>) | null = null

function getDefaultReader(): () => Promise<Stated<MigrationSetDigest>> {
  defaultReader ??= createMigrationSetReader({
    fetchLedger: async () => {
      const { platformServiceGet } = await import('../client.js')
      return platformServiceGet(MIGRATION_LEDGER_PATH, 3_500)
    },
  })
  return defaultReader
}

export interface HealthHandlerOptions {
  toolCount: number
  env?: Record<string, string | undefined>
  readMigrationSet?: () => Promise<Stated<MigrationSetDigest>>
}

/** The /health body: the established liveness fields, plus the deploy identity. */
export function createHealthHandler(options: HealthHandlerOptions) {
  return async function health(_req: Request, res: Response): Promise<void> {
    const env = options.env ?? process.env
    const image = readImageDigest(env)
    const migrations = await (options.readMigrationSet ?? getDefaultReader())()
    res.json({
      status: 'ok',
      service: 'marsys-mcp',
      version: '1.0.0',
      deployed_sha: env['NIRMANA_DEPLOYED_SHA'] ?? null,
      revision: env['K_REVISION'] ?? null,
      image_digest: image.value,
      image_digest_reason: image.reason,
      migration_set: migrations.value,
      migration_set_reason: migrations.reason,
      tools: options.toolCount,
      stream_g_capabilities: ['compute_natal_positions', 'query_dasha_periods', 'query_special_lagnas'],
    })
  }
}
