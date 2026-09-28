// @vitest-environment node

import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

const mocks = vi.hoisted(() => ({ getEvents: vi.fn(), getEventById: vi.fn() }))
vi.mock('@/lib/observatory/queries', () => mocks)
vi.mock('@/app/api/admin/observatory/_guard', () => ({
  guardObservatoryRoute: vi.fn(async () => ({ profile: { role: 'super_admin' } })),
}))

const event = {
  event_id: '10000000-0000-4000-8000-000000000001',
  conversation_id: null,
  conversation_name: null,
  prompt_id: '10000000-0000-4000-8000-000000000002',
  user_id: 'user-1',
  provider: 'openai',
  model: 'gpt-test',
  pipeline_stage: 'planner',
  input_tokens: 1,
  output_tokens: 2,
  cache_read_tokens: null,
  cache_write_tokens: null,
  computed_cost_usd: null,
  latency_ms: 10,
  status: 'success',
  error_code: null,
  started_at: '2026-09-28T00:00:00.000Z',
  finished_at: '2026-09-28T00:00:00.010Z',
}

describe('Observatory nullable MCP conversation serialization', () => {
  beforeEach(() => vi.clearAllMocks())

  it('serializes null conversation_id from the list endpoint', async () => {
    mocks.getEvents.mockResolvedValue({ events: [event], next_cursor: null, total_count: 1 })
    const { GET } = await import('../route')
    const response = await GET(new Request(
      'http://localhost/api/admin/observatory/events?from=2026-09-27T00:00:00Z&to=2026-09-29T00:00:00Z'))

    expect(response.status).toBe(200)
    expect((await response.json()).events[0].conversation_id).toBeNull()
  })

  it('serializes null conversation_id from the detail endpoint', async () => {
    mocks.getEventById.mockResolvedValue({ ...event, created_at: event.started_at })
    const { GET } = await import('../../event/[id]/route')
    const response = await GET(new Request('http://localhost'), {
      params: Promise.resolve({ id: event.event_id }),
    })

    expect(response.status).toBe(200)
    expect((await response.json()).conversation_id).toBeNull()
  })

  it('declares conversation_id nullable in both public OpenAPI event schemas', () => {
    const yaml = readFileSync(resolve(__dirname, '../../openapi.yaml'), 'utf8')
    const list = yaml.slice(yaml.indexOf('    ObservatoryEventListRow:'), yaml.indexOf('    EventsResponse:'))
    const detail = yaml.slice(yaml.indexOf('    EventDetailResponse:'), yaml.indexOf('    ProviderReconcileResult:'))
    for (const schema of [list, detail]) {
      expect(schema).toContain('conversation_id: { type: string, nullable: true }')
    }
  })
})
