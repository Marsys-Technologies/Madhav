import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest } from 'next/server'
import writerDigestInventory from '@/generated/nirmana-writer-digests.json'

const { mockQuery, mockGetPool, mockGetServerUser, mockInvokeRunJob, mockGetJobImageTag } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetPool: vi.fn(),
  mockGetServerUser: vi.fn(),
  mockInvokeRunJob: vi.fn(),
  mockGetJobImageTag: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery, getPool: mockGetPool }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))
vi.mock('@/lib/build/jobInvoker', () => ({ invokeRunJob: mockInvokeRunJob }))
vi.mock('@/lib/cloud_run/jobs', () => ({ getJobImageTag: mockGetJobImageTag }))

import { POST as previewPlan } from '../../plan/route'
import { POST as createRun } from '../route'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const UID = 'owner-uid'
const DIGESTS = writerDigestInventory.writers as Record<string, string>

const REGISTRY = [
  {
    asset_id: 'ga_positions', layer: 'ganita', depends_on: [], estimated_seconds: 30,
    scope: 'per_chart', has_writer: true, target_table: 'chart_facts', count_sql: null,
    natural_key_partition: null, asset_kind: 'data', asset_type: 'data', service_health: null,
    health_probe: null, domain: null,
  },
  {
    asset_id: 'ga_structural', layer: 'ganita', depends_on: ['ga_positions'], estimated_seconds: 60,
    scope: 'per_chart', has_writer: true, target_table: 'chart_facts', count_sql: null,
    natural_key_partition: null, asset_kind: 'data', asset_type: 'data', service_health: null,
    health_probe: null, domain: null,
  },
  {
    asset_id: 'bo_laksana', layer: 'bodha', depends_on: ['ga_structural'], estimated_seconds: 60,
    scope: 'per_chart', has_writer: true, target_table: 'bodha_msr_signals', count_sql: null,
    natural_key_partition: null, asset_kind: 'data', asset_type: 'data', service_health: null,
    health_probe: null, domain: null,
  },
]

function makeReq(path: string, body: object): NextRequest {
  return new NextRequest(`http://localhost${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

function setupMocks(opts: {
  throughput?: Array<{ asset_id: string; state: string }>
  freshness?: Array<{ asset_id: string; state: string; reasons: string[] }>
  receipts?: Array<{ asset_id: string; code_digest: string }>
} = {}) {
  mockGetServerUser.mockResolvedValue({ uid: UID })
  mockGetJobImageTag.mockResolvedValue('tag-1')
  mockInvokeRunJob.mockResolvedValue({ executionName: 'exec-1' })

  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'client' }], rowCount: 1 })
    if (/owner_id[\s\S]*FROM charts/.test(sql)) return Promise.resolve({ rows: [{ owner_id: UID }], rowCount: 1 })
    if (/FROM asset_registry/.test(sql)) return Promise.resolve({ rows: REGISTRY, rowCount: REGISTRY.length })
    if (/FROM asset_throughput/.test(sql)) return Promise.resolve({ rows: opts.throughput ?? [], rowCount: 0 })
    if (/FROM build_protected_assets/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/FROM asset_freshness/.test(sql)) return Promise.resolve({ rows: opts.freshness ?? [], rowCount: 0 })
    if (/FROM asset_provenance_receipts/.test(sql)) return Promise.resolve({ rows: opts.receipts ?? [], rowCount: 0 })
    if (/FROM chart_facts|FROM brahma_remedy_corpus/.test(sql)) return Promise.resolve({ rows: [{ count: '1' }], rowCount: 1 })
    return Promise.resolve({ rows: [], rowCount: 0 })
  })

  const client = {
    query: vi.fn((sql: string) => {
      if (/SELECT id FROM build_runs/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
      if (/INSERT INTO build_runs/.test(sql)) return Promise.resolve({ rows: [{ id: 'run-prep-1' }], rowCount: 1 })
      return Promise.resolve({ rows: [], rowCount: 0 })
    }),
    release: vi.fn(),
  }
  mockGetPool.mockResolvedValue({ connect: vi.fn().mockResolvedValue(client) })
}

describe('NIR-05 whole-layer preparation scope consistency (ganita / bodha)', () => {
  beforeEach(() => vi.clearAllMocks())

  it('plan and runs agree on selective resume for whole-layer ganita when ga_positions is lit+fresh and ga_structural is interrupted', async () => {
    setupMocks({
      throughput: [
        { asset_id: 'ga_positions', state: 'lit' },
        { asset_id: 'ga_structural', state: 'error' },
        { asset_id: 'bo_laksana', state: 'lit' },
      ],
      freshness: [
        { asset_id: 'ga_positions', state: 'fresh', reasons: [] },
        { asset_id: 'ga_structural', state: 'stale', reasons: ['interrupted_preparation'] },
        { asset_id: 'bo_laksana', state: 'fresh', reasons: [] },
      ],
      receipts: [
        { asset_id: 'ga_positions', code_digest: DIGESTS.ga_positions },
        { asset_id: 'ga_structural', code_digest: DIGESTS.ga_structural },
        { asset_id: 'bo_laksana', code_digest: DIGESTS.bo_laksana },
      ],
    })

    const body = { chart_id: CHART, scope: 'layer', scope_target: 'ganita', action: 'build' }
    const planRes = await previewPlan(makeReq('/api/cockpit/plan', body))
    expect(planRes.status).toBe(200)
    const { data: planData } = await planRes.json()
    expect(planData.plan_waves).toEqual([['ga_structural']])
    expect(planData.downstream_may_become_stale).toEqual(['bo_laksana'])

    const runRes = await createRun(makeReq('/api/cockpit/runs', {
      ...body,
      expected_plan: planData.plan_waves.flat(),
      expected_downstream: planData.downstream_may_become_stale,
    }))
    expect(runRes.status).toBe(201)
    expect(mockInvokeRunJob).toHaveBeenCalledExactlyOnceWith('run-prep-1', { forceExecute: true })
  })

  it('returns 409 PLAN_CHANGED for whole-layer bodha when confirmed expected_plan goes stale before dispatch', async () => {
    setupMocks({
      throughput: [
        { asset_id: 'ga_positions', state: 'lit' },
        { asset_id: 'ga_structural', state: 'lit' },
        { asset_id: 'bo_laksana', state: 'stale' },
      ],
      freshness: [
        { asset_id: 'ga_positions', state: 'fresh', reasons: [] },
        { asset_id: 'ga_structural', state: 'fresh', reasons: [] },
        { asset_id: 'bo_laksana', state: 'fresh', reasons: [] },
      ],
    })

    const res = await createRun(makeReq('/api/cockpit/runs', {
      chart_id: CHART,
      scope: 'layer',
      scope_target: 'bodha',
      action: 'build',
      expected_plan: [],
    }))
    expect(res.status).toBe(409)
    expect((await res.json()).code).toBe('PLAN_CHANGED')
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })

  it('terminalizes failed whole-layer ganita run and aborts queued assets on dispatch failure', async () => {
    setupMocks()
    mockInvokeRunJob.mockRejectedValue(new Error('cloud run unavailable'))

    const res = await createRun(makeReq('/api/cockpit/runs', {
      chart_id: CHART,
      scope: 'layer',
      scope_target: 'ganita',
      action: 'build',
    }))
    expect(res.status).toBe(503)
    const body = await res.json()
    expect(body.run_id).toBe('run-prep-1')
    const failCall = mockQuery.mock.calls.find(([sql]) => /UPDATE build_runs\s+SET state = 'failed'/.test(String(sql)))
    expect(failCall?.[1]).toEqual(['cloud run unavailable', 'run-prep-1'])
  })
})
