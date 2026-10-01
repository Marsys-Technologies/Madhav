import { afterEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor, fireEvent, cleanup } from '@testing-library/react'
import { ObservatoryDashboard } from '../ObservatoryDashboard'

const scope = vi.hoisted(() => ({ current: {} as Record<string, unknown> }))
vi.mock('../ObservatoryScope', () => ({ useObservatoryScope: () => scope.current }))
const totals = { transport_attempts: 2, customer_attempts: 1, validation_attempts: 1, transport_success: 1, transport_failed: 1, transport_pending: 0,
  complete_usage: 1, transport_unpriced: 1, input_tokens: '100', output_tokens: '10',
  known_transport_cost_usd: '0.0004', legacy_records: 1, legacy_estimate_usd: '0.5', p50_success_ms: 1500 }
const base = { admin: false, userId: 'alice', scope: 'mine', setScope: vi.fn(), selectedUserId: '', setSelectedUserId: vi.fn(),
  period: '30d', setPeriod: vi.fn(), from: '2026-09-01T00:00:00.000Z', to: '2026-09-30T00:00:00.000Z',
  endpoint: '/api/usage', scopeParams: new URLSearchParams(), users: [] }
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

describe('Observatory screens', () => {
  it('shows the graphical operational overview from transport attempts', async () => {
    scope.current = base
    const fetcher = vi.fn(async (input: string) => {
      const url = new URL(input, 'http://localhost')
      if (url.searchParams.get('view') === 'summary') return Response.json(totals)
      if (url.searchParams.get('groupBy') === 'day') return Response.json({ groups: [{ name: '2026-09-29', ...totals }] })
      return Response.json({ groups: [{ name: 'web', ...totals }] })
    })
    vi.stubGlobal('fetch', fetcher)
    render(<ObservatoryDashboard view="overview" />)
    expect(await screen.findByText('Call activity · UTC')).toBeTruthy()
    expect(screen.getByRole('img', { name: /Provider calls and successful calls over time/ })).toBeTruthy()
    expect(screen.getByText('50%')).toBeTruthy()
    expect(screen.getByText('1 customer call · 1 validation check')).toBeTruthy()
    expect(fetcher.mock.calls.every(([url]) => String(url).startsWith('/api/usage?'))).toBe(true)
  })

  it('shows partial consumption, safe conversation text, and call evidence', async () => {
    scope.current = base
    vi.stubGlobal('fetch', vi.fn(async (input: string) => {
      const url = new URL(input, 'http://localhost')
      switch (url.searchParams.get('view')) {
        case 'summary': return Response.json(totals)
        case 'conversations': return Response.json({ conversations: [{ key: 'conversation-1', conversation_id: 'conversation-1',
          user_id: 'alice', channel: 'web', purpose: 'customer', model: 'model', first_at: '2026-09-29T10:00:00Z',
          last_at: '2026-09-29T10:00:01Z', turns: 1, attempts: 2, success: 1, incomplete_usage: 1,
          unpriced: 1, input_tokens: '100', output_tokens: '10', known_cost_usd: '0.0004', snippet: 'A real user question' }], nextCursor: null })
        case 'trace': return Response.json({ events: [{ id: 'attempt-1', turn_id: 'turn-1', operation_id: 'op-1',
          parent_operation_id: null, channel: 'web', purpose: 'customer', provider: 'openai', model: 'model',
          role: 'planner', status: 'success', aggregation: 'transport', evidence: 'metered',
          started_at: '2026-09-29T10:00:00Z', finished_at: '2026-09-29T10:00:01Z',
          usage: { input: 100, output: 10, source: 'provider_reported' }, computed_cost_usd: '0.0004',
          pricing_status: 'priced', provider_request_id: 'request-1', pricing_snapshot: { id: 'rate-1' } }] })
        default: return Response.json({})
      }
    }))
    render(<ObservatoryDashboard view="consumption" />)
    expect(await screen.findByText('A real user question')).toBeTruthy()
    expect(screen.getByText(/Totals include only reported tokens/)).toBeTruthy()
    expect(screen.getByText('Historical estimates')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: /See questions and calls/ }))
    await waitFor(() => expect(screen.getByText('openai · model · planner · success')).toBeTruthy())
    expect(screen.getByText('Question 1 · 1 model call')).toBeTruthy()
  })

  it('distinguishes an empty period from a failed data source', async () => {
    scope.current = base
    vi.stubGlobal('fetch', vi.fn(async (input: string) => {
      const url = new URL(input, 'http://localhost')
      return Response.json(url.searchParams.get('view') === 'summary' ? { ...totals, transport_attempts: 0, legacy_records: 0 } : { groups: [] })
    }))
    const rendered = render(<ObservatoryDashboard view="overview" />)
    expect(await screen.findByText('No AI activity in this period')).toBeTruthy()
    rendered.unmount()
    vi.stubGlobal('fetch', vi.fn(async () => new Response(null, { status: 503 })))
    render(<ObservatoryDashboard view="overview" />)
    expect(await screen.findByRole('alert')).toHaveProperty('textContent', expect.stringContaining('Activity could not be loaded'))
    expect(screen.getByRole('button', { name: 'Try again' })).toBeTruthy()
  })
})
