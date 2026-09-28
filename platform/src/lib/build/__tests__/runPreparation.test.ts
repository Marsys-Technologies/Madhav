/**
 * Shared run preparation (Jātaka chart workspace, Task 5).
 *
 * The cockpit and the chart-correction transaction plan, freeze and persist
 * runs through these helpers on a caller-supplied Queryable, so a correction
 * runs every read and write inside its own transaction.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import writerDigestInventory from '@/generated/nirmana-writer-digests.json'

vi.mock('server-only', () => ({}))

import {
  BuildPreparationError,
  canonicalManifestJson,
  manifestDigest,
  persistPreparedRun,
  resolveRunPreparation,
  type Queryable,
  type RunPreparationRequest,
} from '../runPreparation'

const CHART = '11111111-2222-4333-8444-555555555555'
const DIGESTS = writerDigestInventory.writers as Record<string, string>

function reg(asset_id: string, extra: Record<string, unknown> = {}) {
  const layer =
    asset_id.startsWith('bg_') ? 'brahmagyan'
      : asset_id.startsWith('ga_') ? 'ganita'
        : asset_id.startsWith('bo_') ? 'bodha'
          : asset_id.startsWith('ka_') ? 'kala'
            : asset_id.startsWith('ph_') ? 'phala' : 'mimamsa'
  return {
    asset_id, layer, depends_on: [], estimated_seconds: 10,
    scope: asset_id.startsWith('bg_') ? 'global' : 'per_chart',
    has_writer: true, target_table: `${asset_id}_t`, count_sql: null,
    natural_key_partition: null, asset_kind: 'data', asset_type: 'data', service_health: null,
    health_probe: null, domain: null,
    ...extra,
  }
}

// Real per-chart writers with sidecar digests, plus one global L0 dependency.
const WRITERS = ['ga_positions', 'ka_kshetra', 'ka_avadhi'].filter((id) => DIGESTS[id])
const REGISTRY = [
  reg('bg_ephemeris'),
  reg(WRITERS[0]),
  reg(WRITERS[1], { depends_on: [WRITERS[0]] }),
  reg(WRITERS[2], { depends_on: [WRITERS[1]] }),
  reg('lel_events', { has_writer: false, target_table: 'life_events' }),
]

interface Fake {
  db: Queryable
  sql: string[]
}

function fakeDb(opts: {
  activeRun?: string | null
  registry?: unknown[]
  protectedIds?: string[]
  throughput?: Array<{ asset_id: string; state: string }>
  freshness?: Array<{ asset_id: string; state: string; reasons: string[] }>
} = {}): Fake {
  const sql: string[] = []
  const db: Queryable = {
    query: vi.fn(async (text: string) => {
      sql.push(text)
      if (/SELECT id FROM build_runs/.test(text)) return { rows: opts.activeRun ? [{ id: opts.activeRun }] : [] }
      if (/FROM asset_registry/.test(text)) return { rows: opts.registry ?? REGISTRY }
      if (/FROM asset_throughput/.test(text)) {
        return { rows: opts.throughput ?? [{ asset_id: 'bg_ephemeris', state: 'lit' }] }
      }
      if (/FROM build_protected_assets/.test(text)) return { rows: (opts.protectedIds ?? []).map((asset_id) => ({ asset_id })) }
      if (/FROM asset_freshness/.test(text)) {
        return { rows: opts.freshness ?? [{ asset_id: 'bg_ephemeris', state: 'fresh', reasons: [] }] }
      }
      if (/INSERT INTO build_runs/.test(text)) return { rows: [{ id: 'run-new' }] }
      return { rows: [] }
    }) as unknown as Queryable['query'],
  }
  return { db, sql }
}

const CORRECTION: RunPreparationRequest = {
  chartId: CHART,
  scope: 'global',
  scopeTarget: null,
  action: 'rebuild',
  allowedScopes: ['per_chart'],
  clearPolicy: 'chart-correction-strict',
  triggeredBy: 'owner-uid',
  requireCompletePlan: true,
}

beforeEach(() => vi.clearAllMocks())

describe('resolveRunPreparation — chart correction', () => {
  it('fixture sanity: the writers carry real sidecar digests', () => {
    expect(WRITERS).toHaveLength(3)
  })

  it('plans every active per-chart writer and nothing global or writer-less', async () => {
    const { db } = fakeDb()
    const prepared = await resolveRunPreparation(db, CORRECTION)
    expect([...prepared.plan].sort()).toEqual([...WRITERS].sort())
    expect(prepared.plan.every((id) => !id.startsWith('bg_'))).toBe(true)
    expect(prepared.plan).not.toContain('lel_events')
    expect(prepared.planWaves.flat()).toEqual(prepared.plan)
  })

  it('freezes a v1 manifest with a sha256 digest over its canonical JSON', async () => {
    const { db } = fakeDb()
    const prepared = await resolveRunPreparation(db, CORRECTION)
    expect(prepared.manifest.version).toBe('nirmana-run-manifest/v1')
    expect(prepared.manifest).toMatchObject({ chart_id: CHART, scope: 'global', scope_target: null, action: 'rebuild' })
    expect(prepared.manifestDigest).toMatch(/^[a-f0-9]{64}$/)
    expect(prepared.manifestDigest).toBe(manifestDigest(prepared.manifest))
    expect(prepared.manifest.assets.map((a) => a.expected_code_digest)).toEqual(prepared.plan.map((id) => DIGESTS[id]))
  })

  it('offers every per-chart asset, writer or not, for the invalidation policy to classify', async () => {
    const { db } = fakeDb()
    const prepared = await resolveRunPreparation(db, CORRECTION)
    const ids = prepared.clearAssets.map((a) => a.asset_id)
    expect(ids).toEqual(expect.arrayContaining([...WRITERS, 'lel_events']))
    expect(ids).not.toContain('bg_ephemeris')
    // Dependency order: an upstream writer precedes its dependants, so reversing clears downstream first.
    expect(ids.indexOf(WRITERS[0])).toBeLessThan(ids.indexOf(WRITERS[2]))
  })

  it('rejects with RUN_ACTIVE when a build is already planned, running or paused', async () => {
    const { db, sql } = fakeDb({ activeRun: 'run-live' })
    await expect(resolveRunPreparation(db, CORRECTION)).rejects.toMatchObject({
      code: 'RUN_ACTIVE',
      details: { existing_run_id: 'run-live' },
    })
    expect(sql.some((s) => /FROM asset_registry/.test(s))).toBe(false)
  })

  it('rejects with PROTECTED when any required per-chart asset is protected — never a partial correction', async () => {
    const { db } = fakeDb({ protectedIds: [WRITERS[1]] })
    const err = await resolveRunPreparation(db, CORRECTION).catch((e) => e)
    expect(err).toBeInstanceOf(BuildPreparationError)
    expect(err.code).toBe('PROTECTED')
    expect(err.details.protected_assets).toEqual([expect.objectContaining({ asset_id: WRITERS[1] })])
  })

  it('rejects with UPSTREAM_BLOCKED when a global dependency is not ready', async () => {
    const { db } = fakeDb({
      registry: [reg('bg_ephemeris'), reg(WRITERS[0], { depends_on: ['bg_ephemeris'] })],
      throughput: [{ asset_id: 'bg_ephemeris', state: 'error' }],
    })
    await expect(resolveRunPreparation(db, CORRECTION)).rejects.toMatchObject({ code: 'UPSTREAM_BLOCKED' })
  })

  it('accepts a current healthy service probe with only the inapplicable output-spec reason', async () => {
    const { db, sql } = fakeDb({
      registry: [
        reg('bg_panchanga', {
          asset_kind: 'service', asset_type: 'service', service_health: 'healthy',
          has_writer: false, target_table: null, health_probe: { type: 'http' },
        }),
        reg(WRITERS[0], { depends_on: ['bg_panchanga'] }),
      ],
      throughput: [{ asset_id: 'bg_panchanga', state: 'service_ok' }],
      freshness: [{
        asset_id: 'bg_panchanga', state: 'unknown', reasons: ['output_digest_spec_unavailable'],
      }],
    })

    const prepared = await resolveRunPreparation(db, CORRECTION)
    expect(prepared.plan).toEqual([WRITERS[0]])
    expect(sql.find((statement) => /FROM asset_registry/.test(statement))).toMatch(/service_health/)
  })

  it('rejects with CODE_DIGEST_UNAVAILABLE when a planned writer has no sidecar digest', async () => {
    const { db } = fakeDb({ registry: [reg('ga_not_a_real_writer_xyz')] })
    await expect(resolveRunPreparation(db, CORRECTION)).rejects.toMatchObject({ code: 'CODE_DIGEST_UNAVAILABLE' })
  })

  it('issues every read on the supplied client (the caller’s transaction)', async () => {
    const { db, sql } = fakeDb()
    await resolveRunPreparation(db, CORRECTION)
    expect(sql.some((s) => /FROM asset_registry/.test(s))).toBe(true)
    expect(sql.some((s) => /FROM build_protected_assets/.test(s))).toBe(true)
    expect(sql.some((s) => /FROM asset_freshness/.test(s))).toBe(true)
  })
})

describe('persistPreparedRun', () => {
  it('inserts one planned run and one queued row per planned asset, without its own transaction', async () => {
    const { db, sql } = fakeDb()
    const prepared = await resolveRunPreparation(db, CORRECTION)
    sql.length = 0
    const runId = await persistPreparedRun(db, prepared, 'owner-uid')
    expect(runId).toBe('run-new')
    expect(sql.filter((s) => /^\s*(BEGIN|COMMIT|ROLLBACK)/i.test(s))).toHaveLength(0)
    const calls = (db.query as unknown as ReturnType<typeof vi.fn>).mock.calls
    const runCall = calls.find(([s]) => /INSERT INTO build_runs/.test(s))!
    expect(runCall[1]).toEqual([
      CHART, 'global', null, 'rebuild', JSON.stringify(prepared.plan),
      JSON.stringify(prepared.manifest), prepared.manifestDigest, 'owner-uid',
    ])
    const assetCall = calls.find(([s]) => /INSERT INTO build_run_assets/.test(s))!
    expect(assetCall[1]).toEqual(['run-new', ...prepared.plan.flatMap((id, i) => [id, i, 'queued'])])
  })
})

describe('canonicalManifestJson', () => {
  it('sorts object keys and preserves array order', () => {
    expect(canonicalManifestJson({ b: 1, a: [3, { d: 1, c: 2 }] })).toBe('{"a":[3,{"c":2,"d":1}],"b":1}')
  })
})
