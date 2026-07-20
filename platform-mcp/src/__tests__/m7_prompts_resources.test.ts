/**
 * M7 — Prompts + Resources registration tests.
 *
 * Tests that:
 *   - registerPrompts() correctly calls server.prompt() for all 3 guided-reading prompts
 *   - registerResources() correctly calls server.resource() / server.resource template for all 10 resources
 *   - The 3 prompts (orient_chart, assess_domain, find_active_yogas) are wired
 *   - Prompts return the expected message shape
 *   - Resources include the chart-context resource (M7.1) and chart catalog resource (M2/M7)
 *
 * Chart-agnostic: uses a synthetic UUID for chart_id — no native chart_id or name.
 * Vitest — not jest.
 */

import { describe, it, expect, vi } from 'vitest'
import { registerPrompts } from '../prompts/index.js'
import { registerResources } from '../resources/index.js'
import type { Principal } from '../types.js'

// ── Synthetic test fixture ────────────────────────────────────────────────────

const SYNTHETIC_CHART_ID = 'cccccccc-0000-0000-0000-000000000099'

function makePrincipal(overrides: Partial<Principal> = {}): Principal {
  return {
    user_uid: 'user-m7-test',
    key_id: 'mcp_test_m7abc001',
    role: 'guest',
    ...overrides,
  }
}

// ── Mock McpServer ─────────────────────────────────────────────────────────────

/**
 * Minimal McpServer mock that tracks registrations.
 * Uses vitest's vi.fn() — no jest.
 */
function makeMockServer() {
  const registeredPrompts: Array<{ name: string; description: string }> = []
  const registeredResources: Array<{ uri: string | RegExp }> = []

  const server = {
    prompt: vi.fn((name: string, description: string, _schema: unknown, _cb: unknown) => {
      registeredPrompts.push({ name, description })
    }),
    resource: vi.fn((uriOrTemplate: string | { uriTemplate: string }, _descOrMeta: unknown, _cb?: unknown) => {
      const uri = typeof uriOrTemplate === 'string'
        ? uriOrTemplate
        : uriOrTemplate.uriTemplate
      registeredResources.push({ uri })
    }),
    _registeredPrompts: registeredPrompts,
    _registeredResources: registeredResources,
  }
  return server
}

// ── M7.2 Prompts tests ────────────────────────────────────────────────────────

describe('M7.2 — registerPrompts() exposes all 3 guided-reading prompts', () => {
  it('calls server.prompt() for orient_chart', () => {
    const server = makeMockServer()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerPrompts(server as any, makePrincipal())
    const names = server._registeredPrompts.map(p => p.name)
    expect(names).toContain('orient_chart')
  })

  it('calls server.prompt() for assess_domain', () => {
    const server = makeMockServer()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerPrompts(server as any, makePrincipal())
    const names = server._registeredPrompts.map(p => p.name)
    expect(names).toContain('assess_domain')
  })

  it('calls server.prompt() for find_active_yogas', () => {
    const server = makeMockServer()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerPrompts(server as any, makePrincipal())
    const names = server._registeredPrompts.map(p => p.name)
    expect(names).toContain('find_active_yogas')
  })

  it('registers exactly 5 prompts (3 R5 + demand_side_chase WP-1.6 + vidhi_plan D-2 V-2)', () => {
    const server = makeMockServer()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerPrompts(server as any, makePrincipal())
    expect(server._registeredPrompts).toHaveLength(5)
  })

  it('server.prompt() is called 5 times', () => {
    const server = makeMockServer()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerPrompts(server as any, makePrincipal())
    expect(server.prompt).toHaveBeenCalledTimes(5)
  })

  it('registers the WP-1.6 demand_side_chase prompt', () => {
    const server = makeMockServer()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerPrompts(server as any, makePrincipal())
    const names = server._registeredPrompts.map(p => p.name)
    expect(names).toContain('demand_side_chase')
  })

  it('orient_chart description mentions B.11 Whole-Chart-Read', () => {
    const server = makeMockServer()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerPrompts(server as any, makePrincipal())
    const p = server._registeredPrompts.find(p => p.name === 'orient_chart')
    expect(p?.description).toContain('B.11')
  })

  it('assess_domain description mentions domain', () => {
    const server = makeMockServer()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerPrompts(server as any, makePrincipal())
    const p = server._registeredPrompts.find(p => p.name === 'assess_domain')
    expect(p?.description?.toLowerCase()).toContain('domain')
  })

  it('find_active_yogas description mentions yoga', () => {
    const server = makeMockServer()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerPrompts(server as any, makePrincipal())
    const p = server._registeredPrompts.find(p => p.name === 'find_active_yogas')
    expect(p?.description?.toLowerCase()).toContain('yoga')
  })
})

// ── M7.2 Prompt callback shape ────────────────────────────────────────────────

describe('M7.2 — orient_chart prompt callback returns correct message shape', () => {
  it('callback returns messages array with role=user', async () => {
    let capturedCallback: ((args: Record<string, unknown>) => Promise<unknown>) | null = null
    const server = {
      prompt: vi.fn((_name: string, _desc: string, _schema: unknown, cb: (args: Record<string, unknown>) => Promise<unknown>) => {
        if (_name === 'orient_chart') capturedCallback = cb
      }),
      resource: vi.fn(),
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerPrompts(server as any, makePrincipal())

    expect(capturedCallback).not.toBeNull()
    const result = await capturedCallback!({ chart_id: SYNTHETIC_CHART_ID }) as { messages: Array<{ role: string; content: { type: string; text: string } }> }
    expect(Array.isArray(result.messages)).toBe(true)
    expect(result.messages[0].role).toBe('user')
    expect(result.messages[0].content.type).toBe('text')
    expect(typeof result.messages[0].content.text).toBe('string')
  })

  it('orient_chart prompt text includes the chart_id', async () => {
    let capturedCallback: ((args: Record<string, unknown>) => Promise<unknown>) | null = null
    const server = {
      prompt: vi.fn((_name: string, _desc: string, _schema: unknown, cb: (args: Record<string, unknown>) => Promise<unknown>) => {
        if (_name === 'orient_chart') capturedCallback = cb
      }),
      resource: vi.fn(),
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerPrompts(server as any, makePrincipal())

    const result = await capturedCallback!({ chart_id: SYNTHETIC_CHART_ID }) as { messages: Array<{ content: { text: string } }> }
    expect(result.messages[0].content.text).toContain(SYNTHETIC_CHART_ID)
  })
})

// ── M7.1 Resources tests ──────────────────────────────────────────────────────

describe('M7.1 — registerResources() exposes resources', () => {
  it('calls server.resource() at least once', () => {
    const server = makeMockServer()
    const principal = makePrincipal()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerResources(server as any, principal)
    expect(server.resource).toHaveBeenCalled()
  })

  it('registers at least 9 resources (core 5 + multi-chart + 4 enrichments)', () => {
    const server = makeMockServer()
    const principal = makePrincipal()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerResources(server as any, principal)
    // registerResources calls server.resource (fixed URIs) and may use ResourceTemplate
    // for dynamic ones. Total calls >= 9.
    expect(server.resource.mock.calls.length).toBeGreaterThanOrEqual(9)
  })
})
